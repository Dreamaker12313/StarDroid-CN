#!/usr/bin/env python3
"""Build both Android ABIs and record proof tied to unchanged source inputs.

Run after the native sources are frozen. --skip-prepare reuses an already
prepared tree; its complete contents are still checked before and after builds.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
ABIS = ("arm64-v8a", "x86_64")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch_order():
    # The prepare script declares the ordered patch stack as literal filenames.
    names = re.findall(r"['\"]([^'\"]+\.patch)['\"]",
                       (ROOT / "scripts/prepare_native.py").read_text())
    return list(dict.fromkeys(Path(name).name for name in names))


def source_hashes():
    paths = list((ROOT / "native").rglob("*.h"))
    paths += list((ROOT / "native").rglob("*.cpp"))
    paths += [ROOT / "patches" / name for name in patch_order()]
    paths += [ROOT / name for name in (
        "scripts/prepare_native.py", "scripts/prepare_presentation.py",
        "scripts/prepare_feedback.py", "scripts/build_native_engine.py",
        "tests/run_native_build82.py", "UPSTREAM.json", "CAMPAIGN-BUILD.json",
        "vendor/libsmacker/smacker.c", "vendor/libsmacker/smacker.h",
    )]
    upstream = json.loads((ROOT / "UPSTREAM.json").read_text())
    archive = ROOT / upstream["source_archive"]["file"]
    if digest(archive) != upstream["source_archive"]["sha256"]:
        raise RuntimeError("Pinned engine archive checksum mismatch")
    paths.append(archive)
    return {str(path.relative_to(ROOT)): digest(path) for path in sorted(set(paths))}


def prepared_hashes():
    stage = ROOT / "native-engine"
    if not (stage / "bwgame.h").is_file():
        raise RuntimeError("Native engine has not been prepared")
    return {str(path.relative_to(stage)): digest(path)
            for path in sorted(stage.rglob("*")) if path.is_file()}


def tree_digest(entries):
    return hashlib.sha256(json.dumps(entries, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def changed(before, after):
    return sorted(name for name in before.keys() | after.keys()
                  if before.get(name) != after.get(name))


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.pending")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-prepare", action="store_true")
    parser.add_argument("--jobs", type=int, choices=(1, 2), default=2,
                        help="Concurrent ABI builds; use 1 on memory-limited hosts")
    args = parser.parse_args()
    out = ROOT / "build-native/native-build82"
    out.mkdir(parents=True, exist_ok=True)
    report_path = ROOT / "validation/native-build82.json"
    report = {"passed": False, "version": "1.0.12", "versionCode": 82,
              "nativeEngineRebuilt": False, "ndk": "r27d", "api": 26,
              "abis": list(ABIS), "parallelJobs": args.jobs,
              "preparedThisRun": not args.skip_prepare,
              "startedUtc": datetime.now(timezone.utc).isoformat()}
    write_report(report_path, report)
    started = time.monotonic()
    try:
        if not args.skip_prepare:
            with (out / "prepare.log").open("w") as log:
                subprocess.run([sys.executable, "scripts/prepare_native.py"],
                               cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        before = source_hashes()
        prepared_before = prepared_hashes()
        report["sourceSha256"] = before
        report["orderedPatches"] = patch_order()
        report["preparedTreeSha256"] = tree_digest(prepared_before)
        report["preparedFiles"] = len(prepared_before)
        tools = Path(os.environ.get("STARDROID_ANDROID_TOOLS",
                     os.environ.get("OPENBW_ANDROID_TOOLS", ROOT / ".tools")))
        ndk = tools / "android-ndk-r27d"
        report["ndkProperties"] = (ndk / "source.properties").read_text().strip()
        compiler = ndk / "toolchains/llvm/prebuilt/linux-x86_64/bin/clang++"
        report["compilerVersion"] = subprocess.check_output(
            [str(compiler), "--version"], text=True).strip()

        def compile_abi(abi):
            log_path = out / (abi + ".log")
            command = [sys.executable, "scripts/build_native_engine.py", abi,
                       "--skip-prepare"]
            begin = time.monotonic()
            with log_path.open("w") as log:
                process = subprocess.run(command, cwd=ROOT, stdout=log,
                                         stderr=subprocess.STDOUT)
            return {"abi": abi, "exitCode": process.returncode,
                    "elapsedSeconds": round(time.monotonic() - begin, 2),
                    "log": str(log_path.relative_to(ROOT)),
                    "command": command}

        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            report["builds"] = list(pool.map(compile_abi, ABIS))
        # Both subprocesses have exited before any success can be recorded.
        changes = changed(before, source_hashes())
        prepared_changes = changed(prepared_before, prepared_hashes())
        report["changedSourceInputs"] = changes
        report["changedPreparedInputs"] = prepared_changes
        if any(build["exitCode"] for build in report["builds"]):
            raise RuntimeError("An ABI compilation failed; see per-ABI logs")
        if changes or prepared_changes:
            raise RuntimeError("Build inputs changed during compilation; rebuild after freezing sources")
        report["librarySha256"] = {
            abi + "/" + name: digest(ROOT / "native-libs" / abi / name)
            for abi in ABIS for name in ("libopenbw.so", "libsmacker.so")
        }
        report["nativeEngineRebuilt"] = True
        report["passed"] = True
    except Exception as error:
        report["error"] = str(error)
    report["elapsedSeconds"] = round(time.monotonic() - started, 2)
    report["finishedUtc"] = datetime.now(timezone.utc).isoformat()
    write_report(report_path, report)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate local supply override, training and morph limits against owned data.
Usage: python3 tests/run_supply81.py CORE_DIR STARCRAFT_MPQ [--skip-prepare]
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('core_dir',type=Path);p.add_argument('starcraft_mpq',type=Path);p.add_argument('--skip-prepare',action='store_true');a=p.parse_args()
if not a.skip_prepare:subprocess.run([sys.executable,str(r/'scripts/prepare_native.py')],cwd=r,check=True)
files=['patches/native-supply81.patch','patches/native-controls80.patch','scripts/prepare_native.py','tests/build_native_host.py','native/runtime.cpp','native/save_state.h','native/generated/wasm_main.cpp','native/generated/wasm_backend.cpp','tests/native_controls80.cpp','tests/native_supply81.cpp','tests/run_supply81.py']
if (r/'native/replay.h').exists():files.append('native/replay.h')
def fingerprints():return {f:hashlib.sha256((r/f).read_bytes()).hexdigest() for f in files}
before=fingerprints()
subprocess.run([sys.executable,str(r/'tests/build_native_host.py'),'supply81','--fast','--skip-prepare'],cwd=r,check=True)
result=subprocess.run([str(r/'build-native/host/native-supply81'),str(a.core_dir.resolve()),str(a.starcraft_mpq.resolve())],cwd=r,capture_output=True,text=True)
print(result.stdout,end='');print(result.stderr,file=sys.stderr,end='');result.check_returncode()
assert before==fingerprints(),'Sources changed during validation; rerun after integration.'
(r/'validation/supply-v81.json').write_text(json.dumps(dict(passed=True,physicalAndroid=False,originalArchivesTested=True,checks=[line for line in result.stdout.splitlines() if line.startswith('PASS ')],sourceSha256=before),indent=2)+'\n')

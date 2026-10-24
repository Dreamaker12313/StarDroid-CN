#!/usr/bin/env python3
"""Run focused 0.40 checks against external, user-owned original game data."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('data', type=Path)
p.add_argument('emperor_map', type=Path)
p.add_argument('--output', type=Path, default=ROOT/'validation/native-revision40-host-v40.json')
args = p.parse_args()
exe = ROOT/'build-native/host/native-revision40'
weave = ROOT/'app/src/main/assets/native/weave.scx'
out = ROOT/'build-native/revision40-release'
out.mkdir(parents=True, exist_ok=True)
cases = [
    ('mission', args.emperor_map.resolve(), '6,000 opening frames: all five original reinforcement buildings are airborne and transfer to the player in the southwest; computer tanks siege; exact save/240-frame continuation.'),
    ('traps', weave, 'All six trap types remain invisible for 90 frames on revealed terrain; framebuffer pixels match fully hidden artwork with map reveal; actual proximity opens them and their weapons damage a passive, disabled test target.'),
    ('viewport', weave, 'Actual render/camera-bottom checks at 640x480, 1280x960, 960x480 and 427x320; viewport ends at logical y=376.'),
    ('skirmish', weave, '60,000 frames of original TLOx script with ordinary 50 minerals/zero gas: mining, gas, Barracks/Factory/Starport/Machine Shop, at least five attack waves, real combat and exact save/240-frame continuation after both same-instance and fresh-game initialization. Passive human units are healed each frame to keep the fixture alive; the AI receives no resource assistance.'),
]

def run(case):
    mode, map_path, scope = case
    try:
        r = subprocess.run([str(exe), str(args.data.resolve()), str(map_path), mode], capture_output=True, text=True, timeout=240)
        log = r.stdout+r.stderr
        passed = r.returncode == 0 and any(line.startswith('PASS ') for line in log.splitlines())
        result = dict(name=mode, passed=passed, exitCode=r.returncode, scope=scope, log=log)
    except subprocess.TimeoutExpired:
        result = dict(name=mode, passed=False, scope=scope, error='Timed out after 240 seconds')
    (out/(mode+'.json')).write_text(json.dumps(result, indent=2)+'\n')
    print(('PASS ' if result['passed'] else 'FAIL ')+mode, flush=True)
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(run, cases))
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
sources = [
    'tests/native_revision40.cpp', 'tests/run_revision40.py', 'tests/build_native_host.py',
    'native/runtime.cpp', 'native/save_state.h', 'scripts/prepare_native.py',
    'scripts/prepare_feedback.py', 'scripts/prepare_presentation.py', 'UPSTREAM.json',
    'app/src/main/assets/native/weave.scx',
] + [str(f.relative_to(ROOT)) for f in sorted((ROOT/'patches').glob('*.patch'))]
report = dict(version='0.40', passed=all(r['passed'] for r in results),
              originalCoreAssets=True, fullPlaythrough=False, cases=results,
              binarySha256=sha(exe), sourceSha256={name:sha(ROOT/name) for name in sources},
              coreDataSha256={name:sha(args.data/name) for name in ('STARDAT.MPQ','BROODAT.MPQ','patch_rt.mpq')},
              emperorMapSha256=sha(args.emperor_map))
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2)+'\n')
raise SystemExit(0 if report['passed'] else 1)

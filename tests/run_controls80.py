#!/usr/bin/env python3
"""Exercise worker cancellation and local invincibility using original game data.

python3 tests/run_controls80.py CORE_DIR STARCRAFT_MPQ [--skip-build]
CORE_DIR must contain STARDAT.MPQ, BROODAT.MPQ and patch_rt.mpq.
No game data is distributed or downloaded by this test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('core_dir', type=Path)
p.add_argument('starcraft_mpq', type=Path)
p.add_argument('--skip-build', action='store_true')
a = p.parse_args()
if not a.skip_build:
    subprocess.run([sys.executable, str(root/'tests/build_native_host.py'), 'controls80', '--fast'], cwd=root, check=True)
result = subprocess.run([str(root/'build-native/host/native-controls80'), str(a.core_dir.resolve()), str(a.starcraft_mpq.resolve())], cwd=root, text=True, capture_output=True)
print(result.stdout, end='')
print(result.stderr, file=sys.stderr, end='')
result.check_returncode()
files = ['patches/native-controls80.patch', 'native/runtime.cpp', 'tests/native_controls80.cpp', 'tests/run_controls80.py']
report = {
    'passed': True,
    'physicalAndroid': False,
    'originalArchivesTested': True,
    'checks': [line for line in result.stdout.splitlines() if line.startswith('PASS ')],
    'limitations': ['Controlled original-map host regressions, not a device test or full mission playthrough.', 'Invincibility is session-only; saved games and new matches start with it disabled.', 'Scripted kills, unit consumption/morphs and spell disables retain normal behavior.'],
    'sourceSha256': {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
}
(root/'validation/controls-v80.json').write_text(json.dumps(report, indent=2)+'\n')

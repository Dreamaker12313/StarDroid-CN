#!/usr/bin/env python3
"""Re-run the existing seek/parity scenarios against integrated 1.1 fixes.

Keeps the historical build-82 report intact. Original archives remain external.
"""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build-native/replay-campaign11'
OUT.mkdir(parents=True, exist_ok=True)
REPORT = ROOT / 'validation/replay-campaign11.json'

def inputs():
    paths = list((ROOT / 'native').rglob('*.h')) + list((ROOT / 'native').rglob('*.cpp'))
    paths += list((ROOT / 'native-engine').rglob('*.h'))
    paths += [ROOT / name for name in ('tests/native_replay82.cpp', 'tests/native_replay81.cpp',
              'tests/build_native_host.py', 'tests/run_replay_campaign11.py', 'scripts/prepare_native.py')]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}

before = inputs()
subprocess.run(['python3', 'tests/build_native_host.py', 'replay82', '--skip-prepare'], cwd=ROOT, check=True)
with (OUT / 'native.log').open('w') as log:
    subprocess.run([str(ROOT / 'build-native/host/native-replay82'),
                    str(ROOT / 'build-native/reign79/core'),
                    str(ROOT / 'app/src/main/assets/native/weave.scx'), str(OUT / 'replay-frame.ppm')],
                   cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=420)
lines = (OUT / 'native.log').read_text().splitlines()
assert any('checks in 3 replay seek scenarios' in line for line in lines), 'Incomplete seek test'
assert inputs() == before, 'Sources changed during tests; rerun after native freeze'
report = {'passed': True, 'appVersion': '1.1', 'simulationRules': 84,
          'scope': 'Existing real-command custom AI, team/hero AI and human replay scenarios; linear/seek parity and checkpoint restoration on a host.',
          'physicalAndroid': False, 'fullCampaignPlaythroughs': False,
          'results': [line for line in lines if line.startswith('PASS')], 'sourceSha256': before}
REPORT.write_text(json.dumps(report, indent=2) + '\n')
print('\n'.join(report['results']))

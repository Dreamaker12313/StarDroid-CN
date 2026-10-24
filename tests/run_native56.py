#!/usr/bin/env python3
"""Run real-engine 0.56 behavior tests; keep imported game files external."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
data = Path(sys.argv[1]).resolve()
out = root / 'build-native/native56'
out.mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, str(root / 'tests/create_room_map55.py')], cwd=root, check=True)
exe = root / 'build-native/host/native-revision56'

def run(case):
    name, mode, args = case
    game_map = root / ('app/src/main/assets/native/weave.scx' if mode == 'macro' else 'build-native/probe55/eight-starts.scx')
    result = subprocess.run([str(exe), str(data), str(game_map), mode, *map(str, args)],
                            cwd=root, capture_output=True, text=True)
    log = result.stdout + result.stderr
    (out / (name + '.log')).write_text(log)
    if result.returncode:
        print(log, flush=True)
        result.check_returncode()
    print(name + ': ' + next(line for line in reversed(log.splitlines()) if line.startswith('PASS ')), flush=True)
    record = {'case': name, 'passed': True, 'output': log}
    if mode == 'macro':
        m = re.search(r'MACRO race=(\d+) level=(\d+) bases=(\d+) upgrades=(\d+) attacks=(\d+) types=([\d,]+)', log)
        record.update(dict(zip(['race', 'difficulty', 'bases', 'upgrades', 'attacks'], map(int, m.groups()[:5]))))
        record['completedUnitTypes'] = [int(n) for n in m[6].split(',') if n]
        record['broodWar'] = bool(args[3])
        record['frames'] = 60000
        record['saveContinuationFrames'] = 48
    return record

cases = [(name, name, []) for name in ['victory', 'cargo', 'detection', 'sound']]
cases += [(f'macro-{bw}-{race}-{difficulty}', 'macro', [race, 60000, difficulty, bw])
          for bw in [0, 1] for difficulty in range(3) for race in range(3)]
with ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(run, cases))

sources = [root / path for path in [
    'tests/native_revision56.cpp', 'tests/native_revision55.cpp', 'tests/create_room_map55.py',
    'native/audio.h', 'native/runtime.cpp', 'native/multiplayer.h', 'native/save_state.h',
    'patches/native-polish56.patch', 'scripts/prepare_native.py',
]] + [Path(__file__)]
report = {'passed': True, 'physicalDevices': False, 'victoryCases': 48, 'cases': results,
          'limitations': 'Bounded deterministic scenarios, not every map or a complete campaign playthrough. Macro tests retain the human opponent to observe 60000 frames; the AI uses normal starting resources and costs.',
          'sourceSha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
(root / 'validation/native-v56.json').write_text(json.dumps(report, indent=2) + '\n')

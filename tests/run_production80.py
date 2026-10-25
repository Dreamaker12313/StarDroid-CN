#!/usr/bin/env python3
"""Run actual AI production regressions with caller-supplied original archives."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('core_dir', type=Path)
parser.add_argument('broodwar_mpq', type=Path)
parser.add_argument('--map', type=Path, default=ROOT/'app/src/main/assets/native/weave.scx')
parser.add_argument('--skip-build', action='store_true')
args = parser.parse_args()
core = args.core_dir.resolve()
broodwar = args.broodwar_mpq.resolve()
map_path = args.map.resolve()
for path in [core/'STARDAT.MPQ', core/'BROODAT.MPQ', core/'patch_rt.mpq', broodwar, map_path]:
    if not path.is_file():
        parser.error(f'Missing input: {path}')
output = ROOT/'build-native/production80'
output.mkdir(parents=True, exist_ok=True)
binary = ROOT/'build-native/host/native-production80'
report_path = ROOT/'validation/ai-production-final80.json'
baseline_path = ROOT/'validation/ai-production-v80.json'
report = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}
report.pop('stagedSourceHashes', None)
report.pop('sourceHashes', None)
report.update(version=80, topic='AI Carrier production and fighter ammunition', passed=False,
              generatedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              scope='Current integrated native source; original-data host simulation. Not Android-device testing or a campaign playthrough.')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(name, command):
    path = output/(name+'.log')
    print('Running '+name, flush=True)
    with path.open('w') as stream:
        result = subprocess.run([str(value) for value in command], cwd=ROOT,
                                stdout=stream, stderr=subprocess.STDOUT)
    text = path.read_text()
    if result.returncode:
        print(text[-12000:], file=sys.stderr)
        raise RuntimeError(f'{name} failed ({result.returncode}); see {path}')
    return text

try:
    # The caller prepares the ordered patch stack once. Do not modify shared
    # native inputs while Android ABI builds may be running alongside this test.
    if not args.skip_build:
        run('build', [sys.executable, ROOT/'tests/build_native_host.py', 'production80', '--skip-prepare'])
    controlled = run('controlled', [binary, core, broodwar])
    natural = run('natural-melee', [binary, core, 'melee', map_path])
    if sum(line.startswith('PASS ') for line in controlled.splitlines()) != 13:
        raise RuntimeError('Incomplete controlled regression output')
    if 'PASS natural hard Protoss melee economy' not in natural:
        raise RuntimeError('Natural melee test did not complete')
    tracked = ['patches/native-ai-production80.patch', 'patches/native-controls80.patch',
               'tests/native_production80.cpp', 'tests/native_abilities79.cpp',
               'tests/run_production80.py', 'native/runtime.cpp',
               'native/generated/wasm_main.cpp', 'native/generated/wasm_backend.cpp',
               'scripts/prepare_native.py']
    report['sourceSha256'] = {name: sha(ROOT/name) for name in tracked}
    report['integratedEngineHashes'] = {name: sha(ROOT/'native-engine'/name) for name in
                                       ['web/campaign_ai.h', 'web/sandbox.h', 'bwgame.h', 'actions.h']}
    report['controlledRegressions'] = controlled.splitlines()
    report['naturalMelee'] = natural.splitlines()
    first = {}
    names = {'72':'Carrier', '73':'Interceptor', '83':'Reaver', '85':'Scarab'}
    for line in natural.splitlines():
        if line.startswith('MELEE first completed type='):
            parts = line.split()
            first[names[parts[-2].split('=')[1]]] = int(parts[-1].split('=')[1])
    report['naturalMeleeSetup'] = {'map':map_path.name, 'mapSha256':sha(map_path),
        'difficulty':'Hard', 'startingMinerals':50, 'startingGas':0,
        'resourceBoost':False, 'opponentKeptAlive':True, 'firstCompletedFrame':first}
    report['data'] = {path.name:{'bytes':path.stat().st_size, 'sha256':sha(path)}
                      for path in [core/'STARDAT.MPQ', core/'BROODAT.MPQ', core/'patch_rt.mpq', broodwar]}
    report['commands'] = ['python3 scripts/prepare_native.py',
        'python3 tests/run_production80.py CORE_DIR BROODWAR_MPQ']
    report['limitations'] = ['Controlled campaign fixtures remove original triggers and units from Reign of Fire terrain.',
        'One natural-economy skirmish map/difficulty sampled.', 'No original-executable frame-parity comparison.']
    report['passed'] = True
finally:
    report_path.write_text(json.dumps(report, indent=2)+'\n')
print('PASS 13 controlled groups and natural-economy melee production; '+str(report_path))

#!/usr/bin/env python3
"""Exercise upgrade cards, actual research and unchanged gameplay on original data."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib, json, subprocess, sys

r = Path(__file__).resolve().parents[1]
data = Path(sys.argv[1]).resolve()
out = r/'build-native/upgrades65'
out.mkdir(exist_ok=True)
exe = r/'build-native/host/native-upgrades'
mp = r/'build-native/probe55/eight-starts.scx'
cases = [(f'upgrades-{bw}-{mode}-{hero}', ['matrix', str(bw), str(mode), str(hero)])
         for bw in range(2) for mode in range(5) for hero in range(2)]
cases += [(name, [name]) for name in ['power','heroes','merge','teams','legacy','victory','cargo','detection','addons','sound']]

def run(case):
    name, args = case
    if name == 'upgrades-1-0-0': args = args + [str(out)]
    p = subprocess.run([str(exe),str(data),str(mp),*args], cwd=r, capture_output=True, text=True)
    log = p.stdout+p.stderr
    (out/(name+'.log')).write_text(log)
    print(name+': '+(next((line for line in reversed(log.splitlines()) if line.startswith('PASS ')), 'FAILED\n'+log) if p.returncode == 0 else 'FAILED\n'+log), flush=True)
    return {'case':name,'passed':p.returncode == 0,'output':log}

with ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(run,cases))

# A fresh reconstruction without this UI patch establishes unchanged simulation inputs.
before = json.loads((r/'tests/fixtures/upgrades1-engine-baseline.json').read_text())
after = {str(p.relative_to(r/'native-engine')):hashlib.sha256(p.read_bytes()).hexdigest()
         for p in (r/'native-engine').rglob('*') if p.is_file()}
changed = [p for p in sorted(set(before)|set(after)) if before.get(p) != after.get(p)]
assert changed == ['web/sandbox.h'], changed
files = ['tests/native_upgrades.cpp','tests/native_revision58.cpp','tests/native_revision57.cpp',
         'tests/native_revision56.cpp','tests/native_revision55.cpp','tests/run_upgrades.py',
         'tests/build_native_host.py','tests/create_room_map55.py','tests/fixtures/upgrades1-engine-baseline.json','scripts/prepare_native.py',
         'patches/native-upgrades1.patch','native/runtime.cpp','native/hero_mode.h',
         'native/audio.h','native/save_state.h','native/multiplayer.h']
files += [str(p.relative_to(r)) for p in sorted((r/'patches').glob('*.patch')) if str(p.relative_to(r)) not in files]
report = {'passed':all(x['passed'] for x in results),'physicalDevices':False,
          'cases':results,'changedPreparedEngineFiles':changed,
          'simulationInputsUnchanged':True,
          'simulationInputSha256':{n:after[n] for n in ['bwgame.h','actions.h','game_types.h','data_types.h','web/campaign_ai.h']},
          'limitations':'Host engine and original data. Research is started via command-card packets with normal costs and duration; its timer is shortened before exercising normal completion. Covers 16 three-level upgrade lines and both Spire producers, original/BW, Melee/FFA/teams, multiplayer and Hero Mode on/off. Gameplay/AI implementation is unchanged. Physical Android input, sound, radio and performance remain untested.',
          'sourceSha256':{n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in files}}
(r/'validation/native-upgrades-v1.0.json').write_text(json.dumps(report,indent=2)+'\n')
sys.exit(0 if report['passed'] else 1)

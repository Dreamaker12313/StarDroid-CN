#!/usr/bin/env python3
"""Exercise original campaign branches with documented diagnostic interventions."""
import argparse, concurrent.futures, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data',type=Path);p.add_argument('maps',type=Path)
args=p.parse_args()
cases=[('zerg04',104,'chrysalis'),('expzerg05',505,'true-colors'),
       ('expterran04',404,'physics-lab'),('expterran04',404,'nuclear-silo'),
       ('expzerg03',503,'kelmorian'),('expprotoss06',306,'khalis'),
       ('expterran07',407,'duran'),('protoss10',210,'finale')]
out=ROOT/'build-native/campaign-branches-v38';out.mkdir(exist_ok=True)
exe=ROOT/'build-native/host/native-campaigns'
def run(case):
    mission,code,name=case;path=out/(name+'.json')
    result=subprocess.run([str(exe),str(args.data),str(args.maps/(mission+'.mpq')),
        str(code),'4800',str(path),'-',name],capture_output=True,text=True,timeout=180)
    (out/(name+'.log')).write_text(result.stdout+result.stderr)
    report=json.loads(path.read_text()) if result.returncode==0 else {'passed':False,'error':result.stderr[-4000:]}
    report.update(mission=mission,case=name,exitCode=result.returncode)
    print(('PASS ' if report['passed'] else 'FAIL ')+name,flush=True)
    return report
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,cases))
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
sources=['tests/native_campaigns.cpp','tests/native_campaign_cases.h','tests/native_objective_attempts.h','tests/native_mission_routes38.h','tests/run_campaign_branches.py',
         'native/runtime.cpp','native/save_state.h','scripts/prepare_native.py',
         'scripts/prepare_feedback.py','scripts/prepare_presentation.py','UPSTREAM.json']
sources += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'patches').glob('*.patch'))]
report=dict(version='0.38',passed=all(r['passed'] for r in results),originalCoreAssets=True,
    originalMaps=True,fullPlaythrough=False,scope='Original trigger outcomes with diagnostic actions documented in native_campaign_cases.h. Duran entrance runs without intervention. Other cases advance timers, remove branch targets, grant minerals, move the objective Probe or preserve player HP. The finale grants minerals, protects Gantrithor, moves it into anti-air combat, replaces destroyed Interceptors, clears defenders near the Overmind and then attacks the original Overmind through its victory sequence.',
    coreDataSha256={n:sha(args.data/n) for n in ('STARDAT.MPQ','BROODAT.MPQ','patch_rt.mpq')},
    sourceSha256={n:sha(ROOT/n) for n in sources},binarySha256=sha(exe),cases=results)
(ROOT/'validation/native-campaign-branches-v38.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['passed'] else 1)

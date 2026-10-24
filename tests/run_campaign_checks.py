#!/usr/bin/env python3
"""Run real-data mission startup and exact save/restore continuation checks.

Inputs are external user-owned game archives and sparse mission MPQs. No game
data is copied into the source distribution. Unattended missions may end in
defeat; this suite records outcomes rather than claiming completed campaigns.
"""
import argparse, concurrent.futures, hashlib, json, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data',type=Path)
p.add_argument('maps',type=Path)
p.add_argument('--frames',type=int,default=2400)
p.add_argument('--missions',nargs='*')
p.add_argument('--output',type=Path,default=ROOT/'validation/native-campaign-real-v40.json')
p.add_argument('--objectives',action='store_true')
p.add_argument('--workers',type=int,default=3)
args=p.parse_args()
catalog=json.loads((ROOT/'missions.json').read_text())
if args.missions:catalog=[m for m in catalog if m['id'] in args.missions]
out=ROOT/'build-native/campaign-real-v40'/args.output.stem;out.mkdir(parents=True,exist_ok=True)
exe=ROOT/'build-native/host/native-campaigns'
def run(m):
    stem=out/m['id'];start=time.monotonic()
    command=[str(exe),str(args.data),str(args.maps/(m['id']+'.mpq')),str(m['code']),str(args.frames),str(stem.with_suffix('.json'))]
    if args.objectives:command += ['-','objectives']
    try:
        result=subprocess.run(command,text=True,capture_output=True,timeout=300)
        stem.with_suffix('.log').write_text(result.stdout+result.stderr)
        report=json.loads(stem.with_suffix('.json').read_text()) if stem.with_suffix('.json').exists() else {'passed':False,'error':result.stderr[-4000:]}
        report.update(mission=m['id'],title=m['title'],exitCode=result.returncode)
        report['passed']=report['passed'] and result.returncode==0
    except subprocess.TimeoutExpired:
        report={'mission':m['id'],'passed':False,'error':'Timed out after 300 seconds'}
    print(('PASS ' if report['passed'] else 'FAIL ')+m['id']+' '+str(round(time.monotonic()-start,2))+'s',flush=True)
    return report
with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:results=list(pool.map(run,catalog))
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
sources=['tests/native_campaigns.cpp','tests/native_campaign_cases.h','tests/native_objective_attempts.h','tests/native_mission_routes38.h','tests/run_campaign_checks.py','tests/build_native_host.py','native/save_state.h','native/runtime.cpp','scripts/prepare_native.py','scripts/prepare_feedback.py','scripts/prepare_presentation.py','UPSTREAM.json']+[str(f.relative_to(ROOT)) for f in sorted((ROOT/'patches').glob('*.patch'))]
report={'version':'0.40','passed':all(r['passed'] for r in results),'originalCoreAssets':True,'originalMaps':True,'fullPlaythrough':False,'missionCount':len(results),'requestedFramesPerMission':args.frames,'continuationFrames':240,'victoryAttempts':args.objectives,'scope':('Assisted objective traversal through original triggers, with unit movement, objective enemy removal, resources, countdown advances, production-unit creation and player invulnerability/healing. No direct switch or victory edits. ' if args.objectives else '')+'Unattended native simulation, rendering, snapshot, fresh map initialization, exact snapshot round trip and continuation comparison. Outcomes are recorded separately from crash/save checks.','coreDataSha256':{name:sha(args.data/name) for name in ('STARDAT.MPQ','BROODAT.MPQ','patch_rt.mpq')},'sourceSha256':{name:sha(ROOT/name) for name in sources},'binarySha256':sha(exe),'missions':results}
args.output.write_text(json.dumps(report,indent=2)+'\n')
print('TOTAL',sum(r['passed'] for r in results),'/',len(results),flush=True)
raise SystemExit(0 if report['passed'] else 1)

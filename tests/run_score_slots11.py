#!/usr/bin/env python3
"""Check score participants against all 64 original campaign maps and save/leave paths."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
r=Path(__file__).resolve().parents[1];out=r/'build-native/score-slots11';out.mkdir(parents=True,exist_ok=True);stage=r/'native-engine'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skip-build',action='store_true');args=p.parse_args()
if not args.skip_build:
 subprocess.run(['gcc','-O2','-c',str(r/'vendor/libsmacker/smacker.c'),'-o',str(out/'smacker.o')],check=True)
 cmd=['g++','-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER']
 cmd+=['-I'+str(d)for d in(stage,stage/'ui',stage/'web')]
 cmd+=[str(r/'tests/native_score_slots11.cpp'),str(r/'native/generated/wasm_backend.cpp'),str(out/'smacker.o'),'-o',str(out/'native-test')]
 subprocess.run(cmd,check=True)
results=[];checks=0
for mission in json.loads((r/'app/src/main/assets/native/missions.json').read_text())+ [{'id':'custom-nearby','code':0,'game':'custom'}]:
 archive=r/'app/src/main/assets/native/weave.scx' if not mission['code'] else r.parent/'reign-data'/('BroodWar.mpq' if mission['game']=='broodwar' else 'StarCraft.mpq')
 fixture=out/(mission['id']+'.stats')
 run=subprocess.run([str(out/'native-test'),str(r/'build-native/reign79/core'),str(archive),str(mission['code']),str(fixture)],cwd=r,text=True,capture_output=True)
 if run.returncode:print(run.stdout+run.stderr);run.check_returncode()
 final=[s for s in run.stdout.splitlines() if s.startswith('PASS ')][-1];print(final,flush=True);checks+=int(re.search(r'PASS (\d+)',final).group(1))
 lines=fixture.read_bytes().splitlines()[1:];rows=[line.split(b'\t')for line in lines]
 results.append({'mission':mission['id'],'code':mission['code'],'result':final,'slots':[int(row[16])for row in rows],'factions':[row[19].decode('cp1252')for row in rows],'fixtureSha256':hashlib.sha256(fixture.read_bytes()).hexdigest()})
files=['patches/native-score-slots11.patch','scripts/prepare_native.py','tests/native_score_slots11.cpp','tests/run_score_slots11.py','app/src/main/assets/native/missions.json','native/save_state.h']
report={'passed':True,'version':'1.1','replayEngine':84,'physicalAndroid':False,'campaignMapCount':64,'checks':checks,'limits':['This verifies score presentation and original map metadata, not full campaign playthroughs.','Two genuine AI players with the same force name remain separate score rows.'],'results':results,'sourceSha256':{p:hashlib.sha256((r/p).read_bytes()).hexdigest()for p in files}}
(r/'validation/score-slots11.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS all 64 campaigns plus custom/Nearby;',checks,'checks')

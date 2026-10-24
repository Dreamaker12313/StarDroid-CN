#!/usr/bin/env python3
"""Run current hero, teams, retail power and economy regressions on actual data."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,subprocess,sys
r=Path(__file__).resolve().parents[1];out=r/'build-native/native58';out.mkdir(exist_ok=True)
data=Path(sys.argv[1]).resolve();exe=r/'build-native/host/native-revision58'
subprocess.run([sys.executable,str(r/'tests/create_room_map55.py')],cwd=r,check=True)
cases=[(x,x,[])for x in ['heroes','merge','teams','legacy','power','addons','sound','victory','cargo','detection']]
cases += [(f'deplete-{race}','deplete',[race])for race in range(3)]
cases += [(f'macro-{bw}-{race}-{level}','macro',[race,level,bw])for bw in range(2)for race in range(3)for level in range(3)]
def run(case):
 name,mode,args=case;mp=r/('app/src/main/assets/native/weave.scx'if mode in ['macro','deplete']else'build-native/probe55/eight-starts.scx')
 p=subprocess.run([str(exe),str(data),str(mp),mode,*map(str,args)],cwd=r,capture_output=True,text=True)
 log=p.stdout+p.stderr;(out/(name+'.log')).write_text(log)
 if p.returncode:print(name+' FAILED\n'+log,flush=True)
 else:print(name+': '+next(x for x in reversed(log.splitlines())if x.startswith('PASS ')),flush=True)
 return {'case':name,'passed':p.returncode==0,'output':log}
with ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(run,cases))
files=['tests/native_revision58.cpp','tests/native_revision57.cpp','tests/native_revision56.cpp','tests/native_revision55.cpp','tests/run_native58.py','tests/create_room_map55.py','patches/native-polish58.patch','scripts/prepare_native.py','native/runtime.cpp','native/hero_mode.h','native/audio.h','native/save_state.h','native/multiplayer.h']
report={'passed':all(x['passed']for x in results),'physicalDevices':False,'cases':results,'limitations':'Real engine and imported original data on host. Eighteen 60000-frame AI scenarios cover all races/difficulties in both expansions; three depleted-main scenarios use 30000 frames. Physical device audio, input, radio and performance still need testing. Bounded maps cannot establish every campaign or map behavior.','sourceSha256':{n:hashlib.sha256((r/n).read_bytes()).hexdigest()for n in files}}
(r/'validation/native-v58.json').write_text(json.dumps(report,indent=2)+'\n')
sys.exit(0 if report['passed'] else 1)

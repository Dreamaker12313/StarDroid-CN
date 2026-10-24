#!/usr/bin/env python3
"""Independent real-engine peers: two computers, both modes, all AI races/editions."""
from pathlib import Path
import subprocess,concurrent.futures,hashlib,json,sys
r=Path(__file__).resolve().parents[1];data=Path(sys.argv[1]).resolve();b=r/'build-native/revision54';b.mkdir(parents=True,exist_ok=True);exe=r/'build-native/host/native-revision54'
def peer(case,slot):
 ffa,race,bw=case;name=f'{ffa}-{race}-{bw}-{slot}';trace=b/(name+'.trace');log=b/(name+'.log')
 with log.open('w')as out:p=subprocess.run([str(exe),str(data),str(r/'app/src/main/assets/native/weave.scx'),str(slot),str(ffa),str(race),str(bw),str(trace)],stdout=out,stderr=subprocess.STDOUT,timeout=180,cwd=r)
 if p.returncode:raise RuntimeError(log.read_text()[-3000:])
 return trace
cases=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
 for ffa in [0,1]:
  for race in [0,1,2]:
   for bw in [0,1]:
    case=ffa,race,bw;futures=[pool.submit(peer,case,slot)for slot in [0,1]];a,bp=[f.result()for f in futures];left,right=a.read_bytes(),bp.read_bytes()
    if left!=right:
     for x,y in zip(left.splitlines(),right.splitlines()):
      if x!=y:raise AssertionError(f'{case}: {x!r} != {y!r}')
     raise AssertionError('Trace lengths differ')
    item={'ffa':bool(ffa),'computerRaces':[race,(race+1)%3],'expansion':bool(bw),'matchingCheckpoints':601,'framesBeforeSave':2400,'continuedFramesAfterSave':240,'crossRoleRestore':True,'threeComputerSoloSaveContinuation':True,'sha256':hashlib.sha256(left).hexdigest()};cases.append(item);print('PASS',item,flush=True)
files=[r/n for n in ['native/runtime.cpp','native/multiplayer.h','native/save_state.h','native/generated/wasm_main.cpp','patches/native-polish54.patch','tests/native_revision54.cpp','tests/native_multiplayer.cpp','tests/run_revision54.py']]
(r/'validation/native-v54.json').write_text(json.dumps({'version':'0.54','passed':True,'originalGameData':True,'physicalAndroid':False,'binarySha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'cases':cases,'controls':['transport and bunker deselection','six airborne command cards','Land replaces pending addon','human departure does not defeat remaining computers'],'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

#!/usr/bin/env python3
"""Runs independent native peers with different UI activity, compares every turn."""
import concurrent.futures, hashlib, json, pathlib, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
data=pathlib.Path(sys.argv[1]).resolve();out=ROOT/'build-native/multiplayer47';out.mkdir(parents=True,exist_ok=True)
exe=ROOT/'build-native/host/native-multiplayer';original=ROOT/'app/src/main/assets/native/weave.scx'
transferred=ROOT/'build-native/map47/nearby-map.mpq'
def peer(case,slot):
    a,b,bw=case;name=f'{a}-{b}-{bw}-{slot}';trace=out/(name+'.trace');log=out/(name+'.log')
    map_path=transferred if slot==1 else original
    with log.open('w') as stream:
        run=subprocess.run([str(exe),str(data),str(map_path),str(slot),str(a),str(b),str(bw),str(trace)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
    if run.returncode:raise RuntimeError(log.read_text()[-3000:])
    return trace
cases=[(a,b,bw) for a,b in [(0,1),(1,2),(2,0)] for bw in [0,1]]
report={'version':'0.47','nearbyRadioTested':False,'physicalPhoneTested':False,'cases':[]}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    for case in cases:
        jobs=[pool.submit(peer,case,slot) for slot in range(2)]
        a,b=[f.result() for f in jobs];left=a.read_bytes();right=b.read_bytes()
        if left!=right:
            for n,(x,y) in enumerate(zip(left.splitlines(),right.splitlines())):
                if x!=y:raise AssertionError(f'{case} diverged at checkpoint {n}: {x!r} != {y!r}')
            raise AssertionError('Trace lengths differ')
        item={'races':list(case[:2]),'expansion':bool(case[2]),'frames':7200,'checkpoints':1801,'sameState':True,'traceSha256':hashlib.sha256(left).hexdigest(),'transferredMapOnGuest':True}
        report['cases'].append(item);print('PASS',item,flush=True)
report['passed']=True
report['sourceSha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'native/runtime.cpp',ROOT/'native/multiplayer.h',ROOT/'tests/native_multiplayer.cpp']}
(ROOT/'validation/native-multiplayer-v47.json').write_text(json.dumps(report,indent=2)+'\n')

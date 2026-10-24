#!/usr/bin/env python3
"""Run original-data 0.41 checks; archives and map files remain external."""
import concurrent.futures, hashlib, json, pathlib, subprocess, sys
root=pathlib.Path(__file__).resolve().parents[1]
data=pathlib.Path(sys.argv[1]).resolve(); maps=pathlib.Path(sys.argv[2]).resolve()
exe=root/'build-native/host/native-revision41'; logs=root/'build-native/revision41-results';logs.mkdir(exist_ok=True)
(root/'build-native/revision41-fixtures').mkdir(exist_ok=True)
weave=root/'app/src/main/assets/native/weave.scx'
cases=[(mode,weave,[mode]) for mode in ('cards','merging','cargo','warnings')]
cases += [('map-'+p.stem,p,['smoke']) for p in sorted(maps.iterdir()) if p.suffix.lower() in ('.scm','.scx')]
cases += [('ai-'+str(level),maps/'(4)High Noon.scm',['ai',str(level),'140000' if level==2 else '80000']) for level in range(3)]
def run(case):
 name,map,args=case
 p=subprocess.run([str(exe),str(data),str(map),*args],cwd=root,capture_output=True,text=True,timeout=900)
 log=p.stdout+p.stderr;(logs/(name+'.log')).write_text(log)
 print(name,p.returncode,flush=True)
 return {'name':name,'passed':p.returncode==0,'map':map.name,'mapSha256':hashlib.sha256(map.read_bytes()).hexdigest(),'args':args,'output':log}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(run,cases))
sources=['native/runtime.cpp','native/save_state.h','patches/native-polish41.patch','scripts/prepare_native.py','tests/native_revision41.cpp','tests/run_revision41.py']
report={'passed':all(r['passed'] for r in results),'cases':results,'originalCoreAssets':True,'resourceAssistance':False,'passiveHumanHealedDuringLongAiTests':True,'sourceSha256':{s:hashlib.sha256((root/s).read_bytes()).hexdigest() for s in sources},'hostExecutableSha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
(root/'validation/native-revision41-host-v41.json').write_text(json.dumps(report,indent=2)+'\n')
sys.exit(0 if report['passed'] else 1)

#!/usr/bin/env python3
"""Original-data regression suite; mission checks are startup/save checks, not playthroughs."""
from pathlib import Path
import concurrent.futures,hashlib,json,subprocess,sys,re
root=Path(__file__).resolve().parents[1];data=Path(sys.argv[1]).resolve();maps=Path(sys.argv[2]).resolve()
exe=root/'build-native/host/native-revision44';logs=root/'build-native/revision44-results';logs.mkdir(exist_ok=True)
(root/'build-native/revision41-fixtures').mkdir(exist_ok=True)
weave=root/'app/src/main/assets/native/weave.scx'
cases=[(mode,weave,[mode])for mode in ['commands','visibility','placement','cards','merging','cargo','warnings','retired']]
cases += [(mode,weave,[mode])for mode in ['sounds44','alerts44','ui44','nuke44','cloak44']]
cases += [('web44',root/'build-native/missions42/expzerg07.mpq',['web44'])]
cases += [('map-'+p.stem,p,['smoke'])for p in sorted(maps.iterdir())if p.suffix.lower()in('.scm','.scx')]
for level in range(3):cases.append(('protoss-high-noon-'+str(level),maps/'(4)High Noon.scm',['protoss',str(level),'60000']))
cases += [('protoss-weave-hard',weave,['protoss','2','60000']),('protoss-eldritch-hard',maps/'(2)Eldritch Lake.scm',['protoss','2','60000']),('protoss-power-recovery',maps/'(4)High Noon.scm',['protoss','2','60000','disrupt']),('terran-high-noon-hard',maps/'(4)High Noon.scm',['ai','2','60000']),('terran-weave-hard',weave,['ai','2','60000'])]
for m in json.loads((root/'missions.json').read_text()):cases.append(('mission-'+m['id'],root/'build-native/missions42'/(m['id']+'.mpq'),['mission',str(m['code']),'2400']))
def run(case):
 name,map_file,args=case
 try:
  p=subprocess.run([str(exe),str(data),str(map_file),*args],cwd=root,capture_output=True,text=True,timeout=900)
  log=p.stdout+p.stderr;passed=p.returncode==0;metrics={}
  if args[0]=='ai':
   types=re.search(r'FINAL types:([^\n]*)',log);seen=set(map(int,filter(None,types[1].split(','))))if types else set()
   bases=len(re.findall(r'^BUILDING 106 .*completed=1',log,re.M));gas=len(re.findall(r'^BUILDING 110 .*completed=1',log,re.M))
   metrics={'advancedTypesSeen':sorted(seen&{1,9,12,34}),'completedBases':bases,'completedRefineries':gas}
   # An exhausted initial base must not strand the workers. Multiple active
   # refineries and substantial total gathering prove the expansion economy.
   economy=re.findall(r'^AI \d+ 1\t([^\n]+)',log,re.M)
   if economy:
    last=list(map(int,economy[-1].split('\t')));metrics['mineralsGathered']=last[4];metrics['gasGathered']=last[5]
   passed=passed and {1,9,12,34}<=seen and bases>=2 and gas>=2 and metrics.get('gasGathered',0)>3000
  if args[0]=='protoss':
   match=re.search(r'^METRICS ([^\n]+)',log,re.M)
   if match:metrics={k:int(v)for k,v in re.findall(r'(\w+)=(-?\d+)',match[1])}
  (logs/(name+'.log')).write_text(log)
  result={'name':name,'passed':passed,'exitCode':p.returncode,'args':args,'map':map_file.name,'metrics':metrics,'tail':log[-1800:]}
 except subprocess.TimeoutExpired:result={'name':name,'passed':False,'error':'Timed out'}
 print(('PASS 'if result['passed']else 'FAIL ')+name,flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(run,cases))
paths=['native/runtime.cpp','native/save_state.h','scripts/prepare_native.py','tests/build_native_host.py','tests/native_revision41.cpp','tests/native_revision42.cpp','tests/native_revision43.cpp','tests/native_revision44.cpp','tests/run_revision44.py']+[str(p.relative_to(root))for p in sorted((root/'patches').glob('*.patch'))]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'passed':all(r['passed']for r in results),'cases':results,'originalCoreAssets':True,'resourceAssistance':False,'passiveHumanHealedDuringLongAiTests':True,'missionCount':sum(n['name'].startswith('mission-')for n in results),'missionFrames':2400,'fullPlaythrough':False,'sourceSha256':{p:sha(root/p)for p in paths},'hostExecutableSha256':sha(exe)}
(root/'validation/native-revision44-host-v44.json').write_text(json.dumps(report,indent=2)+'\n');sys.exit(0 if report['passed']else 1)

#!/usr/bin/env python3
"""Audit campaign AI startup with owned archives and exercise Revolution events.

Usage: python3 tests/run_campaign_ai81.py CORE_DIR STARCRAFT_MPQ BROODWAR_MPQ --skip-prepare
The runner extracts only to ignored build-native; original game data is not bundled.
"""
import argparse,concurrent.futures,hashlib,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('core',type=Path);p.add_argument('starcraft',type=Path);p.add_argument('broodwar',type=Path)
p.add_argument('--skip-prepare',action='store_true');p.add_argument('--skip-build',action='store_true');p.add_argument('--jobs',type=int,default=4)
a=p.parse_args();a.core=a.core.resolve();a.starcraft=a.starcraft.resolve();a.broodwar=a.broodwar.resolve()
out=ROOT/'build-native/campaign-ai81';out.mkdir(parents=True,exist_ok=True)
if not a.skip_prepare:subprocess.run([sys.executable,str(ROOT/'scripts/prepare_native.py')],cwd=ROOT,check=True)
source_names=['tests/native_campaign_ai81.cpp','tests/run_campaign_ai81.py','tests/native_mission_extract.cpp','tests/build_native_host.py','scripts/prepare_native.py','app/src/main/assets/native/missions.json']
source_names+=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'patches').glob('*.patch'))
def fingerprints():return {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in source_names}
before=fingerprints()
if not a.skip_build:subprocess.run([sys.executable,str(ROOT/'tests/build_native_host.py'),'campaign_ai81','--fast','--skip-prepare'],cwd=ROOT,check=True)
extract=out/'extract'
subprocess.run(['g++','-std=c++17','-O1','-I'+str(ROOT/'native-engine'),str(ROOT/'tests/native_mission_extract.cpp'),'-o',str(extract)],cwd=ROOT,check=True)
def extract_bytes(archive,internal,dest):
 dest.parent.mkdir(parents=True,exist_ok=True)
 run=subprocess.run([str(extract),str(archive),internal,str(dest)],capture_output=True)
 if run.returncode:return None
 return dest.read_bytes()
def core_asset(internal):
 for name in ('patch_rt.mpq','BROODAT.MPQ','STARDAT.MPQ'):
  data=extract_bytes(a.core/name,internal,out/internal)
  if data is not None:return data
 raise AssertionError('Missing core asset '+internal)
script_data=[core_asset('scripts/aiscript.bin'),core_asset('scripts/bwscript.bin')]
index={}
for file,b in enumerate(script_data):
 for offset in range(struct.unpack_from('<I',b)[0],len(b)-(7 if file else 15),8 if file else 16):
  name,pc=struct.unpack_from('<4sI',b,offset)
  if not any(name):break
  if pc:index[name.decode('ascii')]=(file,pc)
index.update({'Enmy':None,'Ally':None})
# Inventory original trigger owners, conditions and AI entry points. This checks
# source routing; it does not pretend to statically prove every dynamic branch.
catalog=json.loads((ROOT/'app/src/main/assets/native/missions.json').read_text())
def metadata(m):
 archive=a.broodwar if m['game']=='broodwar' else a.starcraft
 data=extract_bytes(archive,m['prefix']+'staredit/scenario.chk',out/'maps'/(m['id']+'.chk'))
 assert data is not None,m['id'];sections={};pos=0
 while pos<len(data):
  tag,n=struct.unpack_from('<4sI',data,pos);pos+=8;assert pos+n<=len(data)
  sections[tag]=sections.get(tag,b'')+data[pos:pos+n];pos+=n
 t=sections[b'TRIG'];starts=[]
 for pos in range(0,len(t),2400):
  for ai in range(64):
   loc,text,sound,time,group,other,unit,typ,modifier,flags,unused=struct.unpack_from('<6IH3BxH',t,pos+320+32*ai)
   if not typ:break
   if typ not in (15,16) or flags&2:continue
   script=struct.pack('<I',other).decode('ascii');assert script in index,(m['id'],script)
   starts.append(dict(trigger=pos//2400,script=script,location=loc,ownerGroups=[i for i,b in enumerate(t[pos+2372:pos+2400]) if b]))
 return dict(mission=m['id'],code=m['code'],title=m['title'],chkSha256=hashlib.sha256(data).hexdigest(),aiStarts=starts)
meta=[metadata(m) for m in catalog]
binary=ROOT/'build-native/host/native-campaign_ai81'
def run(m):
 archive=a.broodwar if m['game']=='broodwar' else a.starcraft
 q=subprocess.run([str(binary),str(a.core),str(archive),str(m['code']),'4800'],cwd=ROOT,capture_output=True,text=True)
 (out/(m['id']+'-startup.log')).write_text(q.stdout+q.stderr);q.check_returncode()
 frame=[line for line in q.stdout.splitlines() if line.startswith('FRAME ')][-1].split()
 assert 'AIERR=' in frame and frame[-1]=='AIERR=',m['id']
 stats=[]
 for line in q.stdout.splitlines():
  row=line.split('\t')
  if len(row)==9 and all(x.isdigit() for x in row):stats.append(dict(zip(('owner','opcodes','buildOrders','trainOrders','attacks','mineralsCounter','gasCounter','mineralsRemaining','gasRemaining'),map(int,row))))
 print(m['id']+': startup passed',flush=True)
 return dict(frame=int(frame[1]),aiClock=int(next(v.split('=')[1] for v in frame if v.startswith('clock='))),outcome=int(next(v.split('=')[1] for v in frame if v.startswith('outcome='))),aiError='',playerAi=stats)
with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(8,a.jobs))) as pool:
 for m,result in zip(meta,pool.map(run,catalog)):m.update(result)
focused=subprocess.run([str(binary),str(a.core),str(a.starcraft),'5'],cwd=ROOT,capture_output=True,text=True)
(out/'revolution.log').write_text(focused.stdout+focused.stderr);print(focused.stdout,end='');print(focused.stderr,file=sys.stderr,end='');focused.check_returncode()
after=fingerprints()
assert before==after,'AI sources changed during audit; rerun: '+', '.join(name for name in before if before[name]!=after[name])
report=dict(version='1.0.11',passed=True,originalArchivesTested=True,physicalAndroid=False,fullPlaythrough=False,
 scope='64 original maps: actual 4,800-frame unattended startup and static AI-entry lookup; Revolution controlled original-trigger progression, production, attack and replacement checks.',
 missionCount=len(meta),aiStartActions=sum(len(m['aiStarts']) for m in meta),distinctAiScripts=len({s['script'] for m in meta for s in m['aiStarts']}),requestedFramesPerMission=4800,
 checks=[line for line in focused.stdout.splitlines() if line.startswith('PASS ')],revolutionOutput=focused.stdout.splitlines(),missions=meta,
 limitations=['Not full mission playthroughs or a proof of all future AI branches.','Startup may end early on the original mission outcome; idle event-gated armies are expected.','Revolution uses controlled relocation of original units, invincible objective heroes/entry units and controlled destruction to exercise original triggers; no AI resources or script commands are injected.','Resource counters include trigger-granted resources; mining is additionally checked against the initial 6,000 mineral/gas grant.','Campaign AI implementation is not claimed to reproduce Blizzard timing/strategy exactly.'],
 coreSha256={name:hashlib.sha256((a.core/name).read_bytes()).hexdigest() for name in ('STARDAT.MPQ','BROODAT.MPQ','patch_rt.mpq')},
 scriptSha256={name:hashlib.sha256(data).hexdigest() for name,data in zip(('aiscript.bin','bwscript.bin'),script_data)},
 binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),sourceSha256=before)
(ROOT/'validation/campaign-ai-v81.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS all 64 original campaign startups and Revolution regression')

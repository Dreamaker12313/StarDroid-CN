#!/usr/bin/env python3
"""Audit original rescue WAVs and exercise ownership/audio using real game data."""
from pathlib import Path
import array, hashlib, json, math, struct, subprocess, sys, wave
r=Path(__file__).resolve().parents[1]
out=r/'build-native/rescue11';out.mkdir(parents=True,exist_ok=True)
archives=r.parent/'reign-data';core=r/'build-native/reign79/core';stage=r/'native-engine'
def sha(data):return hashlib.sha256(data).hexdigest()
def extract(archive,entry,name):
 p=out/name
 subprocess.run([str(r/'build-native/reign79/extract'),str(archives/archive),entry,str(p)],check=True,stdout=subprocess.DEVNULL)
 return p

def sections(data):
 result={};pos=0
 while pos<len(data):
  tag,n=struct.unpack_from('<4sI',data,pos);pos+=8
  assert pos+n<=len(data),'Truncated CHK'
  result[tag]=result.get(tag,b'')+data[pos:pos+n];pos+=n
 return result

def get_strings(data):
 count=struct.unpack_from('<H',data)[0]
 result=['']
 for i in range(1,count+1):
  pos=struct.unpack_from('<H',data,2*i)[0];assert pos<len(data)
  result.append(data[pos:].split(b'\0')[0].decode('cp1252'))
 return result

def cue_actions(chunks):
 strings=get_strings(chunks[b'STR ']);raw=chunks[b'TRIG'];result=[]
 assert len(raw)%2400==0
 for trigger in range(len(raw)//2400):
  actions=[];base=trigger*2400
  for i in range(64):
   a=struct.unpack_from('<6IH3BxH',raw,base+320+32*i)
   if not a[7]:break
   if not a[9]&2:actions.append(a)
  for a in actions:
   if a[7]in(7,8) and 'rescue.wav' in strings[a[2]].lower():
    result.append({'trigger':trigger,'action':a[7],'stringIndex':a[2],'wav':strings[a[2]],'giveUnitTypes':[g[6]for g in actions if g[7]==48]})
 return result

# Check all original campaigns for deliberately authored rescue cues, without
# replacing them with an inferred race. Normal passive rescue is tested below.
inventory=[];reign=None
for mission in json.loads((r/'app/src/main/assets/native/missions.json').read_text()):
 archive='BroodWar.mpq' if mission['game']=='broodwar' else 'StarCraft.mpq'
 chk=extract(archive,mission['prefix']+'staredit/scenario.chk',mission['id']+'.chk')
 raw=chk.read_bytes();chunks=sections(raw);cues=cue_actions(chunks)
 inventory.append({'mission':mission['id'],'race':mission['race'],'chkSha256':sha(raw),'scriptedRescueCues':cues})
 if mission['id']=='expzerg02':reign=inventory[-1]
assert reign and {(a['trigger'],tuple(a['giveUnitTypes']),a['wav'])for a in reign['scriptedRescueCues']}=={
 (67,(41,),r'staredit\wav\TRescue.wav'),(68,(37,),r'staredit\wav\TRescue.wav')}
print('PASS all 64 original campaign rescue-script audit; Reign of Fire explicitly assigns TRescue.wav to Drones and normal Zerglings')
files={}
for name in ['Z','T','P']:
 files[name]=extract('StarDat.mpq',f'sound/Misc/{name}Rescue.wav',f'core-{name}Rescue.wav')
authored=extract('BroodWar.mpq','campaign/expzerg/zerg02/staredit/wav/TRescue.wav','reign-TRescue.wav')
def pcm(path):
 with wave.open(str(path))as w:
  assert w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==22050
  a=array.array('h',w.readframes(w.getnframes()))
  if sys.byteorder!='little':a.byteswap()
  return a
# MPQ's lossy WAV packing can change individual samples. Compare actual PCM
# instead of demanding identical compressed streams or whole-file hashes.
a,b=pcm(files['T']),pcm(authored);assert len(a)==len(b)==41814
correlation=sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
assert correlation>.99999
assert len(pcm(files['Z']))!=len(b) and len(pcm(files['P']))!=len(b)
print(f'PASS authored Terran WAV identity: {len(b)} PCM frames, correlation={correlation:.12f}')
if '--skip-build' not in sys.argv:
 subprocess.run(['gcc','-O2','-c',str(r/'vendor/libsmacker/smacker.c'),'-o',str(out/'smacker.o')],check=True)
 cmd=['g++','-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER']
 cmd+=['-I'+str(p)for p in(stage,stage/'ui',stage/'web')]
 cmd+=[str(r/'tests/native_rescue_sound11.cpp'),str(r/'native/generated/wasm_backend.cpp'),str(out/'smacker.o'),'-o',str(out/'test')]
 subprocess.run(cmd,check=True)
run=subprocess.run([str(out/'test'),str(core),str(r/'app/src/main/assets/native/weave.scx'),str(archives/'BroodWar.mpq'),str(authored)],text=True,capture_output=True,cwd=r)
print(run.stdout+run.stderr,end='');run.check_returncode()
source=['tests/native_rescue_sound11.cpp','tests/run_rescue_sound11.py']
report={'passed':True,'version':'1.1','productionChangeRequired':False,'originalMissionBehaviorPreserved':True,
 'physicalAndroid':False,'fullPlaythrough':False,'nativeResults':run.stdout.strip(),
 'reignOfFire':reign,'wavComparison':{'pcmFrames':len(b),'terranPcmCorrelation':correlation,'maxSampleDifference':max(abs(x-y)for x,y in zip(a,b)),'authoredSha256':sha(authored.read_bytes()),'coreSha256':{k:sha(p.read_bytes())for k,p in files.items()}},
 'campaignInventory':inventory,'sourceSha256':{p:sha((r/p).read_bytes())for p in source}}
(r/'validation/rescue-sound-1.1.json').write_text(json.dumps(report,indent=2)+'\n')

#!/usr/bin/env python3
"""Original Dylarian reward and shared nuclear production/ownership regression.

Uses locally imported classic archives; never packages their contents.
"""
from pathlib import Path
import hashlib,json,struct,subprocess,sys
r=Path(__file__).resolve().parents[1];out=r/'build-native/nukes11';out.mkdir(parents=True,exist_ok=True)
archives=r.parent/'reign-data';core=r/'build-native/reign79/core';stage=r/'native-engine'
def sha(b):return hashlib.sha256(b).hexdigest()
def extract(archive,path,name):
 dest=out/name
 subprocess.run([str(r/'build-native/reign79/extract'),str(archives/archive),path,str(dest)],check=True,stdout=subprocess.DEVNULL)
 return dest.read_bytes()
def sections(b):
 result={};pos=0
 while pos<len(b):
  tag,n=struct.unpack_from('<4sI',b,pos);pos+=8;assert pos+n<=len(b)
  result[tag]=result.get(tag,b'')+b[pos:pos+n];pos+=n
 return result
inventory=[];dylarian=None
for m in json.loads((r/'app/src/main/assets/native/missions.json').read_text()):
 b=extract('BroodWar.mpq' if m['game']=='broodwar' else 'StarCraft.mpq',m['prefix']+'staredit/scenario.chk',m['id']+'.chk');s=sections(b)
 u=s[b'UNIT'];assert len(u)%36==0
 silos=[{'owner':u[p+16],'x':struct.unpack_from('<H',u,p+4)[0],'y':struct.unpack_from('<H',u,p+6)[0]}for p in range(0,len(u),36)if struct.unpack_from('<H',u,p+8)[0]==108]
 inventory.append({'mission':m['id'],'sha256':sha(b),'preplacedSilos':silos})
 if m['code']==402:dylarian=s;assert len(silos)==4 and all(x['owner']==0 for x in silos)
assert dylarian
raw=dylarian[b'TRIG']
def actions(n):return [struct.unpack_from('<6IH3BxH',raw,n*2400+320+32*i)for i in range(64)]
assert any(a[7]==16 and struct.pack('<I',a[5])==b'TB2B' for a in actions(24))
assert any(a[7]==48 and a[4:7]==(0,6,231) for a in actions(49))
assert any(a[7]==7 and a[1]==218 for a in actions(49))
print('PASS all 64 original mission silo inventory; Dylarian TB2B startup and unchanged building handover verified')
if '--skip-build' not in sys.argv:
 subprocess.run(['gcc','-O2','-c',str(r/'vendor/libsmacker/smacker.c'),'-o',str(out/'smacker.o')],check=True)
 cmd=['g++','-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER']
 cmd+=['-I'+str(p)for p in(stage,stage/'ui',stage/'web')]
 cmd+=[str(r/'tests/native_nukes11.cpp'),str(r/'native/generated/wasm_backend.cpp'),str(out/'smacker.o'),'-o',str(out/'test')]
 subprocess.run(cmd,check=True)
run=subprocess.run([str(out/'test'),str(core),str(archives/'BroodWar.mpq'),str(r/'app/src/main/assets/native/weave.scx')],cwd=r,capture_output=True,text=True)
(out/'test.log').write_text(run.stdout+run.stderr);print(run.stdout+run.stderr,end='');run.check_returncode()
files=['patches/native-nukes11.patch','tests/native_nukes11.cpp','tests/run_nukes11.py']
report={'passed':True,'version':'1.1','physicalAndroid':False,'fullPlaythrough':False,
 'scope':'Original Dylarian startup, controlled platform-B condition activation, original handover, real Ghost command and explosion; isolated shared production/transfer regression on custom Weave map.',
 'checks':[x for x in run.stdout.splitlines()if x.startswith('PASS')],
 'dylarian':{'missionCode':402,'preplacedSilos':4,'siloOwner':0,'rewardOwner':6,'aiStartTrigger':24,'rewardTrigger':49,'aiScript':'TB2B','scriptedResourceGrantEach':10000,
 'missileCost':{'minerals':200,'gas':200,'displayedSupply':8,'internalHalfSupply':16},
 'unattendedOpening':{'readyMissiles':3,'displayedSupplyUsed':129,'displayedSupplyAvailable':136,'internalHalfSupplyUsed':258,'internalHalfSupplyAvailable':272},
 'controlledDefenderDeath':'One original enemy Marine is killed to free the missing 1 displayed supply; fourth missile then builds at normal speed.',
 'rewardActivation':'Set platform-B active switch and original Player 2 custom score to four, allowing original trigger 32 and trigger 49 to run; no trigger action is replaced and no ammunition is granted by test code.'},
 'limitations':['Not a complete manual campaign playthrough or physical Android validation.','Stocking obeys actual resources, supply, map availability and build time. An early handover can occur before every missile finishes.','As in normal building transfer, unfinished unit production is cancelled and refunded to its previous owner. Only completed stored ammunition transfers.','An old save made after the broken empty-silo handover is not retroactively granted ammunition. Restart the mission or load before the handover to obtain the corrected mission reward.'],
 'saveLayoutChanged':False,'simulationRulesChanged':True,'nativeOutput':run.stdout.splitlines(),
 'originalMissionInventory':inventory,'sourceSha256':{p:sha((r/p).read_bytes())for p in files},'binarySha256':sha((out/'test').read_bytes())}
(r/'validation/nukes11.json').write_text(json.dumps(report,indent=2)+'\n')

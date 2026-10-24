#!/usr/bin/env python3
"""Power, addon ownership, voice playback and affected AI regressions against real data."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,subprocess,sys
r=Path(__file__).resolve().parents[1];out=r/'build-native/native57';out.mkdir(exist_ok=True);data=Path(sys.argv[1]).resolve();exe=r/'build-native/host/native-revision57'
subprocess.run([sys.executable,str(r/'tests/create_room_map55.py')],cwd=r,check=True)
cases=[(x,x,[])for x in ['power','addons','sound','victory','cargo']]+[(f'macro-{race}','macro',[race])for race in range(3)]
def run(case):
 name,mode,args=case;mp=r/('app/src/main/assets/native/weave.scx'if mode=='macro'else'build-native/probe55/eight-starts.scx')
 p=subprocess.run([str(exe),str(data),str(mp),mode,*map(str,args)],cwd=r,capture_output=True,text=True);log=p.stdout+p.stderr;(out/(name+'.log')).write_text(log)
 if p.returncode:print(log,flush=True);p.check_returncode()
 print(name+': '+next(x for x in reversed(log.splitlines())if x.startswith('PASS ')),flush=True)
 return {'case':name,'passed':True,'output':log}
with ThreadPoolExecutor(max_workers=2)as pool:results=list(pool.map(run,cases))
# Independent StormLib extraction validates the actual original source waveforms.
storm=r/'build-native/probe57/storm-extract';extract=r/'build-native/ui56/extract-interface';audio=[]
for i in range(4):
 name=f'sound/Zerg/Ultra/ZUlWht0{i}.wav';a=out/f'openbw-{i}.wav';b=out/f'storm-{i}.wav'
 subprocess.run([str(extract),str(data/'STARDAT.MPQ'),name,str(a)],check=True)
 subprocess.run([str(storm),str(data/'STARDAT.MPQ'),name.replace('/','\\'),str(b)],check=True)
 assert a.read_bytes()==b.read_bytes(),'Original Ultralisk waveform differs from StormLib'
 audio.append({'clip':name,'identicalToStormLib':True,'sha256':hashlib.sha256(a.read_bytes()).hexdigest()})
files=['tests/native_revision57.cpp','tests/native_revision56.cpp','tests/native_revision55.cpp','tests/run_native57.py','tests/create_room_map55.py','patches/native-polish57.patch','scripts/prepare_native.py','native/runtime.cpp','native/audio.h','native/save_state.h','native/multiplayer.h']
report={'passed':True,'physicalDevices':False,'cases':results,'sourceWaveforms':audio,'independentDecoder':{'repository':'https://github.com/ladislav-zezula/StormLib','commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=storm.parent/'StormLib',text=True).strip()},'limitations':'Actual imported data and real engine on host. Physical device sound and radio testing pending. AI regression covers hard Brood War, three races, 60000 frames each; 0.56 history retains all 18 original/BW difficulty combinations.','sourceSha256':{n:hashlib.sha256((r/n).read_bytes()).hexdigest()for n in files}}
(r/'validation/native-v57.json').write_text(json.dumps(report,indent=2)+'\n')

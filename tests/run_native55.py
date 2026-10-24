#!/usr/bin/env python3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];data=Path(sys.argv[1]).resolve();mission=Path(sys.argv[2]).resolve();b=r/'build-native/native55';b.mkdir(parents=True,exist_ok=True)
subprocess.run([sys.executable,str(r/'tests/create_room_map55.py')],check=True,cwd=r)
exe=r/'build-native/host/native-revision55';mpq=r/'build-native/probe55/eight-starts.scx';results=[]
def run(case):
 humans,ffa,slot=case;out=b/f'{humans}-{ffa}-{slot}.txt';p=subprocess.run([str(exe),str(data),str(mpq),'multiplayer',str(slot),str(humans),str(ffa),str(out)],cwd=r,capture_output=True,text=True);print(p.stdout+p.stderr,flush=True);p.check_returncode();return {'humans':humans,'ffa':ffa,'slot':slot,'trace':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
cases=[(humans,ffa,slot)for humans,ffa in [(8,0),(6,1)]for slot in range(humans)]
with ThreadPoolExecutor(max_workers=2)as pool:results=list(pool.map(run,cases))
for humans in [8,6]:assert len({v['sha256']for v in results if v['humans']==humans})==1,'Player perspectives diverged'
p=subprocess.run([str(exe),str(data),str(r/'app/src/main/assets/native/weave.scx'),'feedback',str(mission)],cwd=r,capture_output=True,text=True);print(p.stdout+p.stderr,flush=True);p.check_returncode()
files=[r/'native/multiplayer.h',r/'native/runtime.cpp',r/'patches/native-polish55.patch',r/'patches/native-polish58.patch',r/'patches/native-polish59.patch',r/'native/hero_mode.h',r/'native/save_state.h',r/'tests/native_revision55.cpp',r/'tests/create_room_map55.py',Path(__file__)]
(r/'validation/native-v55.json').write_text(json.dumps({'passed':True,'physicalDevices':False,'cases':results,'framesPerPerspective':1440,'checkpointsPerPerspective':360,'feedback':p.stdout,'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

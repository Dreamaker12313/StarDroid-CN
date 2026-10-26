#!/usr/bin/env python3
"""Exercise all Hero Mode production completions using original archives."""
from pathlib import Path
import hashlib,json,subprocess,sys
r=Path(__file__).resolve().parents[1];out=r/'build-native/hero-rescue11';out.mkdir(parents=True,exist_ok=True);stage=r/'native-engine'
if '--skip-build' not in sys.argv:
 subprocess.run(['gcc','-O2','-c',str(r/'vendor/libsmacker/smacker.c'),'-o',str(out/'smacker.o')],check=True)
 cmd=['g++','-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER']
 cmd+=['-I'+str(p)for p in(stage,stage/'ui',stage/'web')]
 cmd+=[str(r/'tests/native_hero_rescue11.cpp'),str(r/'native/generated/wasm_backend.cpp'),str(out/'smacker.o'),'-o',str(out/'test')]
 subprocess.run(cmd,check=True)
run=subprocess.run([str(out/'test'),str(r/'build-native/reign79/core')],cwd=r,text=True,capture_output=True);print(run.stdout+run.stderr,end='');run.check_returncode()
files=['patches/native-hero-rescue11.patch','tests/native_hero_rescue11.cpp','tests/run_hero_rescue11.py']
(r/'validation/hero-rescue-1.1.json').write_text(json.dumps({'passed':True,'version':'1.1','replayEngine':84,'physicalAndroid':False,'nativeResults':run.stdout.strip(),'sourceSha256':{p:hashlib.sha256((r/p).read_bytes()).hexdigest()for p in files}},indent=2)+'\n')

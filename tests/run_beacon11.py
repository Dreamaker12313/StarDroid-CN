#!/usr/bin/env python3
"""Compile and run production touch/beacon command-stream tests with original data."""
from pathlib import Path
import hashlib,json,subprocess,sys
r=Path(__file__).resolve().parents[1];out=r/'build-native/beacon11';out.mkdir(parents=True,exist_ok=True);stage=r/'native-engine'
if '--skip-build' not in sys.argv:
 subprocess.run(['gcc','-O2','-c',str(r/'vendor/libsmacker/smacker.c'),'-o',str(out/'smacker.o')],check=True)
 cmd=['g++','-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER']
 cmd+=['-I'+str(p)for p in(stage,stage/'ui',stage/'web')]
 cmd+=[str(r/'tests/native_beacon11.cpp'),str(r/'native/generated/wasm_backend.cpp'),str(out/'smacker.o'),'-o',str(out/'test')]
 subprocess.run(cmd,check=True)
run=subprocess.run([str(out/'test'),str(r/'build-native/reign79/core')],cwd=r,text=True,capture_output=True);print(run.stdout+run.stderr,end='');run.check_returncode()
files=['native/runtime.cpp','tests/native_beacon11.cpp','tests/run_beacon11.py']
(r/'validation/beacon-1.1.json').write_text(json.dumps({'passed':True,'version':'1.1','physicalAndroid':False,'nativeResults':run.stdout.strip(),'sourceSha256':{p:hashlib.sha256((r/p).read_bytes()).hexdigest()for p in files}},indent=2)+'\n')

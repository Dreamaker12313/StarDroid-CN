#!/usr/bin/env python3
"""Validate exact command dispatch and original hotkeys against locally imported data."""
from pathlib import Path
import hashlib,json,subprocess,sys
r=Path(__file__).resolve().parents[1];out=r/'build-native/hotkey-command11';out.mkdir(parents=True,exist_ok=True);stage=r/'native-engine'
if '--skip-build' not in sys.argv:
 subprocess.run(['gcc','-O2','-c',str(r/'vendor/libsmacker/smacker.c'),'-o',str(out/'smacker.o')],check=True)
 cmd=['g++','-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER']
 cmd+=['-I'+str(p)for p in(stage,stage/'ui',stage/'web')]
 cmd+=[str(r/'tests/native_hotkeys11.cpp'),str(r/'native/generated/wasm_backend.cpp'),str(out/'smacker.o'),'-o',str(out/'test')]
 subprocess.run(cmd,check=True)
run=subprocess.run([str(out/'test'),str(r/'build-native/reign79/core'),str(out)],cwd=r,text=True,capture_output=True);print(run.stdout+run.stderr,end='')
files=['native/runtime.cpp','native/generated/wasm_backend.cpp','patches/native-hotkeys11.patch','scripts/prepare_native.py','tests/native_hotkeys11.cpp','tests/run_hotkeys_native11.py']
(r/'validation/hotkeys-native11.json').write_text(json.dumps({'passed':run.returncode==0,'version':'1.1','simulation':84,'physicalAndroid':False,'nativeResults':run.stdout.strip(),'errors':run.stderr.strip(),'sourceSha256':{p:hashlib.sha256((r/p).read_bytes()).hexdigest()for p in files}},indent=2)+'\n')
run.check_returncode()

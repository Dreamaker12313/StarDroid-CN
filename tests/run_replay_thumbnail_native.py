#!/usr/bin/env python3
"""Focused host validation of the parser backing the replay preview JNI entry."""
from pathlib import Path
import hashlib,json,os,subprocess
r=Path(__file__).resolve().parents[1];out=r/'build-native/replay-thumbnail-native';out.mkdir(parents=True,exist_ok=True)
stage=r/'native-engine'
subprocess.run(['gcc','-O2','-c',str(r/'vendor/libsmacker/smacker.c'),'-o',str(out/'smacker.o')],check=True)
cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER']
cmd+=['-I'+str(p)for p in (stage,stage/'ui',stage/'web')]
cmd+=[str(r/'tests/native_replay_thumbnail.cpp'),str(r/'native/generated/wasm_backend.cpp'),str(out/'smacker.o'),'-o',str(out/'test')]
subprocess.run(cmd,check=True)
fixture=r/'build-native/replay-thumbnail-ui/assets/0/preview/scenario.chk'
result=subprocess.run([str(out/'test'),str(fixture)],check=True,capture_output=True,text=True);print(result.stdout,end='')
names=['tests/native_replay_thumbnail.cpp','tests/native_replay81.cpp','tests/run_replay_thumbnail_native.py','native/replay.h','native/runtime.cpp','app/src/main/java/org/openbw/androidtest/NativeBridge.java']
(r/'validation/replay-thumbnail-native.json').write_text(json.dumps({'passed':True,'scope':'Host native parser used by replayScenario; JNI exports checked separately during APK packaging','result':result.stdout.strip(),'embeddedChkBytes':fixture.stat().st_size,'sourceSha256':{n:hashlib.sha256((r/n).read_bytes()).hexdigest()for n in names}},indent=2)+'\n')

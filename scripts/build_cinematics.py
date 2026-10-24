#!/usr/bin/env python3
"""Build the separately replaceable cinematic libsmacker adapter."""
import hashlib,json,os,subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[1]
for f in json.loads((r/'PORTRAITS-BUILD.json').read_text())['files']:
    if hashlib.sha256((r/f['file']).read_bytes()).hexdigest()!=f['sha256']:raise RuntimeError('libsmacker source mismatch')
sdk=Path(os.environ.get('WASI_SDK',r/'.tools/wasi-sdk-33.0-x86_64-linux'))
output=r/'app/src/main/assets/game/cinematic-decoder.wasm'
subprocess.run([str(sdk/'bin/clang'),'-O2','-mexec-model=reactor','-Wl,-z,stack-size=1048576','-Wl,--max-memory=201326592','-ffile-prefix-map='+str(r)+'=openbw-android','-I'+str(r/'vendor/libsmacker'),str(r/'web/cinematic_decoder.c'),str(r/'vendor/libsmacker/smacker.c'),'-o',str(output)],check=True)
print('Built cinematic decoder',hashlib.sha256(output.read_bytes()).hexdigest())

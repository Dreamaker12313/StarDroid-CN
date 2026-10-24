#!/usr/bin/env python3
"""Build the separately replaceable libsmacker portrait decoder."""
import hashlib,json,os,subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[1]
meta=json.loads((r/'PORTRAITS-BUILD.json').read_text())
for f in meta['files']:
    if hashlib.sha256((r/f['file']).read_bytes()).hexdigest()!=f['sha256']:
        raise RuntimeError('libsmacker source changed: review and update PORTRAITS-BUILD.json')
sdk=Path(os.environ.get('WASI_SDK',str(r/'.tools/wasi-sdk-33.0-x86_64-linux')))
for name,extra in [('portrait',[]),('menu',['-DOPENBW_MENU_DECODER'])]:
    output=r/f'app/src/main/assets/game/{name}-decoder.wasm'
    subprocess.run([str(sdk/'bin/clang'),'-O2','-mexec-model=reactor',*extra,
        '-Wl,-z,stack-size=1048576','-Wl,--max-memory=134217728',
        '-ffile-prefix-map='+str(r)+'=openbw-android','-I'+str(r/'vendor/libsmacker'),str(r/'web/portrait_decoder.c'),
        str(r/'vendor/libsmacker/smacker.c'),'-o',str(output)],check=True)
    print('Built',output)

#!/usr/bin/env python3
"""Rebuild all engine modules from the recorded local source archives."""
import hashlib,json,os,shutil,subprocess,tarfile
from pathlib import Path
r=Path(__file__).resolve().parents[1]
meta=json.loads((r/'ENGINE-BUILD.json').read_text())
campaign=json.loads((r/'CAMPAIGN-BUILD.json').read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(*args,**kw):subprocess.run([str(a) for a in args],check=True,**kw)
run('python3',r/'scripts/build_campaign.py')
stage=r/'build-engine'
sdk=Path(os.environ.get('WASI_SDK',str(r/'.tools'/campaign['sdk']))).resolve()
decoder=stage/'web/media-decoder.wasm'
run(sdk/'bin/clang++','-std=c++14','-O2','-fno-exceptions','-DOPENBW_NO_EXCEPTIONS',
    '-mexec-model=reactor','-Wl,-z,stack-size=1048576','-I'+str(stage),r/'web/media_decoder.cpp','-o',decoder)
run('python3',r/'scripts/build_portraits.py',env={**os.environ,'WASI_SDK':str(sdk)})
run('python3',r/'scripts/build_cinematics.py',env={**os.environ,'WASI_SDK':str(sdk)})
built={'openbw.wasm':stage/'web/openbw.wasm','openbw-campaign.wasm':stage/'web/openbw.wasm',
       'media-decoder.wasm':decoder,'menu-decoder.wasm':r/'app/src/main/assets/game/menu-decoder.wasm','portrait-decoder.wasm':r/'app/src/main/assets/game/portrait-decoder.wasm','cinematic-decoder.wasm':r/'app/src/main/assets/game/cinematic-decoder.wasm'}
for item in meta['binaries']:
    if digest(built[item['file']])!=item['sha256']:
        raise RuntimeError('Rebuild differs from recorded binary: '+item['file']+'; inspect compiler/dependency versions before updating metadata')
for name,file in built.items():
    dest=r/'app/src/main/assets/game'/name
    if file.resolve()!=dest.resolve():shutil.copyfile(file,dest)
print('All retained web modules rebuilt and verified against ENGINE-BUILD.json.')

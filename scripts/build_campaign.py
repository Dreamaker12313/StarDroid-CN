#!/usr/bin/env python3
"""Rebuild the campaign WASM from pinned source and the included patch."""
import hashlib, json, os, shutil, subprocess, tarfile, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'CAMPAIGN-BUILD.json').read_text())
up=json.loads((ROOT/'UPSTREAM.json').read_text())
archive=ROOT/up['source_archive']['file'];patch=ROOT/'patches/campaign.patch'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if digest(archive)!=up['source_archive']['sha256']:raise RuntimeError('Source archive checksum mismatch')
if digest(patch)!=meta['patchSha256']:raise RuntimeError('Campaign patch checksum mismatch; update CAMPAIGN-BUILD.json after reviewing changes')
sdk=os.environ.get('WASI_SDK')
if not sdk:
    cache=ROOT/'.tools';cache.mkdir(exist_ok=True);sdk=cache/meta['sdk']
    compressed=cache/(meta['sdk']+'.tar.gz')
    if not compressed.exists():urllib.request.urlretrieve('https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-33/'+compressed.name,compressed)
    if digest(compressed)!=meta['sdkArchiveSha256']:raise RuntimeError('WASI SDK checksum mismatch')
    if not sdk.exists():
        with tarfile.open(compressed) as t:t.extractall(cache,filter='data')
else:sdk=Path(sdk).resolve()
stage=ROOT/'build-engine'
if stage.exists():shutil.rmtree(stage)
stage.mkdir()
with tarfile.open(archive) as t:t.extractall(stage,filter='data')
subprocess.run(['patch','-p1','-i',str(patch)],cwd=stage,check=True)
subprocess.run(['bash','web/build-wasm.sh'],cwd=stage,env={**os.environ,'WASI_SDK':str(sdk)},check=True)
binary=stage/'web/openbw.wasm'
if digest(binary)!=meta['wasmSha256']:raise RuntimeError('Campaign WASM differs from recorded build; review toolchain or changes before updating the expected hash')
shutil.copyfile(binary,ROOT/'app/src/main/assets/game/openbw-campaign.wasm')
print('Campaign WASM rebuilt and verified:',meta['wasmSha256'])

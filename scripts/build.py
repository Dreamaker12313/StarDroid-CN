#!/usr/bin/env python3
"""Build/sign the native APK; bootstrap pinned SDK/NDK and the Nearby Gradle build."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
import zipfile
import sys, stat

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(os.environ.get('STARDROID_ANDROID_TOOLS',os.environ.get('OPENBW_ANDROID_TOOLS', ROOT / '.tools'))).resolve()
BUILD = ROOT / 'build-native/apk'
OUT = ROOT / 'dist'
SDK = TOOLS / 'android-35'
BT = TOOLS / 'android-15'  # Google's r35 Linux ZIP uses this folder name.

def run(*cmd):
    subprocess.run([str(x) for x in cmd], check=True)

def get(name, url, digest, algorithm):
    TOOLS.mkdir(parents=True, exist_ok=True)
    dest = TOOLS / name
    if not dest.exists():
        print('Downloading ' + name, flush=True)
        urllib.request.urlretrieve(url, dest)
    if hashlib.new(algorithm, dest.read_bytes()).hexdigest() != digest:
        raise RuntimeError('Checksum mismatch: ' + str(dest))
    if name.endswith('.zip'):
        with zipfile.ZipFile(dest) as archive:
            for item in archive.infolist():
                dest = TOOLS / item.filename
                mode = item.external_attr >> 16
                if stat.S_ISLNK(mode):
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.unlink(missing_ok=True)
                    dest.symlink_to(archive.read(item).decode())
                else:
                    archive.extract(item, TOOLS)
                    if mode: dest.chmod(mode & 0o777)

get('platform-35_r02.zip', 'https://dl.google.com/android/repository/platform-35_r02.zip', '0bb560a90a7a2cbd0dd8348224d518b638fe7949', 'sha1')
get('build-tools_r35_linux.zip', 'https://dl.google.com/android/repository/build-tools_r35_linux.zip', '2cfaa0bbb2336e9ec18ed3ecea84fa2e2af607bc', 'sha1')
get('ecj.jar', 'https://repo.maven.apache.org/maven2/org/eclipse/jdt/ecj/3.33.0/ecj-3.33.0.jar', 'f7686c4960cf70c2ebc5c500a73a8cfc04541b730c18f1c5c21329889b137f45', 'sha256')
for name in ['aapt2', 'aapt', 'zipalign', 'apksigner', 'd8']:
    (BT / name).chmod(0o755)
if BUILD.exists(): shutil.rmtree(BUILD)
for d in [BUILD, BUILD / 'classes', BUILD / 'dex', OUT]: d.mkdir(parents=True, exist_ok=True)
MAIN = ROOT / 'app/src/main'
# Only native resources enter this APK. Legacy web sources remain in the source
# archive for history; no HTML, JavaScript, WASM or WebView is shipped.
if '--skip-engine' not in sys.argv:
    get('android-ndk-r27d-linux.zip', 'https://dl.google.com/android/repository/android-ndk-r27d-linux.zip', '22105e410cf29afcf163760cc95522b9fb981121', 'sha1')
    for abi in ['arm64-v8a','x86_64']:run(sys.executable,ROOT/'scripts/build_native_engine.py',abi)
run(sys.executable,ROOT/'scripts/build_nearby.py','--skip-engine')

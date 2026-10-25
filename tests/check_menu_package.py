#!/usr/bin/env python3
"""Verify the menu-update APK against its supplied source baseline and release key."""
import argparse, hashlib, json, os, re, subprocess, zipfile
from pathlib import Path

r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('baseline_source',type=Path)
a=p.parse_args()
tools=Path(os.environ.get('STARDROID_ANDROID_TOOLS',r/'.tools'))
apk=r/'dist/StarDroid-1.0.6.apk'
def run(*args):return subprocess.run(list(map(str,args)),capture_output=True,text=True,check=True).stdout
cert=run('java','-jar',tools/'android-15/lib/apksigner.jar','verify','--verbose','--print-certs',apk)
assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in cert
expected='40e172ca11ff8be42888388f51b94ffb824382dce5235c5f1bd5683b4bb8876e'
assert 'certificate SHA-256 digest: '+expected in cert
badging=run(tools/'android-15/aapt2','dump','badging',apk)
assert "package: name='org.openbw.androidtest' versionCode='76' versionName='1.0.6'" in badging
assert "minSdkVersion:'26'" in badging and "targetSdkVersion:'35'" in badging
run(tools/'android-15/zipalign','-c','-P','16','4',apk)
unchanged=[]
with zipfile.ZipFile(a.baseline_source) as source,zipfile.ZipFile(apk) as built:
    prefix=source.namelist()[0].split('/')[0]+'/'
    for name in built.namelist():
        if name.startswith('lib/'):
            original=prefix+'native-libs/'+name[len('lib/'):]
        elif name.startswith(('assets/native/','assets/missions/')):
            original=prefix+'app/src/main/'+name
        elif name.startswith('assets/libsmacker-'):
            original=prefix+'vendor/libsmacker/'+name[len('assets/libsmacker-'):]
        else:
            continue
        assert built.read(name)==source.read(original),name
        unchanged.append(name)
    assert len([n for n in unchanged if n.startswith('lib/')])==4
    assert not any(n.lower().endswith(('.mpq','.p12','.jks','.keystore')) for n in built.namelist())
lint=(r/'app/build/reports/lint-results-release.txt').read_text()
assert re.search(r'0 errors, \d+ warnings',lint)
report={'passed':True,'version':'1.0.6','versionCode':76,'physicalAndroid':False,
        'apkSha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'apkBytes':apk.stat().st_size,
        'certificateSha256':expected,'originalReleaseSigningIdentity':True,
        'nativeAndAssetEntriesUnchanged':len(unchanged),'nativeEngineRebuilt':False,
        'zipAlignmentBytes':16384,'lint':re.search(r'0 errors, \d+ warnings',lint).group()}
(r/'validation/menu-package-v1.0.6.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

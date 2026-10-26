#!/usr/bin/env python3
"""Package the frozen 1.1 help-format/menu-mnemonic update with verified unchanged native libraries.

Usage: release signing environment variables + python3 tests/package_guide_format11.py PREVIOUS_APK
The SDK/NDK and Gradle 8.9 must already be bootstrapped by scripts/build.py.
"""
from pathlib import Path
import hashlib, json, os, re, shutil, struct, subprocess, sys, tempfile
import urllib.parse, xml.etree.ElementTree as ET, zipfile

ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=Path(sys.argv[1]).resolve()
TOOLS=Path(os.environ.get('STARDROID_ANDROID_TOOLS',ROOT/'.tools'))
OUT=ROOT/'build-native/guide-format11-release'
VERIFIED_LIBS=ROOT/'build-native/hotkeys11-release/native-libs-rebuilt'
OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ('STARDROID_KEYSTORE','STARDROID_STORE_PASSWORD','STARDROID_KEY_ALIAS','STARDROID_KEY_PASSWORD'):
    if not os.environ.get(name):raise RuntimeError('Missing release signing variable: '+name)
assert sha(PREVIOUS)=='fb6198ef0f88778357165b805e62c6ddb5b44648a4679fbe4e2d6fdc43eb6309'
proof_path=ROOT/'validation/native-build-hotkeys11.json'
proof_digest=sha(proof_path)
proof=json.loads(proof_path.read_text())
assert proof['passed'] and proof['nativeEngineRebuilt']
for name,digest in proof['sourceSha256'].items():assert sha(ROOT/name)==digest,name
sources=[p for p in (ROOT/'app/src/main').rglob('*') if p.is_file()]
sources += [ROOT/n for n in ('app/build.gradle','build.gradle','settings.gradle','gradle.properties','scripts/build_nearby.py','tests/package_guide_format11.py')]
before={str(p.relative_to(ROOT)):sha(p) for p in sources}
work=Path(tempfile.mkdtemp(prefix='stardroid-guide-format11-')); assets=work/'assets';libs=work/'libs';assets.mkdir();libs.mkdir()
for name in ('native','missions'):shutil.copytree(ROOT/'app/src/main/assets'/name,assets/name)
for name in ('COPYING','NOTICE.txt'):shutil.copyfile(ROOT/'vendor/libsmacker'/name,assets/('libsmacker-'+name))
for name,digest in proof['librarySha256'].items():
    source=VERIFIED_LIBS/name;assert sha(source)==digest,name
    target=libs/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
init=work/'isolate.gradle'
init.write_text('allprojects { project ->\n project.buildDir = new File("'+str(work)+'/build", project.name)\n project.afterEvaluate { if (project.plugins.hasPlugin("com.android.application")) { project.android.sourceSets.main.jniLibs.srcDirs = [new File("'+str(libs)+'")]; project.android.sourceSets.main.assets.srcDirs = [new File("'+str(assets)+'")] } }\n}\n')
(OUT/'build-path.txt').write_text(str(work))
proxy=[]
for scheme in ('http','https'):
    u=urllib.parse.urlparse(os.environ.get(scheme.upper()+'_PROXY',''))
    if u.hostname:proxy.extend(['-D'+scheme+'.proxyHost='+u.hostname,'-D'+scheme+'.proxyPort='+str(u.port or 80)])
with (OUT/'gradle.log').open('w')as log:
    subprocess.run([str(TOOLS/'gradle-8.9/bin/gradle'),*proxy,'--init-script',str(init),'--no-daemon','--console=plain','clean','assembleRelease','lintRelease'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
assert sha(proof_path)==proof_digest,'Native proof changed'
for name,digest in before.items():assert sha(ROOT/name)==digest,'Package source changed: '+name
for name,digest in proof['sourceSha256'].items():assert sha(ROOT/name)==digest,'Native source changed: '+name
app=work/'build/app';apk=app/'outputs/apk/release/app-release.apk';lint=app/'reports/lint-results-release.xml'
issues=ET.parse(lint).findall('issue');assert not any(i.get('severity')in('Error','Fatal')for i in issues)
bt=TOOLS/'android-15'
def run(*args):return subprocess.check_output(list(map(str,args)),text=True)
def certificate(path):
    result=run('java','-jar',bt/'lib/apksigner.jar','verify','--verbose','--print-certs',path)
    assert 'v2): true' in result
    return re.search(r'certificate SHA-256 digest: (\w+)',result)[1]
cert=certificate(apk);assert cert==certificate(PREVIOUS)=='40e172ca11ff8be42888388f51b94ffb824382dce5235c5f1bd5683b4bb8876e'
run(bt/'zipalign','-c','-P','16','4',apk)
badging=run(bt/'aapt2','dump','badging',apk);previous_badging=run(bt/'aapt2','dump','badging',PREVIOUS)
assert "versionCode='83' versionName='1.1'" in badging
assert re.findall(r'uses-permission[^\n]+',badging)==re.findall(r'uses-permission[^\n]+',previous_badging)
assert "minSdkVersion:'26'" in badging and "targetSdkVersion:'35'" in badging
bridge=(ROOT/'app/src/main/java/org/openbw/androidtest/NativeBridge.java').read_text()
methods=re.findall(r'static native \S+ (\w+)\(',bridge);assert len(methods)==47 and 'replayScenario' in methods
assert re.search(r'ENGINE\s*=\s*84\b',(ROOT/'native/replay.h').read_text())
assert re.search(r'BUILD\s*=\s*84\b',(ROOT/'app/src/main/java/org/openbw/androidtest/NearbyProtocol.java').read_text())
with zipfile.ZipFile(apk)as z,zipfile.ZipFile(PREVIOUS)as old:
    assert z.testzip()is None
    entries={n for n in z.namelist()if n.startswith(('assets/','lib/')) and not n.endswith('/')}
    old_entries={n for n in old.namelist()if n.startswith(('assets/','lib/')) and not n.endswith('/')}
    assert entries==old_entries
    for n in entries:
        assert z.read(n)==old.read(n),n
        if n=='assets/native/ui-languages.tsv':assert z.read(n)==(ROOT/'app/src/main/assets/native/ui-languages.tsv').read_bytes()
    assert not any(n.lower().endswith(('.mpq','.p12','.jks','.keystore','.gid','.fnt','.wasm','.html','.js'))for n in z.namelist())
    for name,digest in proof['librarySha256'].items():
        binary=z.read('lib/'+name);assert hashlib.sha256(binary).hexdigest()==digest,name
        assert binary[:6]==b'\x7fELF\x02\x01'
        if name.endswith('libopenbw.so'):
            symbols=run(TOOLS/'android-ndk-r27d/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm','-D','--defined-only',libs/name)
            for method in methods:assert 'Java_org_openbw_androidtest_NativeBridge_'+method in symbols,method
        phoff=struct.unpack_from('<Q',binary,32)[0];phsize,phcount=struct.unpack_from('<HH',binary,54)
        for i in range(phcount):
            f=struct.unpack_from('<IIQQQQQQ',binary,phoff+phsize*i)
            if f[0]==1:assert f[7]>=16384 and f[2]%16384==f[3]%16384
dest=ROOT/'dist/StarDroid-1.1.apk';dest.parent.mkdir(exist_ok=True);shutil.copyfile(apk,dest)
shutil.copyfile(lint,OUT/lint.name)
report={'passed':True,'version':'1.1','versionCode':83,'apkSha256':sha(dest),'apkBytes':dest.stat().st_size,
    'previousApkSha256':sha(PREVIOUS),'certificateSha256':cert,'originalReleaseSigningIdentity':True,
    'nativeEngineRebuilt':False,'verifiedNativeLibrariesReused':True,'nativeLibrariesUnchangedFromPreviousApk':True,'replaySimulationRules':84,'nearbyProtocolBuild':84,'librarySha256':proof['librarySha256'],'nativeProofSha256':sha(proof_path),
    'jniMethodsVerified':len(methods),'allAssetsUnchanged':True,'permissionsUnchanged':True,'loadAlignmentBytes':16384,
    'lintErrors':0,'lintWarnings':len([i for i in issues if i.get('severity')=='Warning']),
    'physicalDevicesTested':False,'sourceSha256':before}
(ROOT/'validation/package-guide-format11.json').write_text(json.dumps(report,indent=2)+'\n')
(dest.parent/'SHA256SUMS.txt').write_text(sha(dest)+'  '+dest.name+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='sourceSha256'},indent=2))

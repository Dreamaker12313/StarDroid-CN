#!/usr/bin/env python3
"""Validate the delivered APK, native/Java boundary, reports and update identity."""
import hashlib,json,pathlib,re,shutil,subprocess,sys,zipfile,xml.etree.ElementTree as ET
r=pathlib.Path(__file__).resolve().parents[1];apk=r/'dist/StarDroid-1.0.apk';tools=r/'.tools';bt=tools/'android-15';readelf=shutil.which('llvm-readelf') or shutil.which('readelf') or str(tools/'android-ndk-r27d/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf')
def output(*cmd):return subprocess.check_output(list(map(str,cmd)),text=True)
signed=output('java','-jar',bt/'lib/apksigner.jar','verify','--verbose','--print-certs',apk)
cert=re.search(r'certificate SHA-256 digest: (\w+)',signed).group(1)
assert cert=='40e172ca11ff8be42888388f51b94ffb824382dce5235c5f1bd5683b4bb8876e'
if len(sys.argv)>1:
    old=output('java','-jar',bt/'lib/apksigner.jar','verify','--print-certs',sys.argv[1]);assert cert==re.search(r'certificate SHA-256 digest: (\w+)',old).group(1)
subprocess.run([str(bt/'zipalign'),'-c','-P','16','4',str(apk)],check=True)
badging=output(bt/'aapt','dump','badging',apk);assert "name='org.openbw.androidtest'"in badging and "versionCode='65'"in badging and "versionName='1.0'"in badging
assert len(sys.argv)>1, 'Pass the installed previous APK to verify update identity'
previous=output(bt/'aapt','dump','badging',sys.argv[1])
assert "name='org.openbw.androidtest'" in previous
previous_version=re.search(r"versionName='([^']+)'",previous).group(1)
assert int(re.search(r"versionCode='(\d+)'",badging).group(1)) > int(re.search(r"versionCode='(\d+)'",previous).group(1))
for permission in ['INTERNET','ACCESS_COARSE_LOCATION','ACCESS_FINE_LOCATION','BLUETOOTH_SCAN','BLUETOOTH_CONNECT','BLUETOOTH_ADVERTISE','NEARBY_WIFI_DEVICES']:
    assert 'android.permission.'+permission in badging,permission
    if permission in ['ACCESS_COARSE_LOCATION','ACCESS_FINE_LOCATION']:
        declaration=next(line for line in badging.splitlines() if 'uses-permission:' in line and "name='android.permission."+permission+"'" in line)
        assert "maxSdkVersion='32'" in declaration,('legacy-only location permission',declaration)
assert 'android.permission.ACCESS_BACKGROUND_LOCATION' not in badging
assert "application-label:'StarDroid'" in badging
assert "rootProject.name = 'StarDroid'" in (r/'settings.gradle').read_text()
manifest=output(bt/'aapt','dump','xmltree',apk,'AndroidManifest.xml');assert 'com.google.android.gms' not in manifest
methods=re.findall(r'static native\s+[\w\[\]]+\s+(\w+)\(', (r/'app/src/main/java/org/openbw/androidtest/NativeBridge.java').read_text())
libraries={}
with zipfile.ZipFile(apk)as z:
    assert z.testzip()is None
    assert any(n.startswith('classes')and n.endswith('.dex')for n in z.namelist())
    dex=b''.join(z.read(n)for n in z.namelist()if n.startswith('classes')and n.endswith('.dex'))
    for name in ['Lorg/openbw/androidtest/RoomMatch;','Lorg/openbw/androidtest/RoomSnapshot;','Lorg/openbw/androidtest/RoomProtocol;','Lorg/openbw/androidtest/MatchSetup;','Lorg/openbw/androidtest/MatchSnapshot;','Lorg/openbw/androidtest/NativeMapPreview;','Lorg/openbw/androidtest/NativeNearby;','Lorg/openbw/androidtest/NearbyMatch;','Lorg/openbw/androidtest/NearbyMapCodec;','Lorg/openbw/androidtest/NearbyMapCache;','Lorg/openbw/androidtest/LocalTransport;','Lorg/openbw/androidtest/LocalPermissions;']:
        assert name.encode()in dex,name
    assert b'Lcom/google/android/gms/' not in dex
    assert b'Put together by ToadWarrior.' in dex
    assert b'Lorg/openbw/androidtest/NearbyMatch50;' not in dex
    assert 'StarDroid · 1.0'.encode() in dex
    assert b'StarDroid 1.0 Native (65)' in dex
    assert b'Cheats disable replay export.' not in dex
    assert b'OpenBW Android 0.41 Native (42)' not in dex
    assert b'Lorg/openbw/androidtest/NearbyMatch51;' not in dex
    for abi in ['arm64-v8a','x86_64']:
        lib=r/'native-libs'/abi/'libopenbw.so';symbols=output(readelf,'--dyn-syms','--wide',lib)
        for method in methods:assert 'Java_org_openbw_androidtest_NativeBridge_'+method in symbols,method
        for name in ['libopenbw.so','libsmacker.so']:
            lib=r/'native-libs'/abi/name;binary=lib.read_bytes();assert z.read('lib/'+abi+'/'+name)==binary
            if name=='libsmacker.so':
                with zipfile.ZipFile(sys.argv[1])as old_apk:assert old_apk.read('lib/'+abi+'/'+name)==binary,'Decoder changed in upgrade UI fix'
            segments=output(readelf,'-l','--wide',lib)
            for line in segments.splitlines():
                if line.strip().startswith('LOAD'):assert int(line.split()[-1],16)>=16384,line
            libraries[abi+'/'+name]=hashlib.sha256(binary).hexdigest()
    for folder in ['native','missions']:
        for p in (r/'app/src/main/assets'/folder).rglob('*'):
            if p.is_file():assert z.read('assets/'+str(p.relative_to(r/'app/src/main/assets')))==p.read_bytes()
reports=[]
for name in ['branding-v1.0.json','placement-v61.json','native-upgrades-v1.0.json','upgrade-ui-v1.0.json','hud-v59.json','native-v55.json','room-v55.json','room-sockets-v55.json','ui-v58.json','native-results-host-v56.json','tooltip-v56.json','local-permissions-v55.json']:
    item=json.loads((r/'validation'/name).read_text());assert item['passed']
    for path,digest in item.get('sourceSha256',item.get('sources',{})).items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==digest,(name,path)
    reports.append(name)
lint=ET.parse(r/'app/build/reports/lint-results-release.xml');errors=[x.attrib for x in lint.findall('issue')if x.get('severity')in ['Error','Fatal']];assert not errors,errors
report={'version':'1.0','googlePlayServicesRequired':False,'transport':'Android secure Bluetooth + authenticated Wi-Fi Direct; Bluetooth fallback','nativeEngineRebuilt':True,'nativeEngineVersion':'1.0-build65','multiplayerProtocolBuild':60,'upgradeIdentityVerifiedFrom':previous_version,'packageVerified':True,'locationPermissionsCappedAtApi32':True,'backgroundLocationRequested':False,'certificateSha256':cert,'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'bytes':apk.stat().st_size,'abis':['arm64-v8a','x86_64'],'jniMethodsVerified':len(methods),'librarySha256':libraries,'reports':reports,'lintErrors':0,'lintWarnings':len(lint.findall('issue')),'androidHardwareTested':False,'nearbyRadioTested':False,'releaseReady':False}
(r/'validation/native-package-v1.0.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

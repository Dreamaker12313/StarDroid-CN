#!/usr/bin/env python3
"""Verify the 1.0.10 APK, JNI surface, update signing identity and retained assets and updated translations.

Usage: STARDROID_ANDROID_TOOLS=/path/to/tools python3 tests/check_revision80_package.py PREVIOUS_1.0.9_APK
"""
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(os.environ.get('STARDROID_ANDROID_TOOLS', ROOT / '.tools'))
BT = TOOLS / 'android-15'
LLVM = TOOLS / 'android-ndk-r27d/toolchains/llvm/prebuilt/linux-x86_64/bin'
APK = ROOT / 'dist/StarDroid-1.0.10.apk'
PREVIOUS = Path(sys.argv[1])

def run(*args):
    return subprocess.check_output(list(map(str, args)), text=True)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def cert(path):
    output = run('java', '-jar', BT / 'lib/apksigner.jar', 'verify', '--verbose', '--print-certs', path)
    assert 'v2): true' in output
    return re.search(r'certificate SHA-256 digest: (\w+)', output)[1]

certificate = cert(APK)
assert certificate == cert(PREVIOUS) == '40e172ca11ff8be42888388f51b94ffb824382dce5235c5f1bd5683b4bb8876e'
run(BT / 'zipalign', '-c', '-P', '16', '4', APK)
badging = run(BT / 'aapt2', 'dump', 'badging', APK)
old_badging = run(BT / 'aapt2', 'dump', 'badging', PREVIOUS)
assert "name='org.openbw.androidtest' versionCode='80' versionName='1.0.10'" in badging
assert "name='org.openbw.androidtest' versionCode='79' versionName='1.0.9'" in old_badging
assert "minSdkVersion:'26'" in badging and "targetSdkVersion:'35'" in badging
assert re.findall(r'uses-permission[^\n]+', badging) == re.findall(r'uses-permission[^\n]+', old_badging)
bridge = (ROOT / 'app/src/main/java/org/openbw/androidtest/NativeBridge.java').read_text()
methods = re.findall(r'static native \S+ (\w+)\(', bridge)
assert {'rawText', 'archiveText', 'campaignEffect', 'mapScenario', 'cursor'} <= set(methods)
libraries = {}
translation = 'assets/native/ui-languages.tsv'
with zipfile.ZipFile(APK) as package, zipfile.ZipFile(PREVIOUS) as previous:
    assert package.testzip() is None
    entries = {n for n in package.namelist() if n.startswith(('assets/', 'lib/')) and not n.endswith('/')}
    old = {n for n in previous.namelist() if n.startswith(('assets/', 'lib/')) and not n.endswith('/')}
    assert entries == old
    assert package.read(translation) == (ROOT / 'app/src/main' / translation).read_bytes()
    changed = sorted(n for n in old if package.read(n) != previous.read(n))
    # This update changes code and UI translations only. Both engine binaries must be rebuilt;
    # libsmacker can differ because __FILE__ includes the build checkout path.
    engines = {'lib/arm64-v8a/libopenbw.so', 'lib/x86_64/libopenbw.so'}
    decoders = {'lib/arm64-v8a/libsmacker.so', 'lib/x86_64/libsmacker.so'}
    assert engines <= set(changed) <= engines | decoders | {translation}, changed
    assert all(package.read(n) == previous.read(n) for n in old if n.startswith('assets/') and n != translation)
    # The same decoder source is rebuilt; its __FILE__ strings include the
    # checkout path, so its binary hash need not equal the previous checkout.
    assert sha((ROOT / 'vendor/libsmacker/smacker.c').read_bytes()) == 'd2a9adda0f8d36e952cdb44ec2fefbbe1f4146319272e779eed15f6c06a813a5'
    assert not any(n.lower().endswith(('.mpq', '.p12', '.jks', '.keystore', '.gid', '.fnt', '.wasm', '.html', '.js')) for n in package.namelist())
    dex = b''.join(package.read(n) for n in package.namelist() if n.endswith('.dex'))
    for value in ['Diagnostics / credits', 'Copy', 'Original larvae selection', '+ over camera area', 'Interface language', 'One larva morph per press', 'Invincibility', 'Gamepad controls', 'Import StarDroid save', 'Export StarDroid save', 'prepareEntry', 'gamepad-controls']:
        assert value.encode() in dex, value
    for value in ['Menu files need repair', 'Repair menu files', 'Diagnostic report', 'Menu artwork needs attention', 'Landroid/webkit/WebView;']:
        assert value.encode() not in dex, value
    for abi, machine in [('arm64-v8a', 183), ('x86_64', 62)]:
        for name in ('libopenbw.so', 'libsmacker.so'):
            path = ROOT / 'native-libs' / abi / name
            binary = path.read_bytes()
            assert binary == package.read('lib/' + abi + '/' + name)
            assert binary[:6] == b'\x7fELF\x02\x01'
            assert struct.unpack_from('<H', binary, 18)[0] == machine
            phoff = struct.unpack_from('<Q', binary, 32)[0]
            phsize, phcount = struct.unpack_from('<HH', binary, 54)
            loads = 0
            for i in range(phcount):
                fields = struct.unpack_from('<IIQQQQQQ', binary, phoff + phsize * i)
                if fields[0] == 1:
                    assert fields[7] >= 16384 and fields[2] % 16384 == fields[3] % 16384
                    loads += 1
            assert loads
            if name == 'libopenbw.so':
                symbols = run(LLVM / 'llvm-nm', '-D', '--defined-only', path)
                exported = {line.split()[-1] for line in symbols.splitlines() if line.split()}
                for method in methods:
                    assert 'Java_org_openbw_androidtest_NativeBridge_' + method in exported, method
            libraries[abi + '/' + name] = sha(binary)
lint = ET.parse(ROOT / 'app/build/reports/lint-results-release.xml')
assert not [i for i in lint.findall('issue') if i.get('severity') in ('Error', 'Fatal')]
rows = [s.split('\t') for s in (ROOT / 'app/src/main/assets/native/ui-languages.tsv').read_text().splitlines() if s and not s.startswith('#')]
assert len(rows) == len({s[0] for s in rows}) and all(len(s) == 5 and all(s) for s in rows)
protocol = (ROOT / 'app/src/main/java/org/openbw/androidtest/NearbyProtocol.java').read_text()
assert re.search(r'BUILD\s*=\s*80\b', protocol)
# Check only the current change's focused reports. Historical validation files
# describe their own builds and must never be silently relabelled as current.
reports = ['controls-v80.json', 'gamepad-v80.json', 'storage80.json', 'ai-production-final80.json', 'protocol-v80.json', 'map-scroll-v80.json', 'campaign-v80.json', 'music-v80.json', 'native-build80.json', 'cinematic-cache80.json']
for filename in reports:
    checked = json.loads((ROOT / 'validation' / filename).read_text())
    assert checked['passed'], filename
    fingerprints = checked.get('sourceSha256', {})
    assert fingerprints, (filename, 'missing source fingerprints')
    for name, digest in fingerprints.items():
        assert sha((ROOT / name).read_bytes()) == digest, (filename, name)
report = {
    'passed': True, 'version': '1.0.10', 'versionCode': 80,
    'apkSha256': sha(APK.read_bytes()), 'apkBytes': APK.stat().st_size,
    'previousApkSha256': sha(PREVIOUS.read_bytes()),
    'certificateSha256': certificate, 'originalReleaseSigningIdentity': True,
    'nativeEngineRebuilt': True, 'nativeEngineVersion': '1.0.10-build80',
    'changedNativeAndAssetEntries': changed, 'addedAssets': [],
    'unchangedNativeAndAssetEntries': len(old) - len(changed),
    'permissionsUnchanged': True, 'multiplayerProtocolBuild': 80,
    'decoderBinaryChanges': sorted(set(changed) & decoders), 'decoderSourceUnchanged': True, 'jniMethodsVerified': len(methods),
    'loadAlignmentBytes': 16384, 'librarySha256': libraries,
    'translationRows': len(rows), 'lintErrors': 0,
    'lintWarnings': len(lint.findall('issue')), 'physicalDevicesTested': False,
    'regressionReports': reports,
    'sourceSha256': {'tests/check_revision80_package.py': sha(Path(__file__).read_bytes())},
}
(ROOT / 'validation/package-v80.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))

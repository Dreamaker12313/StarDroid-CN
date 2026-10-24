#!/usr/bin/env python3
"""Verify the crash-fix APK, update identity and rebuilt native libraries."""
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
APK = ROOT / 'dist/StarDroid-1.0.apk'
PREVIOUS = Path(sys.argv[1])


def run(*args):
    return subprocess.check_output([str(arg) for arg in args], text=True)


def cert(path):
    result = run('java', '-jar', BT / 'lib/apksigner.jar', 'verify', '--verbose', '--print-certs', path)
    assert 'v2): true' in result
    return re.search(r'certificate SHA-256 digest: (\w+)', result)[1]


certificate = cert(APK)
assert certificate == cert(PREVIOUS), 'Update signing identity changed'
assert certificate == json.loads((ROOT / 'validation/native-trace-package-v1.0.json').read_text())['certificateSha256']
run(BT / 'zipalign', '-c', '-P', '16', '4', APK)
badging = run(BT / 'aapt', 'dump', 'badging', APK)
old_badging = run(BT / 'aapt', 'dump', 'badging', PREVIOUS)
assert "versionCode='69' versionName='1.0'" in badging
assert "versionCode='68' versionName='1.0'" in old_badging
assert "name='org.openbw.androidtest'" in badging and "application-label:'StarDroid'" in badging
assert "sdkVersion:'26'" in badging
assert re.findall(r"uses-permission[^\n]+", badging) == re.findall(r"uses-permission[^\n]+", old_badging)
# Decoder source hash from build 67, before rebuilding in the renamed project.
decoder = 'vendor/libsmacker/smacker.c'
assert hashlib.sha256((ROOT / decoder).read_bytes()).hexdigest() == 'd2a9adda0f8d36e952cdb44ec2fefbbe1f4146319272e779eed15f6c06a813a5'
bridge = (ROOT / 'app/src/main/java/org/openbw/androidtest/NativeBridge.java').read_text()
methods = re.findall(r'static native \S+ (\w+)\(', bridge)
assert methods
libraries = {}
with zipfile.ZipFile(APK) as package, zipfile.ZipFile(PREVIOUS) as previous:
    assert package.testzip() is None
    entries = {name for name in package.namelist() if name.startswith(('assets/', 'lib/')) and not name.endswith('/')}
    assert entries == {name for name in previous.namelist() if name.startswith(('assets/', 'lib/')) and not name.endswith('/')}
    changed = sorted(name for name in entries if package.read(name) != previous.read(name))
    assert changed == [f'lib/{abi}/libopenbw.so' for abi in ('arm64-v8a', 'x86_64')], changed
    assert not any(name.lower().endswith(('.mpq', '.p12', '.jks', '.keystore', '.wasm', '.html', '.js')) for name in package.namelist())
    dex = b''.join(package.read(name) for name in package.namelist() if name.endswith('.dex'))
    for expected in [b'StarDroid 1.0 Native (69)', b'Put together by ToadWarrior.',
                     b'Lorg/openbw/androidtest/AppDiagnostics;', b'Lorg/openbw/androidtest/NativeCrashTrace;', b'Lorg/openbw/androidtest/CameraPan;']:
        assert expected in dex, expected
    for forbidden in [b'Landroid/webkit/WebView;', b'Lcom/google/android/gms/', b'Cheats disable replay export.']:
        assert forbidden not in dex, forbidden
    for abi, machine in [('arm64-v8a', 183), ('x86_64', 62)]:
        for name in ('libopenbw.so', 'libsmacker.so'):
            path = ROOT / 'native-libs' / abi / name
            binary = path.read_bytes()
            assert binary == package.read('lib/' + abi + '/' + name)
            assert binary[:6] == b'\x7fELF\x02\x01'
            assert struct.unpack_from('<H', binary, 18)[0] == machine
            phoff = struct.unpack_from('<Q', binary, 32)[0]
            phsize, phcount = struct.unpack_from('<HH', binary, 54)
            alignments = []
            for i in range(phcount):
                fields = struct.unpack_from('<IIQQQQQQ', binary, phoff + phsize * i)
                if fields[0] == 1:
                    assert fields[7] >= 16384 and fields[2] % 16384 == fields[3] % 16384
                    alignments.append(fields[7])
            assert alignments
            if name == 'libopenbw.so':
                symbols = run(LLVM / 'llvm-nm', '-D', '--defined-only', path)
                for method in methods:
                    assert 'Java_org_openbw_androidtest_NativeBridge_' + method in symbols, method
            libraries[abi + '/' + name] = hashlib.sha256(binary).hexdigest()
lint = ET.parse(ROOT / 'app/build/reports/lint-results-release.xml')
errors = [issue.attrib for issue in lint.findall('issue') if issue.get('severity') in ('Error', 'Fatal')]
assert not errors, errors
regression = json.loads((ROOT / 'validation/native-placement-v1.0.json').read_text())
for report_name in ('native-placement-v1.0.json', 'placement-scroll-v1.0.json'):
    checked = json.loads((ROOT / 'validation' / report_name).read_text())
    assert checked['passed'] and checked['versionCode'] == 69
    for name, digest in checked['sourceSha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
assert hashlib.sha256((ROOT / 'native-engine/ui/ui.h').read_bytes()).hexdigest() == regression['preparedUiSha256']
report = {
    'passed': True, 'version': '1.0', 'versionCode': 69,
    'apkSha256': hashlib.sha256(APK.read_bytes()).hexdigest(), 'apkBytes': APK.stat().st_size,
    'certificateSha256': certificate, 'updateIdentityFromBuild68Verified': True,
    'nativeEngineRebuilt': True, 'nativeEngineVersion': '1.0-build69',
    'changedNativeAndAssetEntries': changed, 'unchangedNativeAndAssetEntries': len(entries) - len(changed),
    'gameAssetsUnchanged': True, 'permissionsUnchanged': True, 'multiplayerProtocolBuild': 60,
    'decoderSourceUnchanged': True,
    'decoderBinariesUnchanged': True,
    'jniMethodsVerified': len(methods), 'loadAlignmentBytes': 16384, 'librarySha256': libraries,
    'lintErrors': 0, 'lintWarnings': len(lint.findall('issue')), 'physicalDevicesTested': False,
    'regressionReports': ['native-placement-v1.0.json', 'placement-scroll-v1.0.json'],
    'sourceSha256': {'tests/check_placement_package.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
}
(ROOT / 'validation/placement-package-v1.0.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))

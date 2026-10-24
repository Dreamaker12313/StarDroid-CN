#!/usr/bin/env python3
"""Verify the native release APK, JNI bindings, architectures and update key."""
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import zipfile
import tarfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(os.environ.get('OPENBW_ANDROID_TOOLS', ROOT / '.tools'))
BT = TOOLS / 'android-15'
LLVM = TOOLS / 'android-ndk-r27d/toolchains/llvm/prebuilt/linux-x86_64/bin'
APK = ROOT / 'dist/OpenBW-Android-0.46.apk'

def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True)

# The removed external Zerg bot must be absent from both source inputs and APK.
for relative in ('vendor/ZZZKBot-7183e37b6b41.tar.gz', 'vendor/bwapi-48124ba8ed1b.tar.gz', 'native/bot_fatal.h', 'app/src/main/assets/game/openbw-bot.wasm'):
    assert not (ROOT/relative).exists(), 'Retired bot input remains: '+relative
upstream=json.loads((ROOT/'UPSTREAM.json').read_text())
with tarfile.open(ROOT/upstream['source_archive']['file']) as source:
    assert not any(m.name=='web/bot' or m.name.startswith('web/bot/') for m in source)
assert 'botDependencies' not in json.loads((ROOT/'ENGINE-BUILD.json').read_text())

signature = run('java', '-jar', BT / 'lib/apksigner.jar', 'verify',
                '--verbose', '--print-certs', APK)
certificate = re.search(r'certificate SHA-256 digest: (\w+)', signature)[1]
assert certificate == json.loads((ROOT / 'validation/apk-v22.json').read_text())['certificateSha256']
assert 'v2): true' in signature and 'v3): true' in signature
run(BT / 'zipalign', '-c', '-P', '16', '4', APK)
badging = run(BT / 'aapt', 'dump', 'badging', APK)
assert "versionCode='47' versionName='0.46'" in badging
assert "name='org.openbw.androidtest'" in badging
assert "sdkVersion:'26'" in badging
assert 'android.permission.INTERNET' not in badging
bridge = (ROOT / 'app/src/main/java/org/openbw/androidtest/NativeBridge.java').read_text()
methods = re.findall(r'static native \S+ (\w+)\(', bridge)
libraries = []
with zipfile.ZipFile(APK) as z:
    assert z.testzip() is None
    for icon in ('res/drawable/ic_launcher.xml','res/drawable/ic_launcher_background.xml','res/drawable/ic_launcher_foreground.xml','res/drawable-v33/ic_launcher.xml'):
        assert icon in z.namelist(), 'Missing Wraith launcher resource: '+icon
    assert not any(n.lower().endswith(('.html', '.js', '.wasm')) for n in z.namelist())
    assert b'Landroid/webkit/WebView;' not in z.read('classes.dex')
    assets = [n for n in z.namelist() if n.startswith('assets/') and not n.endswith('/')]
    for n in assets:
        assert z.read(n) == (ROOT / 'build-native/apk' / n).read_bytes()
    for abi, machine in [('arm64-v8a', 183), ('x86_64', 62)]:
        for name in ['libopenbw.so', 'libsmacker.so']:
            p = ROOT / 'native-libs' / abi / name
            b = p.read_bytes()
            assert z.read('lib/' + abi + '/' + name) == b
            assert b[:6] == b'\x7fELF\x02\x01'
            assert struct.unpack_from('<H', b, 18)[0] == machine
            phoff = struct.unpack_from('<Q', b, 32)[0]
            phsize, phcount = struct.unpack_from('<HH', b, 54)
            alignments = []
            for i in range(phcount):
                fields = struct.unpack_from('<IIQQQQQQ', b, phoff + phsize * i)
                if fields[0] == 1:
                    alignments.append(fields[7])
                    assert fields[7] >= 16384
                    assert fields[2] % 16384 == fields[3] % 16384
            assert alignments
            exports = run(LLVM / 'llvm-nm' if (LLVM / 'llvm-nm').exists() else 'nm', '-D', '--defined-only', p)
            if name == 'libopenbw.so':
                for method in methods:
                    assert 'Java_org_openbw_androidtest_NativeBridge_' + method in exports
            dependencies = re.findall(r'NEEDED.*?\[(.*?)\]', run(LLVM / 'llvm-readelf' if (LLVM / 'llvm-readelf').exists() else 'readelf', '-d', p))
            assert set(dependencies) <= {'libsmacker.so', 'libjnigraphics.so', 'libdl.so', 'libm.so', 'libc.so'}
            libraries.append(dict(abi=abi, file=name, sha256=hashlib.sha256(b).hexdigest(),
                                  bytes=len(b), loadAlignments=alignments, dependencies=dependencies))
apk_hash = hashlib.sha256(APK.read_bytes()).hexdigest()
test_apk_hash = hashlib.sha256((ROOT / 'build-native/instrumentation/native-tests.apk').read_bytes()).hexdigest()

def read_report(name, version='46'):
    path = ROOT / 'validation' / ('native-' + name + '-v' + version + '.json')
    return json.loads(path.read_text()) if path.exists() else {}

def source_matches(result):
    sources = result.get('sourceSha256', {})
    return bool(sources) and all((ROOT / path).is_file() and hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
                                 for path, digest in sources.items())

android_suites = {}
for name in ('android', 'parity', 'polish', 'feedback', 'gameplay-android'):
    result = read_report(name)
    android_suites[name] = (result.get('passed') is True and
                           result.get('apkSha256') == apk_hash and
                           result.get('testApkSha256') == test_apk_hash)
matrix = read_report('gameplay')
matrix_verified = (matrix.get('passed') is True and matrix.get('failCount') == 0 and
                   matrix.get('passCount') == 233 and source_matches(matrix))
presentation = read_report('presentation')
presentation_verified = presentation.get('passed') is True and source_matches(presentation)
imports = read_report('import')
imports_verified = (imports.get('passed') is True and source_matches(imports) and
                    imports.get('baseMaps') == 31 and imports.get('expansionMaps') == 33 and
                    imports['movies']['OpenBW-Cinematics.zip']['entryCount'] == 13 and
                    imports['movies']['OpenBW-Cinematics-BroodWar.zip']['entryCount'] == 4)
patch = read_report('patch-preparation', '46')
patch_verified = patch.get('passed') is True and source_matches(patch)
revision = read_report('revision-android')
revision_verified = (revision.get('passed') is True and revision.get('apkSha256') == apk_hash
                     and revision.get('testApkSha256') == test_apk_hash)
feedback = read_report('feedback-host', '38')
feedback_verified = feedback.get('passed') is True and source_matches(feedback)
export = read_report('mission-export')
export_verified = (export.get('passed') is True and export.get('apkSha256') == apk_hash
                   and export.get('testApkSha256') == test_apk_hash)
missions = read_report('missions-host')
missions_verified = (missions.get('passed') is True and source_matches(missions) and len(missions.get('maps', [])) == 64)
hover = read_report('hover-android')
hover_verified = (hover.get('passed') is True and hover.get('apkSha256') == apk_hash
                  and hover.get('testApkSha256') == test_apk_hash)
saves = read_report('saves-host')
saves_verified = saves.get('passed') is True and source_matches(saves) and saves.get('freshProcessRead') is True
save_android = read_report('saves-android')
save_android_verified = (save_android.get('passed') is True and save_android.get('apkSha256') == apk_hash
                         and save_android.get('testApkSha256') == test_apk_hash and save_android.get('survivesProcessRestart') is True)
audit=read_report('campaign-audit')
audit_verified=(audit.get('passed') is True and audit.get('mapCount')==64 and source_matches(audit))
archive_verified=(save_android_verified and len(save_android.get('originalMissionArchives',[]))==64 and save_android.get('all64ImportedMissionSaveLoadAndNativeMapRead') is True)
real=read_report('campaign-real')
real_verified=(real.get('passed') is True and real.get('originalCoreAssets') is True and real.get('missionCount')==64 and source_matches(real))
branches=read_report('campaign-branches')
branches_verified=(branches.get('passed') is True and len(branches.get('cases',[]))==8 and source_matches(branches))
world=read_report('campaign-android')
world_verified=(world.get('passed') is True and world.get('survivesProcessRestart') is True and world.get('apkSha256')==apk_hash and world.get('testApkSha256')==test_apk_hash)
objectives=read_report('campaign-objectives')
objectives_verified=(objectives.get('passed') is True and objectives.get('missionCount')==64 and objectives.get('victoryAttempts') is True and all(m.get('outcome')==1 for m in objectives.get('missions',[])) and source_matches(objectives))
controls=read_report('controls-android')
controls_verified=(controls.get('passed') is True and controls.get('apkSha256')==apk_hash and controls.get('testApkSha256')==test_apk_hash)
reader=read_report('archive')
reader_verified=reader.get('passed') is True and source_matches(reader)
briefing=read_report('briefing-android')
briefing_verified=(briefing.get('passed') is True and briefing.get('apkSha256')==apk_hash and briefing.get('testApkSha256')==test_apk_hash)
results_ui=read_report('results-host')
results_ui_verified=results_ui.get('passed') is True and source_matches(results_ui)
focused=read_report('revision46-host')
focused_verified=focused.get('passed') is True and source_matches(focused)
focused_ui=read_report('revision46-android')
focused_ui_verified=(focused_ui.get('passed') is True and focused_ui.get('apkSha256')==apk_hash and focused_ui.get('testApkSha256')==test_apk_hash)
release_ready = (focused_ui_verified and focused_verified and briefing_verified and reader_verified and objectives_verified and controls_verified and real_verified and branches_verified and world_verified and audit_verified and archive_verified and saves_verified and save_android_verified and hover_verified and missions_verified and export_verified and all(android_suites.values()) and matrix_verified and presentation_verified
                 and imports_verified and patch_verified and revision_verified and feedback_verified)
report = dict(packageChecksPassed=True, resultsHostRenderVerified=results_ui_verified, focusedRevisionUiVerified=focused_ui_verified, focusedRevisionVerified=focused_verified, briefingAndroidVerified=briefing_verified, package='org.openbw.androidtest', versionName='0.46', versionCode=47,
              apkSha256=hashlib.sha256(APK.read_bytes()).hexdigest(), apkBytes=APK.stat().st_size,
              testApkSha256=test_apk_hash, certificateSha256=certificate, updateCertificateMatches=True, v2Signature=True,
              v3Signature=True, zipCRC=True, zipAligned16KiB=True, assetByteMatches=len(assets),
              webViewClassReferenced=False, webRuntimeAssetsPackaged=False,
              jniMethodsPerArchitecture=len(methods), libraries=libraries,
              androidSuites=android_suites, freshGameplayMatrixVerified=matrix_verified,
              nativePresentationVerified=presentation_verified, combinedImportVerified=imports_verified,
              nativePatchPreparationVerified=patch_verified,
              feedbackHostVerified=feedback_verified, revisionAndroidVerified=revision_verified,
              missionExportAndroidVerified=export_verified, missionHostVerified=missions_verified,
              campaignAuditVerified=audit_verified, originalMissionSaveArchivesVerified=archive_verified,
              hoverAndroidVerified=hover_verified, savesHostVerified=saves_verified, savesAndroidVerified=save_android_verified, packageIntegrityPassed=True, retiredExternalBotAbsent=True, releaseReady=release_ready,
              missingOriginalDataEvidence=[name for name, passed in android_suites.items() if not passed] +
                  [name for name, passed in [('gameplay', matrix_verified), ('presentation', presentation_verified),
                                            ('import', imports_verified)] if not passed],
              gameplayChecks=matrix.get('passCount', 0), hardwareTested=False,
              realCampaignStartupAndSavesVerified=real_verified, campaignBranchesVerified=branches_verified, realAndroidWorldSavesVerified=world_verified,
              controlsAndroidVerified=controls_verified, assistedMissionChecksVerified=objectives_verified,
              assistedVictories=sum(m.get('outcome')==1 for m in objectives.get('missions',[])), archiveReaderVerified=reader_verified)
(ROOT / 'validation/native-package-v46.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
assert real_verified and branches_verified and world_verified, 'Current real campaign evidence missing or mismatched'
assert controls_verified and objectives_verified, 'Current controls or assisted campaign evidence missing or mismatched'
assert reader_verified, 'Current archive-reader evidence missing or mismatched'
assert audit_verified and archive_verified and saves_verified and save_android_verified and hover_verified and missions_verified and export_verified and revision_verified and feedback_verified and patch_verified, 'Current feedback evidence missing or mismatched'
assert all(android_suites.values()), 'Current APK Android validation missing or mismatched'
assert matrix_verified and presentation_verified and imports_verified and patch_verified, 'Current native/source evidence does not match'

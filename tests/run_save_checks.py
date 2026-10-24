#!/usr/bin/env python3
"""Persistent snapshot regression checks; all unit/art data is synthetic."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
exe=root/'build-native/host/native-saves'
logs=[]
with tempfile.TemporaryDirectory(prefix='openbw-snapshot-') as temp:
 path=Path(temp)/'mission.obwstate'
 for args in ([],['write',str(path)],['read',str(path)]):
  p=subprocess.run([str(exe),*args],capture_output=True,text=True)
  logs.append(p.stdout);print(p.stdout,end='')
  if p.returncode:raise SystemExit(p.stderr or p.returncode)
sources=['native/save_state.h','native/runtime.cpp','native/audio.h','tests/native_saves.cpp',
 'tests/native_fixture.h','tests/build_native_host.py','tests/run_save_checks.py','scripts/prepare_native.py',
 'scripts/prepare_feedback.py','scripts/prepare_presentation.py','UPSTREAM.json',
 *['patches/'+n for n in ['campaign.patch','native-gameplay.patch','native-revision.patch','native-missions.patch','native-polish33.patch','native-saves34.patch','native-campaign36.patch','native-finale37.patch','native-controls38.patch']]]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(version='0.38',passed=True,freshProcessRead=True,originalCoreAssets=False,fullCampaignPlaythrough=False,
 checks=[x[5:] for x in logs[0].splitlines() if x.startswith('PASS ')],stdout=''.join(logs),
 binarySha256=sha(exe),sourceSha256={n:sha(root/n) for n in sources})
(root/'validation/native-saves-host-v38.json').write_text(json.dumps(report,indent=2)+'\n')

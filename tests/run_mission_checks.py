#!/usr/bin/env python3
"""Record current native checks; original exported maps remain external inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('maps', type=Path)
args = parser.parse_args()
common = ['UPSTREAM.json', 'native/runtime.cpp', 'native/save_state.h', 'native/audio.h',
          'patches/campaign.patch', 'patches/native-gameplay.patch',
          'patches/native-revision.patch', 'patches/native-missions.patch', 'patches/native-polish33.patch', 'patches/native-saves34.patch', 'patches/native-campaign36.patch', 'patches/native-finale37.patch', 'patches/native-controls38.patch',
          'scripts/prepare_native.py', 'scripts/prepare_presentation.py',
          'scripts/prepare_feedback.py', 'tests/build_native_host.py',
          'tests/native_fixture.h', 'tests/run_mission_checks.py']
for suite in ('feedback', 'missions'):
    executable = ROOT / 'build-native/host' / ('native-' + suite)
    command = [str(executable)] + ([str(args.maps)] if suite == 'missions' else [])
    result = subprocess.run(command, text=True, capture_output=True)
    report = dict(version='0.38', passed=result.returncode == 0,
                  scope='Original CHK records with synthetic unit/terrain state' if suite == 'missions'
                        else 'Synthetic native engine state',
                  originalMissionMaps=suite == 'missions', originalCoreAssets=False,
                  originalCampaignPlaythrough=False, stdout=result.stdout, stderr=result.stderr,
                  binarySha256=sha(executable),
                  checks=[line[5:] for line in result.stdout.splitlines() if line.startswith('PASS ')],
                  sourceSha256={name:sha(ROOT/name) for name in common + ['tests/native_'+suite+'.cpp']})
    report['checkGroups'] = len(report['checks'])
    if suite == 'missions':
        report['maps'] = [{'mission':p.stem, 'bytes':p.stat().st_size, 'sha256':sha(p)}
                          for p in sorted(args.maps.glob('*.chk'))]
    (ROOT/'validation'/('native-'+suite+'-host-v38.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(result.stdout, end='')
    if result.returncode:
        raise SystemExit(result.stderr or f'{suite} failed')

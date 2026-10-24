#!/usr/bin/env python3
"""Ensure a pristine checkout receives gameplay patches, and preparation is repeatable."""
import hashlib, json, pathlib, subprocess, sys, tarfile, tempfile

root = pathlib.Path(__file__).resolve().parents[1]
meta = json.loads((root / 'UPSTREAM.json').read_text())
archive = root / meta['source_archive']['file']
assert hashlib.sha256(archive.read_bytes()).hexdigest() == meta['source_archive']['sha256']
with tempfile.TemporaryDirectory(prefix='openbw-patch-check-') as temp:
    stage = pathlib.Path(temp)
    with tarfile.open(archive) as source:
        source.extractall(stage, filter='data')
    def patch(*args):
        return subprocess.run(['patch', '--batch', *args], cwd=stage,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert patch('-p1', '-i', str(root / 'patches/campaign.patch')).returncode == 0
    gameplay = str(root / 'patches/native-gameplay.patch')
    def applied():
        return patch('--force', '--dry-run', '-R', '-p1', '-i', gameplay).returncode == 0
    assert not applied(), 'Pristine source incorrectly reported as patched'
    assert patch('--forward', '-p1', '-i', gameplay).returncode == 0
    assert applied(), 'Gameplay patch not detected after application'
    sys.path.insert(0, str(root / 'scripts'))
    from prepare_presentation import prepare as presentation
    from prepare_feedback import prepare as feedback
    presentation(stage)
    feedback(stage)
    before = {name: (stage / name).read_bytes() for name in ('web/sandbox.h', 'web/wasm_main.cpp', 'web/campaign.h', 'web/campaign_ai.h', 'ui/ui.h', 'bwgame.h', 'actions.h', 'data_loading.h', 'replay_saver.h')}
    feedback(stage)
    assert all((stage / name).read_bytes() == contents for name, contents in before.items())
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-revision.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-missions.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-polish33.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-saves34.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-campaign36.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-finale37.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-controls38.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-polish39.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-polish40.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-polish41.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-polish42.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-ai43.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-polish44.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-ai45.patch')).returncode == 0
    assert patch('--forward', '-p1', '-i', str(root/'patches/native-polish46.patch')).returncode == 0
    before = {name: (stage/name).read_bytes() for name in before}
    # Fresh reconstruction avoids guessing patch state after later patches have
    # legitimately changed the context of earlier hunks.
    with tempfile.TemporaryDirectory(prefix='openbw-patch-repeat-') as second:
        second=pathlib.Path(second)
        with tarfile.open(archive) as source:source.extractall(second,filter='data')
        for name in ('campaign.patch','native-gameplay.patch'):
            subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches'/name)],cwd=second,check=True,stdout=subprocess.DEVNULL)
        presentation(second);feedback(second)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-revision.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-missions.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-polish33.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-saves34.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-campaign36.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-finale37.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-controls38.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-polish39.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-polish40.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-polish41.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-polish42.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-ai43.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-polish44.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-ai45.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(root/'patches/native-polish46.patch')],cwd=second,check=True,stdout=subprocess.DEVNULL)
        assert all((second/name).read_bytes()==contents for name,contents in before.items())
report = {'passed': True, 'checks': ['pristine source is unpatched', 'gameplay patch applies',
    'applied patch is detected', 'ordered presentation, feedback, revision, mission and polish patches apply',
    'feedback patch is idempotent', 'fresh reconstruction is byte-identical']}
report['sourceSha256'] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
    ('UPSTREAM.json', 'patches/campaign.patch', 'patches/native-gameplay.patch', 'patches/native-revision.patch', 'patches/native-missions.patch', 'patches/native-polish33.patch', 'patches/native-saves34.patch', 'patches/native-campaign36.patch', 'patches/native-finale37.patch', 'patches/native-controls38.patch', 'patches/native-polish39.patch', 'patches/native-polish40.patch', 'patches/native-polish41.patch', 'patches/native-polish42.patch', 'patches/native-ai43.patch', 'patches/native-polish44.patch', 'patches/native-ai45.patch', 'patches/native-polish46.patch',
     'scripts/prepare_native.py', 'scripts/prepare_presentation.py', 'scripts/prepare_feedback.py', 'tests/native_patch_preparation.py')}
(root / 'validation/native-patch-preparation-v46.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))

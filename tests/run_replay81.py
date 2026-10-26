#!/usr/bin/env python3
"""Exercise recorded commands, AI parity, playback isolation and malformed .rep files."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('core_dir', type=Path, help='Directory containing STARDAT.MPQ, BROODAT.MPQ and patch_rt.mpq')
p.add_argument('--map', type=Path, default=ROOT/'app/src/main/assets/native/weave.scx')
p.add_argument('--skip-build', action='store_true')
p.add_argument('--timeout', type=int, default=240)
a = p.parse_args()
inputs = [a.core_dir.resolve()/n for n in ('STARDAT.MPQ', 'BROODAT.MPQ', 'patch_rt.mpq')]
inputs.append(a.map.resolve())
for path in inputs:
    if not path.is_file():
        p.error('Missing input: '+str(path))
out = ROOT/'build-native/replay81'
out.mkdir(parents=True, exist_ok=True)
report_path = ROOT/'validation/replay-v81.json'
tracked = ['tests/native_replay81.cpp', 'tests/run_replay81.py', 'tests/build_native_host.py',
           'native/replay.h', 'native/runtime.cpp', 'native/multiplayer.h', 'native/hero_mode.h',
           'native/save_state.h', 'native/generated/wasm_main.cpp', 'native/generated/wasm_backend.cpp',
           'scripts/prepare_native.py', 'patches/native-supply81.patch', 'patches/native-addon-sound81.patch']
engine = ['bwgame.h', 'actions.h', 'replay.h', 'replay_saver.h', 'web/sandbox.h', 'web/campaign_ai.h']
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def sources():
    return {name:sha(ROOT/name) for name in tracked}
def run(name, command):
    log = out/(name+'.log')
    print('Running '+name, flush=True)
    with log.open('w') as stream:
        result = subprocess.run([str(v) for v in command], cwd=ROOT, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=a.timeout)
    text = log.read_text()
    if result.returncode:
        print(text[-14000:], file=sys.stderr)
        raise RuntimeError(f'{name} failed ({result.returncode}); see {log}')
    return text
report = dict(version=81, topic='Replay capture and playback', passed=False,
              generatedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              scope='Native host simulation with locally supplied original data; not Android-device UI testing.')
try:
    initial = sources()
    initial_engine = {name:sha(ROOT/'native-engine'/name) for name in engine}
    if not a.skip_build:
        # Ordered engine patches are prepared separately. Never regenerate shared
        # native inputs while other ABI builds or tests may be running.
        run('build', [sys.executable, ROOT/'tests/build_native_host.py', 'replay81', '--skip-prepare'])
    text = run('native', [ROOT/'build-native/host/native-replay81', a.core_dir.resolve(), a.map.resolve(), out/'replay-frame.ppm'])
    lines = text.splitlines()
    scenarios = [dict(re.findall(r'(\w+)=(\d+)', line)) for line in lines if line.startswith('PASS roundtrip ')]
    if len(scenarios) != 10 or not any(re.fullmatch(r'PASS \d+ checks in 12 replay scenarios', line) for line in lines):
        raise RuntimeError('Incomplete replay regression output')
    if not any(line.startswith('PASS classic human-only') for line in lines) or not any(line.startswith('PASS nearby two-player') for line in lines):
        raise RuntimeError('Missing classic/nearby replay validation')
    if not any(line.startswith('PASS native renderer:') for line in lines):
        raise RuntimeError('Missing replay renderer validation')
    capture = out/'replay-frame.png'
    with Image.open(out/'replay-frame.ppm') as frame:
        if frame.size != (640, 480):
            raise RuntimeError('Unexpected replay framebuffer dimensions')
        frame.save(capture)
    current_engine = {name:sha(ROOT/'native-engine'/name) for name in engine}
    if sources() != initial or current_engine != initial_engine:
        raise RuntimeError('Native test sources changed during validation; rerun on the integrated source')
    report.update(sourceSha256=initial, integratedEngineHashes=initial_engine,
                  regressions=lines, scenarios=scenarios,
                  nativeFrameCapture={'path':str(capture.relative_to(ROOT)), 'width':640, 'height':480, 'sha256':sha(capture)},
                  data={path.name:{'bytes':path.stat().st_size, 'sha256':sha(path)} for path in inputs},
                  commands=['python3 scripts/prepare_native.py', 'python3 tests/run_replay81.py CORE_DIR'],
                  limitations=['Roundtrips cover ten AI custom matches, one human-only classic replay and one nearby match on one map, each 2200 frames.',
                               'Classic replay bytes are produced by the integrated recorder; no original-executable replay fixture or frame-parity comparison.',
                               'Campaign replays are not supported; recording is for new custom/nearby matches.',
                               'UI presentation is checked separately; these tests do not run on Android.'],
                  passed=True)
except Exception as error:
    report['error'] = str(error)
    raise
finally:
    report_path.write_text(json.dumps(report, indent=2)+'\n')
print('PASS twelve replay roundtrips, malformed-file rejection and recording eligibility; '+str(report_path))

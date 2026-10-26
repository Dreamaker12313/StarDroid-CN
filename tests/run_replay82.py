#!/usr/bin/env python3
"""Verify bounded bidirectional replay seeking against ordinary linear playback."""
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
p.add_argument('--timeout', type=int, default=360)
a = p.parse_args()
inputs = [a.core_dir.resolve()/name for name in ('STARDAT.MPQ', 'BROODAT.MPQ', 'patch_rt.mpq')]
inputs.append(a.map.resolve())
for path in inputs:
    if not path.is_file():
        p.error('Missing input: '+str(path))
out = ROOT/'build-native/replay82'
out.mkdir(parents=True, exist_ok=True)
report_path = ROOT/'validation/replay-v82.json'
tracked = ['tests/native_replay82.cpp', 'tests/native_replay81.cpp', 'tests/run_replay82.py',
           'tests/build_native_host.py', 'native/replay.h', 'native/runtime.cpp', 'native/audio.h',
           'native/multiplayer.h', 'native/hero_mode.h', 'native/save_state.h',
           'native/generated/wasm_main.cpp', 'native/generated/wasm_backend.cpp',
           'app/src/main/java/org/openbw/androidtest/NativeBridge.java',
           'scripts/prepare_native.py', 'patches/native-replay82.patch',
           'patches/native-supply81.patch', 'patches/native-addon-sound81.patch']
engine = ['bwgame.h', 'actions.h', 'replay.h', 'replay_saver.h', 'ui/ui.h', 'web/sandbox.h', 'web/campaign_ai.h']
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def sources():
    return {name:sha(ROOT/name) for name in tracked}
def prepared():
    return {name:sha(ROOT/'native-engine'/name) for name in engine}
def run(name, command):
    log = out/(name+'.log')
    print('Running '+name, flush=True)
    with log.open('w') as stream:
        result = subprocess.run([str(v) for v in command], cwd=ROOT, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=a.timeout)
    text = log.read_text()
    if result.returncode:
        print(text[-16000:], file=sys.stderr)
        raise RuntimeError(f'{name} failed ({result.returncode}); see {log}')
    return text

def values(line):
    return dict(re.findall(r'(\w+)=([\w.]+)', line))

report = dict(version=82, topic='Bounded bidirectional replay seeking', passed=False,
              generatedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              scope='Native host simulation with locally supplied original data; not Android-device UI testing.')
try:
    initial, initial_engine = sources(), prepared()
    if not a.skip_build:
        run('build', [sys.executable, ROOT/'tests/build_native_host.py', 'replay82', '--skip-prepare'])
    text = run('native', [ROOT/'build-native/host/native-replay82', a.core_dir.resolve(), a.map.resolve(), out/'replay-frame.ppm'])
    lines = text.splitlines()
    scenarios = [values(line) for line in lines if line.startswith('PASS seek scenario=')]
    timings = [values(line) for line in lines if line.startswith('PASS checkpoint timing ')]
    stress = [values(line) for line in lines if line.startswith('PASS checkpoint stress ')]
    bounded = [values(line) for line in lines if line.startswith('PASS bounded seek ')]
    if len(scenarios)!=3 or not any(re.fullmatch(r'PASS \d+ checks in 3 replay seek scenarios', line) for line in lines):
        raise RuntimeError('Incomplete seek regression output')
    if len(timings)!=3 or len(stress)!=1 or int(stress[0]['units'])<200 or len(bounded)!=1:
        raise RuntimeError('Missing snapshot timings or crowded-world validation')
    required = ('PASS 24-hour replay:', 'PASS unavailable-checkpoint fallback:', 'PASS intermediate seek rendering')
    if any(not any(line.startswith(prefix) for line in lines) for prefix in required):
        raise RuntimeError('Missing responsiveness, reload fallback or render regression')
    capture = out/'replay-frame.png'
    with Image.open(out/'replay-frame.ppm') as frame:
        if frame.size!=(640,480):
            raise RuntimeError('Unexpected replay framebuffer dimensions')
        frame.save(capture)
    if sources()!=initial or prepared()!=initial_engine:
        raise RuntimeError('Native sources changed during validation; rerun on integrated source')
    report.update(sourceSha256=initial, integratedEngineHashes=initial_engine,
                  regressions=lines, scenarios=scenarios, checkpointTimings=timings,
                  syntheticCrowdedSnapshot=stress[0], boundedWork=bounded[0],
                  limits={'simulationFramesPerPump':128, 'simulationTimeSliceTargetMs':6,
                          'checkpointCount':8, 'retainedCheckpointAllocatedByteBudget':48*1024*1024,
                          'snapshotSerializationByteLimit':64*1024*1024, 'replayFileByteLimit':32*1024*1024},
                  nativeFrameCapture={'path':str(capture.relative_to(ROOT)), 'width':640, 'height':480, 'sha256':sha(capture)},
                  data={path.name:{'bytes':path.stat().st_size, 'sha256':sha(path)} for path in inputs},
                  commands=['python3 scripts/prepare_native.py', 'python3 tests/run_replay82.py CORE_DIR'],
                  limitations=['Seek parity uses native-recorded fixtures on one map: 7000-frame AI, 4600-frame team/hero AI and 2200-frame classic human playback.',
                               'The 24-hour duration fixture verifies queued/cancellable work, not completion of 24 hours of simulation.',
                               'The 200-unit snapshot stress fixture is synthetic and is separate from unmodified real-command seek parity fixtures.',
                               'The 6ms simulation target excludes one world-sized snapshot capture/restore or fallback reload; measured host times do not establish Android device timings.',
                               'The 48 MiB limit covers retained checkpoint capacity, not process memory: serialization can transiently allocate up to 64 MiB, with a temporary restored world and admitted replay bytes up to 32 MiB.',
                               'Android touch, frame rate and playback speed controls are validated separately; this harness does not run on a device.'],
                  passed=True)
except Exception as error:
    report['error']=str(error)
    raise
finally:
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2)+'\n')
print('PASS replay seeking, state parity, bounded work and checkpoint lifecycle; '+str(report_path))

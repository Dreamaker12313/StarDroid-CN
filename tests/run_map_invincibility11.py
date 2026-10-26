#!/usr/bin/env python3
"""Exercise map protection, real attack orders and harvesting with original MPQs."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build-native/attackability11'
OUT.mkdir(parents=True, exist_ok=True)
REPORT = ROOT / 'validation/map-invincibility11.json'
REPORT.unlink(missing_ok=True)
CORE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / 'build-native/reign79/core'
subprocess.run(['gcc', '-O2', '-c', str(ROOT / 'vendor/libsmacker/smacker.c'), '-o', str(OUT / 'smacker.o')], check=True)
command = [os.environ.get('CXX', 'g++'), '-std=c++17', '-O0', '-g0', '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections', '-pthread', '-DOPENBW_ENABLE_UI', '-DOPENBW_NO_SDL_IMAGE', '-DOPENBW_NO_SDL_MIXER']
command += ['-I' + str(ROOT / part) for part in ('native-engine', 'native-engine/ui', 'native-engine/web')]
command += [str(ROOT / 'tests/native_map_invincibility11.cpp'), str(ROOT / 'native/generated/wasm_backend.cpp'), str(OUT / 'smacker.o'), '-o', str(OUT / 'test')]
subprocess.run(command, check=True, cwd=ROOT)
result = subprocess.run([str(OUT / 'test'), str(CORE)], check=True, capture_output=True, text=True, cwd=ROOT)
print(result.stdout, end='')
names = ['patches/native-map-invincibility11.patch', 'tests/native_map_invincibility11.cpp', 'tests/run_map_invincibility11.py']
report = {
    'passed': True,
    'scope': 'Original DAT defaults for all 228 unit types; live resource attack orders, glaive target rejection, splash/direct damage, campaign crystals, normal enemy buildings, explicit protection and harvesting by all three races.',
    'baseline': 'Before the patch, the same map loader reported runtime invincible=false for every Weave mineral/geyser while its original units.dat invincible flag was true.',
    'limitation': 'Tests initialize maps and UPRP properties. Existing saved runtime state is not rewritten, so old saves containing already-unprotected objects require a mission restart.',
    'result': result.stdout.strip(),
    'sourceSha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names},
    'originalDataSha256': {name: hashlib.sha256((CORE / name).read_bytes()).hexdigest() for name in ('STARDAT.MPQ', 'BROODAT.MPQ', 'patch_rt.mpq')},
    'mapSha256': hashlib.sha256((ROOT / 'app/src/main/assets/native/weave.scx').read_bytes()).hexdigest(),
}
REPORT.write_text(json.dumps(report, indent=2) + '\n')

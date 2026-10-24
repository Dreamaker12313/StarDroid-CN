#!/usr/bin/env python3
"""Guard-page and AddressSanitizer regression for native screen-edge drawing.

Usage: python3 tests/run_placement.py /path/to/game-data [--skip-build]
Optional --baseline-binary compares an already-built unpatched harness.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('data', type=Path)
parser.add_argument('--skip-build', action='store_true')
parser.add_argument('--baseline-binary', type=Path)
args = parser.parse_args()
out = ROOT / 'build-native/scroll69'
out.mkdir(parents=True, exist_ok=True)
if not args.skip_build:
    subprocess.run([sys.executable, str(ROOT / 'tests/build_native_host.py'), 'placement', '--asan'],
                   cwd=ROOT, check=True)
env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:abort_on_error=1:symbolize=1')
map_file = ROOT / 'app/src/main/assets/native/weave.scx'


def run(binary, case, label):
    completed = subprocess.run([str(binary.resolve()), str(args.data.resolve()), str(map_file), case],
                               cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=120)
    (out / (label + '.log')).write_text(completed.stdout)
    return completed


baseline = []
if args.baseline_binary:
    for case, function in [('ghost-repro', 'draw_placement_ghost'), ('rgba-repro', 'line_rectangle_rgba')]:
        result = run(args.baseline_binary, case, case + '-baseline')
        reproduced = (result.returncode != 0 and 'AddressSanitizer: SEGV' in result.stdout
                      and 'WRITE memory access' in result.stdout and function in result.stdout)
        assert reproduced, f'Unpatched {case} did not reproduce the expected write fault'
        baseline.append({'case': case, 'reproduced': reproduced, 'fault': 'SIGSEGV on write',
                         'function': function, 'returnCode': result.returncode})

binary = ROOT / 'build-native/host/native-placement-asan'
result = run(binary, 'all', 'after')
assert result.returncode == 0, result.stdout[-10000:]
assert 'AddressSanitizer:' not in result.stdout, result.stdout[-10000:]
counts = re.search(r'building_types=(\d+) PASS mode=all rectangle_cases=(\d+) ghost_cases=(\d+) rendered_frames=(\d+)', result.stdout)
assert counts, result.stdout[-10000:]
source_files = ['tests/native_placement.cpp', 'tests/run_placement.py', 'tests/build_native_host.py',
                'scripts/prepare_native.py', 'patches/native-placement68.patch', 'patches/native-scroll69.patch', 'native/runtime.cpp',
                'native/generated/wasm_main.cpp', 'native/generated/wasm_backend.cpp']
report = {
    'passed': True, 'version': '1.0', 'versionCode': 69,
    'baseline': baseline,
    'buildingTypes': int(counts[1]), 'rectangleCases': int(counts[2]),
    'ghostCases': int(counts[3]), 'renderedFrames': int(counts[4]),
    'scrollFrames': int(re.search(r'scroll_frames=(\d+)', result.stdout)[1]),
    'sanitizer': 'GCC AddressSanitizer, guard pages, row-padding and prefix canaries; leak detection disabled',
    'coverage': [
        'Indexed and RGBA outlines: exhaustive small rectangles, inverted/empty/one-pixel/extreme coordinates',
        'All four edges, fully offscreen and full-image rectangles; tight and padded row strides',
        'Real building sprites/footprints: blocked and valid locations, add-ons and morphs',
        '640x480, 1280x720 and 457x343 displays at zoom 0.5, 1, 1.4 and 3',
        'Full render path: ordinary/refinery/flying-building-plus-addon placement and edge-spanning selection',
        'Host-owned scrolling in eight directions, four zoom levels, map limits and stationary release; no second native pan',
    ],
    'physicalDeviceTested': False,
    'limitations': 'Host rendering and memory checks. Samsung crash-site behavior reproduced; post-fix Android device play and the separate Vivo closure remain unverified.',
    'sourceSha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_files},
    'preparedUiSha256': hashlib.sha256((ROOT / 'native-engine/ui/ui.h').read_bytes()).hexdigest(),
    'testBinarySha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
}
if args.baseline_binary:
    report['baselineBinarySha256'] = hashlib.sha256(args.baseline_binary.read_bytes()).hexdigest()
destination = ROOT / 'validation/native-placement-v1.0.json'
destination.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: report[key] for key in ('passed', 'buildingTypes', 'rectangleCases', 'ghostCases', 'renderedFrames')}))

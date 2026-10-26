#!/usr/bin/env python3
"""Exercise physical-input policy on the host and compile it against Android SDK 35."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
java_home = root / '.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64'
sdk = root / '.tools/android-35/android.jar'

def tool(name):
    bundled = java_home / 'bin' / name
    return str(bundled) if bundled.exists() else shutil.which(name)

def run(args):
    result = subprocess.run(args, cwd=root, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout

sources = ['app/src/main/java/org/openbw/androidtest/DesktopControls.java',
           'tests/DesktopControls11Test.java', 'tests/run_desktop_policy11.py']
before = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources}
assert sdk.exists(), 'Android SDK 35 android.jar is required for the API compile and constant extraction.'

with tempfile.TemporaryDirectory(prefix='stardroid-desktop-policy-') as temp:
    work = Path(temp)
    api = work / 'api'; api.mkdir()
    run([tool('javac'), '-Xlint:all', '-cp', str(sdk), '-d', str(api), str(root / sources[0])])
    stubs = work / 'android/view'; stubs.mkdir(parents=True)
    # Read real SDK constants rather than maintaining another hand-written Android key table.
    bodies = {
        'InputDevice': '''private final int sources, type;
          public InputDevice(int sources, int type) { this.sources=sources; this.type=type; }
          public int getSources() { return sources; }
          public int getKeyboardType() { return type; }''',
        'KeyEvent': '''private final int key, source; private final InputDevice device;
          public KeyEvent(int key, int source, InputDevice device) { this.key=key; this.source=source; this.device=device; }
          public int getKeyCode() { return key; }
          public int getSource() { return source; }
          public InputDevice getDevice() { return device; }
          public static boolean isGamepadButton(int key) {
            return key >= KEYCODE_BUTTON_A && key <= KEYCODE_BUTTON_MODE
                || key >= KEYCODE_BUTTON_1 && key <= KEYCODE_BUTTON_16;
          }''',
        'MotionEvent': '',
    }
    for name, body in bodies.items():
        description = run([tool('javap'), '-constants', '-classpath', str(sdk), 'android.view.' + name])
        constants = re.findall(r'public static final int ([A-Z_0-9]+) = (-?\d+);', description)
        assert constants, 'SDK constants missing: ' + name
        declarations = '\n'.join('public static final int ' + key + ' = ' + value + ';' for key, value in constants)
        (stubs / (name + '.java')).write_text('package android.view; public class ' + name + ' {\n'
                                             + declarations + '\n' + body + '\n}\n')
    host = work / 'host'; host.mkdir()
    run([tool('javac'), '-Xlint:all', '-d', str(host), *map(str, stubs.glob('*.java')),
         str(root / sources[0]), str(root / sources[1])])
    output = run([tool('java'), '-ea', '-cp', str(host), 'org.openbw.androidtest.DesktopControls11Test'])

after = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources}
assert before == after, 'Input policy sources changed during validation; rerun.'
report = dict(passed=True, androidApiCompile=35, physicalAndroid=False,
              limitation='Policy tests use host event shims with real SDK constants; physical USB/Bluetooth input needs device testing.',
              sourceSha256=before, checks=output.strip().splitlines(),
              reference=['https://developer.android.com/reference/android/view/MotionEvent',
                         'https://source.android.com/docs/core/interaction/input/touch-devices'])
(root / 'validation').mkdir(exist_ok=True)
(root / 'validation/desktop-policy11.json').write_text(json.dumps(report, indent=2) + '\n')
print(output, end='')
print('PASS production DesktopControls compiles against Android SDK 35')

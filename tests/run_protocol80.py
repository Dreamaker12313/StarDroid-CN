#!/usr/bin/env python3
"""Check current production lockstep protocol without rewriting old reports."""
from pathlib import Path
import hashlib, json, subprocess

r = Path(__file__).resolve().parents[1]
src = r / 'app/src/main/java/org/openbw/androidtest'
build = r / 'build-native/protocol80'
build.mkdir(parents=True, exist_ok=True)
jar = r / 'build-native/json-20240303.jar'
assert hashlib.sha256(jar.read_bytes()).hexdigest() == '3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed'
names = ['NearbyProtocol', 'NearbyMatch', 'MatchSetup', 'MatchSnapshot', 'NearbyMapCodec', 'NearbyMapCache', 'NativeData']
files = [src / (name + '.java') for name in names] + [r / 'tests/NearbyProtocolTest.java']
subprocess.run(['java', '-jar', str(r / '.tools/ecj.jar'), '-source', '1.8', '-target', '1.8',
                '-proc:none', '-classpath', str(jar), '-d', str(build), *map(str, files)], check=True)
result = subprocess.run(['java', '-cp', str(build) + ':' + str(jar), 'org.openbw.androidtest.NearbyProtocolTest',
                         str(r / 'build-native/nearby-weave.chk'), str(r / 'build-native/map80')],
                        check=True, capture_output=True, text=True)
print(result.stdout, end='')
report = {'passed': True, 'protocolBuild': 80, 'physicalRadioTested': False, 'output': result.stdout.strip(),
          'sourceSha256': {str(p.relative_to(r)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in files + [Path(__file__)]}}
(r / 'validation/protocol-v80.json').write_text(json.dumps(report, indent=2) + '\n')

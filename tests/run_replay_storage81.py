#!/usr/bin/env python3
"""Exercise replay storage on real files, without Android or original game data."""
from pathlib import Path
import hashlib, json, subprocess, tempfile

root = Path(__file__).resolve().parents[1]
source = root / 'app/src/main/java/org/openbw/androidtest/NativeReplays.java'
test = root / 'tests/ReplayStorage81Test.java'
# Workspace synchronization can resurrect deleted fixtures; exercise deletion in /tmp.
with tempfile.TemporaryDirectory(prefix='stardroid-replay-storage81-') as tmp:
    work = Path(tmp)
    subprocess.run(['javac', '-encoding', 'UTF-8', '-d', str(work/'classes'), str(source), str(test)], check=True)
    result = subprocess.run(['java', '-cp', str(work/'classes'), 'org.openbw.androidtest.ReplayStorage81Test', str(work/'files')], capture_output=True, text=True)
    print(result.stdout + result.stderr, end='')
    result.check_returncode()
report = {
    'passed': True, 'physicalAndroid': False, 'result': result.stdout.strip(),
    'sourceSha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [source, test, Path(__file__)]},
}
(root/'validation/replay-storage-v81.json').write_text(json.dumps(report, indent=2)+'\n')

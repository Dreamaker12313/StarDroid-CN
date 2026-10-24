#!/usr/bin/env python3
"""Check MPQ lookup and CRC tables against synthetic and supplied archive bytes."""
from pathlib import Path
import argparse,hashlib,json,subprocess
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('stardat',type=Path);a=p.parse_args()
exe=r/'build-native/host/native-archive'
result=subprocess.run([str(exe),str(a.stardat)],capture_output=True,text=True)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
names=['tests/native_archive.cpp','tests/run_archive_checks.py','scripts/prepare_native.py','scripts/prepare_feedback.py','scripts/prepare_presentation.py','UPSTREAM.json']+[str(x.relative_to(r)) for x in sorted((r/'patches').glob('*.patch'))]
report=dict(version='0.38',passed=result.returncode==0,scope='Hash-table probing, ordinary/CRC sector offsets, exclusion of checksum payload, malformed-offset rejection and byte-exact extraction of three supplied raw font payloads. Payload readability is separately checked by Android.',originalCoreAssets=True,stdout=result.stdout,stderr=result.stderr,binarySha256=sha(exe),sourceSha256={n:sha(r/n) for n in names},stardatSha256=sha(a.stardat))
(r/'validation/native-archive-v38.json').write_text(json.dumps(report,indent=2)+'\n');print(result.stdout,end='');raise SystemExit(result.returncode)

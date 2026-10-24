#!/usr/bin/env python3
"""Decode a user-supplied mission ZIP with the engine's MPQ reader; no downloads.

Run scripts/prepare_native.py first. Decoded original maps remain external inputs,
not source-package assets. Temporary sparse MPQs preserve encrypted block offsets.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from rebuild_mission_mpq import rebuild


def extract(source, destination):
    executable = ROOT / 'build-native/host/native-mission-extract'
    executable.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['g++', '-std=c++17', '-O2', '-I', str(ROOT / 'native-engine'),
                    str(ROOT / 'tests/native_mission_extract.cpp'), '-o', str(executable)], check=True)
    allowed = {m['id'] for m in json.loads((ROOT / 'missions.json').read_text())}
    destination.mkdir(parents=True, exist_ok=True)
    results, seen = [], set()
    with zipfile.ZipFile(source) as outer, tempfile.TemporaryDirectory(dir=destination) as temporary:
        listing = json.loads(outer.read('manifest.json'))
        assert listing['format'] == 'openbw-mission-export-v1'
        work = Path(temporary)
        for mission in listing['missions']:
            name = mission['mission']
            assert name in allowed and name not in seen
            seen.add(name)
            info = outer.getinfo(mission['file'])
            assert info.file_size <= 80 * 1024 * 1024
            packed = outer.read(mission['file'])
            assert hashlib.sha256(packed).hexdigest() == mission['sha256']
            with zipfile.ZipFile(io.BytesIO(packed)) as inner:
                manifest = json.loads(inner.read('manifest.json'))
                assert manifest['mission'] == name and len(manifest['entries']) == 1
                entry = manifest['entries'][0]
                assert entry['size'] <= 64 * 1024 * 1024
            bundle, archive = work / 'bundle.zip', work / 'mission.mpq'
            bundle.write_bytes(packed)
            rebuild(bundle, archive)
            target = destination / (name + '.chk')
            subprocess.run([str(executable), str(archive), entry['name'], str(target)],
                           capture_output=True, text=True, check=True)
            chk = target.read_bytes()
            assert len(chk) == entry['size']
            results.append(dict(mission=name, title=mission['title'], bytes=len(chk),
                                sha256=hashlib.sha256(chk).hexdigest()))
            archive.unlink()
    (destination / 'index.json').write_text(json.dumps(results, indent=2) + '\n')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    result = extract(args.export, args.destination)
    print(f'Decoded {len(result)} original mission maps ({sum(m["bytes"] for m in result):,} CHK bytes).')

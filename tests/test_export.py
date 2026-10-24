#!/usr/bin/env python3
"""Exercise the same Java exporter used on Android, including a >512 MB file."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from rebuild_mission_mpq import cipher, hash_name, rebuild

tools = Path(os.environ['OPENBW_ANDROID_TOOLS'])
fixture_dir = Path(os.environ.get('OPENBW_TEST_MPQS', '/tmp/openbw-test-data'))
report = {'checks': []}
work = Path(tempfile.mkdtemp(prefix='openbw-export-test-'))
classes = work / 'classes'; classes.mkdir()
with tarfile.open(ROOT / json.loads((ROOT/'UPSTREAM.json').read_text())['source_archive']['file']) as archive:
    reader_path = work / 'scdat_reference.py'
    reader_path.write_bytes(archive.extractfile('web/scdat.py').read())
spec = importlib.util.spec_from_file_location('scdat_reference', reader_path)
reader = importlib.util.module_from_spec(spec); spec.loader.exec_module(reader)
subprocess.run(['java', '-jar', str(tools / 'ecj.jar'), '-source', '1.8', '-target', '1.8', '-proc:none', '-d', str(classes),
    str(ROOT / 'app/src/main/java/org/openbw/androidtest/MissionBundle.java'), str(ROOT / 'tests/ExportHarness.java')], check=True)


def run(mpq, bundle, names, success=True):
    listing = work / 'names.txt'; listing.write_text('\n'.join(names) + '\n')
    p = subprocess.run(['java', '-Xmx48m', '-cp', str(classes), 'ExportHarness', str(mpq), str(bundle), str(listing)], text=True, capture_output=True)
    if success and p.returncode: raise AssertionError(p.stderr)
    if not success and p.returncode == 0: raise AssertionError('Expected rejection')
    return p


# Use actual existing data archives; compare every selected packed byte and
# verify unrelated files cannot be looked up after reconstruction.
for mpq in sorted(fixture_dir.glob('*')):
    if not mpq.is_file(): continue
    names = [r'arr\units.dat', r'arr\weapons.dat', r'scripts\does-not-exist.bin']
    bundle, filtered = work / (mpq.name + '.zip'), work / (mpq.name + '.filtered')
    before = hashlib.sha256(mpq.read_bytes()).digest()
    run(mpq, bundle, names)
    manifest = rebuild(bundle, filtered)
    assert manifest['missing'] == [names[2]]
    with mpq.open('rb') as source, filtered.open('rb') as result:
        for entry in manifest['entries']:
            source.seek(entry['offset']); result.seek(entry['offset'])
            assert source.read(entry['packedSize']) == result.read(entry['packedSize'])
    assert hashlib.sha256(mpq.read_bytes()).digest() == before
    original_reader, filtered_reader = reader.MPQ(mpq), reader.MPQ(filtered)
    for name in names[:2]: assert original_reader.extract(name) == filtered_reader.extract(name)
    assert filtered_reader.find(r'arr\sfxdata.dat') is None
    report['checks'].append('Real ' + mpq.name + ': packed and decoded round-trip; unrelated file hidden; source unchanged')

# A sparse, valid MPQ with payloads beyond 600 MB checks large offsets under
# a 48 MB Java heap, without including any actual game assets in the fixture.
names = (ROOT / 'app/src/main/assets/missions/terran01-files.txt').read_text().splitlines()
hashes = bytearray(b'\xff' * (32 * 16)); blocks = bytearray()
payloads = []; offset = 607_000_000
for i, name in enumerate(names):
    data = ('test-payload-' + str(i)).encode() * 400
    payloads.append((offset, data))
    slot = hash_name(name, 0) & 31
    while struct.unpack_from('<I', hashes, slot * 16 + 12)[0] != 0xffffffff: slot = (slot + 1) & 31
    struct.pack_into('<IIHHI', hashes, slot * 16, hash_name(name, 1), hash_name(name, 2), 0, 0, i)
    blocks += struct.pack('<IIII', offset, len(data), len(data), 0x81000000)
    offset += len(data)
large = work / 'large.mpq'; htpos = offset; btpos = htpos + len(hashes); end = btpos + len(blocks)
with large.open('wb') as f:
    f.write(struct.pack('<4sIIHHIIII', b'MPQ\x1a', 32, end, 0, 3, htpos, btpos, 32, len(names)))
    for off, data in payloads: f.seek(off); f.write(data)
    f.seek(htpos); f.write(cipher(hashes, hash_name('(hash table)', 3), True))
    f.seek(btpos); f.write(cipher(blocks, hash_name('(block table)', 3), True))
bundle = work / 'large.zip'; run(large, bundle, names)
filtered = work / 'large-filtered.mpq'; m = rebuild(bundle, filtered)
with filtered.open('rb') as f:
    for off, data in payloads: f.seek(off); assert f.read(len(data)) == data
assert bundle.stat().st_size < 100000
report.update({'largeInputBytes': large.stat().st_size, 'exportZipBytes': bundle.stat().st_size, 'heapLimitMB': 48})
report['checks'].append('607 MB archive: selected data beyond 512 MB exported under 48 MB heap; round-trip exact')
rejected = run(large, work/'missing.zip', ['absent-mission.chk'], success=False)
assert 'not found' in rejected.stderr
report['checks'].append('Wrong archive / missing required mission rejected')

# An EXE-style archive with a 512-byte prefix must retain relative MPQ offsets.
prefixed = work / 'prefixed.mpq'
with large.open('rb') as src, prefixed.open('wb') as dst:
    dst.write(b'MZ' + bytes(510)); dst.write(src.read(32))
    for off, data in payloads: dst.seek(off + 512); dst.write(data)
    dst.seek(htpos + 512); dst.write(cipher(hashes, hash_name('(hash table)', 3), True))
    dst.seek(btpos + 512); dst.write(cipher(blocks, hash_name('(block table)', 3), True))
run(prefixed, work/'prefix.zip', names)
rebuild(work/'prefix.zip', work/'prefix-rebuilt.mpq')
report['checks'].append('MPQ inside an executable-style prefix supported')
(ROOT/'validation').mkdir(exist_ok=True)
(ROOT/'validation/export-tests.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))

#!/usr/bin/env python3
"""Check raw encrypted MPQ tail padding without distributing original game data."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import sys

r = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(r / 'scripts'))
from rebuild_mission_mpq import cipher, hash_name

out = r / 'build-native/sector77'
out.mkdir(parents=True, exist_ok=True)
extract = out / 'extract'
(out / 'extract.cpp').write_text('''#include "data_loading.h"
#include <fstream>
#include <iostream>
int main(int n,char**v){try{bwgame::data_loading::mpq_file<> a(v[1]);
bwgame::a_vector<uint8_t>b;a(b,v[2]);std::ofstream f(v[3],std::ios::binary);
f.write((char*)b.data(),b.size());}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
''')
subprocess.run(['g++', '-std=c++17', '-O0', '-I' + str(r / 'native-engine'),
                str(out / 'extract.cpp'), '-o', str(extract)], check=True)

def fixture(length, encrypted=True, padded=True, corrupt=False, tabled=True, plain=None, compressed=None):
    name = 'test.dat'
    plain = plain if plain is not None else bytes((127 + i) & 255 for i in range(length))
    offset = 32
    flags = 0x80000000 | (0x200 if tabled else 0) | (0x30000 if encrypted else 0)
    key = ((hash_name(name, 3) + offset) ^ length) & 0xffffffff
    data = b''
    ends = [4 * ((length + 4095) // 4096 + 1) if tabled else 0]
    for i in range(0, length, 4096):
        sector = compressed if compressed is not None else plain[i:i + 4096]
        if padded:
            sector += bytes((-len(sector)) % 4)
        if corrupt and i + 4096 >= length:
            sector = sector[:-1] + b'\x01'
        if encrypted:
            words = len(sector) // 4 * 4
            sector = cipher(sector[:words], (key + i // 4096) & 0xffffffff, True) + sector[words:]
        data += sector
        ends.append(ends[-1] + len(sector))
    table = struct.pack('<' + 'I' * len(ends), *ends) if tabled else b''
    if encrypted and table:
        table = cipher(table, (key - 1) & 0xffffffff, True)
    block = table + data
    ht, bt = offset + len(block), offset + len(block) + 64
    header = struct.pack('<4sIIHHIIII', b'MPQ\x1a', 32, bt + 16, 0, 3, ht, bt, 4, 1)
    hashes = bytearray(b'\xff' * 64)
    struct.pack_into('<IIHHI', hashes, (hash_name(name, 0) & 3) * 16,
                     hash_name(name, 1), hash_name(name, 2), 0, 0, 0)
    blocks = struct.pack('<IIII', offset, len(block), length, flags)
    mpq = header + block + cipher(hashes, hash_name('(hash table)', 3), True) + cipher(blocks, hash_name('(block table)', 3), True)
    source, dest = out / 'synthetic.mpq', out / 'decoded.dat'
    source.write_bytes(mpq)
    call = subprocess.run([str(extract), str(source), name, str(dest)], capture_output=True)
    if corrupt:
        assert call.returncode != 0 and b'invalid encrypted sector padding' in call.stderr
    else:
        assert call.returncode == 0, call.stderr.decode(errors='replace')
        assert dest.read_bytes() == plain

cases = 0
for size in [0, 1, 2, 3, 4, 61, 62, 63, 64, 4093, 4094, 4095, 4096, 4097, 8191]:
    for tabled in [False, True]:
        for encrypted, padded in [(True, True), (True, False), (False, False)]:
            fixture(size, encrypted, padded, tabled=tabled)
            cases += 1
for size in [1, 2, 3, 61, 62, 63, 4093, 4094, 4095]:
    for tabled in [False, True]:
        fixture(size, corrupt=True, tabled=tabled)
        cases += 1
# A valid literal/match PKWARE stream whose 15-byte representation becomes
# exactly as large as its 16-byte output when encrypted with word padding.
bits = []
def put(value, count):
    bits.extend((value >> i) & 1 for i in range(count))
for _ in range(2):
    put(0, 1); put(65, 8)
for _ in range(7):
    put(1, 1); put(1, 2); put(1, 1); put(3, 2); put(0, 2)
put(1, 1); put(0, 2); put(0, 2); put(56, 6); put(31, 5)
stream = bytes(sum(bits[i + j] << j for j in range(min(8, len(bits) - i))) for i in range(0, len(bits), 8))
compressed = b'\x08\x00\x06' + stream
assert len(compressed) == 15
fixture(16, plain=b'A' * 16, compressed=compressed)
cases += 1
# A raw sector that resembles the compression prefix must remain raw when it
# lacks a complete, strictly bounded encoded stream and end marker.
fixture(16, plain=b'\x08\x00\x06' + b'plain content')
cases += 1
files = [Path(__file__), r / 'patches/native-polish77.patch', r / 'scripts/prepare_native.py']
report = {'passed': True, 'version': '1.0.7', 'versionCode': 77,
          'syntheticCases': cases,
          'cases': ['encrypted padded tails', 'encrypted unpadded tails', 'plain raw sectors',
                    'word-aligned sectors', 'nonzero padding rejection', 'empty files and multi-sector boundaries',
                    'raw files with no compression/offset table'],
          'preparedDataLoadingSha256': hashlib.sha256((r / 'native-engine/data_loading.h').read_bytes()).hexdigest(),
          'sourceSha256': {str(p.relative_to(r)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(r / 'validation/archive-v77.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS', cases, 'encrypted/raw sector padding checks')

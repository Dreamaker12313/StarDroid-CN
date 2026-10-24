#!/usr/bin/env python3
"""Copy an external StarDat fixture and damage only its optional font8 entry.

The invalid sector table reproduces the reported OpenBW exception. Never use
this on a user's import; all output belongs in the temporary test directory.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from rebuild_mission_mpq import cipher, hash_name

source, destination = map(Path, sys.argv[1:3])
if source.resolve() == destination.resolve() or destination.exists():
    raise ValueError('Choose a new temporary output file')
data = bytearray(source.read_bytes())
magic, header, size, version, shift, htpos, btpos, htn, btn = struct.unpack_from('<4sIIHHIIII', data)
assert magic == b'MPQ\x1a' and header == 32 and version == 0
hashes = cipher(data[htpos:htpos + htn * 16], hash_name('(hash table)', 3))
blocks = bytearray(cipher(data[btpos:btpos + btn * 16], hash_name('(block table)', 3)))
name = 'font\\font8.fnt'
block = next(struct.unpack_from('<I', hashes, at + 12)[0]
             for at in range(0, len(hashes), 16)
             if struct.unpack_from('<II', hashes, at) == (hash_name(name, 1), hash_name(name, 2)))
assert block < btn
offset, packed, unpacked, flags = struct.unpack_from('<IIII', blocks, block * 16)
assert offset >= 32 and packed >= 8 and offset + packed <= len(data)
struct.pack_into('<IIII', blocks, block * 16, offset, 8, 8, 0x80000200)
data[offset:offset + 8] = bytes(8)
data[btpos:btpos + btn * 16] = cipher(blocks, hash_name('(block table)', 3), True)
destination.write_bytes(data)
print('Created unreadable font8 regression fixture')

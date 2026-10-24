#!/usr/bin/env python3
"""Reconstruct a filtered, sparse MPQ from an Android Mission 1 bundle.

The output retains original block offsets so encrypted FIX_KEY entries keep
working. Its apparent size can be ~600 MB; only selected blocks occupy disk.
Use a normal MPQ reader to extract scenario.chk / WAVs. No game binary is run.
"""
import argparse
import json
from pathlib import Path
import struct
import zipfile


def crypt_table():
    table, seed = [0] * 1280, 0x100001
    for i in range(256):
        for j in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            high = (seed & 0xffff) << 16
            seed = (seed * 125 + 3) % 0x2AAAAB
            table[i + j * 256] = high | (seed & 0xffff)
    return table


CRYPT = crypt_table()
MASK = 0xffffffff


def hash_name(name, kind):
    a, b = 0x7fed7fed, 0xeeeeeeee
    for c in name.upper().replace('/', '\\').encode('latin1'):
        a = (CRYPT[kind * 256 + c] ^ (a + b)) & MASK
        b = (c + a + b + (b << 5) + 3) & MASK
    return a


def cipher(data, key, encrypt=False):
    seed, output = 0xeeeeeeee, bytearray()
    for word, in struct.iter_unpack('<I', data):
        seed = (seed + CRYPT[1024 + (key & 255)]) & MASK
        coded = word ^ ((key + seed) & MASK)
        plain = word if encrypt else coded
        output += struct.pack('<I', coded)
        key = (((~key << 21) + 0x11111111) | (key >> 11)) & MASK
        seed = (plain + seed + (seed << 5) + 3) & MASK
    return output


def rebuild(bundle, destination):
    with zipfile.ZipFile(bundle) as z:
        for info in z.infolist():
            if info.file_size > 128 * 1024 * 1024:
                raise ValueError('Oversized bundle entry')
        manifest = json.loads(z.read('manifest.json'))
        if manifest.get('format') != 'openbw-mission-bundle-v1':
            raise ValueError('Unknown bundle format')
        header = z.read('header.bin')
        if len(header) != 32:
            raise ValueError('Invalid header')
        magic, header_size, archive_size, version, shift, htpos, btpos, htn, btn = struct.unpack('<4sIIHHIIII', header)
        if magic != b'MPQ\x1a' or version != 0 or header_size != 32 or not 32 <= archive_size <= 2**32 - 1:
            raise ValueError('Unsupported MPQ header')
        hashes = cipher(z.read('hash-table.bin'), hash_name('(hash table)', 3))
        blocks = cipher(z.read('block-table.bin'), hash_name('(block table)', 3))
        if len(hashes) != htn * 16 or len(blocks) != btn * 16:
            raise ValueError('Invalid table sizes')
        if max(htpos + len(hashes), btpos + len(blocks)) > archive_size:
            raise ValueError('Table extends beyond archive')
        selected_slots, selected_blocks = set(), set()
        for entry in manifest['entries']:
            block = entry['block']
            if not isinstance(block, int) or not 0 <= block < btn:
                raise ValueError('Invalid block')
            offset, packed, size, flags = struct.unpack_from('<IIII', blocks, block * 16)
            if [offset, packed, size, flags] != [entry['offset'], entry['packedSize'], entry['size'], entry['flags']]:
                raise ValueError('Manifest does not match MPQ metadata')
            if offset < 32 or offset + packed > archive_size:
                raise ValueError('Invalid payload range')
            if z.getinfo(f'blocks/{block}.bin').file_size != packed:
                raise ValueError('Truncated payload')
            for slot in entry['hashSlots']:
                if not isinstance(slot, int) or not 0 <= slot < htn:
                    raise ValueError('Invalid hash slot')
                a, b, _, _, mapped = struct.unpack_from('<IIHHI', hashes, slot * 16)
                if mapped != block or a != hash_name(entry['name'], 1) or b != hash_name(entry['name'], 2):
                    raise ValueError('Filename hash mismatch')
                selected_slots.add(slot)
            selected_blocks.add(block)
        # Deleted entries preserve probe chains; empty entries must remain empty.
        for slot in range(htn):
            current, = struct.unpack_from('<I', hashes, slot * 16 + 12)
            if slot not in selected_slots and current != MASK:
                struct.pack_into('<I', hashes, slot * 16 + 12, 0xfffffffe)
        for block in range(btn):
            if block not in selected_blocks:
                blocks[block * 16:block * 16 + 16] = bytes(16)
        with open(destination, 'wb') as output:
            output.truncate(archive_size)
            output.write(header)
            output.seek(htpos); output.write(cipher(hashes, hash_name('(hash table)', 3), True))
            output.seek(btpos); output.write(cipher(blocks, hash_name('(block table)', 3), True))
            for entry in manifest['entries']:
                output.seek(entry['offset'])
                output.write(z.read(f"blocks/{entry['block']}.bin"))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; choose another path')
    data = rebuild(args.bundle, args.output)
    print(f"Rebuilt {len(data['entries'])} selected entries into {args.output}")
    print('Apparent size is the original archive size; unselected data is sparse/absent.')

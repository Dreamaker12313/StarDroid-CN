#!/usr/bin/env python3
"""Inventory original campaign score candidates without changing simulation data.

This is an independent CHK audit, not an original-game score-screen capture.
The renderer/native tests separately verify how these slots are presented.
"""
import argparse
import collections
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--maps', type=Path, default=ROOT / 'build-native/score-names11')
parser.add_argument('--report', type=Path, default=ROOT / 'validation/score-roster-audit11.json')
args = parser.parse_args()
catalog = json.loads((ROOT / 'app/src/main/assets/native/missions.json').read_text())
controller_names = {
    0: 'inactive', 1: 'computer in game', 2: 'occupied human',
    3: 'rescue passive', 4: 'rescue active', 5: 'computer slot',
    6: 'human slot', 7: 'neutral', 8: 'closed', 9: 'observer',
    10: 'human left', 11: 'computer left',
}
# Original map slots are 5 (computer) and 6 (human), becoming 1/2 at runtime.
participants = {1, 2, 5, 6}
helpers = {3, 4, 7}
maps = []
for mission in catalog:
    path = args.maps / (mission['id'] + '.chk')
    raw = path.read_bytes()
    chunks = {}
    offset = 0
    while offset < len(raw):
        tag, size = struct.unpack_from('<4sI', raw, offset)
        offset += 8
        assert offset + size <= len(raw), (path, tag, size)
        chunks[tag] = raw[offset:offset + size]
        offset += size
    owners, races, force = chunks[b'OWNR'], chunks[b'SIDE'], chunks[b'FORC']
    strings = chunks[b'STR ']
    string_count = struct.unpack_from('<H', strings)[0]

    def text(index):
        if index == 0:
            return ''
        assert 0 < index <= string_count
        start = struct.unpack_from('<H', strings, index * 2)[0]
        assert start < len(strings)
        return strings[start:strings.index(b'\0', start)].decode('cp1252')

    names = [text(index) for index in struct.unpack_from('<4H', force, 8)]
    placed = collections.Counter()
    starts = collections.Counter()
    units = chunks[b'UNIT']
    assert len(units) % 36 == 0
    for offset in range(0, len(units), 36):
        owner = units[offset + 16]
        kind = struct.unpack_from('<H', units, offset + 8)[0]
        placed[owner] += 1
        if kind == 214:
            starts[owner] += 1
    slots = []
    for slot, controller in enumerate(owners[:8]):
        assert force[slot] < 4
        if controller in (0, 8):
            continue
        slots.append({
            'slot': slot, 'controller': controller,
            'controllerName': controller_names.get(controller, 'unknown'),
            'race': races[slot], 'force': force[slot],
            'forceName': names[force[slot]], 'forceFlags': force[16 + force[slot]],
            'placedUnitsIncludingStartLocations': placed[slot],
            'startLocations': starts[slot],
            'participant': controller in participants,
            'helper': controller in helpers,
        })
    assert owners[mission['player']] == 6
    maps.append({
        'mission': mission['id'], 'title': mission['title'], 'code': mission['code'],
        'localPlayer': mission['player'], 'chkSha256': hashlib.sha256(raw).hexdigest(),
        'participantSlots': [s['slot'] for s in slots if s['participant']],
        'helperSlots': [s['slot'] for s in slots if s['helper']],
        'slots': slots,
    })

assert len(maps) == len(catalog) == 64
by_id = {m['mission']: m for m in maps}
# Exact original slots responsible for the five reported screenshots.
reported_helpers = {
    'terran01': [2], 'terran02': [2, 3], 'protoss05': [2],
    'expzerg10': [2], 'expzerg01': [0, 1],
}
for mission, slots in reported_helpers.items():
    assert by_id[mission]['helperSlots'] == slots, mission
all_slots = [slot for mission in maps for slot in mission['slots']]
participant_names = sorted({slot['forceName'].strip() for slot in all_slots if slot['participant']})
report = {
    'passed': True,
    'scope': 'Independent original CHK OWNR/SIDE/FORC/STR/UNIT inventory; presentation only',
    'mapCount': len(maps),
    'participantSlotCount': sum(slot['participant'] for slot in all_slots),
    'helperSlotCount': sum(slot['helper'] for slot in all_slots),
    'reportedScreenshots': reported_helpers,
    'participantFactionNames': participant_names,
    'longestParticipantFactionName': max(participant_names, key=len),
    'originalDataAnomalies': [
        {'mission': 'zerg07', 'slot': 4, 'forceName': '----',
         'note': 'Original computer faction is an authored placeholder, not a corrupt string lookup.'},
    ],
    'limits': [
        'This audits the original map metadata, not an original executable score-screen capture.',
        'Equal faction names can belong to distinct real computer players; do not merge their scores.',
        'Zero score or no surviving units is not evidence that a real participant should be hidden.',
        'Neutral/rescue controller changes during play require initial-participant metadata for stable presentation.',
    ],
    'maps': maps,
    'sourceSha256': {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(__file__), ROOT / 'app/src/main/assets/native/missions.json')
    },
}
args.report.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'mapCount', 'participantSlotCount',
    'helperSlotCount', 'reportedScreenshots', 'longestParticipantFactionName')}, indent=2))

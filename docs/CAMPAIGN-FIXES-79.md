# StarDroid 1.0.9 development changes

These are unreleased source changes targeting 1.0.9 / build 79. The published
1.0.8 APK and the checked-in 1.0.8 native libraries do not contain them. Rebuild both Android native libraries
before packaging; do not use `--skip-engine` with the old libraries. The existing
`NATIVE-BUILD.json` describes the published 1.0.8 artifacts, not these changes.

## Reign of Fire

After rescuing the two starting Drones, the original mission checks for exactly
zero Drones and exactly zero completed buildings. Both Drones can start buildings
before either building finishes, making that loss condition true.

The campaign loader now recognizes this specific mission condition and includes
unfinished buildings in its zero-buildings check. Genuine loss of all Drones and
buildings still causes defeat. Ordinary custom-map trigger comparisons keep their
existing behavior, and the imported mission file is not modified.

Existing saves made before defeat benefit from the correction when the mission
is loaded with the new engine. A save already recording defeat cannot undo it.

## Pre-placed Nydus canals

The map loader now resolves explicit Nydus connections in the original UNIT
records. Eye for an Eye has four canals in two pairs. Vile Disruption and To Chain
the Beast also contain pre-linked canals. The same loader handles custom Use Map
Settings maps. It preserves deliberately unlinked canals, including those in
Escape from Aiur, and rejects ambiguous or invalid connections.

New games retain these connections through saving and loading. Saves made by an
older engine serialize the missing connections: restart the affected mission to
receive the corrected initial pairings. No original game files need re-importing.

## Campaign unit names

The UI now honors the unit names supplied by UNIS/UNIx map records instead of
always showing the underlying unit's default name. The Insurgent intentionally
uses a Tassadar unit named Aldaris. This fix respects that name without changing
the unit's abilities, model, portrait, or the map's rules. It also applies to other
renamed campaign characters and custom-map units, including localized map names.

The Insurgent's original triggers deliberately enable shared vision of Aldaris's
player during the objective. That visibility is preserved. Stukov's dedicated unit
and portrait match the imported data, and his opening fog visibility was checked
in Patriot's Blood.

## Computer ability use

Combat spell decisions now run for computer-controlled players without requiring
an active base. This includes regular casters and heroes such as Aldaris/Tassadar
and Infested Kerrigan. Casters can join attack waves, and ongoing casts are not
replaced by another wave order or an Archon merge.

The shared logic covers Storm, EMP, Plague, Stasis, Maelstrom, Ensnare, Disruption
Web, Feedback, Lockdown, Irradiate, Yamato, Broodlings, Mind Control, Parasite and
Optical Flare, with supporting behavior for Matrix, Restoration, Dark Swarm,
Consume, Stim and Cloak. Custom-game computers can request research for abilities
used by their normal units; campaign technology remains controlled by the map.

Casts respect allowed technology, research, energy, unit type, visible targets,
scene pauses and explicit movement orders. Area spells reject targets heavily
mixed with friendly units. Pending orders reserve targets to avoid duplicate
casts, and normal save/load stores this state without a new save schema.

This does not introduce new strategic policies for nuclear strikes, Recall or
Hallucination. Existing automatic healing, siege, Lurker and transport behavior
remains in place.

## Targeting in fog of war

Previously seen enemy buildings now show the red targeting flash and selection
circle below their remembered artwork. The fix preserves the frozen building
image and does not add live health bars or reveal unseen buildings/mobile units.
Host rendering tests cover real attack and default-order input, ring color,
layering, timing, selection persistence and visibility guards.

## Map-list scrollbar

The original arrows have brighter olive shading, and a small beveled circular
handle makes the scroll position visible against the stone artwork. Touch input
now uses the same track as the drawing and keeps the finger's grip offset during
a drag. Arrow steps, list swipes and selecting a map still work normally.

Production touch-method tests cover empty/short lists and 2,001/10,000-map lists,
including redraws during a drag, both endpoints, list inertia and canceled taps.

## Brood War music

The supplied original BroodWar.mpq includes the new race theme followed by the
original first theme inside each race's `music/*1.wav`. The original segment starts
at about 3:56 for Terran and Zerg and 4:13 for Protoss. The complete files run for
about 8:38–8:53. Tracks 2 and 3 then complete the normal rotation.

Host checks confirmed that importing preserves the complete files and the native
mixer plays the original portion through the end. The same playlist method serves
campaigns, custom games and nearby multiplayer. No extra copy was appended, which
would repeat the original first theme twice in each cycle.

## Multiplayer compatibility

Build 79 uses a new simulation compatibility identifier because AI behavior has
changed. All peers must use the same build; build 78 peers are rejected during
the handshake rather than allowed to start a mismatched simulation.

## Verification

Tests use the caller's own original archives; no game data is included. These are
controlled mission and host audio checks, not complete campaign playthroughs or
physical Android device tests.

```sh
python3 tests/build_native_host.py campaign79 --fast
build-native/host/native-campaign79 /path/to/core /path/to/BroodWar.mpq /path/to/StarCraft.mpq all
python3 tests/build_native_host.py missions --fast --skip-prepare
build-native/host/native-missions /path/to/64-extracted-chks
python3 tests/build_native_host.py abilities79 --fast --skip-prepare
build-native/host/native-abilities79 /path/to/core /path/to/BroodWar.mpq
python3 tests/run_music79.py --data-dir /path/to/original-archives
python3 tests/run_map_scroll79.py /path/to/core --extract /path/to/mpq-extractor
```

The core directory must contain `STARDAT.MPQ`, `BROODAT.MPQ`, and `patch_rt.mpq`.
Music checks use `StarCraft.mpq` and `BroodWar.mpq` in the supplied directory.
Validation results are recorded under `validation/`.

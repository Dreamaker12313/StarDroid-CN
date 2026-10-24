# 0.32 mission fixes

The supplied export decoded successfully: 64 original campaign maps, including
their placed units, player settings and triggers. Core game archives and speech
were not part of the export. Original maps remain external test inputs and are
not shipped in this source package or APK.

## Findings and changes

**Agent of the Swarm (original Zerg 4):** Raynor and the other Terran computer
occupy different forces, with all force flags clear. The engine applied force
alliances but omitted the default alliance between computer participants. Its
real victory trigger checks for zero Raynor Command Centers without requiring
the Chrysalis to hatch first. This combination permits the reported premature
ending. Computer players with Start Locations now begin allied across forces.
The rule runs once during map loading, before simulation, and preserves stronger
force settings and subsequent trigger changes. Human players and computer slots
without Start Locations do not gain this default alliance.

**True Colors (Brood War Zerg 5):** the three opening Lurkers move into three
locations before their owner turns hostile to the Terran and Protoss factions.
The missing starting alliance could cause combat burrowing before they reached
those locations. The alliance fix restores that setup. Automatic burrowing now
also respects an explicit Move order, including the scripted exit after the
ambush. Idle and AttackMove Lurkers can still burrow for combat.

**Ceasefires:** the Set Alliance Status trigger now uses the same engine action
as ordinary alliance changes. Existing enemy attack orders drop targets that
have become allies. Alliance changes remain directional as defined by the map.

Blizzard documents the special treatment of slots without Start Locations and
the directional alliance action in its
[StarEdit trigger FAQ](https://classic.battle.net/scc/faq/triggers.shtml).

## Validation scope

`tests/native_missions.cpp` reads original OWNR, FORC, UNIT, MRGN and TRIG
records and calls the native alliance, condition, order and campaign AI code.
It checks all 64 maps' computer alliances and force flags; Zerg 4's Raynor ending
condition and hatch Wait/switch ordering; and True Colors' three approach
locations, betrayal, combat burrow, unburrow/exit orders and ceasefire.

Unit artwork, terrain and animation are synthetic fixtures. Movement completion,
burrow animation completion and the Chrysalis death count are explicitly supplied
by the test. This is not a full combat or campaign simulation. It does not verify
the report of destroyed/reappearing building artwork, original audio, or a
complete mission playthrough. Both native ABIs are rebuilt for this revision.

The previous ten native feedback groups are rerun. Reports include source and
binary hashes; mission records include external CHK hashes. The full original-data
release gate remains enabled and incomplete until its required evidence exists.

## Reproduce

```sh
python3 scripts/prepare_native.py
python3 tests/extract_mission_export.py /path/OpenBW-Missions.zip /path/external-maps
python3 tests/native_patch_preparation.py
python3 tests/build_native_host.py missions
python3 tests/build_native_host.py feedback
python3 tests/run_mission_checks.py /path/external-maps
python3 scripts/build.py
python3 tests/build_instrumentation.py
python3 tests/native_package.py
```

The last command records package integrity separately and exits nonzero while
the full original-data release requirements are incomplete. The new source patch
is `patches/native-missions.patch`, applied after `native-revision.patch`.

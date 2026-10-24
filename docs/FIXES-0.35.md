# 0.35 — Mission saves and Duran's command card

The 0.34 save error joined two different failures into one message. Imported
mission MPQs retain their original CD archive offsets for encrypted FIX_KEY
blocks. For example, True Colors has a 106,223-byte packed map block inside a
571,552,776-byte sparse archive. Applying a 256 MiB limit to the apparent file
length rejected the map before a save could be written.

Large MPQs now use an offset-preserving sparse map container in the save ZIP.
It stores the header, hash table, block table, occupied blocks, and any prefix
or trailer. On load these ranges are restored at their original offsets in a
sparse file. No block is re-encrypted or moved. The 256 MiB limit applies to
stored content; bounds and the SHA-256 digest are checked before game loading.
Missing maps, incomplete maps and actual size-limit failures have distinct errors.

A second bug accepted only mission codes 0–100 on readback. Most campaign codes
are higher. Validation now uses the campaign catalog, checks the mission ID,
and rejects invalid metadata before overwriting a previous slot.

Save ZIP format 2 is used for sparse maps; previous format-1 saves still load.
The native world snapshot remains version 1 and the game engine is unchanged.
Loaded sparse maps can be saved again without the original import bundle.

Both Duran variants now put Cloak/Decloak in slot 7 (bottom left) and Lockdown
in slot 8 (bottom centre), using one-based command-card positions. Other Ghost
and Infested Kerrigan layouts retain their existing positions.

## Verification scope

- All 64 original exported CHKs: 1,869 triggers, active references, playable
  player/race metadata, victory ownership and explicit next-mission routes.
- All 13 condition types used by those maps dispatched in the native engine
  under initial/later switch and timer states: 8,414 evaluations. These use
  synthetic unit/terrain data, not full world simulation.
- Existing native alliance, Raynor, Lurker, Hatchery and save-state regressions.
- Android import/save/load tests read original maps back through the native MPQ
  decryptor/decompressor and compare CHK bytes. Snapshot bytes in this file-I/O
  suite are synthetic; native world snapshots have a separate native suite.

The original AI bytecode, core unit/art/audio data, and physical Android device
are unavailable here. This is a feedback build, not certification of every
campaign playthrough or original-game AI parity. The audit found seven maps
using unimplemented leaderboard displays (objective counters). Their separate
victory/defeat triggers are present; those UI counters remain a known gap.
See validation/native-campaign-audit-v35.json for per-mission details.

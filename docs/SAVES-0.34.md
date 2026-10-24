# Save/load and morph completion — 0.34

Use Game Menu → Save Game during a mission or custom game. Six slots show the
mission/map title, save date and elapsed game time. An occupied slot requires
confirmation before replacement. Load Game is available in the game menu and
Saved Games in the Single Player campaign chooser. Loading during play asks
before replacing current progress; it returns to a paused menu with Resume Game.
A failed save leaves the current game paused and the previous saved file intact.

Saves are stored in app-private files, survive process shutdown and normal APK
updates, and are removed by Android's Clear Data/uninstall. They contain their
own prepared map archive (including any mission speech), so replacing imported
mission bundles or clearing temporary map files does not remove the save's map.
The original core game files remain required. These are OpenBW snapshots, not
Blizzard .sav files; importing/exporting saves is not implemented in this build.

## Native snapshot

Schema 1 uses explicit little-endian scalar fields and stable typed reference
indexes. It does not serialize native memory addresses, object padding or STL
representations. Unit, bullet, sprite, image and order pool allocation/free order,
unit generations, intrusive lists, paths, cargo/gather links and creep recession
queues are rebuilt before the restored world replaces the initial map state.

The snapshot includes economy/supply, upgrades/research, orders/production/morphs,
unit abilities/status effects, RNG, visibility/exploration, last-seen fog sprites,
mission trigger action positions/waits/switches/scores, campaign AI towns/threads,
selection/control groups/camera, outgoing commands and replay history. Mission
text, portraits and voice position are restored by the Android host. A load does
not replay the briefing or startup tips, or reannounce all existing units.

The custom-game ZZZKBot reattaches and replans from the restored world; its private
strategy memory is not serialized. Units and pending command batches are retained.
Campaign AI interpreter state is serialized. One-shot combat sounds and touch
placement/targeting gestures are cleared on load.

A versioned native header binds the snapshot to the loaded CHK, DAT, iscript and
terrain input. Size/reference bounds and a payload checksum reject corrupt or
incompatible snapshots before native state replacement. The outer ZIP contains
manifest.json, state.bin and map.mpq with SHA-256 hashes. Android AtomicFile and
fsync protect the previous slot if writing is interrupted. Current limits are
64 MiB of native state and 256 MiB per map archive. Files are read/hashed before
a running game is replaced. If map initialization fails after replacement has
begun, the load reports an error and returns to the front end; the slot remains.

## Zerg completion sound

The event poll already tracks completed type changes, including morphs which
retain a unit ID. Lair/Hive/Greater Spire DAT records can have no per-unit ready
sound. Completed Zerg structures now fall back to the shared ZChRdy00 building
sound in the user's sound table. Completion uses global playback, including
buildings outside the camera. Existing DAT ready sounds take precedence. Startup
buildings, unfinished morphs and cancellations do not emit completion sounds.

## Verification scope

Native synthetic tests exercise serialized object graphs, resources/research,
production, fog, RNG, replay history, campaign AI and trigger waits; round trips
are byte-identical and also read in a fresh process. Damaged, truncated,
incompatible-version and wrong-map saves are rejected. Android tests exercise
persistent ZIP contents, failed/interrupted overwrite recovery, tamper rejection,
process restart, JNI loading and actual slot-menu callbacks. The 64 original
mission CHKs remain external inputs to the mission regression checks.

Original core archives/audio are unavailable in this workspace. A complete
save/load playthrough with original assets, a running custom bot, actual Lair/
Hive/Greater Spire sound playback and physical-device checks remain outstanding.
This release is a feedback candidate, not a fully validated original-data build.
See the current validation/native-*-v34.json reports for exact evidence.

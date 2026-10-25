# PC save compatibility

Review date: 2026-10-26. This is a format research note; the release does not provide save-file import/export. Normal in-game saving and loading remain available.

## Internal save format

StarDroid saves use `.obwsave`: a ZIP containing `manifest.json`, `state.bin`, and the saved map (`map.mpq` or `map.sparse`). `NativeSaves.java` validates the manifest and map/state SHA-256 values. The native state is StarDroid's explicit-field `OBWSAV1` codec, currently schema 4, with readers for schemas 1–4. `native/save_state.h::header` checks the format, map/data signature, and match settings; `restore` decodes and validates a replacement world before committing it.

Renaming another engine's save to `.obwsave` does not convert its state.

## Original StarCraft / Brood War saves

Classic single-player saves normally use `.sng` and `.snx`. This checkout does **not** contain a reader or converter for their saved simulation state. Original PC saves therefore cannot currently resume in StarDroid. Loading only their mission or map would restart play and must not be presented as restoring the save.

No original `.sng` / `.snx` fixture was available in the supplied project/data for continuation tests. This is an implementation and validation gap, not a claim that conversion is impossible.

## Other implementations inspected

| Project | Inspected source | Finding |
| --- | --- | --- |
| StarDroid 1.0.9 | `app/src/main/java/org/openbw/androidtest/NativeSaves.java`; `native/save_state.h`; native source reconstructed from pinned OpenBW plus patches | Own portable snapshot schema. No Blizzard save loader in the inspected stack. |
| OpenSnowstorm, commit `d67171711a063b28602c4dfdc3e3a7389c1c7f4d` | [`serialization.h`](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/serialization.h); [`ui/gfxtest.cpp`](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/ui/gfxtest.cpp) | Own `.osv` format with `SNOW` magic and version 10, serialized pools/POD state and reference remapping. Its persistent save support is not an original-PC-save importer. |
| Teippi, commit `05c006c2f74ad11285c39d37135aed03d1fb8806` | [`src/save.cpp`](https://github.com/neivv/teippi/blob/05c006c2f74ad11285c39d37135aed03d1fb8806/src/save.cpp); [`src/offsets_funcs_1161.h`](https://github.com/neivv/teippi/blob/05c006c2f74ad11285c39d37135aed03d1fb8806/src/offsets_funcs_1161.h) | A plugin for the original 32-bit engine, not a standalone converter. Its save path delegates header/compression and trigger/DAT chunks to engine functions at version-specific addresses. Its object serialization also contains plugin-specific state. |

## Work needed for true PC import

1. Obtain known-version original saves and matching game data/maps, covering campaign and custom games, both expansions, and saves before/after key actions.
2. Implement bounded, version-aware parsing of the original header, compressed chunks, unit/sprite/projectile/order references, player resources/research, visibility/creep, path state, triggers and AI execution state.
3. Translate these structures into OpenBW's world and campaign-controller state. The two engines' AI and internal object layouts are not interchangeable.
4. Verify continued play against the original saved position: unit orders, cargo, production/refunds, triggers, dialogue, victory/defeat, AI progression, and save/load round trips. Reject unsupported versions or untranslatable state without modifying existing progress.

There is no verified drop-in original-save loader in the projects reviewed above. A UI file picker alone would not provide original PC compatibility.

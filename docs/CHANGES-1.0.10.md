# StarDroid 1.0.10 — build 80

## Gameplay fixes

- **Invincibility:** Options → Miscellaneous → Cheats now has an Invincibility toggle. It protects the player's units and buildings from combat damage, including shields, Defensive Matrix, EMP shield loss and Spawn Broodlings. Computer opponents and allied computer players remain vulnerable. Scenario-scripted deaths and voluntary consumption/morphs still work. The cheat is unavailable in multiplayer and resets when loading a save or starting a game.
- **Carrier and Reaver AI:** computer-controlled Carriers and Reavers now buy and replace Interceptors and Scarabs in campaigns as well as custom games, including heroes and captured units without an active base. Normal costs, capacity, technology and map restrictions apply. The Carrier tech path already existed; a supply-planning deadlock with four or five supply free is fixed so a six-supply Carrier request can proceed.
- **Drone Cancel:** an idle Drone no longer retains a stale Cancel command after failed construction. Cancelling while walking to build now stops that order; cancelling a building already morphing returns the Drone with the normal refund. Pending SCV and Probe construction use the same corrected cancellation path.

## Control groups and controllers

- Tap an empty group to assign the current selection; hold any group to replace its assignment. Tap an assigned group to recall it; double tap to center. Assigned groups show their unit count. Small finger movement within the same button no longer silently drops the press. Physical keyboard Ctrl+number assignment is preserved.
- The **Command buttons** size setting also scales control groups and their touch targets. Groups wrap to two rows if enlarged resources would overlap them.
- **Gamepad controls** is available in App Options and the in-game Controls menu. The left stick moves the pointer and the right stick/D-pad pans the camera. Pointer/camera speeds, dead zone, stick swapping and all twelve supported button bindings are configurable. Imported cursor artwork is used when available, with a fallback pointer for incomplete imports.

Default controller bindings:

| Button | Action |
| --- | --- |
| A / Cross | Select/click; hold and move to box-select |
| B / Circle | Right-click move/interact |
| X / Square | Attack targeting |
| Y / Triangle; Select / View | Cancel/back |
| Left shoulder | Hold for precision pointer movement |
| Right shoulder | Recall current control group |
| Left/right trigger | Previous/next control group |
| Left stick press | Assign current control group |
| Right stick press | Stop |
| Start / Menu | Game menu |

Alternative bindings include Hold Position, Select Larvae and zoom controls. Touch remains available. Held inputs are cleared on focus loss, controller disconnection and settings changes. Digital and analog trigger reports are deduplicated.

## Smaller caches

Imported content previously retained each source CD archive's entire logical size in the cache, producing almost 4 GB of apparent cache with a mission loaded. Sparse files did not necessarily occupy that much physical storage. Cache preparation now packs only the needed blocks and rekeys offset-encrypted data without changing decoded assets. Existing caches migrate automatically, and new imports use the same fix.

Movies are now prepared individually only when played. Once the decoder owns the movie, its temporary archive is closed and removed. The app also removes the two old whole-movie caches automatically. Music remains cached to avoid preparation pauses during gameplay.

With the supplied classic files, normal persistent content cache totals about **235 MB (225 MiB)**, plus a compact active mission, instead of nearly 4 GB apparent size. A single movie temporarily uses additional disk space while opening; opening it may take a little longer. Video quality, audio and imported files remain unchanged. Actual savings depend on the device's filesystem and imported files. See [STORAGE-80.md](STORAGE-80.md) for measurements.

Normal in-game saving and loading are unchanged. Save-file import/export is not included.

## OpenSnowstorm review

[OPENSNOWSTORM-REVIEW.md](OPENSNOWSTORM-REVIEW.md) identifies useful replay-viewing, replay-regression, timing and keyboard-binding ideas. No code from that fork was copied. Its desktop UI, incomplete AI planner and different save format are not replacements for StarDroid's implementations.

## Installation and validation

Install the signed APK over the existing app; do not uninstall to update. The application ID and signing certificate are unchanged. Use **build 80 on all nearby multiplayer devices** because AI behavior has changed. No game-data re-import is required. Diagnostics / credits remains available.

Validation passed: 10 worker/cheat regression groups, 13 AI production groups and a natural Hard AI match, 22 campaign regression groups, 345 controller/group checks, 122 scrollbar checks, 24 cache/save checks, 269 original-asset comparisons and all 17 cinematics. The package check verified both native architectures, all 42 JNI methods, the original signing identity and 16 KiB alignment. Lint reported zero errors. Focused reports are in `validation/`. They use original locally imported data where indicated. Physical Android/controller testing and full campaign playthroughs are still pending.

The source checkout retains the historical build 78 native prebuilts. Rebuild both ABIs with `python3 scripts/build.py`; do not package those old libraries with `--skip-engine`. The provided 1.0.10 APK contains freshly rebuilt build 80 engines.

# OpenBW Android — test 0.22

Offline Android WebView/WASM port for personal testing. Android 8+ (API 26),
landscape, target API 35. Original game data is imported locally and is not bundled.

## Install and import

Install **OpenBW-Android-0.22.apk** over the existing app. Keep the app installed
so its files and settings remain intact.

Open **App Options → Import game files**. The file picker accepts several files
at once, identifies them, and installs the matching content:

| File | Content |
| --- | --- |
| StarDat.mpq, BrooDat.mpq, Patch_rt.mpq | Required core game data |
| StarCraft.mpq | Original campaigns, voices, music, interface and mission openings |
| BroodWar.mpq | Expansion campaigns, voices, music and mission openings |
| Original Install.exe | Corresponding CD archive, detected from its contents |
| Previously exported mission ZIP | Existing mission bundle compatibility |

For this update, select the large **StarCraft.mpq** and **BroodWar.mpq** once to
install the expanded catalog. Existing core MPQs do not need to be reimported.
Installed counts and import errors are shown in App Options. The old mission
export controls have been removed. Imports use validated paths and replace each
installed bundle atomically; a failed bundle preserves its previous version.
The app has no network permission and does not download game data.

**Single Player** now opens the original **Original / Expansion** chooser,
followed by the matching campaign screen. The catalog includes all 30 original
missions, Boot Camp, and 33 expansion map files covering all 26 main missions,
both Terran 5 variants, six Zerg 4 variants, and Dark Origin. Hidden variants are
selected by the original mission's next-scenario trigger. The secret mission is
also available from the Zerg mission list for testing.

## Changes in 0.22

- Restored the original victory/defeat message sounds and race-specific building
  placement thump. Worker acknowledgements remain separate.
- Hatchery/Lair building morphs are offered when allowed by the mission. A unit
  with missing prerequisites stays visible and grey, while mission-forbidden
  units remain hidden. Zerg 2 can morph a Lair and unlock a Spire.
- Single Eggs show the unit being morphed next to the progress bar. Groups retain
  Egg group icons without a production queue.
- Refineries/Extractors/Assimilators show HP as well as remaining gas. Vulnerable
  objective powerups retain HP; invincible ones do not. The Chrysalis no longer
  has a placeholder armor panel.
- Beacons and objective powerups transfer silently. Real unit rescues retain
  their original rescue cue and selection flash.
- Menu panels move smoothly, start quickly, and ease to a stop (560 ms entry,
  320 ms exit). Original bitmap text and artwork move together.
- App Options replaces Campaign Editor and leads directly to the consolidated
  native setup page. In-game sound, speed, video and testing controls share the
  original blue dialog frame, bitmap labels, and consistent spacing.
- Campaign execution adds expansion script indices, multirun/call branches,
  more AI instructions, death/score conditions, ownership transfers, unit stat
  changes, countdown pausing, and next-scenario branching. Ground/air location
  flags and Exact comparisons now follow the original CHK encoding. Empty TBL
  sound references are silent. Missions may start with no player units while
  their introduction creates or transfers the opening force.

## Controls

| Gesture | Action |
| --- | --- |
| Tap friendly unit | Select it |
| Double tap unit | Select units of that type |
| Tap destination with military units | Attack-move / attack target |
| Tap destination with workers | Move, gather or contextual action |
| Drag world | Pan camera |
| Hold, then drag | Select a group |
| Two-finger pinch | Zoom; optional zoom-out is under Video |
| Tap / drag minimap | Move camera |
| Build command | Position preview, then confirm with Build |
| Tap production icon | Cancel that training/morph/research item |
| Menu above portrait | Pause simulation; music continues |
| Android Back | Cancel targeting, return through menus, or open App Options at title |

**Menu → Options** contains Sound, Speed, Video and Testing Cheats.
Widescreen and zoom-out are optional. **Test Victory** opens the original result
flow without completing the mission. Testing cheats disable replay export.
Original menu and command-card sounds are independent of music volume.

## Scope and remaining work

The original maps, briefings, dialogue, technology restrictions and triggers are
loaded from the user's game files. All catalog entries have startup/integration
checks; this is not certification of complete manual campaign playthroughs.
Physical Android audio, memory use, and sustained frame rate still need device
checks. Widescreen and touch placement are port adaptations.

Campaign AI remains a reconstruction with one production manager per computer
player. It executes the original scripts, pays normal costs, and performs
build/train/morph/research/attack actions. Multi-town expansion, transport
coordination, tactical spellcasting, guard behavior and campaign-specific
leaderboards do not yet match the retail game. Save/load, full cinematic
sequencing, and multiplayer remain unfinished. ZZZKBot is the separate Zerg
skirmish opponent.

## Build

On Linux x86-64 with Python 3.12+ and Java 17+ (`java` and `keytool`):

```sh
python3 scripts/build.py
```

This regenerates web assets from the pinned source and adaptation scripts,
checks all module hashes, downloads/checks Android SDK tools and ECJ if needed,
then compiles, signs and verifies the APK. No Gradle is required.
`OPENBW_ANDROID_TOOLS` selects an existing SDK cache.

All seven WASM binaries can be rebuilt from the included source snapshots with
WASI SDK 33 and CMake (tested with 4.4.0):

```sh
python3 scripts/build_engines.py
python3 scripts/build.py
```

`WASI_SDK` selects an existing SDK; otherwise the campaign build downloads and
checks it. CMake must be on PATH. `ENGINE-BUILD.json` records every shipped binary
and the pinned BWAPI/ZZZKBot archives. `CAMPAIGN-BUILD.json` records the common
engine patch and SDK. `UPSTREAM.json` retains the provenance of the original
unmodified fork. `patches/campaign.patch` includes the engine and bot-build
changes. The standalone media decoder is `web/media_decoder.cpp`; the console
and music host sources are in `web/`. Portrait decoding uses unmodified libsmacker 1.2.0 in a separate replaceable
`portrait-decoder.wasm`; see `PORTRAITS-BUILD.json`, `vendor/libsmacker/COPYING`,
`web/portrait_decoder.c` and `scripts/build_portraits.py`. Its full source is
included and the APK carries its LGPL notice. The cinematic adapter in `web/cinematic_decoder.c` builds a separate
`cinematic-decoder.wasm` with original PCM audio and frame-at-a-time video.
Use `scripts/build_cinematics.py` to rebuild it. The same portrait adapter builds a separate
`menu-decoder.wasm` with a 320×256 / 180-frame limit for original menu/briefing panels;
the portrait decoder keeps its previous 128×128 limits and identical binary hash. Bot build timestamps are fixed for
reproducible output. Engine source is extracted into `build-engine/` at build time.

The development signing key is retained from earlier versions:
`signing/test-key.p12`, alias `openbw-test`, password `android`.
Keep the package ID/key for in-place updates; this is not a production signing key.

## Tests

`VALIDATION.md` describes the current evidence and limits. Reports are under
`validation/`; original game files, screenshots and recordings are excluded.
Node integration tests require Playwright and a Chromium executable.

```sh
OPENBW_CHROME=/path/to/chrome OPENBW_V22_FIXTURES=/path/to/unpacked-bundles node tests/campaign_v22.cjs
OPENBW_CHROME=/path/to/chrome node tests/menu_motion_v22.cjs
OPENBW_CHROME=/path/to/chrome OPENBW_BOT_REPORT=bot-v22.json node tests/bot_startup.cjs
```

`OPENBW_V22_MISSIONS` accepts comma-separated catalog IDs. Set
`OPENBW_V22_DETAIL=0` for only startup checks and `OPENBW_V22_FRAMES` for the
simulation duration. Fixtures default to `/tmp/openbw-v22-fixtures` with a
folder per mission and interface/music/story bundles. Core MPQs default to
`/tmp/openbw-test-data`. All tests use desktop Chromium, not an Android emulator.
`tests/GameContentHarness.java` runs the real combined archive importer and
bundle validators in a desktop JVM (org.json is required).

## Provenance / credits

- Engine: [OpenBW](https://github.com/OpenBW/openbw) contributors.
- Browser engine and host: [heiner/openbw](https://github.com/heiner/openbw),
  commit `469d2037e2fd03085dac4729912f4188bc2a778b`, deployed at
  [openbw.heiner.ai](https://openbw.heiner.ai/).
- Bot bridge: [OpenBW/bwapi](https://github.com/OpenBW/bwapi).
- Zerg opponent: [ZZZKBot](https://github.com/chriscoxe/ZZZKBot), Chris Cox.
- Weave: Alexandre Coderre-Chabot, [acodcha/sc](https://github.com/acodcha/sc),
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), unmodified. See
  `app/src/main/assets/game/maps/ATTRIBUTION.md`.
- StarCraft / Brood War names and original game data belong to Blizzard.
  This is an unofficial test app.

Upstream OpenBW does not provide a clear top-level license grant in the pinned
source snapshot. This package does not claim to resolve that or grant new rights
to third-party code/data. Resolve upstream licensing before public redistribution.


Mission filename metadata comes from [PyMS](https://github.com/poiuyqwert/PyMS),
commit `bfc5d3aad0b5614a5aff72c223f8efa00afddfa4`, `PyMS/Data/Listfile.txt`.
The MIT notice is included in `app/src/main/assets/missions/PyMS-LICENSE.txt`.

Campaign opcode layout reference: [PyMS AIBIN.py](https://github.com/poiuyqwert/PyMS/blob/bfc5d3aad0b5614a5aff72c223f8efa00afddfa4/PyMS/FileFormats/AIBIN.py).
All original and expansion mission filenames use the same pinned PyMS Listfile metadata.
No original campaign maps, AI bytecode, voices, music or portraits are bundled.

Interface geometry is read from the original `rez/statbtnt.bin`, `statbtnp.bin`,
`statbtnz.bin`, `statport.bin`, `stat_f10.bin` and `glumain.bin` when developing
this host. File-format references: pinned PyMS `DialogBIN.py` and `FNT.py`.
These proprietary BINs, artwork, fonts and animations are not packaged.

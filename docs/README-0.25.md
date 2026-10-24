# OpenBW Android 0.25 — native

The game now runs as compiled C++ on Android. JNI connects the engine to an
Android SurfaceView, Android Canvas draws the original interface, and a native
PCM mixer feeds AudioTrack. There is no WebView, JavaScript, or WebAssembly in
the APK. It supports 64-bit ARM and x86 Android devices, Android 8.0 or newer.
Original game files are imported locally and are not included.

This is a native test build. Version 0.25 follows a fresh comparison with the
retained 0.22 browser version and the 0.24 native baseline. It restores Registry
and mission history, custom-map setup, original menu geometry, music controls,
1×–16× speed presets, order lines, and testing controls. It also corrects menu
animation layers and labels, briefing timing and speaker borders, group
wireframe selection, targeting gestures, and two-finger camera movement.
See `docs/WEBVIEW-NATIVE-PARITY.md` for the request checklist and `VALIDATION.md`
for the exact comparisons, Android checks, and remaining limits.

## Install

Install **OpenBW-Android-0.25.apk** over 0.22, 0.23 or 0.24. The package ID and signing key are
unchanged, so existing imported game files and campaign bundles are retained.
Do not uninstall the old app first. Display and sound preferences now use native
Android preferences; browser-only preferences start at the native defaults.
The first launch rebuilds a local cache from the existing imported bundles.

New installs: open **App Options → Import game files** and select the classic
files. Several files may be selected together.

| File | Content |
| --- | --- |
| StarDat.mpq, BrooDat.mpq, Patch_rt.mpq | Required core data |
| StarCraft.mpq | Original campaigns, voices, original fonts/interface, music, story openings and introduction |
| BroodWar.mpq | Expansion campaigns, voices, music and story openings |
| Original Install.exe | Corresponding CD archive, detected from its contents |
| Previously exported mission ZIP | Compatible existing mission bundle |

No additional import is required when these files were already imported in
0.22. The app has no network permission. Original fonts are used when installed;
a system-font fallback keeps the core game usable before the interface import.

## Native features

- Original and Brood War campaign selection, with the existing 64-map catalog,
  original briefing scripts, portraits, dialogue, technology restrictions,
  mission openings, mission branching, and score screens.
- Native C++ simulation and software rasterizer. The Android display presents
  its framebuffer with the original PCX/GRP/FONT/BIN interface artwork.
- Native audio for effects, voices, victory/defeat, music and building placement.
  Menu, portrait and introduction Smacker video decoding uses libsmacker.
- The existing Zerg ZZZKBot opponent runs natively for custom games. Select one
  computer slot or close all slots for practice; select a race or Random.
  Custom SCM/SCX imports validate and show map information before you press OK.
  The included Weave test map remains available.
- Vsync-driven menus with a quick start and smooth easing into place. In-game
  sound, speed, video and testing controls use the original blue dialog artwork.
- Existing 0.22 gameplay fixes remain: Lair/Hive availability, visible disabled
  technology, Egg target icons, refinery HP and gas, Chrysalis panel cleanup,
  and silent beacon transfers.
- Fixed deferred creep cleanup when mass building destruction fills the
  engine's creep-recession pool, encountered in Brood War Zerg 6 validation.

## Controls

| Gesture | Action |
| --- | --- |
| Tap friendly unit | Select |
| Double tap unit | Select units of that type |
| Tap destination with military units | Attack-move or attack target |
| Tap destination with workers | Move, gather, or contextual action |
| Drag world | Pan camera |
| Hold, then drag | Select a group |
| Pinch and move two fingers | Zoom and pan; optional zoom-out is under Video |
| Tap or drag minimap | Move camera |
| Building preview | Drag into position, then tap Build |
| Tap production icon | Cancel that item |
| Tap group wireframe | Select that individual unit |
| Menu above portrait | Pause and open game options |
| Android Back | Cancel targeting or return through menus |

## Remaining limits

This is a native test build, not the original Blizzard executable. Campaign AI
still has one production manager per computer player; multi-town expansion,
transport coordination, tactical spellcasting and some campaign behavior remain
incomplete. Save/load, replay loading, multiplayer and full cinematic
sequencing are not implemented in this native build. Custom-game replay export
is available from the score screen; testing cheats disable it. The introduction is
available from the title screen. Physical-device performance, audio routing,
and extended campaign playthroughs require further device testing. Custom games
currently support one computer opponent, whereas the browser host can run
multiple bot workers. Passing a startup check does not certify that every mission can be completed.

The native software rasterizer still performs its rendering on the CPU. Native
compilation removes the browser runtime; it does not establish a particular
frame rate or guarantee lower power consumption on every phone.

## Build from source

On Linux x86-64 with Python 3.12+, a JRE 17+, and `make`:

```sh
python3 scripts/build.py
```

The script downloads and checks Android SDK platform 35, build tools 35, NDK
r27d, and ECJ 3.33.0. It installs CMake 4.4.0 into its tools cache if needed,
reconstructs the pinned engine and bot sources, compiles both native ABIs,
compiles Java, signs the APK, verifies signatures and 16 KiB native-library
alignment, and compares packaged assets byte for byte. `OPENBW_ANDROID_TOOLS`
selects the tools cache. No Gradle or browser SDK is needed.

After a Java/UI-only edit, `python3 scripts/build.py --skip-engine` packages the
already compiled native libraries. To rebuild one ABI directly:

```sh
python3 scripts/build_native_engine.py arm64-v8a
```

`native/runtime.cpp` is the JNI/runtime adapter; `native/audio.h` implements the
mixer. `NativeSurface`, `NativeArt`, `NativeGlue`, `NativeHud`, `NativeCampaign`
and `NativeResults` implement Android presentation. `NativeData` reconstructs
sparse MPQs from existing imported bundles while preserving encrypted offsets.
`prepare_native.py` records the native portability and lifetime fixes, applied
after `patches/campaign.patch`. Vendor archives and their pinned hashes are
recorded in `UPSTREAM.json` and `ENGINE-BUILD.json`. Generated engine sources
are not needed in the source archive and are reconstructed during a build.
`NATIVE-BUILD.json` records this release's native sources and library hashes.

libsmacker is a separate, replaceable `libsmacker.so`. Its complete unmodified
source and LGPL license are in `vendor/libsmacker/`; the APK carries the notice
and license. Rebuilding the APK permits replacing that library. The development
signing key is retained in `signing/test-key.p12`, alias `openbw-test`, password
`android`; it is not a production signing key.

The legacy web source is retained as implementation history and as provenance
for the command layout data. It is not packaged or executed by the native app.
See `docs/README-0.22.md` for that older architecture.

## Validation

See `VALIDATION.md` for results and limitations. `tests/native_campaigns.py`
exercises all catalog maps with a compiled desktop version of the same C++
engine. `tests/native_controls.cpp` exercises commands, morphing, presentation
queries, and the native audio mixer. `tests/NativeDataHarness.java` tests all
imported bundles using the actual Android cache reconstruction code.
`tests/NativeInstrumentation.java` and `tests/NativeParityInstrumentation.java`
are built into a separate test APK. They check Android presentation, native
commands, original menu navigation, real touch gestures, bot restart, and
introduction playback. `tests/browser_reference_v25.cjs` captures matching
scenes from the unchanged browser runtime. None of the test harness is included in the application APK.
Private game files and test screenshots are excluded from the source package.

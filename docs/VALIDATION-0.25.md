# OpenBW Android 0.25 native validation

Version 0.25 was compared against the retained 0.22 browser version and the
0.24 native APK. The browser ran in touch-enabled Chromium; both native APKs
ran in an Android 9/API 28 x86_64 emulator at 960 × 640. The browser's 46 game
asset files were checked byte for byte against the retained source archive and
were not changed for this comparison.

Both final candidate Android suites passed. The two runs captured 40 scenes;
selected comparison screenshots were inspected locally. No OpenBW or AndroidRuntime
errors were logged by either final test process.

The emulator is version 37.2.12, using software CPU emulation and SwiftShader
without KVM. These runs do not measure phone performance. No physical ARM phone
or speaker output was tested. Both ARM64 and x86_64 libraries were compiled.

Original game archives are private external fixtures. No original MPQs,
campaign maps, voices, artwork, screenshots, or recordings are included in the
APK or source package. The freely licensed Weave test map is included.

## Fresh comparison and regression evidence

| Report | What it checks |
| --- | --- |
| `validation/browser-reference-v25.json` | Unchanged 0.22 running in Chromium: title, Original/Expansion chooser, Registry, campaign/history, custom setup, Zerg 2 HUD, pause/options, sound/speed/video/testing, victory and score screens |
| `validation/campaign-v22-parity.json` | Browser Zerg 2 Lair, disabled technology, Egg target, Extractor HP/gas, Chrysalis details, original build/victory PCM fingerprints, silent beacon transfer and expansion chooser |
| `validation/native-android-v24-parity-baseline.json` | Retained 0.24 APK rerun in the same Android emulator before changes |
| `validation/native-parity-v25.json` | Candidate navigation, attached menu labels/stationary figures, map validation and explicit start, practice/alternate computer slot, briefing speech, options and actual Android touch sequences |
| `validation/native-android-v25.json` | Candidate campaign controls, native audio and AudioTrack, production HUD, scores, custom AI, restart, widescreen, portraits, suspend/resume and introduction |
| `validation/native-controls-v25.json` | Compiled desktop C++ command/audio checks, building placement, beacon ownership, render resizing and cancellation |
| `validation/native-package-v25.json` | Candidate APK identity, signatures, architecture/JNI bindings, asset bytes, library alignment, and absence of a browser runtime |

The Android tests are separate instrumentation APKs. MotionEvents exercise the
visible command cards, menus, briefing drag, group wireframes, camera gestures,
placement preview, Build and Cancel. Diagnostic selection, resources, instant
production, map reveal and forced outcomes make the scenes repeatable. They do
not constitute unassisted campaign playthroughs. Final Android reports retain
the candidate APK hash; package validation requires that hash to match.

The native controls run verifies the original `ZBldgPlc.wav` PCM is scheduled
when a building order is issued. It transfers a neutral beacon and verifies
that rescue/new-unit notifications do not increase. The imported victory WAV
produces 95,990 nonzero samples. The original introduction decodes at 320 × 308
with 2,082 frames; its first five seconds produce 479,581 nonzero audio samples.
These verify decoding and mixing, not the phone speaker, Bluetooth routing or
perceived audiovisual synchronization.

## Corrections from the comparison

- Restored Registry/profile selection, mission history with an explicit OK,
  original custom-map setup and validation, and navigation between these screens.
- Restored the original pause/options geometry and Help/end navigation; added
  back mute, music enable/track/next, 1×–16× speeds, order lines, zoom presets,
  defeat and reset controls in the blue options screens.
- Corrected menu animation layering, multiline/bottom-aligned campaign captions,
  labels attached to their sliding panels and stationary campaign figures.
  Entry uses a 560 ms ease-out and exit a 320 ms ease-out, driven by Android vsync.
- Corrected briefing recording duration, text expiry, scrolling lead-in, original
  portrait masks/frames and active-speaker borders. Eleven Protoss 2 transmission
  recordings are checked against their actual decoded duration.
- Restored individual group-wireframe taps, separate unit wire bitmaps and
  original hero/status borders; corrected targeting drags, pinch midpoint pan,
  gesture cancellation on pause and adaptive command hints.
- Kept the building ghost 48 physical screen pixels above the finger, with
  explicit Build/Cancel and placement validity governing the Build button.
- Matched the compact victory dialog and profile name on the score screen.
- Custom setup now supports a chosen computer slot or all slots closed for
  practice. Native orders are applied to the selected computer slot. The native
  bot host currently supports one computer, which the setup states explicitly.

The consolidated App Options import screen, Original/Brood War chooser and
64-map catalog remain available. The existing Lair/Spire path, mission-allowed
locked commands, Egg target, Extractor HP/gas, Chrysalis cleanup and beacon
sound fixes were rechecked instead of being assumed from source alone.

The extended test run exposed an instrumentation clock error: its manual render
helper supplied simulation time while the app supplied elapsed display time.
This could move the click-marker animation backwards and cause a bounds error.
The helper now uses the app's clock. UI tests also wait for rendered frames and
finished transitions before tapping; they do not rely on a fixed short sleep.
An emulator System UI ANR was dismissed during setup, before the final runs.

## Retained evidence, not fresh full-campaign claims

`validation/native-campaigns-v23.json` records all 64 catalog maps starting and
advancing in the compiled desktop engine, each requesting 2,400 simulation
frames. Original outcome triggers can end a run sooner. The campaign interpreter
and simulation are unchanged by this release. This retained run includes the
fix for deferred creep removal when the recession pool fills in Brood War Zerg 6.
It is a startup/AI smoke test, not proof that every mission can be completed.

`validation/native-import-v23.json` records the actual Java `NativeData` code
reconstructing all 70 imported bundles and reusing their caches. That importer
is unchanged. Updating the APK retains the existing core files and imported
bundles; it does not require uninstalling or importing them again.

## Repeating the checks

Build the app first, then the instrumentation package; do not build their Java
classes concurrently:

```sh
python3 scripts/build.py
python3 tests/build_instrumentation.py
adb install -r dist/OpenBW-Android-0.25.apk
adb install -r build-native/instrumentation/native-tests.apk
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativeParityInstrumentation
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativeInstrumentation
```

The device must already contain the user's imported game files. The touch-only
subset uses `-e section touch` before the instrumentation component name.

Desktop checks:

```sh
python3 tests/build_native_host.py controls
build-native/host/native-controls /path/to/fixture-directory
python3 tests/native_package.py
```

The fixture directory contains `STARDAT.MPQ`, `BROODAT.MPQ`, `patch_rt.mpq`,
`StarCraft.mpq` and `BroodWar.mpq`; desktop CD files start at the MPQ header.
The Android importer also accepts original installer wrappers. Browser captures
use `tests/browser_reference_v25.cjs` and `tests/campaign_v22.cjs` with the
external fixture directories documented in those scripts.

## Remaining limits

Campaign AI has one production manager per computer player. Multi-town behavior,
coordinated transports, tactical spellcasting and some mission behavior remain
incomplete. Custom games support one native computer opponent; the browser host
can run multiple bot workers. Save/load, replay loading, multiplayer and full
cinematic sequencing are not implemented. Custom-game replay export is available;
testing cheats disable it.

Physical-device frame pacing, audio routing/sync, Activity destruction/recreation,
large imports, long matches and complete campaigns still require device/playthrough
validation. The native CPU rasterizer does not guarantee a particular frame rate
or lower power use just because the browser runtime has been removed.

# OpenBW Android 0.26 validation

The compiled native gameplay matrix passed **202 checks with zero failures**.
It exercises all 50 standard structure types, 39 train/morph unit types,
both Templar merges, both ammunition types, all 24 research items and all
50 upgrade types through their maximum levels (82 upgrade-level completions).
The detailed scope, fixes and test conditions are in
`docs/GAMEPLAY-TESTS-0.26.md`.

Both final Android campaign/audio and menu/touch suites passed. The new Android
construction checks passed as separate Terran and corrected Zerg sections on
the same APK. Together they captured 46 scenes. Selected scenes were inspected;
no OpenBW or AndroidRuntime errors were logged by the final test processes.

## Fresh evidence

| Report | Coverage |
| --- | --- |
| `validation/native-gameplay-v26.json` | Construction, unit production, tech trees, costs, refunds, queues, supply/resource rejection, creep/power, morphs, infestation and Nydus endpoints |
| `validation/native-controls-v26.json` | Campaign Lair/Spire requirements, disabled commands, Egg target, Extractor HP/gas, Chrysalis details, build/victory audio, silent beacon transfers, touch cancellation, resizing and introduction decoding |
| `validation/native-android-v26.json` | Campaign controls, native audio/AudioTrack, production HUD, scores, custom AI, restart, widescreen, portraits, suspend/resume and introduction |
| `validation/native-parity-v26.json` | Navigation, menu labels/figures, custom-map validation/start, practice and alternate computer slot, briefing speech, options and Android touch gestures |
| `validation/native-gameplay-android-v26.json` | Actual Android command-card and placement touches for busy Lift Off, blocked landing/add-ons, completed add-on and Nydus exit |
| `validation/native-package-v26.json` | APK identity and signature, JNI bindings, both architectures, asset bytes, library alignment, test APK hashes and absence of a browser runtime |

## Fixes from this test pass

- Keep Lift Off disabled while a building is busy.
- Validate landing footprints before enabling Build confirmation.
- Validate both the parent and add-on footprints when placing an add-on.
- Offer Build Nydus Exit on a completed, unlinked Nydus Canal. The exit uses
  valid creep, costs no additional resources, and links both endpoints.
- Avoid a null ground-weapon dereference in the unit diagnostic readout.

The new fixes are stored in `patches/native-gameplay.patch`. Reconstructing the
engine from the retained vendor source, campaign patch and new gameplay patch
was checked against the tested engine source. The original browser assets are
unchanged.

## Test conditions and interpretation

The construction matrix runs the native simulation on the included Weave map.
Fixture resources, accelerated production and nearby worker placement keep the
run practical. Actions still use ordinary command cards/orders and actual
placement, prerequisites, resource charges, supply and completion logic.
Cancellation and queue cases restore normal timing. The infestation fixture
adds a damaged enemy Command Center; a Queen then infests it through the normal
command before producing an Infested Terran.

Android tests use a separate instrumentation APK, with real MotionEvents for
command cards, menus, placement preview, Build/Cancel and gestures. Selection,
resources, map reveal, instant production and forced outcomes are fixture
controls. These are repeatable regression tests, not unassisted playthroughs.

The Android environment is Android 9/API 28 x86_64, emulator 37.2.12 at
960 × 640, software CPU emulation and SwiftShader without KVM. Both ARM64 and
x86_64 release libraries were compiled. Emulator speed does not establish phone
performance. Decoded/mixed PCM and AudioTrack checks do not verify physical
speaker output, Bluetooth routing or perceived audiovisual synchronization.

Original game archives are private external fixtures. No original MPQs,
campaign maps, voices, artwork, screenshots or recordings are included in the
APK or source package. The freely licensed Weave test map is included.

## Retained comparison and import evidence

The 0.25 comparison report is preserved at `docs/VALIDATION-0.25.md`.
`validation/browser-reference-v25.json` records the unchanged 0.22 browser
version running in touch-enabled Chromium; `validation/campaign-v22-parity.json`
records its campaign/audio checks. The browser was not rerun for this gameplay
pass. The native parity suite was rerun against the retained expectations.

`validation/native-campaigns-v23.json` records all 64 catalog maps starting and
advancing in the compiled desktop engine, requesting 2,400 frames each (original
outcome triggers can stop a run sooner). This is retained startup/AI smoke
evidence, not proof that every mission is completable.

`validation/native-import-v23.json` records the actual Java importer rebuilding
all 70 bundles and reusing its caches. The importer is unchanged. The update
retains the same package and signing certificate, so existing imported files
are retained when installing over the earlier app.

## Repeating the checks

Build the app before the test APK; their Java builds must not run concurrently:

```sh
python3 scripts/build.py
python3 tests/build_instrumentation.py
adb install -r dist/OpenBW-Android-0.26.apk
adb install -r build-native/instrumentation/native-tests.apk
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativeInstrumentation
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativeParityInstrumentation
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativeGameplayInstrumentation
```

The device must already contain the user's imported game files. The parity
touch-only subset uses `-e section touch` before the component name.

```sh
python3 tests/build_native_host.py gameplay
build-native/host/native-gameplay /path/to/game-files app/src/main/assets/native/weave.scx report.json
python3 tests/build_native_host.py controls
build-native/host/native-controls /path/to/game-files
python3 tests/native_package.py
```

The desktop fixture directory contains `STARDAT.MPQ`, `BROODAT.MPQ`,
`patch_rt.mpq`, `StarCraft.mpq` and `BroodWar.mpq`. Desktop CD files start at the
MPQ header. The Android importer also accepts original installer wrappers.

## Remaining limits

Construction cancellation was sampled across races rather than repeated for
every structure. Nydus endpoints were checked, but not a full transport/combat
scenario. Every combat matchup, spell target, long match and complete campaign
has not been tested.

Campaign AI still has one production manager per computer player. Multi-town
behavior, coordinated transports, tactical spellcasting and some mission
behavior remain incomplete. Custom games support one native computer opponent.
Save/load, replay loading, multiplayer and full cinematic sequencing remain
unsupported. Custom-game replay export is available; testing cheats disable it.

Physical-device frame pacing, audio routing/sync, Activity destruction/recreation
and large imports still require device validation. Native rendering alone does
not guarantee a particular frame rate or reduced power use.

# OpenBW Android 0.24 native validation

This is a native test release. A fresh Android 9 AOSP x86_64 emulator boots,
installs the APK, loads the imported files, and runs the game. The original
0.23 build completed its Android integration run on this emulator. Version
0.24 adds the interface corrections listed below and extends the Android test
coverage. The final run passes; results are recorded in
`validation/native-android-v24.json`.
The emulator uses software CPU emulation and SwiftShader without KVM. Its
frame rate is not a phone-performance measurement. No physical phone was used.

Original game archives are external test fixtures. No original MPQs, campaign
maps, voices, artwork, screenshots, or recordings are included in this source
package or APK. The freely licensed Weave test map is included.

## Completed checks

- `validation/native-campaigns-v23.json`: all 64 catalog maps start and advance
  in the compiled desktop C++ engine. Each run requests 2,400 simulation frames;
  original victory/defeat triggers may stop a run earlier. The simulation,
  campaign interpreter and rendering sources are the same sources compiled for
  Android. This is a startup/AI smoke test, not complete campaign playthroughs.
- `validation/native-controls-v23.json`: Zerg 2 exposes the Lair command and
  completes the morph through the native input stream. A mission-available
  Mutalisk remains visible but disabled without a Spire. A Drone Egg reports
  its target and icon; the Young Chrysalis has no placeholder armor details;
  an Extractor is placed and reports HP plus gas. Controlled resources and
  instant production accelerate these checks.
- The same controls report checks actual PCM output from the imported victory
  WAV and decodes the original introduction using native libsmacker:
  320 x 308 pixels, 2,082 frames, with nonzero audio samples. This verifies
  decoding and mixing, not the phone speaker or Android audio routing.
- `validation/native-import-v23.json`: the actual Java `NativeData` code
  reconstructs all 70 existing content/mission ZIP bundles into sparse MPQs
  and reuses the resulting caches. Core MPQs and imported bundles retain the
  existing filenames and application data directory.
- Both `arm64-v8a` and `x86_64` libraries compile and link with NDK r27d.
  The engine and computer-opponent code are native C++; Android Java handles
  presentation and input, and AudioTrack consumes the native mixer output.
- `validation/native-package-v24.json`: APK v2/v3 signatures, the retained
  update certificate, ZIP CRC, all packaged assets, all JNI method exports,
  library architectures, dependencies and 16 KiB segment/ZIP alignment pass.
  The APK contains no HTML, JavaScript, WASM, or WebView class reference.
- Final Java sources compile through ECJ and D8 for Android API 26+. The
  application declares no Internet permission.

The campaign smoke test exposed the original deferred creep-removal fatal path
in Brood War Zerg 6. The native source preparation now retries removal after
capacity becomes available; all 64 maps passed after this correction.

## Android emulator verification

`validation/native-android-v24.json` records the new run on Android 9/API 28,
emulator 37.2.12, at 960 x 640. The APK update retains the three core MPQs and
70 imported content/mission ZIPs installed under 0.23. The separate test APK
uses Android MotionEvents for menu and command taps and briefing dragging;
diagnostic selection, resources, instant morphing, and forced outcomes make
the gameplay checks repeatable. Android screenshots are inspected locally.

The checks cover the title and game chooser, Brood War campaign menu, Zerg 2
briefing, Lair command and completed morph, disabled Mutalisk explanation,
Drone Egg target, Chrysalis details, game options, victory/results, a native
computer-opponent session, race restart, a Terran production queue, damaged
Protoss HP/shields, widescreen console, portrait variants, suspend/resume of
the game surface, and the introduction. The native mixer produces nonzero
PCM samples and AudioTrack reports playing. The headless emulator does not
verify speaker sound, Bluetooth routing, or audiovisual synchronization.

The previous Android 11 attempt is retained in
`validation/native-android-v23.json`. It failed in Android's network service
before installation. The fresh Android 9 run also encountered a System UI
ANR during its initial boot; that was dismissed before the final app checks.
These environment problems are separate from the application's test results.

`tests/NativeInstrumentation.java` and `tests/build_instrumentation.py` provide
a separate test APK for a working emulator/device. It checks native menus,
briefing, Zerg controls, options, outcomes, bot restart and introduction
playback. That test APK and harness are not packaged in the application.

With the APK installed and personal game files already imported:

```sh
python3 scripts/build.py --skip-engine
python3 tests/build_instrumentation.py
adb install -r dist/OpenBW-Android-0.24.apk
adb install -r build-native/instrumentation/native-tests.apk
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativeInstrumentation
```

## Interface corrections in 0.24

- Original larger briefing font, smooth automatic dialogue scrolling with
  manual dragging, and text/portraits that move with the briefing panels.
- Original weighted idle portraits, varying talking clips, opaque portrait
  backgrounds, and briefing-monitor shading/scanlines.
- Combined Protoss shield/HP numbers, damage-dependent HP color, energy
  numbers, Detector/status labels, race-specific supply labels, appropriate
  Kills visibility, and tappable stat descriptions.
- Original production labels, queue numbers, empty-slot artwork and connector.
- Mirrored widescreen console extensions and the introduction's 640 x 308
  presentation instead of a cropped 640 x 616 image.

The compiled engine libraries are unchanged from 0.23. The 64-map desktop
campaign run and import checks are retained evidence, not rerun claims.

## Repeating desktop and package checks

With `gcc` and `g++` installed, build the desktop harnesses:

```sh
python3 tests/build_native_host.py controls
python3 tests/build_native_host.py engine
build-native/host/native-controls /path/to/fixture-directory
python3 tests/native_campaigns.py build-native/host/native-engine /path/to/fixture-directory
python3 tests/native_package.py
```

The fixture directory must contain `STARDAT.MPQ`, `BROODAT.MPQ`, `patch_rt.mpq`,
`StarCraft.mpq` and `BroodWar.mpq`; the CD files supplied to the desktop harness
must start at their MPQ header. The Android importer also accepts the original
CD installer wrappers.

## Remaining limits

The campaign AI uses one production manager per computer player. Multi-town
behavior, coordinated transports, tactical spellcasting, and some mission
behavior remain incomplete. Save/load, replay loading, multiplayer, and full
cinematic sequencing are not implemented. Custom-game replay export remains
available; testing cheats disable recording. Phone performance, multi-touch
timing, audio routing, Activity destruction/recreation, import memory use, and
sustained play need device validation. The emulator run is not a full campaign
playthrough. Native compilation alone does not prove a performance gain.

Historical browser-build evidence is in `docs/VALIDATION-0.22.md`; it is not
Android-native validation.

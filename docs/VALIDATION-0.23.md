# OpenBW Android 0.23 native validation

This is a native test release. The Android APK compiles and passes package
checks, and the native engine passes the desktop checks below. **The Android
interface has not been validated on a running device.** The available emulator
failed in Android's system services before APK installation could complete;
no physical Android device was available. Do not interpret the desktop results
as phone frame-rate, touch, display, or audio-output measurements.

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
- `validation/native-package-v23.json`: APK v2/v3 signatures, the retained
  update certificate, ZIP CRC, all packaged assets, all JNI method exports,
  library architectures, dependencies and 16 KiB segment/ZIP alignment pass.
  The APK contains no HTML, JavaScript, WASM, or WebView class reference.
- Final Java sources compile through ECJ and D8 for Android API 26+. The
  application declares no Internet permission.

The campaign smoke test exposed the original deferred creep-removal fatal path
in Brood War Zerg 6. The native source preparation now retries removal after
capacity becomes available; all 64 maps passed after this correction.

## Android verification blocked

`validation/native-android-v23.json` records the failed test environment:
Android 11 AOSP x86_64, emulator 37.2.12, software CPU emulation without KVM.
Android's `system_server` crashed with `IllegalStateException: Lost network
stack`; the package service disappeared and APK installation failed. No app
startup, touch interaction, native Android bot session, or Android screenshot
can be claimed from that attempt.

`tests/NativeInstrumentation.java` and `tests/build_instrumentation.py` provide
a separate test APK for a working emulator/device. It checks native menus,
briefing, Zerg controls, options, outcomes, bot restart and introduction
playback. That test APK and harness are not packaged in the application.

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
available; testing cheats disable recording. Phone performance, touch timing,
audio routing, lifecycle behavior, import memory use, and sustained play need
device validation. Native compilation alone does not prove a performance gain.

Historical browser-build evidence is in `docs/VALIDATION-0.22.md`; it is not
Android-native validation.

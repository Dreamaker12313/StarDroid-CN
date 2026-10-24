# Building StarDroid

[Back to the project](../README.md)

## Supported build environment

The supplied scripts target **x86-64 Linux**. Windows users can use an x86-64 Linux environment such as WSL2; native Windows and macOS builds are not covered by these scripts.

Install these prerequisites:

- Python 3.10 or later.
- JDK 17, including `java`, `javac`, and `keytool`.
- Git and the `patch` command.
- Internet access for the first tool and Gradle dependency download.
- Several gigabytes of free disk space for the SDK, NDK, caches, and native compilation.

The pinned toolchain is Android platform 35, Build Tools 35.0.0, NDK r27d, Gradle 8.9, and Android Gradle Plugin 8.7.3. Downloaded tool archives are checksum-checked by the build scripts. Review the Android SDK/NDK terms when using those tools.

## Build the APK

From the repository root:

```sh
python3 scripts/build.py
```

This downloads the pinned tools, prepares the vendored engine with the patches in `patches/`, compiles ARM64 and x86-64 native libraries, stages the APK assets, and builds the Android package. Game MPQs are not required to compile the app and are never bundled by this build.

Outputs:

- `dist/StarDroid-1.0.apk`
- `dist/SHA256SUMS.txt`

The visible version remains **1.0**, with Android version code **70** for this release. The application ID remains `org.openbw.androidtest` for compatibility with existing installations and JNI bindings. The installed app name is **StarDroid**.

Use `STARDROID_ANDROID_TOOLS` to select a tool-cache directory. The historical `OPENBW_ANDROID_TOOLS` variable is still accepted. The default is `.tools/` in the repository. The helper writes a local `local.properties` pointing Gradle at the staged SDK.

## Signing

A checkout does **not** include the distributed APK's signing key. With no signing variables set, the release build uses Android's local development signing configuration so contributors can install their own build.

To sign with a key you control, set these environment variables before building:

| Variable | Value |
| --- | --- |
| `STARDROID_KEYSTORE` | Absolute path to your keystore. |
| `STARDROID_STORE_PASSWORD` | Keystore password. |
| `STARDROID_KEY_ALIAS` | Signing-key alias. |
| `STARDROID_KEY_PASSWORD` | Key password. |
| `STARDROID_STORE_TYPE` | Optional; defaults to `PKCS12`. |

All four required variables must be supplied together. Supply credentials locally or through a private CI secret store; do not commit them. `signing/`, keystores, and environment files are ignored.

Android only permits in-place updates with the same application ID and signing identity. A contributor's development-signed APK cannot update the distributed APK. Use a separate test device/emulator when preserving an existing installation's imports and saves matters. The published v1.0 APK retains the project's established release signing identity.

## Faster rebuilds

After the initial toolchain setup, reuse the supplied/current native libraries when only Java, Android resources, or documentation changed:

```sh
python3 scripts/build_nearby.py --skip-engine --offline --lint
```

Omit `--offline` if Gradle dependencies are not cached. `--skip-engine` must not be used to test an engine or native patch change.

To rebuild the native engine explicitly:

```sh
python3 scripts/prepare_native.py
python3 scripts/build_native_engine.py arm64-v8a --skip-prepare
python3 scripts/build_native_engine.py x86_64 --skip-prepare
python3 scripts/build_nearby.py --skip-engine --lint
```

Run `prepare_native.py` once before building both ABIs. The generated `native-engine/` tree is disposable; change the patch sources instead of editing that tree alone. libsmacker is rebuilt as a separate shared library, so it can be modified and replaced along with a rebuilt app.

## Tests and validation

`tests/` contains focused Java and native harnesses. Many historic runners require local classic MPQs, extracted fixtures, or previously built helper programs; they are not a single self-contained test suite. Those game-data fixtures are intentionally not distributed.

After tool setup, the pure Java room/protocol test uses the included test-only JSON dependency:

```sh
python3 tests/run_room55.py
```

After preparing its native host binary and eight-start fixture, the upgrade simulation harness accepts your own game-data directory:

```sh
python3 tests/run_upgrades.py /path/to/classic-game-data
```

The screen-edge crash regression uses AddressSanitizer and guard pages with
real building sprites from your local MPQs:

```sh
python3 tests/run_placement.py /path/to/classic-game-data
```

The touch/camera regression covers time-based scrolling, release/cancel behavior,
production gesture routing, and all-direction fractional pans:

```sh
python3 tests/run_scroll70.py /path/to/classic-game-data
```

This runner also needs the existing `build-native/ui58/extract-interface` asset
extractor and the test JSON JAR used by the older UI runners. Its artwork is
extracted from your MPQs into the ignored build directory.

This builds the host test, checks both outline formats and the full placement
render path, and writes `validation/native-placement-v1.0.json`. The optional
`--baseline-binary` argument runs an already-built unpatched copy of the same
harness to verify both original write faults. To check the signed APK against
an existing build 69 APK after assembly:

```sh
python3 tests/check_scroll70_package.py /path/to/build-69.apk
```

Read the runner and its prerequisites before running a data-dependent harness. Reports in `validation/`, `NATIVE-BUILD.json`, and [VALIDATION.md](../VALIDATION.md) record the inputs and scope of the development checks. Historical reports describe their original build, not an assertion that every old runner runs on a clean machine.

For a change, run checks relevant to that change and test on a real device where needed. Multiplayer needs checks on more than one physical device. Do not commit imported MPQs, extracted original artwork/audio, keystores, or local build outputs.

## Source layout

| Path | Purpose |
| --- | --- |
| `app/src/main/java/` | Android menus, input, content import, audio, saves, and local networking. |
| `native/` | C++ runtime, JNI bridge, networking, saves, and Hero Mode. |
| `patches/` | Changes applied to the pinned upstream engine. |
| `vendor/` | Pinned engine source archive and libsmacker source. |
| `native-libs/` | Prebuilt ARM64 and x86-64 shared libraries for faster Android builds. |
| `scripts/` | Build and preparation tools. |
| `tests/`, `validation/` | Regression harnesses and recorded test results. |
| `web/`, `app/src/main/assets/game/` | Historical web host, not shipped in the native APK. |
| `docs/` | Player/developer guides, change notes, and hero data. |

The pinned engine revision and archive hash are in [UPSTREAM.json](../UPSTREAM.json). Third-party attribution is in [THIRD_PARTY.md](../THIRD_PARTY.md).

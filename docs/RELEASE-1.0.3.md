# StarDroid 1.0.3

Android version code 73 · Android 8.0+ · ARM64 and x86-64

## Menu import correction

The supplied screenshots show a missing interface bundle, substitute text, and the neutral moon background in the campaign screen. The additional warning identifies `glue/palcs/backgnd.pcx` as missing or unreadable. Complete maps, music and movies do not prove the interface bundle imported successfully.

The importer previously rejected every interface entry larger than 262,144 bytes, including its decoded size. A valid uncompressed 640 × 480 background is 308,097 bytes. Rejecting that one image aborts the interface export, so its font files are not installed either. This reproduces one way to get the reported combination; the affected tester's actual archive has not been supplied.

The normal **Import game files** flow now accepts interface entries up to 1 MiB, retaining the 4 MiB total payload limit, bounded metadata and original filename allowlist. Both `files/font/` and `font/` locations are supported. New imports and replacements use the same corrected path. Failed imports preserve the existing bundle, and a font-only import cannot replace a bundle containing campaign artwork.

Fallback system text uses proportional spacing, so it no longer wraps short campaign labels as widely. Missing original fonts now produce a recorded warning. The fallback background remains available if the original asset truly is absent.

## Diagnostic report

**App Options → Diagnostic report** is available whether or not a menu error has been recorded. The main menu's former credits button is explicitly labeled **Diagnostics**. The report can be copied, shared through Android's chooser, or saved as a `.txt` file.

It contains the app/device version, archive sizes and SHA-256 fingerprints, interface entry sizes, selected font and asset sources, requested and loaded palettes, rejected/missing assets, the latest import result, and existing crash information. Import outcomes and the latest menu snapshot persist across restarts. Hashing runs on the I/O worker. Game payloads are not included or sent automatically.

## Installation and recovery

1. Install **StarDroid-1.0.3.apk over the existing app** without uninstalling or clearing app data. The application ID and original release signing identity are unchanged.
2. In **App Options → Import game files**, select the full classic **StarCraft.mpq** or original StarCraft **Install.exe** again. StarCraft.mpq and StarDat.mpq are different files. The corrected interface import runs automatically, alongside the normal content import.
3. Let the import finish, then choose **Return to game menu** and reopen the campaign screen.
4. If it still looks wrong, return to **App Options → Diagnostic report** and copy, share or save the report. Include the latest import result and menu snapshot.

The update cannot recreate artwork absent from the selected archive. A version mismatch has not been established. The new fingerprints allow comparing the tester's archives with a known working installation.

## Validation

- Reproduced the old 1.0.2 importer rejecting a valid 308,097-byte PCX.
- Production `GameContent.install` tested on synthetic MPQs: 31 base campaign maps, fresh interface import, replacement from an executable with an embedded MPQ, both font path conventions, oversize rejection, existing-content preservation and exact fingerprint output.
- Imported bundle reconstructed through `NativeData`, decoded with the native archive reader, then loaded by actual `NativeArt` and `NativeGlue`. Both campaign menus selected the imported background and all five menu fonts with no recovery warning.
- 33 menu asset checks and 13 fallback labels/actions pass, using real external core archives and fault injection. Host Canvas renders inspected; animated Smacker layers are not rendered by this shim.
- Release assembly and lint pass: 0 errors, 10 existing warnings. APK signature and 16 KiB ZIP alignment verified. All 76 native-library and bundled-asset entries are unchanged from 1.0.2.
- No physical Android device or emulator installation/interaction test was performed. The tester's actual archive and the new diagnostic report remain unavailable.

No GitHub release was published by this update. Game assets and signing secrets are not included in the source archive.

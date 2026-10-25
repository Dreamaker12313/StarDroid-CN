# StarDroid 1.0.2

Android version code 72 · Android 8.0+ · ARM64 and x86-64

## Fix

If original menu artwork could not load, version 1.0.1 discarded the entire menu theme. Every button without an explicit replacement label then read “Continue.” Seven such buttons identify the campaign selection screen.

The “Original interface” check only showed that an imported bundle existed. Its validation required eight font entries but did not require the campaign background and text palette. Successfully importing all maps and movies did not prove the menus would load.

Version 1.0.2:

- Tries usable copies from the other installed archives when an image, dialog or font in a higher-priority archive cannot be decoded.
- Retains the campaign layout and actions with the standard original menu theme if its campaign palette is missing or unreadable.
- Gives the last-resort menu real action names and direct access to App Options and Diagnostics.
- Keeps player-ID selection and dialogs usable without menu artwork; other unavailable setup screens show recovery steps instead of a blank screen.
- Supports uncompressed 8-bit PCX images and rejects malformed dialog pointers safely.
- Records the failed asset paths, avoids treating a bundle's presence as complete menu validation, and warns when a new interface import lacks campaign palette entries.
- Skips an unreadable optional title image and clears cached dialog layouts after re-importing.

## Install and recover

Install the accompanying **StarDroid-1.0.2.apk over the existing app**. Do not uninstall or clear app data. The supplied APK retains the project's original signing certificate and application ID. Imports, saves and preferences remain in place.

First try opening the campaign menu after updating. If the original campaign theme is still unavailable, open **App Options → Import game files** and re-import the complete classic **StarCraft.mpq** or original **StarCraft Install.exe**. This is different from StarDat.mpq. Fonts, campaign artwork, maps and movies can be separate entries in an archive.

If core menu files are also missing, re-import **StarDat.mpq, BrooDat.mpq and Patch_rt.mpq from the same classic installation**, then choose **Return to game menu**. If the warning remains, open **Diagnostics → Copy** and include the report with the bug report. Renaming a file cannot supply missing internal assets.

On version 1.0.1, Android Back can return to App Options. Re-importing a complete campaign archive can fix absent campaign artwork; it cannot fix the fallback-label bug in the old app. The seven old campaign buttons, top to bottom, are Protoss, Terran, Zerg, Back, Load Game, Play Replay and Custom Game.

## Validation and limits

The host regression reproduces the 1.0.1 failure with real core archives and exercises recovery with missing palettes, damaged higher-priority entries, decoder exceptions and malformed data. It checks fallback labels/actions and renders the actual NativeArt/NativeGlue classes through an AWT Canvas shim.

Release assembly, Android lint, signature verification and ZIP alignment are checked. Native libraries and bundled assets remain byte-identical to 1.0.1. This is a Java menu/import update, with no simulation or multiplayer protocol changes.

The affected person's actual archives and diagnostics were not supplied. Their precise failed entry is therefore not proven. Physical-device installation and interaction remain untested for this update. Missing artwork cannot be reconstructed from absent game data; the readable fallback remains available.

No GitHub release was published by this repair.

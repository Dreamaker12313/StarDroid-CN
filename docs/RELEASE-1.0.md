# StarDroid 1.0

An Android adaptation of classic StarCraft and Brood War, put together by **ToadWarrior**.

## Download and install

Download **[StarDroid-1.0.apk](https://github.com/kinopiowarrior/StarDroid/raw/refs/heads/main/distribution/StarDroid-1.0.apk)**. The [source archive](https://github.com/kinopiowarrior/StarDroid/archive/refs/heads/main.zip) is available separately. It supports Android 8.0+ on ARM64 and x86-64. Install over an existing matching installation without uninstalling to keep its imported content, profiles, settings, and saves.

The APK contains the engine and Android app, **not the original game data**. Import your own `StarDat.mpq`, `BrooDat.mpq`, and `Patch_rt.mpq`. Import the original `StarCraft.mpq` and `BroodWar.mpq` installation-media archives for campaign and movie content. See the [installation and controls guide](https://github.com/kinopiowarrior/StarDroid#install) for the complete setup steps and touch gestures.

Join the [StarDroid Discord community](https://discord.gg/F2FnjUrtQ) for help, feedback, and player discussion.

## Included

- StarCraft and Brood War campaigns, briefings, and imported media.
- Touch selection, camera panning, pinch zoom, optional control groups, and placement confirmation.
- Custom Melee, Free for All, and Teams matches with computer opponents.
- Bluetooth local multiplayer with optional Wi-Fi Direct, configurable lobbies, chat, map transfer, and a start countdown.
- Optional Hero Mode: six buildable hero forms per race, available to humans and computers.
- Single-player and host-managed multiplayer saves.
- Importable maps, map thumbnails, and scrollable map lists.
- Next-level upgrade icons remain visible while locked, with the required technology shown.

## Release details

- Display version: **1.0**
- Android version code: **70**
- Package: `org.openbw.androidtest` (retained for update compatibility)
- APK SHA-256: `592b57427b6f91cc4e80add4f08d92c34f1af90130564f0740401106f0218e58`

Use this same release APK on every multiplayer device. The signing key is not included in the source; independently signed builds cannot update this APK in place.

Automated regression checks passed for the recorded build. Broader physical-device testing is still needed for installation, touch/audio behavior, radio interoperability, and complete campaign playthroughs. Replay loading/export, internet matchmaking, host migration, and mid-match reconnect are not supported player features.

Build 70 starts scrolling sooner near the top, left and right edges. It adds
**Camera settings → Scroll while placing**, enabled by default and saved between
sessions. Smooth, time-based scrolling remains available in every direction. While
placing a building, drag beneath the command bar to scroll down; release to
stop before confirming. The preview stays visible and underlying controls do
not receive the drag. Small ordinary and two-finger pans retain fractional
movement, avoiding uneven rounding in opposite directions.

This includes the build 68 fix for the native crash when a building-placement outline reaches the
bottom edge of the image, plus the same buffer overrun in selection-box drawing.
The corrected renderers pass guarded-buffer and AddressSanitizer checks,
including the new moving-camera path. Both native libraries and all assets match build 69 byte for byte, retaining
the tested renderer fix. Simulation rules and the multiplayer protocol are unchanged.

**Credits → Copy** retains native crash stacks from Android 12+ when available.
An older retained crash can still appear after installing this update; check its
timestamp. Post-fix device play still needs confirmation, and the separate Vivo
closure is not yet diagnosed.

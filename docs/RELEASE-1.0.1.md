# StarDroid 1.0.1

**Android version code 71 · Android 8.0+ · ARM64 and x86-64**

## Change

**Minimap hold issues orders is now off by default.** Fresh settings, missing saved settings, and control presets use the new default. Minimap taps and drags still move the camera. You can enable hold-to-order under **Menu → Options → Touch Controls → Camera settings**.

Existing saved choices are preserved when updating. If you previously had this option enabled, turn it off in Camera settings to use the new default on that installation.

This update changes the default and app version only; the engine, native libraries, game assets, and other control defaults are unchanged.

## Install

Download **StarDroid-1.0.1.apk** from the [release assets](https://github.com/kinopiowarrior/StarDroid/releases/tag/v1.0.1) and install it over version 1.0 **without uninstalling**. The APK uses the same application ID and signing identity so imported game files, saves, and settings are preserved.

Game data is not included. New players should follow the [installation guide](../README.md#install). The source ZIP is for development. Release assets include **SHA256SUMS.txt** for download verification.

## Validation

Release assembly and lint passed (0 errors, 10 warnings), along with 14 preference checks. The signing identity matches version 1.0, and all 76 native-library and asset entries are unchanged. Physical-device testing was not performed for this update.

[Player guide](PLAYER-GUIDE.md) · [Discord community](https://discord.gg/F2FnjUrtQ)

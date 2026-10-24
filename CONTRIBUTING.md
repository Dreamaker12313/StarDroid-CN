# Contributing to StarDroid

Start with the [build guide](docs/BUILDING.md) and the [validation record](VALIDATION.md).

## Reporting a problem

Open a GitHub issue with:

- Device model, Android version, and the APK release/build. The visible version is 1.0, so an APK checksum is useful when comparing builds.
- Campaign or custom/multiplayer mode; mission/map name; races, difficulty, teams, and Hero Mode setting.
- Steps to reproduce, expected behavior, and what happened instead.
- For multiplayer: which device hosted, number of devices/computers, connection mode, and whether the issue began before or after the match started.
- A screenshot or short recording when it explains the problem, and relevant logs with personal information removed.

Do not attach game MPQs, installation archives, signing keys, or private credentials. Describe where original data came from without uploading it.

## Proposing a change

Keep changes focused and explain what user-visible problem they solve. Run the relevant tests, report which checks ran, and distinguish automated testing from physical-device verification. Preserve imported files, saves, profiles, and touch preferences during upgrades.

Engine changes belong in the patch/preparation workflow, with native libraries rebuilt for both supported ABIs. The generated `native-engine/` directory is not the maintained source. Do not change package IDs, save-format markers, or multiplayer compatibility identifiers solely to rename old internal labels.

Follow the classic interface's fonts, normal/hover colors, and rounded borders. Check text wrapping, touch targets, overlays, and clipping at more than one interface size. New controls should be usable on touch devices without a mouse or keyboard.

This release stays at **version 1.0**. Coordinate internal version-code, protocol, and save-format changes with the maintainer. See [THIRD_PARTY.md](THIRD_PARTY.md) before adding external code or assets.

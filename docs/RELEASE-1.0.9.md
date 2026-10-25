# StarDroid 1.0.9

Android version code **79** · Android **8.0+** · **ARM64 and x86-64**

## Campaign fixes

- **Reign of Fire:** starting buildings with both rescued Drones no longer causes a false defeat. Unfinished buildings now count for this mission's loss check. Actual defeat and victory conditions still work.
- **Pre-placed Nydus canals:** restore the map-defined connections in **Eye for an Eye**, **Vile Disruption**, and **To Chain the Beast**. The same fix supports custom Use Map Settings maps and preserves deliberately unlinked canals.
- **Campaign characters:** use imported map-specific names instead of the underlying unit's default name. Correct Aldaris, DuGalle, and Raszagal portraits where the missions reuse other unit types, including idle and talking portraits. Stukov's dedicated portrait was checked and retained. The Insurgent's original shared vision of Aldaris is preserved.

## Computer abilities

- Computer-controlled casters can use combat abilities in campaigns and custom games even without an active production base. Hero casters are included.
- Covers **Psionic Storm**, EMP, Plague, Stasis, Maelstrom, Ensnare, Disruption Web, Feedback, Lockdown, Irradiate, Yamato, Broodlings, Mind Control and Optical Flare, plus supporting abilities such as Defensive Matrix, Restoration, Dark Swarm, Consume, Stim and Cloak.
- Decisions respect allowed technology, research, energy, visible targets, friendly units, pauses and scripted movement. Pending casts are protected from conflicting attack-wave orders and duplicate targeting.

## Targeting and scrolling

- Previously seen enemy buildings show the **red targeting flash and selection circle beneath their remembered artwork** in explored fog. Unseen units and live health information stay hidden.
- The map list has **brighter original arrows and a small circular scroll handle**. Dragging keeps its grip position through redraws; arrows, track taps and list swipes remain functional.

## Brood War music — all three races

- **Next track now reaches four themes for Terran, Zerg and Protoss.** In the supplied classic archives, the first Brood War music file contains the expansion theme followed by the original StarCraft first theme. Previously, pressing Next skipped that embedded second theme.
- The player now checks the imported audio and can jump to that theme before advancing to tracks 2 and 3. Normal automatic playback remains complete, without duplicating themes.
- Unrecognized or missing reference files safely retain full-file playback. This applies to campaign, custom and nearby multiplayer battle music.

## Install and compatibility

Download **StarDroid-1.0.9.apk** and install it **over the existing app without uninstalling**. The application ID and original signing identity are unchanged, preserving imported content, settings and saves. No game files need re-importing.

- Use **build 79 on every nearby multiplayer device**, with matching game data.
- For missing Nydus connections already stored in an older save, **restart that mission** to load the corrected map links. Saves made before Reign of Fire's false defeat benefit from the corrected loss check; already-defeated saves cannot undo the outcome.
- Original game data is not included. **Diagnostics / credits** remains available; no menu repair button is added.
- **SHA256SUMS.txt** covers the APK and matching source ZIP.

## Validation and developer notes

The final campaign regression suite passed **22 checks**; **42 imported portrait movie variants**, **21 AI abilities**, **122 scrollbar checks**, **1,428 protocol assertions**, and all three races' four-stop music controls passed. APK assembly, both native architectures, the original signing identity, all **41 JNI exports**, unchanged permissions/assets and **16 KiB alignment** were verified. Lint passed with **0 errors and 11 warnings**.

These are controlled host and package checks, not full campaign playthroughs. Physical Android testing remains pending.

The source ZIP matches the release tag. Its retained `native-libs/` prebuilts are from 1.0.8: **rebuild both ABIs with `python3 scripts/build.py`** before packaging this source; do not use `--skip-engine` with those old libraries. The released APK contains the rebuilt 1.0.9 libraries. Build and test records are in `validation/native-build79.json`, `validation/package-v79.json` and the other build 79 reports.

Put together by **ToadWarrior**, using **OpenBW**. [Discord community](https://discord.gg/F2FnjUrtQ)

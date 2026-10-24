# Feedback review and polish — 0.27

This update keeps the classic interface and the native engine. It builds on the
0.26 gameplay corrections and adds Android UI, touch and audio improvements.

| Earlier feedback | Status in this update |
| --- | --- |
| Missing victory sound | Victory/defeat cues have their own channel. Click, transition and score sounds cannot replace them. Battle music stops at the outcome. |
| Build command needs its original “DON” sound | Original building-placement WAV behavior is retained from the tested native engine. |
| Beacons should not play the rescued-unit sound | Silent beacon transfers are retained. |
| Hatchery upgrade / Spire path in Zerg mission 2 | Lair/Spire availability and mission restrictions are retained; Android checks exercise Lair morphing. |
| Eggs should identify what is building | Target icons and production progress remain in the HUD. |
| Show mission-allowed units greyed out until available | Disabled icons remain visible. Missing Zerg prerequisite tooltip labels are filled in, including Spire for Mutalisks. |
| Extractor should show health | The HP and remaining-gas readouts are retained. |
| Chrysalis should not show placeholder armor | Invincible mission-object detail cleanup is retained. |
| Menus should start quickly and settle smoothly | Panels use a 420 ms cubic ease-out entrance and 220 ms exit; menus are independent of the gameplay FPS cap. Mission/profile lists scroll by pixels with short deceleration. |
| Add the remaining missions and Brood War chooser | The existing Original/Brood War chooser and 64-map catalog remain. Campaign completeness limits still apply. |
| Replace Campaign Editor with App Options | Retained; the import/options screen now has a centered layout and clearer content status. |
| Consolidate imports, retain useful setup tools | One game-file import action remains. A collapsible guide opens for new users; installed-content counts and diagnostics remain. No mission-export action is exposed. |
| Improve the blue in-game options UI | Original blue button frames, clearer checkboxes/sliders, selected-track highlighting and pressed command feedback replace flatter controls. |
| General sound polish | Battle-track selection respects briefing/results music; dialogue ducks music smoothly; Android focus loss/backgrounding pauses sound; mute applies immediately. |
| Native app consistency | The APK remains native C++/JNI/SurfaceView/AudioTrack with no WebView, JavaScript or WASM. |

Dialogs also block underlying buttons, and dragging away from a command cancels
its tap. The sound sheet includes Preview sound. Test-victory controls are kept
in Testing Cheats rather than duplicated in ordinary options.

The final validation reports and exact APK/test-APK hashes are in `validation/`.
See `VALIDATION.md` for fresh Android checks and the retained 202-case gameplay
matrix. Earlier browser and native captures were used for visual comparison;
the browser was not rerun for this UI-only pass.

The update uses the existing package and signing key. Installing it over the
previous app preserves imported files. Original game data is not included.

Known limits remain: incomplete campaign AI behavior, one custom computer
opponent, and no save/load, replay loading, multiplayer or complete cinematic
sequencing. Emulator tests do not certify physical-phone sound, performance,
or full campaign playthroughs.

# StarDroid 1.0.12 — build 82

## Replay layout and notifications

- The replay list now uses the imported menu's actual list rectangle. Filenames and the scrollbar stay within the original red window with either the load-menu artwork or the older custom-menu fallback.
- Replay information stays in the original information window. The generic blue panel is removed. Import and Export are side by side, with DELETE beneath them.
- Saving and exporting a replay show an in-game black/red confirmation with OK. Completion notices wait for other dialogs to close and are discarded if their original screen has been left.
- Playback controls use pixel red borders, black backgrounds and the imported fonts. The unrelated desktop slider that appeared as a purple/blue strip is removed.

## Working replay seeking

Tap or drag the timeline to move forward or backward. The engine restores a suitable checkpoint, then simulates to the requested frame. Work is spread across rendered frames; the display shows the current and target times while seeking. Pause, playback speed, viewpoint and camera settings are retained. Intermediate game sounds are silenced so jumping through a battle does not replay a backlog of effects.

The replay file format is unchanged: recordings from build 81 remain supported with matching game data. Checkpoints are kept in memory, with at most eight retained and a 48 MiB limit on their buffer capacity. That is a cache limit, not total process memory. A snapshot or restore handles one whole world; the catch-up loop itself is limited to 128 simulation frames or roughly 6 ms per rendered frame. If checkpoints cannot be kept, backward seeking reloads the original replay and catches up incrementally.

## Pixel controls and campaign transitions

- Menu scrollbars use the requested stepped red triangle arrows, rectangular rail and hollow red circle thumb. Existing larger touch targets, arrows, track taps and dragging remain available.
- Campaign completion marks are green pixel ticks. Existing per-player completion records are retained.
- Campaign characters, race/episode labels and their hit areas appear only after the menu buttons finish sliding in. Their animation starts at that point, including on reentry and when the first decoded movie frame is already cached.

## Updating and validation

Install the signed APK over the existing app without uninstalling. Existing imports, player IDs, completion records, saves and settings are retained. No data reimport is needed for these fixes. Multiplayer protocol 80 and replay format 81 are unchanged; build 82 contains no new simulation rules.

Focused reports are in `validation/*v82.json` and `validation/native-build82.json`. They cover original and fallback menu artwork, all five UI languages, scrolling and touch routing, saved-replay confirmations, campaign transition boundaries, deterministic seeking and native rendering. Physical Android testing remains pending.

The repository retains historical native prebuilts. Rebuild both ABIs before packaging; the supplied APK contains freshly rebuilt engines.

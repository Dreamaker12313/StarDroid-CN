# StarDroid 1.0.11 — build 81

## Replays

- **Load Replay** opens a local replay list using the original load-menu artwork, with map/player information and the original **DELETE** button. Deletion asks for confirmation. Import and export support sharing compatible `.rep` files.
- **Save Replay** on the results screen keeps a recording from a newly started custom or nearby match. Playback includes pause, 1×–8× speed, player viewpoints and restart. Playback cannot issue orders, use cheats, or create game saves.
- StarDroid recordings preserve AI difficulty, player setup, teams, Hero Mode and base-defence settings. They require the same engine build and game data, including human-only recordings. Cheats, restoring a game save, or changing AI defence behaviour during a match disable its replay recording.
- Classic human-only Melee/Free-for-All files are accepted. Original-executable parity is not verified. Campaign recordings, old computer recordings without StarDroid settings, Remastered extensions and other game types are unsupported and receive an explanation.
- Original replay-menu assets are included automatically on new game-data imports. Older imports use the existing menu fallback until the original CD archive is imported again. No additional game data is bundled.

## Controls and supply

- **Touch Controls** is now **Controls**. Gamepad settings use the game's panels, buttons and sliders, including when opened from App Options. Opening or closing settings retains the active game.
- All twelve controller bindings, pointer/camera speed, dead zone, stick swapping, help and reset remain available. Held input is cleared when navigating or changing bindings.
- Control groups are 20% larger before applying **Commands & control groups** scaling. The new 100% equals the former 120%; the new 120% equals the former 144%. Touch targets and wrapping scale with the buttons.
- **Unlimited supply (200)** is a single-player cheat under **Options → Miscellaneous → Cheats**. It provides supply up to the normal 200 cap, including simultaneous larva morphs and paired units. Costs, technology and production times still apply. It affects only the local player, resets on a new game or loaded save, and leaves actual supply-building totals intact.

## Add-on construction sound

All six Terran add-ons now play the original SCV construction-placement cue when the local player's build order is accepted. Opening or cancelling placement, blocked sites, insufficient resources, repeated pending requests, AI orders and replay viewing do not play the acknowledgement. The cue is shared by touch, keyboard and gamepad commands; production rules and costs are unchanged.

## Campaign progress and mission selection

- Victories add a green circled check next to completed missions for the Player ID that started them. Each ID has its own persistent progress. Saves retain that owner when loaded or continued.
- Recreating a deleted ID starts fresh. Defeats, cinematics, custom games, multiplayer and replays do not award campaign completion. Earlier builds did not record completion history, so past victories cannot be reconstructed automatically.
- The mission scrollbar is wider, with larger arrows and draggable grip. OK and Cancel are wider, and long mission names leave room for completion marks.

## Updating

Install the signed APK over the existing app without uninstalling to preserve imports, saves, IDs and preferences. Normal in-game saving and loading remain available. Save-file import/export is not included. **Diagnostics / credits** remains available.

The source repository retains historical native prebuilts. Build both ABIs from the current sources before packaging; do not use `--skip-engine` with those old binaries.

## Revolution and campaign AI audit

Revolution intentionally keeps its main Confederate AI inactive until a mission trigger fires. The original triggers activate it when the Confederate buildings near the Antigan base are cleared, or when the player's aircraft enters a designated lower-map region. Ground troops entering that region do not activate it. Its first attack also has a scripted delay, and much of the requested base is already pre-placed.

A regression follows the original Kerrigan rescue and Antigan handover, then sends the rescued Wraith through the aircraft trigger. The Confederate AI activates, gathers and spends resources, builds add-ons, trains units, and attacks. The original mission timing is preserved. Startup checks also cover all 64 campaign maps; these are bounded script-startup tests, not complete playthroughs. See [campaign AI audit](CAMPAIGN-AI-81.md).

## Validation

The native replay tests compare the complete saved simulation and AI state across 12 scenarios, each 2,200 frames, with real movement/production commands and periodic rendering. They cover all races and difficulties, teams, Hero Mode, a nonzero multiplayer slot and human-only classic replay data. Malformed command, map, string-table and footer tests reject bad files before playback. Classic-format fixtures were produced by the integrated recorder; they are not a comparison with Blizzard's executable.

Focused checks passed: 95 add-on audio checks, five supply regression groups, 4,184 controls checks, 131 campaign-progress/mission-menu checks, 132 replay UI checks, 40 replay-storage checks and six original replay-asset comparisons. The campaign audit resolves 609 original AI-start actions and runs all 64 maps through their startup window. Both native architectures were rebuilt from the recorded source inputs.

Reports are stored under `validation/*v81.json` and `validation/native-build81.json`. Physical Android/controller testing and full campaign playthroughs remain pending. The signed-package check records the final APK, original signing certificate, JNI exports, 16 KiB alignment, translations and lint result.

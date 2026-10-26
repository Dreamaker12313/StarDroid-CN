# StarDroid 1.1 — build 83

- A replay made with different app rules now reports: “The selected replay was recorded with a different version of the app.” The message is translated in all five UI languages.
- Hero Mode completion sounds use the hero's race-specific campaign rescue cue. This includes all 18 trainable heroes and the merged Tassadar/Zeratul Archon. Duke's siege changes do not replay the spawn cue; normal unit and campaign sounds remain unchanged.
- Sound Settings retains mute, music enable, effects volume and music volume. The track picker, Next track and sound preview controls are removed; old manual track choices no longer override automatic playback.
- Verified the four-theme Brood War loop for Terran, Zerg and Protoss using the supplied classic archives. Each expansion `race1.wav` contains the Brood War theme followed by the original first theme, then `race2.wav` and `race3.wav` complete the loop. Campaigns, custom games and nearby matches share automatic playback. Missing expansion imports fall back to the original soundtrack.

This sound/menu revision keeps version **1.1 / code 83** and simulation compatibility **84**. It does not introduce another replay or multiplayer compatibility break.

Earlier fixes in this revision:

- Minerals, neutral geysers and originally protected campaign objects keep their DAT protection during map initialization. Explicit mission invincibility triggers still work; refineries and destructible objectives remain attackable.
- Dylarian Shipyards' bunker command uses the complete trigger region. Shared AI maintains eligible nearby garrisons without taking troops from human orders, scripted movements, attack waves or transports.
- Active computer towns stock nuclear silos through normal paid production. Computer silos finish and link their missiles correctly, and stored missiles follow their silo when ownership changes. This fixes the missing stock behind Dylarian Shipyards' four-nuke reward; ordinary supply, training time and mission restrictions still apply.
- Tapping a visible beacon with owned movable units selected issues a ground move to its center and retains the selection. Selection-only gestures, explicit spell targeting and replay inspection keep their existing behavior.
- Single-unit, group and cargo wireframes use the imported original color remap. Zerg damage and Protoss shield strength have separate color bands, and the display refreshes when those bands change. Mechanical-part damage ordering and exact transition thresholds remain a deterministic approximation of the classic renderer.
- Campaign results use original faction names. The local Player ID is retained, with its faction beneath; nearby players retain their participant names.
- App Options can move imported data to a detected removable SD card. Transfers verify copies before switching and deleting originals, keep saves/replays/settings internal, and block concurrent imports or gameplay. Missing cards are reported without switching folders.
- Original Reign of Fire triggers explicitly use the Terran rescue sound for normal Zerglings and Drones. This authored difference remains; generic rescues use the rescued unit's race, including Protoss.

Version name **1.1** and Android version code **83** are unchanged. Install over the previous 1.1 APK without uninstalling or reimporting data. Restart affected missions: an older save can retain incorrect resource flags or already-transferred empty silos.

The simulation compatibility identifier is now **84**. Both nearby multiplayer devices must install this revised APK. Earlier StarDroid recordings require the APK that recorded them; their replay files are not deleted. This prevents silent replay divergence or multiplayer desynchronization despite the unchanged public version.

Validation uses the supplied original archives, host simulation and Java rendering/filesystem tests. Physical Android, removable-card hardware and full campaign playthroughs remain unverified. See the campaign11, wireframes11, bunker-ai11, beacon, map-invincibility11, rescue-sound, score-names11 and data-storage11 reports under `validation/`.

Earlier 1.1 interface improvements remain included:

- Replay selection buttons use the same imported font palette and normal/hover/disabled states as other menus.
- Replay selection plays the original slide-in, lock and slide-out cues. Starting a replay waits for the exit transition.
- Selected replays display their embedded map thumbnail above match details. No separate map import is required. The preview keeps the map aspect ratio and fits the original and legacy replay windows. Missing preview assets do not prevent playback.
- The launcher icon is slightly smaller and lower, centered with clear edge padding in normal and monochrome launchers.

All 1.0.12 replay features remain included.

# StarDroid 1.1 — build 83

- Menu text buttons show highlighted shortcut letters, including in-game menus. Original keys take priority; buttons use a visible **[key]** suffix when the shortcut cannot be highlighted in their caption. App Options and the battlefield MENU button retain their normal labels.
- The minimap terrain button has a hover/touch-hold description and shows its **Tab** shortcut. Tooltip borders match the player's race: blue for Terran, red for Zerg and yellow for Protoss.
- Mouse and keyboard help uses bold **Mouse:** and **Keyboard:** headings, with a blank line between the sections.

- Added mouse and keyboard controls: selection boxes, context-sensitive right-click orders, queued orders, camera movement, wheel zoom/list scrolling, original or QWE/ASD/ZXC grid hotkeys and control groups. Command tooltips show the active key in brackets, with the key highlighted. Mouse and keyboard settings keep their help together in one screen. Mouse/keyboard and gamepad settings are available from the in-game Controls menu. Touch controls remain available.

- Corrected the original Shield Battery **Recharge Shields** hotkey to **R**.

- Hover and touch-hold descriptions stay visible while a command error or target prompt is shown. The description sits above the message with a gap, including enlarged interfaces and widescreen.
- Removed **Play original music**. Music volume **0** turns music off; **Mute all sound**, separate Effects/Music sliders and **Next track** remain. An old disabled-music setting migrates to volume 0 once, so updating does not unexpectedly turn music on.

- Campaign results show actual player slots and omit neutral/rescue-only map helpers. The starting roster remains stable after capture, defeat and save/load; zero-score participants and separate opponents sharing a faction name remain visible. All 64 campaign maps were audited.
- Long faction and player names use the largest original font that fits the name column, keeping the complete name clear of the score bars.
- Replay buttons are transparent and use the original wide menu font, size and colors. Import and Export remain side by side; **Delete** is centered at the bottom of the left panel. Original OK/Cancel artwork and placement are retained.

- A replay made with different app rules now reports: “The selected replay was recorded with a different version of the app.” The message is translated in all five UI languages.
- Hero Mode completion sounds use the hero's race-specific campaign rescue cue. This includes all 18 trainable heroes and the merged Tassadar/Zeratul Archon. Duke's siege changes do not replay the spawn cue; normal unit and campaign sounds remain unchanged.
- Sound Settings retains mute, effects volume and music volume. **Next track** advances the current in-game soundtrack, including the second theme embedded in each race’s first Brood War music file. Long-track seeking also fixes an integer overflow that previously jumped to the wrong position. The manual track picker and sound preview remain removed; old manual track choices no longer override automatic playback.
- Verified the four-theme Brood War loop for Terran, Zerg and Protoss using the supplied classic archives. Each expansion `race1.wav` contains the Brood War theme followed by the original first theme, then `race2.wav` and `race3.wav` complete the loop. Campaigns, custom games and nearby matches share automatic playback. Missing expansion imports fall back to the original soundtrack.

This revision keeps version **1.1 / code 83** and simulation compatibility **84**. It does not introduce another replay or multiplayer compatibility break.

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

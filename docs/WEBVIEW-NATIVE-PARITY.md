# WebView 0.22 → native regression review

This review uses the retained, unchanged 0.22 browser assets and the player's
private imported game files. The reference runs in Chromium with touch events;
the candidate runs in the Android 9 x86_64 emulator. Neither substitutes for
performance or speaker/audio-sync testing on the user's ARM phone.

The checklist combines the visible chat, recovered earlier OpenBW requests,
and the previous releases' actual regression tests. Unrelated game-project
preferences returned by history search were excluded.

| Requested behavior | Review area |
| --- | --- |
| Classic artwork, fonts, 640×480 proportions | Title, Registry, campaign history, custom setup, briefing, HUD, pause/results |
| Original/Expansion chooser, all missions | Both campaign menus, imported 64-map catalog, hidden next-scenario variants |
| App Options and one import entry point | Core files, both CD archives, legacy ZIPs, status/errors; no obsolete mission export UI |
| Fast start and smooth stopping menus | 560 ms entry, 320 ms exit, attached labels, stationary campaign figures |
| Briefing speech, scrolling, portraits | Original voice length, recording-based scroll lead, manual drag, active-speaker border, Replay/Start |
| Portrait idle weighting and monitor rim | Original portdata weights, talking animation, black background, rim compositing |
| Quick drag / hold-drag / military tap | Pan, box selection, attack-move, friendly selection, workers' contextual orders |
| Two-finger movement, zoom and widescreen | Pinch + pan, zoom floor, fixed HUD scale, group spacing, minimap |
| Building preview and larger Cancel | Preview 48 screen pixels above finger, explicit Build, invalid site disabled, no accidental orders |
| Production information | Egg target, queue icons/ordinals/cancel, no worker walking queue or group Egg queue |
| Zerg 2 tech | Lair/Spire path, locked mission-allowed units grey, forbidden units absent |
| Health/status | Extractor HP + gas; invincible Chrysalis no HP/armor; shield/HP colors, Detector/supply fields |
| Upgrade/command details | Original icon palette, Reaver Scarabs and ammo, stable Forge slots, Pylon aura |
| Sound | Victory/defeat cue, race building thump, ready/rescue distinction, silent beacons |
| Original pause/options aesthetic | Original menu geometry, Help/end navigation, compact blue settings, direct Test Victory |
| Sound/speed/video/testing options | Mute, music enable/track/next, 1×–16× speed, zoom presets, order lines, defeat/reset cheats |
| Results | Compact victory dialog, original score tabs, profile name, replay gating |
| Lifecycle | Pause/input cancellation, resume without catch-up, stored preferences, Back navigation |

## Observed native 0.24 regressions

The running reference and source comparison exposed omitted Registry/history
and custom-setup flows; simplified pause-menu geometry; lost music controls,
speed presets, order lines and defeat/reset controls; missing exit transitions;
campaign figures moving with the panels; targeting drags becoming camera drags;
pinch without midpoint panning; stale gestures on pause; fixed-size command
hints; an oversized victory dialog; incorrect campaign caption alignment and
animation layering; and group wireframes that could not select a unit. These are adapter regressions, not new
gameplay features.

Current verification results and remaining limitations are recorded in
`VALIDATION.md` and the JSON reports under `validation/`. Screenshots and game
files remain private test fixtures and are excluded from the distributable.

## Presentation differences corrected in 0.25

The screenshot review found that multiline captions used a single-line height,
the Zerg caption ignored bottom alignment, and title/campaign animation chains
used the briefing layer order. All three now follow the corresponding browser
layout rules. Disabled pause-menu labels also remove embedded highlight colors.

The native briefing now uses the audio playback position and never shortens a
recording to a smaller CHK timer. Timed text expires, transmission text clears
between speakers, scrolling uses the browser's lead-in, and the original masked
portrait borders and active-speaker frames are composited above the portrait.

Group selection now uses a separate bitmap per unit, original hero/status
borders, and working taps to select one unit. Custom imports retain the setup
screen on failure and wait for an explicit start. The native bot remains limited
to one computer opponent; the setup makes this limit visible and also permits
closed slots and practice games. This is a documented remaining difference from
the browser's multiple independent bot workers.

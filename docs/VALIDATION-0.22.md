# OpenBW Android 0.22 validation

Original game files are external test fixtures. None are included in the APK or
source ZIP. These tests run the real WASM in desktop Chromium with touch
emulation; no physical Android device was available.

Current evidence:

- `campaign-v22-all.json`: all 64 original/expansion map files import, open their
  briefing, start the simulation, and advance 2,400 frames without a JavaScript
  or campaign AI interpreter error. Player units are periodically healed. Brood
  War Zerg 1's seven rescue Hives are also protected during this unattended test;
  otherwise its original Hive-loss condition correctly causes defeat. This is
  not a complete playthrough or an AI balance test.
- The same report exercises Zerg 2: Lair morph completes, Mutalisk remains visible
  but disabled without a Spire, an Egg displays its target icon, the Chrysalis
  has no armor panel, an Extractor completes and displays HP plus remaining gas,
  and a beacon changes owner without a rescue cue.
- Actual WebAudio buffer fingerprints match the imported original
  `ZBldgPlc.wav` at placement and `youwin.wav` at the victory message.
- The Original/Expansion chooser opens the correct original expansion artwork
  and mission lists. Sound settings and the Egg/refinery status panels were
  visually inspected with original art and fonts.
- `menu-motion-v22.json`: live registry/campaign transitions produce smooth
  frame-to-frame movement with attached text, fast initial movement and easing
  at the end; entry is 560 ms and exit is 320 ms.
- `content-import-v22.json`: the actual Java combined importer identifies both
  CD archives and passes every map through the app's bundle validator: 31 base
  and 33 expansion map files, with music and mission openings. Existing core
  MPQs and older mission ZIPs remain accepted through the consolidated picker.
- `campaign-branches-v22.json`: original T4 Physics Lab/Nuclear Silo objectives
  select the two T5 variants; Z3 Exact(0) infestation selects Z4a; the P6 ground
  location completes the Khalis objective; T7's zero-count legacy create record
  creates Duran. Controlled movement, resources, healing and kills accelerate
  the original triggers rather than replacing their objective scripts.
- `bot-v22.json`: rebuilt skirmish bot advances 600 lockstep ticks with active
  worker gathering and supply tracking.
- `campaign-v22-building-moves.json`: the final structure-placement change was
  checked again on all four catalog maps containing building-capable Move Unit
  actions (P5, T4, T5a, T6 in Brood War).
- `source-patch-v22.json`: the release patch applies to the pinned clean source
  archive; all twelve changed/new engine source files match the compiled tree.
- `apk-v22.json`: version 0.22 / code 23 retains the update certificate; APK v2/v3
  signatures, alignment, ZIP CRC and every packaged asset are verified.

Campaign AI has broader original-bytecode coverage, but still uses one production
manager per owner. Multi-town tactics, coordinated transports, spellcasting and
leaderboards are incomplete. All campaign files being launchable does not imply
all missions have been played through normally. Save/load, full cinematic
sequencing and multiplayer remain unfinished. Phone audio, import memory use,
and sustained frame rate need on-device testing.

# Earlier: OpenBW Android 0.21 validation

Tests use real engine WASM and external original MPQ/CD fixtures in desktop
Chromium. Physical Android testing is pending. Private game files, screenshots
and recordings are excluded from the APK and source release.

Current release:

- `polish-v21.json`: live Protoss 2, Terran 5 and Terran 1 engine checks.
  Aldaris continues through the old 12.08-second cutoff to his actual 13.08-second
  ending. The five Raynor/Kerrigan banter events advance with one recording-length
  wait (5.352, 3.430, 2.092, 6.501 and 1.345 seconds), including short replies.
- Actual Probe placement creates a Forge; a fingerprint of the original
  `PPrYes03.wav` confirms the command acknowledgement reached WebAudio. Forge
  armor/shield slots remain 1/2 after the weapon option disappears. Terran 1 hides
  its empty Advanced Build submenu.
- Reaver single/group cards contain one Scarab button at slot 6; production
  increases its displayed ammunition count. Probe status uses armor, shield,
  weapon order. Native icon sizes are retained in the widened, spaced layout.
- Pylon selection changes terrain pixels in all four quadrants. The initial
  image check caught unsigned iscript overlay offsets; signed decoding restored
  the original elliptical field. Original translucency/GRPs are used. Screenshots
  of the field, command cards, group/status layout, Protoss briefing, pause menu,
  victory message and score page were inspected.
- `menu-motion-v21.json`: real registry/campaign navigation sampled per animation
  frame. Entry takes about 900 ms with discrete steps; exit plus entry takes
  about 1600 ms. Labels share their artwork's animated parent.
- `placement-v21.json`: actual touch placement/cancel/confirm creates exactly one
  Supply Depot at 67% zoom in widescreen; command/minimap/portrait sizes remain
  unchanged and video options restore correctly.
- `bot-v21.json`: final rebuilt bot advances 600 lockstep ticks with active worker
  gathering and supply tracking.
- `source-patch-v21.json`: all eleven modified engine files match a clean pinned
  source archive after applying the release patch.
- `apk-v21.json`: signed version 0.21/code 22, retained certificate, alignment,
  ZIP CRC and byte-for-byte packaged asset verification.

The native tests use controlled selection, instant production, diagnostic healing
and accelerated ticks to reach the cases; these are not full normal-speed mission
playthroughs. Original dialog/font data drives the menus, but wide spacing,
transition cadence and the Protoss glow compositing are adaptations that still
need comparison on the phone. No physical Android test was performed here.

Previous 0.20 evidence:

- `mobile-v20.json`: real T1/P2/Z2 WASM engines with original data. Hive/upgrade
  positive and negative checks; Metabolic Boost foreground colors match Blizzard's
  original GIF (83 gold pixels and 73 dark-brown pixels); workers hide internal
  building queues; a Larva morphs to Hydralisk with the same ID and its original
  ready WAV reaches WebAudio. Sound verification lets scripted selection voices
  finish first, avoiding contention caused by accelerated fixture setup.
- All three consoles retain HUD dimensions in widescreen; 50% zoom doubles the
  engine render surface, and turning it off restores 100%. Options survive a
  restart while the briefing remains 4:3. Captures of all race extensions were
  inspected. Widescreen is an adaptation of the original console artwork.
- Actual touch events verify drag-to-pan without selection, hold-drag group
  selection without panning, non-worker attack-move taps, friendly-unit selection,
  worker contextual mode and cancellation when the menu opens. Two-finger pinch
  respects the zoom-out floor; minimap input works after zooming. Building preview,
  cancellation and confirmation complete one depot at 67% zoom in widescreen.
- The earlier `console_v19.cjs` integration was rerun against the new engine:
  production queues, cancellation, group Egg icons, shield/HP colors, portrait
  layering and Zerg 2's four-worker AI quota still pass (`console-v19.json`).
- `bot-v20.json`: rebuilt bot engine loads and advances 600 lockstep ticks.
- `source-patch-v20.json`: all eleven engine source files match after applying
  the patch to a clean copy of the pinned archive.
- `apk-v20.json`: version 0.20/code 21, retained signing certificate, ZIP CRC
  and byte-for-byte packaged asset verification.

Desktop Chromium touch emulation is not an Android device test. Please test
pinch/hold timing, audio and frame rate on the phone, especially at 50% zoom.

Previous 0.19 evidence:

- `console-v19.json`: live T1/P2/Z2 engines; five-item production queues, queued
  and current-item touch cancellation, original dialog rectangles and numeric
  sprites, cyan shield pixels, exact HP threshold crossings, rescued Hunter
  Killer/Drone frame distinction, selected Larva-to-Egg redraw, group suppression
  and single-Egg Mutating progress. No browser errors. Image hashes are recorded
  rather than proprietary pixels.
- `portrait-compositing-v19.json`: all original monitor-rim pixels within the
  portrait rectangle match in screenshots at 2×: Terran 789/789, Zerg 618/618,
  Protoss 890/890. More than 1,600 portrait pixels are visible through each
  opening, ruling out an opaque console hiding the movie.
- Zerg 2 after roughly 6,800 accelerated frames has the script-requested four
  Probes, active gas/mineral orders, increasing gathered resources and no AI
  interpreter error. This verifies the small quota, not exact retail gas-worker
  allocation or a full normal-speed playthrough.
- `bot-v19.json`: rebuilt bot runs 600 lockstep ticks and gathers resources.
- `source-patch-v19.json`: patch applies to the clean pinned archive; all eleven
  engine files match the compiled working source.
- `apk-v19.json`: signed version 0.19/code 20, retained update certificate, ZIP
  CRC and packaged-asset byte comparison. Physical Android testing remains for
  the user; desktop touch emulation is not an on-device test.

Earlier feature evidence (not all rerun for 0.19):

- `portrait-scheduler-v18.json`: 1,000 simulated animation decisions verify
  original 85/5/5/5 weights, zero-weight exclusion, pause/resume and empty state.
- `feedback-v18.json`: actual SCV SMK normal idle repeats with original
  87/5/5/3 weights. Raynor and whole-base rescues produce yellow circle pixels,
  blink to green and expire. The direct victory shortcut opens the original
  message/results and disables replay export after the cheat.
- `mission-import-v18.json`: original T5/Z2/P2 archive export/install/local
  serving; all nine opening texts/art; bounded-memory and invalid replacement
  checks. The two unused missing WAV strings are omitted from import lists;
  all active briefing and mission voice references are present.
- `campaign-next-v18.json`: original objectives and defeat triggers for Terran
  5, Zerg 2 and Protoss 2. Covers Kerrigan/base rescue, Confederate AI activation,
  Chrysalis pickup by normal right-click approach, drop on carrier death,
  recovery/delivery, timed Fenix
  reinforcements and the Cerebrate objective. Controlled warps, diagnostic
  healing and kills accelerate testing; this does not replace full playthroughs.
- `bot-v18.json`: final bot build advances 600 lockstep ticks, gathers resources
  and preserves unit-detail/touch exports after shared engine changes.
- `source-patch-v18.json`: complete patch applies to the pinned clean source and
  matches the compiled source files.
- `build-v18.json`: version 0.18/code 19, original signing certificate,
  v2/v3 signatures, ZIP alignment/CRC, packaged assets and seven WASM hashes.

The carried Chrysalis is visually inspected with the original assets. Rescue
blink cadence is reconstructed; idle probabilities come directly from the
original data. New campaign AI retains the existing shared production manager
per owner. Manual powerup dropping, save/load, later missions and complete
cinematic sequencing remain unfinished.

## Earlier: 0.17 validation

- `results-hud-v17.json`: all six race/outcome message and score screens, four
  tabs, original art/fonts and playing outcome music. Custom setup rejects a bad
  map, parses a valid local map, and waits for OK. Real HP changes exercise
  green/yellow/red numbers; status icons retain gray artwork and blue frames.
  Empty/resource portraits have no world-sprite fallback. Zerg 1 exercises the
  128px minimap, Overlord Detector and four live Control fields.
- `touch-building-v17.json`: actual emulated touch drag/release keeps the build
  preview 48 physical pixels above the finger and spends nothing. Cancel is
  free. Explicit Build completes exactly one depot for 100 minerals.
- `bot-v17.json`: newly built bot advances 600 live lockstep ticks, gathers with
  Zerg workers and reports supply; detail and touch exports remain available.
- `interface-v17.json`: Java export/install/local-serving checks for the eight
  fonts, five palette files and three new custom-menu panels. Corrupt,
  incomplete-font and missing-font replacements are rejected safely.
- `build-v17.json`: fresh engine build hashes, APK version 0.17/code 18,
  preserved signing identity, v2/v3 signatures, alignment/CRC checks and packaged
  asset comparison. All seven WASM hashes match ENGINE-BUILD.json.

Original outcome dialogs, score layouts, custom setup, Overlord details and the
touch preview were visually inspected. Custom setup currently supports Melee
with one Zerg AI. Save/load and full retail scoring edge cases remain unfinished;
this is not a claim of full retail behavioral or pixel equivalence.

## Earlier: 0.12 validation

Compared the supplied screenshots and 102 native frames from the original
1.16.1 Mission 3 recording (see REFERENCES.md). The user-linked YouTube media
stream was unavailable. Tests use external original MPQ/CD fixtures and real
WASM in desktop Chromium; Android hardware testing is pending.

- `reference-v12.json`: completed all six retail Mission 3 briefing speeches;
  decoded audio time drives scrolling; pause/resume freezes both; Replay resets
  speakers and text; nine-line Mengsk wrapping matches native footage; continued
  end scrolling, original bright-green hotkey initials, 128×118 portrait monitors
  and alternating scanlines were checked. HUD tests verify the 96×96 centered
  minimap, terrain touch/Tab toggles, remaining green local markers, balanced
  3+2 blue-framed group layout, bitmap timer and pause-menu engine suspension.
  The briefing and final HUD runs are also retained separately.
- `interface-v12.json`: main/Registry/campaign/mission navigation, unavailable
  screens guarded, stationary dark-until-hover campaign characters; original
  briefing entrance/exit and projector, Replay and Start, suspension; game menus,
  cheats, sound settings, restart/quit, and three race consoles at three sizes.
- `bot-v12.json`: final rebuilt bot engine starts and runs 600 lockstep ticks;
  Zerg workers gather, bot supply is active, detail and touch exports remain.
- `source-patch-v12.json`: all ten patched files exactly match the compiled
  source after applying the patch to the pinned upstream archive.
- `build-v12.json` / `.txt`: versionCode 13 / versionName 0.12, same package and
  signing key, verified v2/v3 signatures, ZIP alignment/CRC and every packaged
  asset byte-compared with the tested working tree.

Both core/campaign and bot WASM were rebuilt. The final HUD changes were checked
again after rebuilding. Briefing, late Mengsk scrolling, group selection,
minimap, Menu and pause dialog were visually inspected at 640×480.

Portrait dimming/scanline strength, group borders and scrolling motion remain
reconstructions. This is not proof of complete original visual equivalence,
later-campaign support, or Android performance. No proprietary fixtures,
reference videos or screenshots are included in the deliverables.

# Earlier 0.11 validation

Original 1.16.1 footage was sampled at native 640×480 and compared with the
player-provided FNT/PCX/BIN/DAT assets; details and links are in REFERENCES.md.
Testing uses real WASM and external MPQ/CD/mission fixtures in desktop Chromium
with genuine emulated touch events. Android hardware testing is still pending.

- `interface-v11.json`: Registry/campaign navigation, stationary dark race
  figures and hover, briefing lifecycle/Start/Replay, menus and three race
  consoles at three phone/tablet viewport sizes.
- `hud-v11.json`: compact original unit-name lettering, bitmap resource counts,
  messages/objectives, production queue geometry and cancellation.
- `font-startup-v11.json`: unreadable installed font entries cannot abort title,
  briefing or gameplay with valid, absent or damaged optional interface imports.
- `polish-v11.json`: actual Mission 3 rejects raw Medic production with Academy
  and cheats; skirmish still trains it. Armor research raises the SCV's displayed
  level/bonus. Research icons/caption/cancel work. Native touch input selects,
  moves, gathers and box-selects. Two-finger pan/pinch, interrupted drags and
  background suspension preserve the selection. The countdown stays at the top.
  Camera placement crosses the top/left bounds before selecting a live unit,
  exercising the signed-clamping fix that previously jumped to the far corner.
- `bot-v11.json`: newly compiled bot module starts, advances 600 lockstep ticks
  and gathers with Zerg workers; new detail/touch exports remain available.
- `source-patch-v11.json`: patch applies to pinned upstream; all ten modified
  source files match those compiled into the shipped engines.
- `build-v11.json`: retained signing certificate, versionCode 12 / versionName
  0.11, ZIP alignment/CRC, and all 41 packaged assets compared byte-for-byte.

Fonts, main/campaign menu frames, briefing, timer and unit details were visually
inspected. Timing/scroll behavior remains reconstructed and uncommon ability
panels are not exhaustive. No full pixel-equivalence or Android performance
claim is made. Proprietary fixtures and screenshots are excluded from releases.

# Earlier 0.10 validation

Original 1.16.1 footage and data were compared as documented in REFERENCES.md.
Tests run with desktop Chromium touch emulation and external local MPQ/CD/font/
Mission 1 fixtures. No Android hardware or emulator was available.

- `interface-v10.json`: main → Registry → campaign → mission history → briefing
  → gameplay → pause menus → restart/quit. Tests create/select/delete/persisted
  profiles, no main-menu slide, seven race clips, guarded unavailable campaigns,
  imported-mission availability, briefing script/speaker placement, text scrolling,
  hover intro/loop, suspend/resume and duplicate Start. Existing command-grid,
  portrait, menu, cheat and pause checks pass for three races and viewport sizes.
- `menu-navigation-v10.json`: all five original UI sounds decode and play;
  Diagnostics returns to a visible interactive title; early Back/Start, repeated
  Cancel, and Start waiting for the briefing exit complete without engine races.
- `font-startup-v10.json`: deliberately unreadable base-MPQ font8 plus valid,
  absent and damaged optional interface imports. Title, custom games, portraits,
  pause menus, briefing and campaigns start in all three cases, without page errors.
- `hud-v10.json`: original-size Command Center name, bitmap resources and actual
  mission messages/objectives, icon production queue/bar geometry, and cancelling
  an occupied queue cell while the engine continues running.
- `interface-import-v10.txt`: actual Android exporter/validator on the external
  CD archive, eight fonts plus five campaign palette entries, atomic install,
  local serving, invalid-replacement retention, and fontless-archive rejection.
- `build-v10.json`: signature, package/version, alignment, ZIP CRC, complete
  packaged-asset comparison and source-archive checks.

The menu decoder alone was rebuilt to support the original 356×304 campaign
hover movies. The five other WASM modules, including gameplay/AI and portrait
codecs, retain their previous checksums. VersionCode 11 / versionName 0.10,
package and signing certificate retained for an in-place update.

Screenshots of the main menu, Registry, campaign selector, history panel,
briefing, battlefield, production panel and pause menu were visually inspected.
These captures and all proprietary fixtures are excluded from deliverables.
The source ZIP includes build inputs, validation reports, reference notes and
the original-asset-free runtime.

This establishes the tested paths above, not full pixel equivalence, complete
original menu functionality or performance on an Android phone. Re-import the
interface once after 0.9 to load the small CD campaign frame/palette.

# Earlier 0.8.1 validation


The reported `font/font8.fnt: too many compressed sectors in file` failure was
reproduced against unmodified 0.8 application assets. Fault injection changes
only font8 in a temporary copy of the external StarDat fixture, leaving all
gameplay assets and the supplied original archive unchanged. Even a valid local
font import did not prevent the old loader from aborting startup.

`validation/font-startup-v08-repro.json` records that failure. The new
`validation/font-startup-v081.json` records successful startup with the same
unreadable base-MPQ font and each of these interface-import states:

- Valid: all eight original fonts load; title and briefing use bitmap lettering.
- Missing: title, briefing and game use fallback lettering and remain playable.
- Unreadable: an imported font's sector table is deliberately damaged. Its
  decoder failure is contained; fallback lettering and gameplay still work.

Each case starts from the title, enters Play Custom, advances the simulation,
selects an SCV, renders an animated portrait, opens/resumes the Game Menu, then
enters the original Mission 1 briefing and starts the campaign. No page errors.
The title's eight SMKs and briefing's three SMKs load in all cases.

The full original UI integration suite also passes (`interface-v081.json`):
original fonts, briefing speaker timing/replay, title and lifecycle music,
command-grid geometry for all races, modal pause, cheats, restart and quit.

The game/campaign/bot/media/portrait/menu WASM binaries are unchanged from 0.8.
The fix is in the JavaScript font-loading path; a private decoder isolates it
from console/portrait artwork. Installed fonts are no longer probed. Existing
font imports are used directly; no data migration or re-import is required.

Desktop Chromium touch emulation only. Android installation and device behavior
still need the user's check. The package/signing identity is retained, with
versionCode 9 / versionName 0.8.1. Build verification is in `build-v081.json`.
Visual parity limits documented for 0.8 still apply.

# Earlier v0.8 validation

Desktop Chromium touch emulation and a desktop JVM; no Android device/emulator
available. Original test MPQs, CD fonts and Mission 1 data are external fixtures
and are excluded from both deliverables. The user reports 0.7 working on phone.

## Original interface assets

`validation/interface-v08.json` records the current integrated run with original
bitmap fonts imported from the large CD archive, plus generated music tones:

- Original title PCX and eight idle/hover SMKs; animations and music suspend and
  resume with lifecycle. Original labels, positions and bitmap lettering render.
- Original Terran briefing PCX panels, three projector SMKs and four portrait
  windows. The original Mission 1 script places Adjutant in the fourth monitor,
  then Duke in the first while Adjutant remains visible. Timed speech, text
  scrolling, Replay clearing prior speakers and Start entering gameplay pass.
- Native font exporter extracts all eight fonts from the real 601,389,682-byte
  prefixed archive. Validation, local serving, invalid replacement preservation
  and fontless-archive rejection pass (`interface-import-v08.txt`).
- Uniform 640×480 stage; command cells, portrait and Menu bounds pass at
  640×360, 900×412 and 1280×720 for all three races. Worker build and Cancel
  return to the correct card. Wide displays intentionally have side borders.
- Original Game Menu and End Mission geometry and textures; modal engine/audio
  pause, lifecycle pause preservation, keyboard isolation, mission objectives,
  money, instant production/reset, 16× speed, mute, restart and quit-to-title pass.
- Generated music validates title selection/playback and pause behavior. This
  is not a listening-quality check of the original CD tracks on the phone.

## Regressions and build

- Mission 1 rescue, mining, Barracks, ten Marines and Victory pass. Raynor loss
  produces Defeat. No page exceptions (`campaign-v08.json`). A missing optional
  font bundle is expected in this separate regression fixture and uses fallback.
- Canceling the actual construction queue chip advances 900 simulation frames
  without a depot or resource charge; the same SCV builds a completed depot
  afterwards (`cancel-v08.json`).
- Gameplay/campaign/bot/audio/portrait WASM hashes are unchanged from 0.7. Only
  the menu decoder is rebuilt, raising its height cap to 256 for the 236-pixel
  original projector animation. Original assets are not bundled in the APK.
- Signed APK ZIP integrity, zipalign, package/version, signature and exact
  packaged asset bytes pass. `build-v08.json` records the APK hash and size.
- Package remains `org.openbw.androidtest`; versionCode 8 / versionName 0.8.
  The development signing identity is unchanged, allowing an in-place upgrade.

## Visual limits and phone checks

The original artwork, fonts and dialog coordinates are used, but no pixel-level
comparison against the running original executable has been performed. Some
unit-status/production details, the mission selector and settings are still
custom. Briefing text scrolling and projector/fade timing are approximate.
Original-game UI parity is not claimed. Save/load, multiplayer, editor and FMV
playback remain unavailable.

On the phone, install over the existing app. From the main title, use Android
Back → Game Files → Import original fonts from StarCraft.mpq. Check original
lettering, briefing portrait borders/text, the console and command grid,
Android Back, lifecycle audio and touch targets. Device-specific rendering and
memory/thermal behavior still need the user's test.

# Earlier v0.7 validation

Desktop Chromium touch emulation; no Android device/emulator available.
External classic MPQs and the user's original Mission 1 bundle were used, and
are excluded from both deliverables. User reports the previous 0.6 works on phone.

## New interface

`validation/interface-v07.json` records the current integrated run:

- Original Brood War title PCX and four main-menu SMKs render; menu panels
  advance frames and stop/resume with lifecycle. Worker terminates after decode.
- Mission availability disables unimported missions; choosing Wasteland enters
  the original briefing and game. Options and title-to-game navigation work.
- The fixture's original fonts are encrypted, so the tested path uses fallback
  fonts. A bounds-checked FNT renderer supports readable FONT files. No key
  extraction or font decryption is implemented.
- Command buttons follow the original 36×34 geometry and fit the three-by-three
  grid. Terran/Protoss positions and Zerg's five-pixel offset are accounted for.
  Portrait and Menu positions stay within the tested phone/tablet viewports.
- Build-submenu Cancel and Android Back dispatch a real Escape scancode and
  return to the worker card. The Menu button is above the portrait; the former
  battlefield toolbar is hidden.
- Game Menu pauses the frame counter and audio. Native suspend/resume preserves
  that pause. Back moves through submenus, Return resumes, and an existing manual
  pause survives opening/closing the menu. Keyboard input does not open chat
  behind a modal. Focus stays within the dialog.
- Objectives, money, instant production/reset, 16× speed, mute, restart/cancel,
  restart-to-briefing and end-to-main-menu all pass.
- Java-exported four-tone music fixture includes title.wav. Title playback,
  options, paused playback position, and transitions work. This validates code,
  not listening quality of the user's original CD tracks.

## Regression checks

- Mission 1 briefing/rescue/mining/Barracks/ten-Marines/Victory and Raynor-loss/
  Defeat run with zero browser errors, including when the menu is never opened.
- Actual production-chip cancellation advances 900 frames without abort; the
  same SCV subsequently constructs a completed Supply Depot.
- Animated briefing/SCV portraits, voice/pause, money button, 16× speed, and an
  instant depot completing two frames after its foundation pass through the
  reorganized menus. Reset restores normal production and speed.
- Skirmish touch movement, pinch zoom, command-grid targeting Cancel and audio
  pass. ZZZKBot reaches frame 5046, constructs a Spawning Pool and trains Zerglings.
  Player instant production still leaves enemy construction at normal speed.
- The core plain/campaign/bot engines and portrait decoder are byte-for-byte
  unchanged from 0.6. The only new WASM is the bounded menu-animation decoder,
  built from the same vendored libsmacker with its existing LGPL notices/source.

## Remaining phone checks

Install over the existing app, then check cold launch/title animations, menu
hit targets, native Back, Game Files/diagnostics, background/foreground audio,
custom-map file picker and long-session memory/heat. Native routing is compiled
and reviewed; browser tests emulate its redirects, not the Android OS itself.
Save/load, complete original dialog parity and later campaign missions remain
unimplemented. Signing identity and package ID are unchanged.

# Earlier v0.6 validation

## Campaign AI and missions

The actual original Terran 2/3 maps and base MPQs were supplied externally to
browser integration tests. They are not in the APK/source archive.
`validation/campaign-ai.json` records unit snapshots and script counters.

- Original Ter3 starts from its computer-owned location trigger; no unsupported
  opcode or browser exception. First wave: frame 1254. Seven initial waves
  include Zerglings, Hydralisks and Mutalisks and inflict player casualties.
- Drones gather both minerals and gas through normal orders.
- Controlled removal of workers and the Spawning Pool causes normal Drone
  morphing and reconstruction of a new Pool. The original map/AI bytes are
  unmodified; `openbw_debug_kill` is test fault injection, never called by UI.
- Full 30-minute timer reaches 0:00; original evacuation and Victory finish at
  frame 43136. This unattended timer test continually heals human buildings;
  it does not claim an unaided campaign playthrough. Nineteen attack dispatches
  and 32 production requests occurred in this run.
- Mission 3 base destruction triggers Defeat. Mission 2 Infested Command Center
  destruction triggers Victory; Raynor destruction triggers Defeat. These use
  controlled unit removal to isolate the original trigger conditions.
- Both briefings and voice audio start. Every referenced Mission 2/3 WAV is in
  the locally exported bundles. Two absent Mission 2 listfile entries are not
  referenced by its map; neither is required.
- Java exporter reads the actual >600 MB prefixed archive under a 48 MB heap.
  It exports Mission 2 (22 entries) and Mission 3 (17 entries); importer and all
  served bytes round-trip exactly. Mission filename allowlists and atomic
  replacement preserve existing data when import fails.

## Current regression results

- ZZZKBot skirmish reaches frame 5045, builds a completed Spawning Pool and
  produces Zerglings. Human instant-production does not complete enemy work.
- Animated briefing/unit portraits, talking/pause state, money button, 16×
  speed, instant building, and resetting testing controls pass.
- Depot cancellation is exercised through its actual UI queue control; the
  simulation advances afterwards and the SCV builds a fresh depot successfully.
- Mission 1 original briefing/rescue/mining/Barracks/10-Marines/Victory and
  Raynor-loss/Defeat all pass on the new engine.
- A fresh extraction of the pinned engine archive plus the packaged patch
  rebuilds byte-for-byte to the recorded plain/campaign WASM checksum.

## Scope and limits

The VM reads original scripts. Its town/production/target management is newly
implemented, not a claim of original AI parity. Only Missions 1–3 are exposed.
Unsupported commands stop the affected thread visibly. Expansion/transport/
advanced spell management are future work. Mission 2 has no base-building AI.

Desktop Chromium touch emulation is used here. No Android phone/emulator was
available; installation, audio focus, thermal load and WebView device behaviour
still need the user's phone test. Existing package and signing key are retained.

## Regression evidence

The Mission 1 rescue/build/train/Victory/Defeat suite passes on the new engine.
Other current regression results are in `validation/` and final build results
are recorded below. Earlier v0.5 feature verification is retained here for
context, not substituted for current campaign testing.

# Earlier v0.5 validation

Desktop Chromium with touch emulation and the original MPQs supplied outside
the project. No Android device/emulator was available. Installation, WebView
behavior, speaker quality and sustained 16× performance need phone testing.

## Animated portraits

Original SMK movies are extracted from base MPQs and decoded by libsmacker in a
separate worker/WASM instance. Tests render Adjutant and Duke briefing portraits,
an SCV portrait, and Protoss/Zerg selection portraits. Idle/talking animation,
speaker switching, changing frames and native pause/resume pass. Briefing and
in-game screenshots were visually inspected. No portrait movies are bundled.

Input size, dimensions, frame count, output size and WASM memory are limited.
The decoded-clip cache is bounded at 16 MiB. Missing clips retain the static
fallback. Source, license and rebuilding instructions are included. See
`portraits-testing.json` and `production-testing.json`.

## Testing cheats

- The actual touch money button adds 10,000 minerals and 10,000 gas.
- The 16× setting advanced 191 simulation frames in a half-second desktop sample;
  this is a functional check, not an Android performance guarantee.
- A Supply Depot completes within two frames of its foundation appearing, with
  full health and the engine's completed flag set. SCV travel still takes time.
- Terran SCV training, Supply Depot, Barracks, Engineering Bay, Academy,
  infantry armor upgrade and Stim research finish through normal engine paths.
- Protoss Pylon warp-in and Zerg Drone/Spawning Pool morphs finish normally.
  Required animation sequences remain: Pylon 71 frames and Pool 12 frames in
  the recorded sample, after initial placement.
- Disabling instant production restores normal training progress. Reset also
  selects original Fastest speed. Production defaults off on a new game.
- Tech, placement, resource and supply checks remain enabled. Cheats affect
  the human player only. The bot's unfinished Pool progressed from 727/750 to
  738/750 HP over 20 frames while the player's instant-production cheat was on.
- Map reveal and resource grants last until the next game. Reset does not remove
  them, as explained in the UI. Cheat-modified replay export is disabled.

## Bot and campaign regressions

The rebuilt ZZZKBot module runs over 5,000 frames, completes a Spawning Pool,
and produces Zerglings. This demonstrates the existing skirmish bot, not the
original campaign AI. At v0.5, strategic campaign scripts were unimplemented.
Only Terran Mission 1 was supported in v0.5.

The original Mission 1 suite passes: sparse archive loading, original starting
units/resources, mission voices, Raynor rescue/dialogue, normal mining,
Barracks construction, Marine production/Victory and Raynor death/Defeat.
The SCV/depot cancellation regression passes: 900 frames after UI cancel,
no unwanted depot/resource charge, then successful construction by that SCV.

Touch movement, pinch, targeting cancellation, manual/native pause and audio
initialization pass. Console layout stays in 640×360, 900×412 and 1280×720.
Music checks cover Java-exported generated-tone fixtures, original mission
ADPCM voice decoding, playlists, speech ducking, volume/mute and pauses.
Full CD music listening remains a device check. Completed browser tests report
no page errors or external requests.

## Build and package

All five modules are rebuilt from pinned sources and the included patch using
WASI SDK 33; hashes are checked against `ENGINE-BUILD.json`. The Android APK is
compiled with API 35 tools and the original development signing key.
Package `org.openbw.androidtest`, versionCode 5, versionName 0.5, minSdk 26,
targetSdk 35. APK signature schemes v2/v3, alignment and asset byte comparison
are checked. See `package.json` and `engine-rebuild.json`.

Private screenshots, original game data, SDKs and build directories are excluded
from the source ZIP. Tests, pinned source snapshots, source patches, codecs and
the existing development key are included for rebuilding and in-place updates.

## v0.6 APK build

Package `org.openbw.androidtest`, versionCode 6, versionName 0.6, minSdk 26,
targetSdk 35. Same signing certificate as previous APKs. v2/v3 signatures,
ZIP CRC, alignment, manifest and every bundled asset verified.

APK SHA-256: `552f8ed8fb7d2c08fc7a986a461d0c98a4502eca1e1e91bb5516eec83b5d7370`.

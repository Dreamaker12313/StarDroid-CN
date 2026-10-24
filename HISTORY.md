# OpenBW Android 0.61

Following Build and Cancel controls always stay below the visible placement
preview, including over the HUD. They draw on top, with a dark backing for clear
labels. Covered controls cannot receive taps, holds or releases through the row,
including the gap between Build and Cancel.

The option remains in **Game Menu → Options → Touch Controls → Command Settings**
and defaults to On. Allow zoom out also defaults to On; saved preferences remain.
Install **OpenBW-Android-0.61.apk** over the existing app without uninstalling.
The native engine and multiplayer protocol are unchanged from 0.59/0.60.

See [0.61 changes](docs/FIXES-0.61.md) and [validation](VALIDATION.md).
Physical-device testing remains pending.

# Historical revision: 0.60

Build and Cancel can now follow the building placement preview. The setting is
enabled by default under **Game Menu → Options → Touch Controls → Command Settings**.
Turn off **Build buttons follow placement** to restore their fixed position.
The buttons stay on screen and avoid the minimap, command card and touch controls.

Install **OpenBW-Android-0.60.apk** over the current app without uninstalling.
Imports, preferences and saves are retained. This interface update uses the same
native engine and multiplayer protocol as 0.59; those two versions can connect.

See [0.60 changes](docs/FIXES-0.60.md) and [validation](VALIDATION.md).
Automated checks pass; physical-device touch testing remains pending.

# Historical revision: 0.59

Locks hero command icons to fixed positions and separates unit effects from
Detector text. Hero Mode computers on all difficulties pursue all six heroes,
start earlier and build extra upgrade buildings for parallel production.
Hero build times exactly match their normal counterparts.

Install **OpenBW-Android-0.59.apk** over the current app on **all devices**.
Do not uninstall. Existing imports, preferences and saves are retained.
Older multiplayer builds are rejected before map transfer.

See [0.59 changes](docs/FIXES-0.59.md) and [validation](VALIDATION.md).
Level 3 Zerg air attack/armor requires a Hive, and can be researched at either
an ordinary Spire or a Greater Spire. This original rule is unchanged.

# Historical revision: 0.58

Adds optional Hero Mode (six heroes per race) and teams to custom/multiplayer
lobbies, including saved matches. Fixes depleted-base AI recovery and score-fill
sound, strengthens Hard skirmish AI, restores retail Protoss tech counting, and
adds original-style Player ID dialogs and a surrounding Pylon icon ring.

Install **OpenBW-Android-0.58.apk** over the current app on **all devices**.
Do not uninstall. Imports, preferences and saves are retained. Older multiplayer
simulation versions are rejected before map transfer.

See [0.58 changes](docs/FIXES-0.58.md), [validation](VALIDATION.md) and the
[Hero Mode roster and costs](docs/campaign-heroes.json). Choose Teams under Game
Type and tap T1–T8 beside slots to assign allies. Hero Mode is above the map name.
Campaign build orders and hero statistics are unchanged. Physical-device input,
listening and radio checks remain pending.

# Historical revision: 0.57

Added unpowered building feedback, attached-add-on requirements, selection sound
debouncing, a Pylon icon and ToadWarrior's credit. The powered-tech prerequisite
rule from this version is reverted to retail behavior in 0.58.
See [0.57 changes](docs/FIXES-0.57.md).

# Historical revision: 0.56

Fixes competitive victory detection, transport Load controls, Ultralisk selection
voices, score timing/audio and original score bars. Polishes menu colors, hover,
red borders, lobby chat/status, the Protoss Replay transition and the Wraith icon.

Multiplayer starts with player-name selection. Host map selection shows capacity;
slot configuration and player movement happen in the created lobby. The existing
up-to-eight-device multiplayer, computers, Free for All and save/load remain.

Custom and multiplayer AI now reserves expansion/upgrade resources, retries
blocked construction and reaches advanced units and detectors across all races.
Campaign build orders are unchanged; available detectors react to invisible attacks.

Install **OpenBW-Android-0.56.apk** over the existing app on **all devices**.
Do not uninstall. Imports, preferences and saves are preserved. Older multiplayer
simulation versions are rejected before map transfer.

See [0.56 changes](docs/FIXES-0.56.md), [validation](VALIDATION.md) and
[campaign hero comparison data](docs/campaign-heroes.json). Hero prices are
proposals only. Physical-device installation, radio, touch and listening checks
remain pending.

# Historical revision: 0.55

Fixes overlapping tooltips, responsive command inspection, stationary results
backgrounds, the Ultralisk voice and Duran's introduction/rescue. Polishes the
original multiplayer and custom-game panels and redraws the Wraith launcher icon.

Multiplayer supports up to eight devices within the map slot limit, computers,
host-controlled slot positions, chat, settings and saved matches. Choose the
expansion from the main menu, then Host Game, Join Game or Load Saved. Choose
races in the lobby. Tap a player and then a destination slot to move them.

Install **OpenBW-Android-0.55.apk** over the existing app on **all devices**.
Do not uninstall. Existing imports, preferences and saves are preserved.

See [0.55 changes and setup](docs/FIXES-0.55.md) and [validation](VALIDATION.md).
Automated checks pass; physical-device installation, radio and keyboard testing
remain pending. Actual simultaneous connections depend on device radio support.

# Historical revision: 0.54

Adds original-style multiplayer setup and lobbies, a five-second countdown,
scrolling map lists with terrain previews, multiple computers, Free for All,
host-selected speed, and multiplayer save/load. Includes the requested unit,
flying-building, result-screen and new-install default fixes.

Install **OpenBW-Android-0.54.apk** over the existing app on **both phones**.
Use **Multiplayer → Host Game / Join Game**. The host saves/loads multiplayer
matches; **Multiplayer → Load Saved Game** hosts a saved match for later play.
Bluetooth and Wi-Fi Direct work without Google Play services or internet access.
Existing imports, settings and single-player saves are preserved.

See [0.54 changes and setup](docs/FIXES-0.54.md). Automated native, protocol,
pacing and menu-rendering checks pass; physical-phone confirmation is pending.

# Historical revision: 0.53

Multiplayer now works without Google Play services. It uses Android Bluetooth
pairing, automatically upgrades to Wi-Fi Direct when available, and keeps
Bluetooth as a fallback. The 0.52 host pacing fix and 0.51 map-transfer and
command-buffering improvements are retained.

Install **OpenBW-Android-0.53.apk** over the existing app on **both phones**.
Enable Bluetooth and Wi-Fi, choose **Multiplayer → Host Game / Join Nearby**,
select the host's phone name and confirm the pairing codes. Use **Bluetooth only**
if desired. Existing imports, settings and saves are kept.

Automated transport, permission, map, pacing and package checks pass. Physical
phone discovery, pairing, radio handover and performance remain unverified.
See [0.53 changes and setup](docs/FIXES-0.53.md).

# Historical revision: 0.52

Fixes host-only multiplayer frame bursts after a late start or network stall.
The scheduler now resumes a steady cadence automatically instead of repeatedly
waiting and rushing through command batches. Tabbing out is no longer needed
for the reproduced timing bug. Game speed and input buffering stay unchanged.

Install over the existing app on both phones. Network diagnostics now include
frame spacing and pacing recovery, and the diagnostic heading shows the actual
build version. The reproduced host bursts disappear in automated tests;
physical-phone confirmation remains pending. See [0.52 fixes and validation](docs/FIXES-0.52.md).

# Historical revision: 0.51

Improves Google Nearby command scheduling, concurrent packet delivery and map
transfer. Commands are sent one turn ahead with a 168 ms input buffer. Maps use
a transfer window, optional compression and a verified cache. The game still
targets Fastest speed.

Install over the existing app on both phones. During a multiplayer match, open
**Game Menu → Options → Network** for the optional overlay and detailed timing
report. Automated synchronization, latency, transport and package checks pass;
physical two-phone performance remains untested. See [0.51 changes and measured
test results](docs/FIXES-0.51.md).

# Historical revision: 0.50

Fixes the immediate missing location permission error in Google Nearby Host/Join.
Install over 0.49 on both phones. When prompted, allow Location while using the
app with Precise location enabled, and allow Nearby devices. Existing imports,
saves and settings stay in place. No background location permission is requested.

Permission and protocol regression tests pass. Physical two-phone testing is
still pending. See [0.50 changes](docs/FIXES-0.50.md).

# Historical revision: 0.49

Google Nearby multiplayer, packaged as an update over 0.48. Install over the
existing app to retain imported game files, solo saves and settings. Both phones
need 0.49 and Google Play services. Open **Multiplayer → Host Game / Join Nearby**,
allow Nearby permissions and confirm matching pairing codes.

Game speed remains Fastest. This build restores the Google networking backend;
it does not claim a frame-rate or latency improvement. Physical two-phone
radio and installation testing remain pending. See [0.49 changes](docs/FIXES-0.49.md).

# Historical revision: 0.47

Adds two-phone nearby multiplayer using coordinated Bluetooth/BLE and Wi-Fi.
Open **Multiplayer → Host Game / Join Nearby**, confirm the matching pairing
code, and let the map transfer. The host starts once both players are ready.
Choose any race and StarCraft or Brood War rules. No internet server is needed.

Install over the existing app on both phones. Each needs Google Play services
and the same imported core files. Shared pause, command synchronization, state
checks and connection-loss handling are included. Multiplayer saves, reconnect
and AI slots are not included in this first two-player build.

Desktop synchronization and protocol checks passed. Physical two-phone radio
and Android interaction testing remain pending.
See [0.47 changes and build instructions](docs/FIXES-0.47.md) and
[validation scope](VALIDATION.md).

# Historical revision: 0.46

Polished original-art victory/defeat score screens with corrected text and
slide-in/out transitions. Custom Game also slides in/out and applies the selected
StarCraft/Brood War rules to both players and the AI. Includes an original Wraith
wireframe launcher icon. See [0.46 changes](docs/FIXES-0.46.md) and
[validation scope](VALIDATION.md).

Install over the existing app to keep imports and saves. Local multiplayer is
feasible but is not included; the change notes describe the remaining work.

# OpenBW Android 0.45

Zerg is available as a skirmish opponent using the original Brood War AI scripts.
Easy, Medium and Hard apply to all three computer races, including Terran.
See [the 0.45 changes](docs/FIXES-0.45.md) and the current validation record below.

# OpenBW Android 0.44

Fixes race-specific placement and landing sounds, Terran building/addon
completion voices, tank mode announcements, addon command visibility and slots,
supply-cost icons, cloak shimmer/detection, false attack alerts and repeated
pings. Immobile selections inspect tapped units without setting rally points.

Ghost Nuclear Strike has its original icon, remains grey without a ready
missile, and now uses the correct targeting order. Drawing of the Web retains
its original restrictions: Queens allowed, offensive air and transports disabled.

Install over the existing app to retain imports and compatible saves. Both
ARM64 and x86_64 are included, with the same package ID and update certificate.
See [0.44 changes](docs/FIXES-0.44.md) and [validation scope](VALIDATION.md).

# Historical revision: 0.43

Custom Game now offers Terran or Protoss computer opponents, each with Easy,
Medium and Hard difficulty. Tap the computer player's race to change it.
Protoss uses the original PLOx/PMEx/PHIx scripts from the imported game data,
with an OpenBW manager for a normal four-Probe melee start.

The previous Zerg skirmish bot, its compiled web module, vendor archives and
BWAPI build dependency are removed. Human Zerg play and original Zerg campaign
scripts remain supported. Campaign, practice and Terran saves retain schema 2;
old external Zerg-bot skirmish saves are rejected with a clear message before
replacing the running game.

Install over the existing app to preserve imports and compatible saves.
See [0.43 changes](docs/FIXES-0.43.md) and [validation scope](VALIDATION.md).

# Historical revision: 0.42

Fixes cloaked-enemy visibility, initial mission fog snapshots, group Carrier/Reaver ammunition, innate Feedback, Shield Battery commands, merge availability and cargo command visibility.

Adds the original title screen, target/placement feedback, resource icons in tooltips, a cleaner skirmish layout and persistent interface-size controls. Terran skirmish AI expands its economy and trains advanced and support units with normal resources.

See [0.42 changes](docs/FIXES-0.42.md) and [validation scope](VALIDATION.md). This build keeps the existing package ID, signing key and save format.

# Historical revision: 0.41

Command feedback uses plain game text above the console for minerals, gas,
energy, Overlords, Supply Depots and Pylons. Available but unresearched spells
stay visible in grey; low energy leaves researched buttons bright.
Interceptor and Scarab buttons disappear at capacity, including queued ammunition.
Archon merges show progress and announce completion only after the merge ends.
Transport passengers use the original wireframes, borders and cargo-space sizes.

Custom Game supports a persistent map collection, multiple map files and ZIP
imports. Import **OpenBW-Skirmish-Maps.zip** from **Custom Game → Import maps / ZIP**
to add eight original Blizzard maps. The Terran computer offers original Easy,
Medium and Hard campaign scripts, with Hard selected for a new game. Its manager
reserves add-on space and keeps training from interrupting add-on construction.

Install this APK over the existing app to retain imports and saves. Start a new
Terran match to select another difficulty. See [0.41 changes](docs/FIXES-0.41.md)
and [validation](VALIDATION.md) for the checks and remaining limits.

# Historical revision: 0.40

Fixes Emperor's Flight's airborne building arrival and handover, adds computer
tank siege decisions, and keeps retracted traps hidden until they open.
The map ends at the center console, control groups sit higher, and resource
icons/text can be enlarged in Video settings. An original attack/move icon
button sits above the selection cursor and follows its chosen side.

Custom Game now offers a first **Terran Easy** opponent using the original
Brood War campaign Easy AI script. Tap the computer's race to switch between
Terran and the existing Zerg opponent. See [0.40 changes](docs/FIXES-0.40.md)
for controls, checks, AI scope and remaining limits.

Install over the existing app to keep imports and saves. Restart Emperor's
Flight to get the corrected opening.

# Historical revision: 0.39

Fixes off-map stale terrain, the last survivor's wireframe, Infested Kerrigan's
command slots and mission beacons accepting combat damage. Load/Unload use the
original orders.dat icon frames. Opening text fits the available screen area.

The one-shot selection cursor defaults to **Left**. Optional **control group
buttons** are under **Game Menu → Options → Touch Controls → Selection settings**
and start disabled. Hold a numbered group button for 450 ms to assign the current
selection, tap to recall, and double tap to center the camera. Groups are saved
with the game. Existing custom cursor-side choices are preserved.

Install over the existing app to keep imports and saves. See
[0.39 fixes and validation](docs/FIXES-0.39.md) for checks and remaining limits.

# Historical revision: 0.38

Fixes Dylarian's final-platform counter, Tarsonis's opening handover and mixed-race
worker construction. Adds independent supply displays, one-shot drag selection,
configurable ground-tap orders, cargo controls and the Miscellaneous menu.
Corrects Ghost ability positions and Zerg/Protoss briefing visuals.

All 64 original missions, including the four previously unresolved attempts,
reach their original victory triggers in assisted diagnostic checks. These are
not unassisted human playthroughs.

Install over the existing app to preserve imports and saves. Use a fresh mission
when checking corrected opening sequences. See [the 0.38 notes](docs/FIXES-0.38.md)
and VALIDATION.md for test results and remaining limits.

# Historical revision: 0.37

Fixes Eye of the Storm's missing Command Center, hero Carrier/Reaver fighter
cleanup, and scripted unit-removal crashes. Adds resource-error feedback,
configurable touch controls, larger green mission text, and local base defense.

Install over the existing app to preserve imports and saves. Restart Eye of the
Storm to get its corrected opening base. See [the 0.37 notes](docs/FIXES-0.37.md)
and VALIDATION.md for exact changes, test assistance and remaining limits.

# Historical revision: 0.36

Original-data testing now covers startup and exact save continuation for all
64 missions, plus seven focused mission checks. This build fixes missing-voice
archive crashes and dialogue timing, reused movement state after loading, the
Patriot's Blood entrance alliances, and doors that could not close/reopen.

Install over the existing app to preserve imports and saves. The 0.35 sparse
map save fix and Duran's bottom-left Cloak/bottom-centre Lockdown are retained.
See [the 0.36 notes](docs/FIXES-0.36.md) for fixes and the limits of these tests.

# Historical revision: 0.35

Save/load now accepts sparse mission archives and every catalogued campaign ID.
Samir Duran and Infested Duran use bottom-left Cloak/Decloak and bottom-centre
Lockdown. Install this signed APK over the existing app to keep imports and saves.

See [the 0.35 notes](docs/FIXES-0.35.md) for the save-format compatibility and the
64-map audit, including limits on full playthrough verification.

# OpenBW Android 0.34 — Save/load and Zerg morph sounds

The game now runs as compiled C++ on Android. JNI connects the engine to an
Android SurfaceView, Android Canvas draws the original interface, and a native
PCM mixer feeds AudioTrack. There is no WebView, JavaScript, or WebAssembly in
the APK. It supports 64-bit ARM and x86 Android devices, Android 8.0 or newer.
Original game files are imported locally and are not included.

Version 0.34 adds six persistent save slots. Use **Game Menu → Save Game**
while playing; load from **Game Menu → Load Game** or **Single Player → Saved Games**.
Each save includes its map and mission voices, units, orders, research, resources,
mission triggers, campaign AI, fog, camera and selection. Loading returns to the
paused game menu. Replacing a slot and replacing a running game ask for confirmation.
Saves survive closing the app and installing an update with the same signing key.
Lair, Hive, Greater Spire and colony morphs use the original shared Zerg building
completion sound when their DAT ready sound is empty. See `docs/SAVES-0.34.md`
for the save format, checks and limitations.

Version 0.33 fixes neutral Hatchery transfers so creep and larva production start
when you receive the base in **True Colors**. Hover over a command with a mouse
or stylus, or hold it for 280 ms on touch and slide between buttons, to inspect
live costs, supply, descriptions and requirements. Release after inspecting to
close the tooltip; a quick tap activates the command. **Play Introduction** now
uses the same Original/Expansion chooser as campaign selection and keeps your
campaign preference. See `docs/POLISH-0.33.md` for checks and remaining limits.

Version 0.32 restores starting computer alliances across different forces, fixes
triggered ceasefires, and lets Lurkers finish scripted Move orders. The supplied
64 mission maps exposed the early Raynor ending in **Agent of the Swarm** and
the three-Lurker ambush in **True Colors**. Original map records are checked with
synthetic engine data; full mission playthroughs and original artwork remain
unverified. See `docs/MISSIONS-0.32.md` for the evidence and limits.

Version 0.31 adds **App Options → Export missions**. Choose a folder in Android's
Save dialog, then attach **OpenBW-Missions.zip** to the project chat. It exports
all installed campaign maps with their units, alliances, briefing text and
triggers. Voices and movies are omitted to keep the upload small. Nothing is
uploaded automatically and installed files are not changed.
See `docs/MISSION-EXPORT-0.31.md` for the format and validation scope.

Version 0.30 applies map force alliances before units load, restores map unit
properties, adds computer Lurker combat burrowing, and corrects trap/door order
and animation handling. It also improves touch selection, global command voices,
critter feedback, research/upgrade announcements, hero command slots, tooltips,
briefing cleanup/scrolling, menu hover sounds, and story/Replay rendering.
Core game archives were unavailable during this revision. Full Chrysalis mission
playthroughs and original-art visual fixes still need a device check.
The earlier 202-check gameplay result belongs to 0.28, not this build.
See `docs/FEEDBACK-0.30.md` for the changes, current checks, and remaining work.

## Install

Install **OpenBW-Android-0.53.apk** over your existing version. The package ID and signing key are
unchanged, so existing imported game files and campaign bundles are retained.
Do not uninstall the old app first. Display and sound preferences now use native
Android preferences; browser-only preferences start at the native defaults.
The first launch rebuilds a local cache from the existing imported bundles.

New installs: open **App Options → Import game files** and select the classic
files. Several files may be selected together.

| File | Content |
| --- | --- |
| StarDat.mpq, BrooDat.mpq, Patch_rt.mpq | Required core data |
| StarCraft.mpq | Original campaigns, voices, fonts/interface, music, story openings and 13 cinematics |
| BroodWar.mpq | Expansion campaigns, voices, music, story openings and 4 cinematics |
| Original Install.exe | Corresponding CD archive, detected from its contents |
| Previously exported mission ZIP | Compatible existing mission bundle |

Existing maps and core files remain installed. **Reimport StarCraft.mpq and
BroodWar.mpq once in App Options to add the newly supported cinematics.** Both
archives can be selected together. Imports stay on the device; mission export
saves only to the location you choose. The app has no network permission.
Original fonts are used when installed; a system-font
fallback keeps the core game usable before the interface import.

## Changes retained from 0.28

- Menu music continues through navigation. Mission splash/cinematic taps are silent.
- Original/Expansion labels sit below their logos. Menu panels use a cubic
  ease-out entrance and exit, clipped inside the black letterbox borders.
- Mission lists include Boot Camp and the original intermissions in campaign order.
  Victory progression plays the corresponding movie before the next mission;
  selecting a movie directly returns to the mission list. Cinematics have no Skip
  overlay; tapping or Back still dismisses them.
- Briefing captions follow the playing recording. Version 0.30 holds the first
  viewport, then moves the full transcript in one continuous crawl.
  Timing is estimated from text and punctuation;
  it is not word-aligned. Dragging still allows manual reading.
- Race-specific BIN coordinates align command icons with the console. Creep Colony
  morphs occupy the lower left/middle, Hydralisk Den the lower left, and Zerg
  producer rally commands the upper middle. Rally is available only on unit
  producers, including Hatcheries when the mission forbids their Lair morph.
  Unarmed units have no Attack command.
- Touch Cancel leaves build menus, placement and production correctly. Ordinary
  targeting keeps the unit's command slots, including Drone Burrow.
- Original portrait rims and progress-bar artwork replace partial masks and plain
  bars. Empty portraits stay black. Changing selected units briefly shows monitor
  static, including two units of the same type. The static is synthesized.
- Resource quantities are centered in the information panel, with “Vespene Gas.”
  Menu/terrain buttons respond visually while pressed. Original tips have previous,
  next and startup controls. Tips/objectives use larger original fonts on translucent
  blue panels; touch-control help remains in Options.
- Placed Terran addons connect after all map units load. Scripted camera movement
  uses the visible map height; the bottom map edge can scroll above the HUD.

## Native features

- Original and Brood War campaign selection, with the existing 64-map catalog,
  original briefing scripts, portraits, dialogue, technology restrictions,
  mission openings, mission branching, and score screens.
- Native C++ simulation and software rasterizer. The Android display presents
  its framebuffer with the original PCX/GRP/FONT/BIN interface artwork.
- Native audio for effects, voices, victory/defeat, music and building placement.
  Menu, portrait and introduction Smacker video decoding uses libsmacker.
- The existing Zerg ZZZKBot opponent runs natively for custom games. Select one
  computer slot or close all slots for practice; select a race or Random.
  Custom SCM/SCX imports validate and show map information before you press OK.
  The included Weave test map remains available.
- Vsync-driven menus with a quick start and smooth easing into place. In-game
  sound, speed, video and testing controls use the original blue dialog artwork.
- Existing 0.22 gameplay fixes remain: Lair/Hive availability, visible disabled
  technology, Egg target icons, refinery HP and gas, Chrysalis panel cleanup,
  and silent beacon transfers.
- Fixed deferred creep cleanup when mass building destruction fills the
  engine's creep-recession pool, encountered in Brood War Zerg 6 validation.

## Controls

| Gesture | Action |
| --- | --- |
| Tap friendly unit | Select |
| Double tap unit | Select units of that type |
| Tap destination with military units | Attack-move or attack target |
| Tap destination with workers | Move, gather, or contextual action |
| Drag world | Pan camera |
| Hold, then drag | Select a group |
| Pinch and move two fingers | Zoom and pan; optional zoom-out is under Video |
| Tap or drag minimap | Move camera |
| Building preview | Drag into position, then tap Build |
| Tap production icon | Cancel that item |
| Tap group wireframe | Select that individual unit |
| Menu above portrait | Pause and open game options |
| Android Back | Cancel targeting or return through menus |

## Remaining limits

This is a native test build, not the original Blizzard executable. Campaign AI
still has one production manager per computer player; multi-town expansion,
transport coordination, tactical spellcasting and some campaign behavior remain
incomplete. Save/load is available; the custom opponent replans from the restored
world instead of retaining its private strategy memory. Replay loading and
multiplayer are not implemented. Custom-game replay export
is available from the score screen; testing cheats disable it. The introduction is
available from the title screen. Physical-device performance, audio routing,
and extended campaign playthroughs require further device testing. Custom games
currently support one computer opponent, whereas the browser host can run
multiple bot workers. Passing a startup check does not certify that every mission can be completed.

The native software rasterizer still performs its rendering on the CPU. Native
compilation removes the browser runtime; it does not establish a particular
frame rate or guarantee lower power consumption on every phone.

## Build from source

On Linux x86-64 with Python 3.12+, a JRE 17+, and `make`:

```sh
python3 scripts/build.py
```

The script downloads and checks Android SDK platform 35, build tools 35, NDK
r27d, and ECJ 3.33.0. It installs CMake 4.4.0 into its tools cache if needed,
reconstructs the pinned engine and bot sources, compiles both native ABIs,
compiles Java, signs the APK, verifies signatures and 16 KiB native-library
alignment, and compares packaged assets byte for byte. `OPENBW_ANDROID_TOOLS`
selects the tools cache. No Gradle or browser SDK is needed.

After a Java/UI-only edit, `python3 scripts/build.py --skip-engine` packages the
already compiled native libraries. To rebuild one ABI directly:

```sh
python3 scripts/build_native_engine.py arm64-v8a
```

`native/runtime.cpp` is the JNI/runtime adapter; `native/audio.h` implements the
mixer. `NativeSurface`, `NativeArt`, `NativeGlue`, `NativeHud`, `NativeCampaign`
and `NativeResults` implement Android presentation. `NativeData` reconstructs
sparse MPQs from existing imported bundles while preserving encrypted offsets.
`prepare_native.py` records the native portability and lifetime fixes, applied
after `patches/campaign.patch`. Vendor archives and their pinned hashes are
recorded in `UPSTREAM.json` and `ENGINE-BUILD.json`. Generated engine sources
are not needed in the source archive and are reconstructed during a build.
`NATIVE-BUILD.json` records this release's native sources and library hashes.

libsmacker is a separate, replaceable `libsmacker.so`. Its complete unmodified
source and LGPL license are in `vendor/libsmacker/`; the APK carries the notice
and license. Rebuilding the APK permits replacing that library. The development
signing key is retained in `signing/test-key.p12`, alias `openbw-test`, password
`android`; it is not a production signing key.

The legacy web source is retained as implementation history and as provenance
for the command layout data. It is not packaged or executed by the native app.
See `docs/README-0.22.md` for that older architecture.

## Validation

See `VALIDATION.md` for results and limitations. `tests/native_campaigns.py`
exercises all catalog maps with a compiled desktop version of the same C++
engine. `tests/native_controls.cpp` exercises commands, morphing, presentation
queries, and the native audio mixer. `tests/NativeDataHarness.java` tests all
imported bundles using the actual Android cache reconstruction code.
`tests/NativeInstrumentation.java`, `tests/NativeParityInstrumentation.java`,
`tests/NativePolishInstrumentation.java`, `tests/NativeFeedbackInstrumentation.java`
and `tests/NativeGameplayInstrumentation.java`
are built into a separate test APK. They check Android presentation, native
commands, original menu navigation, real touch gestures, bot restart, and
introduction playback, dialog isolation, list scrolling and audio interruptions. `tests/browser_reference_v25.cjs` captures matching
scenes from the unchanged browser runtime. None of the test harness is included in the application APK.
Private game files and test screenshots are excluded from the source package.

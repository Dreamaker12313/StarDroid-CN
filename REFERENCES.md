# 0.30 implementation references

Inspected 2026-10-21. These references are not game assets included in this package.

- [CHK force flags](https://docs.scmjs.dev/chk/forc/): allied, allied-victory and shared-vision bits.
- [GPTP original doodad order reconstruction](https://github.com/BoomerangAide/GPTP/blob/master/GPTP/hooks/orders/doodad_orders.cpp): trap acquisition/reveal/hide, door order signals and forced doodad animation calls.
- [GPTP research/upgrade completion reconstruction](https://github.com/BoomerangAide/GPTP/blob/master/GPTP/hooks/orders/research_upgrade_orders.cpp) and [sound IDs](https://github.com/BoomerangAide/GPTP/blob/master/GPTP/SCBW/enumerations/SoundId.h): advisor completion events and race sound filenames.
- [BWAPI technology documentation](https://github.com/bwapi/bwapi/blob/main/Documentation/dox/techtypes.dox) and pinned BWAPI UnitType.cpp in the bundled dependency archive: hero ability eligibility, including Infested Kerrigan's Psionic Storm.

# Original menu and briefing references — 0.13

## Visual evidence

[World of Longplays / JadedZerg: PC Longplay 372 — StarCraft / Brood War](https://archive.org/details/PC_Longplay_372_Starcraft_Brood_War).
The collection's `PC_Longplay_372_Starcraft.mp4` shows version **1.16.1**
on the main menu. Inspected on 2026-10-14. The recording is evidence, not an
asset distributed with this project.

- 00:01–00:06: original main-menu labels, idle objects, button colors and hover.
- 02:38–02:56: Single Player → game-type popup → new character name/Registry →
  three-race campaign selector → Terran campaign introduction. Examined at two
  samples/second. Main-menu objects do **not** individually slide away on this
  route. Registry panels do slide, while their background stays stationary.
- 03:37.9–03:40.7: Start idle/hover at ten samples/second. Its label is stationary
  around x513/y380; the projector appears above it. BIN response coordinates and
  text offsets explain why the old full-widget button and label were misplaced.
- 03:45–05:15: mission/transmission text, resource counts, selected-unit text,
  production widgets and command hints. A native 640×480 frame at 04:05 shows
  the small unit-name glyphs, three resource columns and unboxed mission text.
- 03:15.8–03:17.2: Terran briefing entrance, inspected at 20 samples/second.
  The room background appears first. Separate monitors and button panels move
  horizontally in from the left and right, then labels and briefing actions start.
- 03:34–03:42: idle briefing and Start hover; the hologram becomes visible on
  hover. A red frame marks the current speaker. Inactive monitors and the text
  and objective panels let the background show through.
- 03:40.6–03:42: Start/exit, inspected at 20 samples/second. Captions and portraits
  clear, panels slide out, the empty room remains briefly, then gameplay appears.

The briefing sampled here is Boot Camp. The Android port still launches the
supported Missions 1–3; this change does not add the tutorial or its Skip button.
The recording is compressed and cannot establish exact palette arithmetic or
every original engine timer. Reference samples remain outside the deliverables.

## Data and source inspection

Original assets are read from the player's local MPQs, with patch/BroodWar/base
precedence. Nothing extracted from the game is included in the APK or source ZIP.

| Original data | Use in this build |
| --- | --- |
| `rez/glulogin.bin`, `glue/login/plist.pcx`, `glue/palnl/*` | Registry geometry, background, panels and typography |
| `rez/glucmpgn.bin`, `glue/campaign/*.pcx` | Three race selectors, pedestal/label positions and bottom buttons |
| `glue/campaign/{disk,terr,terron,zerg,zergon,prot,proton}.smk` | Seven original animated selector clips, up to 356×304 |
| CD archive `glue/palcs/{backgnd,tfont,teffect}.pcx`, `dlg.grp`, `tile.grp` | Actual campaign frame/palette imported alongside fonts; these are in the large CD MPQ, not the tested base archives |
| `rez/gluhist.bin`, `glue/campaign/phist.pcx` | Starting-mission selection layout and panel |
| `rez/statdata.bin`, `rez/statres.bin`, `game/tfontgam.pcx` | Console geometry, resource columns, small unit text and in-game color ramps |
| CHK `STR ` strings | Newlines, deliberate indentation, palette controls and alignment directives retained |
| `rez/glumain.bin` | Main-menu button positions, labels, hotkeys, animation offsets and flags |
| `glue/mainmenu/*.smk` | Eight actual idle/hover clips; native frame dimensions and intervals |
| `rez/glurdyt.bin` | Terran monitor, portrait, text, objectives and button geometry |
| `glue/readyt/*.pcx`, `glue/palrt/pcancel.pcx` | Original panel art; native image dimensions retained |
| `glue/palrt/teffect.pcx` | Identifies palette index 138 used for the dark glass regions |
| `glue/readyt/tframeh1.pcx` through `tframeh4.pcx` | Actual red speaker-frame artwork |
| `glue/readyt/proj.smk`, `proloop.smk`, `start.smk` | Start hologram; intro-to-loop timing follows clip frame count and interval |
| `glue/palmm/tfont.pcx`, `glue/palrt/tfont.pcx` | Normal green and highlighted button text; original hotkey control colors |
| Imported `files/font/font*.fnt` | Bitmap fonts; the safe isolated font import from 0.8.1 is retained |
| `sound/glue/{mousedown2,mouseover,swishin,swishlock,swishout}.wav` | Original click, hover, slide and panel-lock sounds |

`starton.smk` exists in the archive but is **not** referenced by `glurdyt.bin`.
Its name alone was not treated as evidence that the original uses it.

BIN structure/flag cross-check:
[PyMS DialogBIN.py, commit bfc5d3aad0b5614a5aff72c223f8efa00afddfa4](https://github.com/poiuyqwert/PyMS/blob/bfc5d3aad0b5614a5aff72c223f8efa00afddfa4/PyMS/FileFormats/DialogBIN.py).
This identifies SMK flags for fade, dark, repeat and hover. BIN geometry does not
provide the complete transition choreography.

FNT/color-control cross-check:
[PyMS FNT.py at the same pinned commit](https://github.com/poiuyqwert/PyMS/blob/bfc5d3aad0b5614a5aff72c223f8efa00afddfa4/PyMS/FileFormats/FNT.py).
Game and glue screens use different color-ramp tables; the game table has three
64-pixel rows. Glyph dimensions are not CSS point sizes. The 0.10 estimate of a
119-pixel font8 unit-name advance was wrong; the 0.11 comparison below resolves
the actual font10 glyphs with compact spacing.

Engine-behavior cross-check:
[decompile-sc renderer viewport research, commit 475f0a123dcda77eff89cdf045d6980b1b7203fa](https://github.com/inwenis/decompile-sc/blob/475f0a123dcda77eff89cdf045d6980b1b7203fa/research/renderer-viewport.md).
Its discussion of address `0x004DCDE2` identifies a glue-screen dialog slide.
Used as corroborating research only; no implementation code from that project
was copied into this port.

## Reconstructed behavior and remaining limits

The port uses a 750 ms eased horizontal entrance and 350 ms exit, with a short
empty-room hold and fade. Panel direction is chosen by its original center;
portrait/text contents move with their parent panel. Start/Cancel are serialized
and the mission engine starts only after the exit finishes. Android Back during
entrance queues a cancel. The same animation clock freezes during suspension.

These briefing curves, the 60% dark-glass alpha and 250 ms hologram fade are
reconstructions, not the original engine's palette/timing implementation.
Registry/campaign panel entrance uses a reconstructed 650 ms easing; the main
menu has no slide entrance or departure. Main-menu/race SMK pixels and timing,
PCX panel art, font glyphs, BIN positions and sounds are loaded from game data.

Start's original widget is x417/y240, 217×240, but its response rectangle is
x435/y279 through x619/y400. Text occupies the separate BIN offset region;
centering the 60-pixel “Start” label in that region places it at x513/y380.
The same separation prevents large race hover movies from becoming overlapping
full-screen hit areas.

Registry identities persist in localStorage. Name-entry/delete/unsupported
notices are reconstructed with original tiles and fonts. The original history
panel lists only the three missions currently supported; it is not a complete
original campaign-unlock system. Zerg/Protoss campaign gameplay, the game-type
chooser, campaign intro crawl, FMVs, save/load and later missions remain absent.
Queue digits, tooltip borders, glass alpha and some status elements are still
approximations. No original asset or reference recording is distributed.


## 0.11 native-resolution typography and controls

Used the same original 1.16.1 recording, directly sampled at 640×480:
02:38 main menu; 02:46.8 campaign selection; 03:22/03:30 tutorial briefing;
04:05 unit panel; 07:30 SCV details; 20:00 mission transmissions;
23:30/24:10/24:50 Mission 3 briefing; 30:00/40:00 countdown and command cards.
The race SMK records mark the character layers as dark (flag 2), while pedestal
and hover-overlay layers have different flags. Only surrounding panels slide.

Compared actual FNT glyph masks with native recording pixels, testing six font
files and three advance rules. Normalized local image correlation is diagnostic,
not proof of pixel equivalence (the recording is lossy). Best matches:

| Text sample | Font file | Additional advance | Correlation |
| --- | --- | --- | --- |
| Single Player | font16x | 1 pixel | 0.924 |
| Briefing “Ending transmission. Priority Alert!” | font14 | 1 pixel, 19-pixel lines | 0.920 |
| Briefing Objectives heading | font16 | 1 pixel | 0.917 |
| Briefing objective sentence | font10 | 1 pixel | 0.887 |
| Unit name Terran Command Center | font10 | 0 pixels | 0.907 |
| Unit HP 1500/1500 | font8 | 0 pixels | 0.958 |
| Kills: 0 | font10 | 0 pixels | 0.930 |
| Countdown 7:34 | font16 | 1 pixel | 0.899 |

Spaces use half the font header's maximum width. Runtime-width behavior is also
cross-checked against [BWAPI Font.cpp](https://github.com/bwapi/bwapi/blob/main/bwapi/BWAPI/Source/BW/Font.cpp).
The compact status path differs from the glue/message drawing path; applying one
universal extra-pixel rule was incorrect. These are original glyphs, not a TTF
approximation. Fonts remain isolated from protected installed-font entries.

Selected combat-icon rectangles follow statdata.bin (104,51 and 39-pixel steps,
relative to the 138,388 console origin). Command/research/upgrade indices come
from the decoded original GRP and DAT records. The blue status-icon ramp uses
ticon.pcx's disabled/status ramp. Damage, hits, kills, armor, shield armor and
upgrade levels are read from the selected unit and its actual player's state.

The numeric countdown is centered at x=256 in original 640-pixel coordinates,
with top=0; the resource region begins at x=436. The footage has no “Time remaining”
caption. Android touch gestures are deliberate adaptations, not original mouse
behavior. Automatic briefing scroll timing is reconstructed from transmission
length; manual drag/wheel reading is an addition.


## 0.12: supplied Mission 3 comparison

- User reference: [Kebooooo — Starcraft, Terran Mission 3: Desperate Alliance](https://www.youtube.com/watch?v=8TjEPq0Al2A),
  2009-06-07, 640×480. The page and metadata were accessible on 2026-10-15;
  video downloads and browser playback returned unavailable media/black video.
  Do not characterize this link as watched end to end.
- Supplied screenshots show the pale timer at x256, native gold MENU, minimap
  terrain button, balanced 3+2 selection, bright hotkey initials, scanlines and
  dim inactive briefing portraits. Screenshots are comparison evidence only.
- The original JadedZerg recording above was decoded at native resolution,
  once per second from 23:20 through 25:01 (102 frames), covering the Adjutant
  and both Mengsk transmissions, ending alert, and transition into Mission 3.
  Mengsk's second speech wraps to nine 19-pixel lines; the opening is held for
  about four seconds, then rises ~6–7 pixels/second and ends with about three
  lines visible. The new timing formula reconstructs that behavior while using
  actual speech playback time. This video renders portraits anomalously dark;
  that brightness was not copied. Portrait shading instead follows the supplied
  screenshots and original normal/active frame assets.
- `dlgs/terran.grp` frame atlas: Menu frames 0/1/2 (64×20); terrain 3/4/5
  (64×24); blue group borders reconstructed from frame 12; segmented
  game-dialog buttons 103–108. Zerg/Protoss use their
  corresponding in-game GRPs. Previously these were taken from glue-screen art.
- `glue/readyt/tframe{1,2,3,4}.pcx` and `tframeh{1,2,3,4}.pcx` are the original
  128×118 normal/active monitor frames. SMK content is 60×56, doubled and centered;
  alternate scanline darkening and idle dimming are reconstructed effects.
- Retail Mission 3 CHK has DIM=96×96. Its MBRF transmissions store their WAV
  lengths at +12 and a zero subtraction at +20 (modifier 9). Previously the
  adjustment field was ignored and the modifier mapping was incorrect.
  Source references: [PyMS TRG definitions](https://github.com/poiuyqwert/PyMS/blob/master/PyMS/FileFormats/TRG.py)
  and [scmJS trigger record documentation](https://docs.scmjs.dev/triggers/the-trigger-record/).

The APK and source package contain decoders and renderer code, not extracted
PCX/GRP/FNT/SMK/WAV files, recordings or reference screenshots.

## 0.13: classic HUD and scrolling regressions

- Blizzard's [classic Siege Tank page](https://classic.battle.net/scc/terran/ut.shtml/)
  references [but03.jpg](https://classic.battle.net/images/battle/scc/terran/PICS/but03.jpg),
  downloaded and visually inspected at 640×480. The selected Marine shows armor
  before its weapon, white status icon glyphs within blue frames, lower level
  counters and the 14×14 Terran supply silhouette. This is original low-resolution
  game imagery. The white status ramp is `unit/cmdbtns/ticon.pcx` ramp 5; command
  disabled ramp 4 is no longer reused. Blue frames and their lower number divider
  are reconstructed with the original dialog-frame corners/edges.
- Blizzard's [Brood War final tournament report, game 7](https://classic.battle.net/scc/br/final7.shtml)
  and [s17.jpg](https://classic.battle.net/images/battle/scc/br/pics/final7/s17.jpg)
  were opened/downloaded and inspected. The native 640×480 Dragoon status area
  verifies armor, weapon, then shield ordering. The early beta's differing console
  positions and stats are not treated as a 1.16.1 geometry reference.
- The existing native recording's 20:00 frame contains the speech line
  “What the hell did they do to”. Comparing the FNT masks gives correlation
  0.791 for font10 with one added pixel of letter spacing; font10 without that
  spacing scores 0.258. Consecutive speech baselines are 16 pixels apart.
  Mission text now preserves that spacing. Unit names still use compact spacing.
- Original `game/icons.grp`: frame 0 minerals, 1/2/3 Zerg/Terran/Protoss gas,
  4/5/6 Zerg/Terran/Protoss supply; all are uncompressed 14×14 frames. These
  replace in-world delivery/supply-building sprites in the resource HUD.
- The supplied countdown and native recording use font16. Its original anchor
  at x256 is preserved; a deliberate 1.25× display scale implements the user's
  request for a larger timer. This scale is not claimed as original 1:1 sizing.
- A full Mission 3 playback checks all six speeches, wrapping/scroll position,
  audio synchronization, suspension, manual override expiry and replay. A
  separate run forces all fonts absent and checks visible DOM text movement;
  the previous canvas-only path could not scroll this content. Corrupting the
  imported font8 block verifies that the later imported fonts still load.
- Installed StarDat font payloads in the fixture are not `FONT` data even after
  MPQ decompression. Recovery accepts only structurally plausible FONT headers.
  Readable CD files remain `files/font/font*.fnt`; no encryption keys, original
  fonts or other extracted game content are included in the release.


## 0.14: lifecycle, original frames, and campaign presentation

- User's 2026-10-16 screenshots identify displaced campaign labels, the invented
  green command outline, Android tap tint, and missing idle Start globe.
- Actual classic `rez/glucmpgn.bin`: Load Saved (5) and Load Replay (11) belong
  to `pBotL` (1); Play Custom (10) and Cancel (9) to `pBotR` (3). All contents
  now receive their parent's identical pixel displacement. Registry has the
  equivalent explicit owner mapping, instead of judging each label by its center.
- Actual `rez/glurdyt.bin`: Start uses `start.smk` flags 7 (fade/dark/repeat),
  `proj.smk` flags 0 and `proloop.smk` flags 4. The standalone `starton.smk`
  exists but is not referenced by this original dialog's animation chain; it
  is not substituted for the recorded projector sequence.
- `unit/cmdbtns/tcmdbtns.grp` frame 12 is the original 36×36 status frame with
  the angled number corner; corresponding P/Z frames use the same slot.
  Frames 0/1 are command backplates. This replaces the earlier reconstruction
  from the unrelated small `dlgs/terran.grp` selection frame. `statdata.bin`
  puts status slots at (104,51), (143,51), ... relative to (138,388).
  `statbtnt.bin` puts command buttons at (505,358), (551,358), (597,358), with
  36×34 rectangles and 40-pixel row pitch; exact existing coordinates retained.
- Original `rez/estt01.txt`–`estt03.txt` supply captions, palta scene/font palette
  paths and 5000 ms display durations. `estt0t.txt` supplies the 35000 ms Rebel
  Yell opening page; its unsupported Boot Camp page is not shown as Wasteland.
  The current lower-left text bounds/fades are reconstructed, not measured
  against a new original-executable run.
- `smk/starintr.smk` and `smk/terran1.smk` are 320×308, 15 fps, stereo 16-bit
  22050 Hz. The displayed image stretches horizontally to the original 640×308
  movie area inside a 640×480 black screen. Original early Wasteland green
  interference is in the decoded video itself (cross-checked with FFmpeg).
- All media are read from the player's local CD archive; none are packaged.
  Development fixtures use the same classic archive referenced by the pinned
  browser upstream, outside the source tree. File names continue to use the
  pinned PyMS Listfile metadata cited above. Original libsmacker source and
  LGPL notices are included; the new adapter's source is supplied separately.


## 0.15: command geometry, Start selection and three-race campaign tests

- The user's latest screenshots and requested changes supersede the 0.14 status
  frame choice: armor/weapon blue frames are removed. Group selection frames
  stay. Buildings retain their gameplay armor but omit its detail icon.
- GRP cropped glyph dimensions are centered inside the original 36×34 command
  cells. The previous full-canvas placement retained asymmetric blank padding.
- `glue/readyt/starton.smk` is loaded as a distinct selected state; the old
  projector-only interpretation in 0.14 was insufficient on touch. Its bounds
  are aligned to the normal globe. Selected feedback lasts 160 ms before exit.
- Classic `rez/glurdyz.bin` / `glurdyp.bin`, `glue/palrz` / `palrp`, and each
  race's `glue/ready*` animations provide the new original briefing rooms.
- Classic CHK data supplies Terran 4's player 0, Zerg 1's player 3 and Protoss 1's
  player 7. Terran 4 action 39 moves units; action 42 changes doodad state.
  Zerg 1's win trigger requires a completed Spawning Pool and Hydralisk Den,
  and elimination of the enemy buildings. Protoss 1's starting base is rescuable.
- Installation order behavior was checked against the 1.16.1 reverse-engineering
  source at https://github.com/BoomerangAide/GPTP/blob/master/GPTP/hooks/orders/doodad_orders.cpp
  (inspected 2026-10-16): door collision/elevation changes follow iscript signal
  bit 1; traps reveal/hide through SpecialState animations. The small new OpenBW
  implementations are included in `patches/campaign.patch`.
- Iscript `setspawnframe` direction behavior was checked against the original
  author reference https://pr0nogo.wikidot.com/rs-misc (inspected 2026-10-16).
- Existing pinned PyMS Listfile metadata supplies the new archive filenames;
  original map/music/art/voice bytes remain external local test fixtures.
- Integration tests additionally found that Remove Unit at Location mutated the
  spatial index during an active query. The target list is now collected before
  removal; this fixes the Protoss 1 rescue encounter. Placement for campaign
  teleports ignores reachability from the old room while still checking terrain
  and occupancy; beacons do not block placement on their mission pads.


## 0.17: classic result screens, custom setup and status panel

- Original files: `rez/gluscore.bin`, `rez/glucustm.bin`, `rez/ok.bin`,
  `rez/statdata.bin`; `glue/pal{tv,td,pv,pd,zv,zd}` and matching score directories;
  `glue/create/{plistmap2,pinfo,pslots}.pcx`; command-frame GRP frame 12;
  `rez/stat_txt.tbl` entries 815–826 and 831. Read from private local archives.
- Blizzard's original Overlord guide and its status-panel GIF establish the
  Detector label, blue armor frame and Control Used/Provided/Total/Max display:
  https://classic.battle.net/scc/zerg/units/overlord.shtml
  https://classic.battle.net/images/battle/scc/zerg/pix/units/o01.gif
- Original-engine victory dialog reference (640×480, not Remastered):
  https://github.com/phyous/tsai-sc/releases/download/v0.1.0/victory-screen.png
  It shows the two-line Congratulations message and Victory button above the HUD.
- The user's 20261016_054311 screenshot corrects the earlier icon-color request:
  restore the white/gray status palette and original blue border/level inset.
- Health-number thresholds follow the original-compatible renderer's 66/33
  health-bar thresholds. Touch preview/confirmation is an Android accommodation.
- Score-screen layout/art come from the original data. Tab/count transitions and
  touch file browsing are host implementations, not a claim of full retail parity.


## 0.18: portrait idles, rescue feedback and the next missions

- Original `arr/portdata.dat` (110 rows × 12 bytes) contains four idle weights
  after the idle/talking filename tables. Actual SCV weights are 87/5/5/3;
  common portraits use 85/5/5/5; Dropship uses 90/5/0/5. These data select
  `Fid00`–`Fid03`, without altering animation playback speed.
- NimoStar's original StarCraft 1.16.1 reverse-engineering notes describe the
  four probability tables and selector at 0x44EB90:
  https://staredit.net/topic/18925/ (inspected 2026-10-16).
- The user's rescue-flash observation and original `tselect.pcx` yellow ramp
  guide the temporary selection circle. Its 60-frame duration and 6-frame
  blink cadence are reconstructed; no frame-exact timing claim is made.
- Privately inspected original CHK/TRIG/MBRF/MRGN and `aiscript.bin` data for
  Terran 5 (Revolution), Zerg 2 (Egression), and Protoss 2 (Into the Flames)
  define the player slots, objective events, voices, rescue AI, Chrysalis
  delivery and timed Fenix reinforcements. Imported `estt05`, `estz02` and
  `estp02` text/art provide the mission openings.
- Existing classic result art and layouts are unchanged by the new offline
  Test Victory shortcut; it invokes the same tested original-message flow.

## 0.19 — production, selection frames and portrait compositing

- Privately decoded classic `rez/statdata.bin`: production slots are (104,14),
  (104,53), (143,53), (182,53), (221,53), each 39×36 relative to (138,388).
  Progress control 7 is (144,39,107,9); incomplete-unit control 13 is
  (125,39,107,9), with label -30. Group tiles use 33×34 controls.
- Original `unit/cmdbtns/{t,z,p}cmdbtns.grp`: queue border frames 2/4,
  empty-number frames 6–10, connector 11; normal group frame 13, hero 19,
  parasite 25 and hallucination 31. `dlgs/*.grp` frame 12, previously enlarged
  here, is a 16×16 dialog control rather than the correct group-unit frame.
- GPTP's independent StarCraft 1.16.1 reverse-engineering was inspected to
  cross-check control selection and damage boundaries (2026-10-16):
  https://github.com/BoomerangAide/GPTP/blob/master/GPTP/hooks/interface/status_display/unit_stat_selection.cpp
  https://github.com/BoomerangAide/GPTP/blob/master/GPTP/hooks/interface/status_display/advanced/status_buildmorphtrain.cpp
  https://github.com/BoomerangAide/GPTP/blob/master/GPTP/hooks/interface/status_display/advanced/status_base_text.cpp
  https://github.com/BoomerangAide/GPTP/blob/master/GPTP/SCBW/scbwdata.h
  No GPTP source or proprietary asset bytes are included in this release.
- The original shield/HP string has no player-blue prefix: shields retain the
  default cyan and HP alone receives the green/yellow/red code. Integer HP
  percent is red below 33, yellow through 66, then green.
- Original console PCXs use palette index 138 in the portrait opening. Cutting
  only those pixels inside the 60×56 monitor preserves the irregular frame;
  merely moving an unmasked opaque console in front would hide the portrait.
- Original Zerg 2 `Zer2` bytecode at 15974 starts campaign/town, disables the
  default opening, requests Nexus 1, Probe 4 (priority 130), Gateway 2,
  Cybernetics Core 1 and Stargate 1. It funds a deliberately small workforce.
  Private bytecode and campaign maps remain outside the release.


## 0.20: mobile view, touch and morph completion

- Blizzard's original Zergling and Spawning Pool pages distinguish Metabolic
  Boost (movement) from Adrenal Glands (attack):
  https://classic.battle.net/scc/zerg/units/zergling.shtml
  https://classic.battle.net/scc/zerg/popup/pool.htm
  Original Metabolic Boost button reference:
  https://classic.battle.net/images/battle/scc/zerg/pix/upgrades/mboost.gif
- `bwgame.h::unit_can_upgrade` already requires a completed Hive for Adrenal
  Glands and permits Metabolic Boost without one. Tests issue both upgrade
  requests against the original Zerg 2 mission without a Hive.
- Command icons use ticon ramps 0 (normal), 1 (disabled) and 2 (active),
  correcting the earlier use of ramps 3/4/5. Status-detail icons keep ramp 5.
  The original Metabolic Boost reference has 83 RGB(252,204,44) foreground pixels
  and 73 RGB(52,32,12) pixels; both counts now match the decoded game icon.
- Widescreen and zoom-out are optional port features, not retail behavior.
  All three original console PCXs supply the extension strip; no generated
  replacement race art is used. Title/briefing geometry stays 640×480.
- Completed Zerg morphs reuse the original unit ID. The ready-voice cache now
  remembers unit type too. The imported original Hydralisk ready WAV is decoded
  and played by the existing engine audio bridge; no replacement audio is used.


## 0.21: command cards, transmission timing, and original dialogs

- Original CHK records from Protoss 2: the first Aldaris WAV is approximately
  13.08 seconds; its Transmission action subtracts 1000 ms. The previous host
  stopped the recording at 12.08 s. The host now preserves the complete voice.
- Terran 5's Raynor/Kerrigan Transmission actions store editor WAV length in
  `time_n` and Add(0) in `group2_n`/modifier. Treating `time_n` as the adjustment
  doubled each wait. The engine now uses the actual adjustment and voice length.
- Original 1.16.1 status-panel reverse engineering:
  https://github.com/BoomerangAide/GPTP/blob/master/GPTP/hooks/interface/status_display/stats_panel_display.cpp
  confirms armor, shields, ground/air weapon, then hangar count order.
  https://github.com/BoomerangAide/GPTP/blob/master/GPTP/hooks/interface/status_display/panels/panels_generators.cpp
  confirms Reavers use inside count, Carriers inside + outside, and frame 12.
- PyMS dialog definitions and renderer:
  https://github.com/poiuyqwert/PyMS/blob/master/PyMS/FileFormats/DialogBIN.py
  https://github.com/poiuyqwert/PyMS/blob/master/PyMS/PyBIN/WidgetNode.py
  distinguish left/center label types, font flags, and the disabled/normal/pressed
  groups of three button frames. Centered game buttons use 112–120.
- Original `rez/gluscore.bin`: title control 2 is centered, font16x, (16,18,204,24);
  total-score heading 8 uses font16x; elapsed-time control 9 uses font16 at y438.
  No Remastered assets or fonts are used.
- `rez/glurdyp.bin`: Glow is flags 7 (fade/dark/repeat), Ring is flags 4 (repeat).
  The Android compositor keeps the glow's dark matte from covering the room.
- Wide layout, stepped glue transitions and touch confirmation are host
  adaptations. Their precise timing/compositing still needs phone comparison;
  this update does not claim pixel-perfect parity for every classic screen.

The original Psi Field iscript (333) overlays images 586/585/587 at signed
byte offsets (-126,-77), (126,77), (-126,77), then positions image 584 at
(126,-77). `imgol`/`imgul` now decode signed coordinates; unsigned decoding
placed the left quadrants on the right and the upper overlay below the center.
The renderer retains the original GRPs and tileset translucency table.

Original-grid corroboration: the author's 2003 QWE/ASD/ZXC hotkey conversion
(https://groups.google.com/g/alt.games.starcraft/c/GAIZFahTXbg) places the Forge
upgrades at 0/1/2, Armory weapons at 0/1 and plating at 3/4, Science Facility
energy at 2, Covert Ops upgrades at 3/4, Overlord upgrades at 3/4/5, Observer
speed/sight at 0/1, and Carrier capacity at 2. This is historical corroboration,
not an exhaustive executable button-table extraction.


## 0.22: production, campaign catalog, import flow and audio

- The user's supplied classic screenshots guide Egg target display, refinery
  HP/gas, Chrysalis detail removal, and the blue options presentation. The
  controls and smooth 560/320 ms ease-out transitions are Android adaptations.
- Original `arr/sfxdata.dat` and `rez/sfxdata.tbl` resolve sound IDs 4/5/6 to
  Zerg/Terran/Protoss building placement, 21 to `Misc\youwin.wav`, 22 to
  `Misc\youlose.wav`, and 32/33/34 to the race rescue cues. Audio is imported
  from the user's archives, never synthesized or bundled.
- The independently inspected StarCraft 1.16.1 status routines distinguish
  resource amounts from health, suppress invincible-unit HP, and omit armor on
  powerups: https://github.com/BoomerangAide/GPTP/tree/master/GPTP/hooks/interface/status_display
- Original `rez/glugamemode.bin` provides the Original/Expansion dialog;
  `rez/gluexpcmpgn.bin` and `glue/expcampaign/*` provide expansion campaign art.
  Original `mapdata.dat`, story text and the pinned PyMS Listfile identify the
  full catalog, including internal base Terran numbering, both T5 branches,
  six Z4 branches and Dark Origin. No map or original media bytes are included.
- Pinned PyMS `AIBIN.py` documents 16-byte aiscript entries versus 8-byte
  bwscript entries. `TRG.py` documents Exactly=10 and action operands:
  https://github.com/poiuyqwert/PyMS/blob/bfc5d3aad0b5614a5aff72c223f8efa00afddfa4/PyMS/FileFormats/AIBIN.py
  https://github.com/poiuyqwert/PyMS/blob/bfc5d3aad0b5614a5aff72c223f8efa00afddfa4/PyMS/FileFormats/TRG.py
- Private CHK records establish ground-height exclusions at bits 1/2/4 and air
  exclusions at 8/16/32, T7's legacy zero-count Create Unit entrance, T4's
  building-move intro, and the original next-scenario branch strings. T4's six
  silo destinations intentionally overlap their DAT collision boxes; this port
  consequently places grounded structures at the requested trigger center. Startup
  zero-unit armies are valid while their intro is creating the opening force.
- GPTP's independently authored move helper is used as a structural reference
  for refreshing spatial data around campaign teleports:
  https://github.com/BoomerangAide/GPTP/blob/master/GPTP/SCBW/api.cpp
  This port does not claim complete retail trigger/AI parity.

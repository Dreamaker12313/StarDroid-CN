# StarDroid 1.1 original menu hotkeys and help formatting

Version 1.1 / Android code 83 and simulation compatibility 84 remain unchanged.

- Main-menu and dialog labels retain the imported BIN's original highlighted letters, color resets and secondary-line colors. Replacement captions and translations preserve a mnemonic only when that letter survives; explicit replacement hotkeys take precedence. Disabled captions stay disabled, and clipped-away keys are not moved to a different letter. Original-font checks cover 225 actual BIN captions across nine menus and five languages: 1,181 checks and 900 renders. [Menu highlights](validation/menu-hotkeys11.json).
- Visible, enabled menu buttons accept their highlighted keyboard key. Typing, modifiers, held repeats, transitions, disabled buttons, ambiguous matches and stale page/dialog bindings are guarded. Command-grid modes remain separate from menu shortcuts. All 1,377 production Java routing checks pass. [Input routing](validation/desktop-input11.json).
- Combined help uses bold bitmap **Mouse:** and **Keyboard:** headings with a blank line between sections. All five translations fit: 266 text checks, 4,800 panel checks, 10 text renders and 90 complete settings renders. [Guide layout](validation/desktop-guide11.json).
- Packaging reuses the verified, unchanged native libraries. Signed-APK checks cover the original update identity, unchanged assets/permissions, both ABIs, 47 JNI methods and 16 KiB alignment. [Package proof](validation/package-guide-format11.json).

These are host-rendering/input and Android build checks. Physical Android hardware remains untested. Earlier reports below refer to their recorded source revisions.

# StarDroid 1.1 hotkey settings and highlighted command keys

Public version 1.1 / Android code 83 and simulation compatibility 84 remain unchanged.

- Original and QWE/ASD/ZXC grid bindings use the live displayed command layout. Grid input dispatches the exact command identity and validates it again natively, preserving Shift queues and rejecting stale/invalid commands; it never falls through to an unrelated original letter. A zero-step input flush handles rapid submenu changes. Original Shield Battery Recharge Shields is corrected from B to R after checking imported command text. Native validation passes 4,249 checks across 230 command cards and 1,074 identities, plus 125 desktop/replay regression checks. [Native command checks](validation/hotkeys-native11.json).
- Production Java routing, settings defaults/persistence and camera options pass 1,017 checks, including caps/foreign layouts, held keys, text entry, all grid positions, immediate menu-close input, fresh command lookup, replay guards and in-game-only settings access. Existing gamepad checks pass 4,173 cases. [Java input/settings](validation/desktop-input11.json), [gamepad regression](validation/gamepad-v81.json).
- Command headings append the active key in normal brackets with a yellow letter. Checks cover original and grid modes, all races, five UI languages, disabled/synthetic Cancel/More commands, original and fallback fonts, and unchanged resource icons. Hotkey validation passes 13,874 checks with 130 original/fallback-font renders. Hover and command errors still coexist, with 12,974 regression checks. [Hotkey rendering](validation/hotkey-tooltips11.json), [error/hover regression](validation/hover-errors11.json).
- One Mouse & keyboard settings panel contains both help sections, hotkey choice, four camera/zoom toggles and a camera-speed slider. Arrow keys appear only in Keyboard help. Mouse/keyboard and gamepad settings are available only through the in-game Controls menu. Actual panel/button/body callbacks pass 4,680 checks across 90 renders; 266 text checks verify all five languages fit. [Settings layout](validation/desktop-guide11.json).
- Both Android ABIs are rebuilt, with separate signed-package checks for version, original update certificate, JNI exports, 16 KiB alignment, permissions and asset contents. [Native build](validation/native-build-hotkeys11.json), [signed APK](validation/package-hotkeys11.json).

These are host/native simulation, rendering, Android API/build and lint checks. Physical Android USB/Bluetooth input and phone installation remain unverified. Earlier reports below refer to their own source revisions.

# StarDroid 1.1 mouse and keyboard controls

Public version 1.1 / Android code 83 and simulation compatibility 84 remain unchanged.

- Physical mouse input has independent left-selection/box-drag, double-click and Ctrl-click selection, context-sensitive right orders, Shift queues, minimap interaction, wheel zoom/list scrolling and middle/edge camera movement. Hardware keyboard input uses physical command keys, held modifiers, arrow-camera movement and assign/append/recall control groups. [Input policy](validation/desktop-policy11.json) covers 260 assertions and actual Android SDK35 compilation.
- Production Android event-routing tests cover 273 assertions, including duplicate Android mouse edges, held releases, foreign-layout hotkeys, HUD/menu isolation, text-dialog mouse buttons, focus/device cleanup, transitions, widescreen/zoom/letterbox transforms, and the Activity handoff. Existing touch/gamepad checks remain passing. [Routing](validation/desktop-input11.json), [gamepad/settings regression](validation/gamepad-v81.json).
- Native engine tests cover 125 assertions, including same-frame modifier snapshots, queued commands, group assignment/append/recall, selection and cancellation, multiplayer input validation, and a deterministic replay roundtrip. Paused replays permit inspection without accepting gameplay commands; checkpoint rewind retains that behavior. Ordinary paused games stay blocked. [Native input](validation/desktop-native-1.1.json).
- The original-style Controls/App Options guide is translated into all five UI languages. Guide checks explicitly load the original font metadata: 265 body checks and 2,270 complete-panel checks cover 110 settings renders. [Guide layout](validation/desktop-guide11.json).
- Both Android ABIs are rebuilt from the changed native sources. Signed APK checks verify the original update identity, 47 JNI exports, 16 KiB alignment, unchanged permissions and intended assets only. Lint reports zero errors and 13 warnings. [Native build](validation/native-build-desktop11.json), [package](validation/package-desktop11.json).

These are host event/simulation/rendering checks and Android SDK/build checks. Physical USB/Bluetooth peripherals, phone installation and Android OS event delivery have not been tested. Historical reports below remain tied to their recorded sources; some older artwork fixtures omitted font.gid and therefore exercised the styled fallback font. The new guide fixture verifies original-font loading explicitly.

# StarDroid 1.1 sound controls and simultaneous feedback

Version 1.1 / Android code 83 and simulation compatibility 84 remain unchanged.

- The redundant music-enable toggle is removed. Production preference tests cover fresh defaults, old on/off settings, persistent one-time migration, reopening, actual slider changes, mute/gains/ducking/focus and end-of-track recovery from volume 0. Next track and all-race soundtrack/seek coverage remain intact. [Music volume](validation/music-volume11.json).
- Production hover/held-hint dispatch and HUD rendering show descriptions together with command errors or target prompts. Tests cover race palettes, 640/960 layouts, enlarged description/command sizes, five UI languages, multiline messages, expiry, disabled tooltips and modal guards. Status pixels remain intact and normal tooltip placement is unchanged when no status is present. [Hover/error rendering](validation/hover-errors11.json).
- Signed APK checks reuse the exact verified native libraries from the prior score revision because native sources are unchanged. Signature, JNI exports, 16 KiB alignment, permissions, assets and Android lint are checked again. [Package proof](validation/package-sound-hover11.json).

These are host/rendering/audio and Android build checks; physical-phone installation, touch and listening were not tested. Earlier reports below refer to their own recorded source versions.

# StarDroid 1.1 score, replay-menu and music revision

Version 1.1 / Android code 83 and simulation compatibility 84 remain unchanged.

- All 64 original campaign maps were audited independently: 208 participant slots and 99 neutral/rescue helpers. Native score queries match the original human/computer roster, retain zero-score and defeated/left participants, omit helpers after controller changes, preserve distinct same-faction opponents and survive save/load. Queries leave simulation state/RNG unchanged. [Map audit](validation/score-roster-audit11.json), [native roster checks](validation/score-slots11.json).
- Score names use complete original faction strings and adaptive bitmap font sizes within the name column. Pixel/layout checks cover all campaign force names, the five reported mission rosters, all race/victory backgrounds, tabs, supported UI languages, localized data and eight-player rows. [Score layout](validation/score-layout11.json).
- Replay buttons use transparent interiors and original menu font/color/size. Original OK/Cancel rendering is retained; Delete is title case and centered at the bottom. Pixel/input checks cover both menu layouts, five languages, enabled/disabled/hover states, list/thumbnail/scrollbar, confirmations and replay controls. [Replay menu](validation/replay-buttons11-ui.json).
- Next track invokes the actual settings-button callback and skips each of the four Brood War themes. A reproduced 32-bit overflow in native music seeking is fixed before multiplication. Exact JNI seek/position functions and PCM samples are checked at all three real embedded-theme boundaries. Automatic EOF, rapid presses, missing assets, phase/mute guards, all 18 music imports/decodes and SDK compilation also pass. [Music checks](validation/music-next11.json).
- Both Android ABIs and the signed update APK have separate source-bound proofs: [native build](validation/native-build-score-polish11.json), [package](validation/package-score-polish11.json).

These checks use original data, host simulation/rendering/audio and Android build tools. Physical-device listening/touch and original-executable score-screen parity were not tested. Historical reports below remain tied to their recorded sources.

# StarDroid 1.1 sound and replay-message revision

Version 1.1 / Android code 83 and simulation compatibility 84 remain unchanged.

- Hero Mode audio: actual training and rebuilding of all 18 heroes, hero Archon completion, Duke siege transitions and saved announcement state, unchanged selection/order/campaign voices, and no simulation checksum or RNG changes. [Hero sound report](validation/hero-rescue-1.1.json).
- Brood War music: all 18 supplied race WAVs survive production import byte-for-byte and decode/play to their ends. Each expansion first track includes the matching original theme, verified for all three races. Automatic selection and game-entry routing cover campaign, custom, nearby, replay and saved games. Manual controls/overrides are removed, and Android SDK compilation passes. [Music report](validation/music11.json).
- Replay mismatch errors use the requested wording for both older and future rule versions while retaining current-format acceptance and safe rejection. [Native guard report](validation/hero-rescue11-compat-native.json), [nearby guard report](validation/hero-rescue11-compat-nearby.json).
- Both ABI rebuilds and signed APK packaging are recorded separately: [native proof](validation/native-build-hero-rescue11.json), [package proof](validation/package-hero-rescue11.json).

These are host/data and build checks; physical-device listening and touch testing were not performed. Older reports below remain tied to their recorded sources.

# StarDroid 1.1 campaign, storage and wireframe revision

Public version remains 1.1 / Android code 83; simulation compatibility is 84.

- Original-data resource and crystal tests cover map/trigger initialization, real attacks, mutalisk bounce, splash, explicit protection toggles and mining by every worker race: [report](validation/map-invincibility11.json).
- Original Dylarian Shipyards garrisons change from zero occupants to 45 troops across 12 bunkers. Region, capacity, replacement, attack-wave, transport and save-continuation checks: [report](validation/bunker-ai11.json).
- Nuclear production, silo readiness, original reward triggers, ownership transfer and Ghost firing are covered in [nuclear checks](validation/nukes11.json). The test respects original costs, supply and training time; it is not a full mission playthrough.
- Beacon input covers all six types, three owners, workers/combat units/civilians, explicit selection/targeting, queues, fog and replay guards: [report](validation/beacon-1.1.json).
- Wireframe tests inspect all 228 single, 131 group and 106 transport frames, compare pixels against imported GRP/remap data, and exercise live selection and damage redraws: [report](validation/wireframes11.json). Host contact sheets were inspected; exact original damage thresholds remain an approximation.
- All 64 campaign force-name mappings and rescue-sound references were inspected. Native/Java score-name and rescue tests use the original archives: [score names](validation/score-names11.json), [rescue sounds](validation/rescue-sound-1.1.json).
- SD migration tests cover verified copies, internal-only personal files, failure/retry paths, process-wide operation ownership and preserved resume behavior: [report](validation/data-storage11.json). They use real host files and Android API compilation, not physical removable media.
- Replay and nearby compatibility guards reject different simulation rules without replacing the current world: [native](validation/compat11-native.json), [nearby](validation/compat11-nearby.json). Combined linear/seek parity is recorded separately in [replay regression](validation/replay-campaign11.json).

- Both Android ABIs were rebuilt from the frozen patch stack. Signed APK checks verify the original update certificate, all 47 JNI exports, unchanged permissions, 16 KiB alignment and only the intended translation-asset changes. Lint reports zero errors and 13 warnings. See [native build](validation/native-build-campaign11.json) and [package proof](validation/package-campaign11.json).

Physical Android installation, removable-card interruption/remount, touch/controller use and radio interoperability remain unverified. Earlier validation records below remain historical and refer to their own recorded sources.

# StarDroid 1.0.8 validation (build 78)

Current reports: [map imports](validation/maps-v78.json), [native AI and larva input](validation/native-v78.json), [languages](validation/languages-v78.json), [speech/preferences](validation/presentation-v78.json), [saves](validation/saves-v78.json), [protocol](validation/protocol-v78.json) and [APK](validation/package-v78.json).

- 2,501 distinct map scenarios imported and reimported with a 128 MiB Java heap; 5,111 assertions cover sorting, deduplication, progress, corrupt entries, safe paths, count/size bounds and temporary-file cleanup.
- Dropships, Shuttles and upgraded Overlords each deliver nine attackers across real disconnected terrain in campaign and melee modes, including repeat trips, capacity, upgrade gating, destroyed-carrier cleanup and deterministic save/restore. The Shuttle case also exercises scripted attacks without a production town. A ferried SCV resumes Command Center construction.
- The original Zerg 4 mission advances 18,000 frames: 31 ground units observed loading, 21 unloading, no AI interpreter error. Ship losses and combat occur normally; this is not a full playthrough.
- All 64 campaign maps load and advance 48 frames. Transport requests for 144 computer-player slots respect each mission's unit and upgrade restrictions.
- Larva checks cover single/group morphs, rapid and spaced presses, remaining-larva buttons, queued-input saves, insufficient minerals, two Zerglings per larva and unchanged Hydralisk group morphs.
- 488 English-data and 491 Russian-data language assertions cover all five choices, Cyrillic/accent glyphs, original fonts and label bounds. 17 speech/preferences and 1,430 nearby protocol assertions pass.
- Schema 4 saves round-trip in memory and across processes, preserve airlifts, read schemas 1–3 and reject corrupt or mismatched saves. Previously removed external-bot saves remain unsupported.
- Release assembly/lint, original signing identity, JNI exports, both ABIs, unchanged permissions and 16 KiB ELF/APK alignment are checked by `tests/check_revision78_package.py`.

Physical Android installation, touch/audio/cutout behavior and Bluetooth/Wi-Fi Direct radio testing remain pending. These are bounded regression scenarios, not 64 full playthroughs. Original game archives remain external.

The following sections describe historical builds and their recorded sources.

# StarDroid 1.0.7 validation (build 77)

Reports: [native gameplay](validation/native-v77.json), [archive decoding](validation/archive-v77.json), [languages](validation/languages-v77.json), [speech and preferences](validation/presentation-v77.json), [protocol](validation/protocol-v77.json), [fonts](validation/encrypted-fonts-v1.0.7.json), [menu regression](validation/menu-recovery-v1.0.7.json), [imports](validation/menu-import-v1.0.7.json), and [APK](validation/package-v77.json).

- Actual English Reign of Fire: 6,500 simulated frames, original mission SCV carrying the psi emitter, and the reported `Z2M20RAY.wav` line with concurrent effects. All 18 worker/object combinations cover pickup, following, save/load, death/drop and reacquisition. Neutral and guard ownership plus resource/double-carry exclusions pass.
- Hatchery, Lair and Hive select only connected larvae, at most three; empty buildings and the opt-out global selection pass. Preference migration defaults on and saves explicit off.
- Native sound pool tests protect unit speech and mission speech from effects. Production Java presentation passes 17 checks covering queued transmissions, save restoration, fast-speed subtitle lifetime and briefing completion. These are mixer/state tests, not listening tests on a phone.
- Supplied Russian StarCraft normal import: 31 maps, story/audio and campaign artwork. Imported first mission runs 1,200 native frames, renders and round-trips its save exactly. Russian BroodWar campaign archive was unavailable; Russian BrooDat core data was tested.
- 110 synthetic raw/encrypted sector checks include zero/word/multi-sector boundaries, padded tails, compression-size collisions and false-positive protection. Actual Russian orders data and the formerly damaged platform explosion palette decode byte-identically to the English assets.
- 387 English-data and 486 Russian-data language checks cover detection, CP1251/CP1252, imported fonts, Cyrillic and accented glyphs, five language choices and translated original dialog bounds. The FONT transparent-run pixel regression passes. Rendered menu/label previews were visually inspected using a desktop Canvas shim; animated Smacker layers are omitted.
- 1,854 encrypted-font checks retain the StarDat font fix. This run did not supply an independent reference; the independent byte comparison from build 76 remains historical evidence. Menu regression passes 3,686 font checks, 41 asset checks and 13 fallback label/action checks. Import regression passes 33 checks.
- 1,430 protocol assertions pass, including incompatible-build rejection, data/map checksums, ordering, delays, pauses and disconnect behavior. Build 77 is required on every multiplayer device.
- Final release assembly and lint pass (0 errors, 10 warnings). Original signing certificate, application ID, version 1.0.7/code 77, API 26/35, all 40 JNI methods and 16 KiB APK/ELF alignment verified. Both ABI libraries match the APK; all existing bundled assets remain unchanged and only the translation table is added. Smacker source is unchanged and was rebuilt.
- No new original fonts, game archives, installation metadata or signing keys are bundled. Credits diagnostics and Copy remain; menu repair/report UI remains removed.
- Physical Android installation, touch controls, cutout behavior, listening tests and multiplayer radios were not tested. No full campaign playthrough is claimed. Historical device/runtime evidence below is not a new build-77 test.

# Historical validation: StarDroid 1.0.6 (original encrypted fonts, build 76)

Reports: [encrypted original fonts](validation/encrypted-fonts-v1.0.6.json), [menu/font regression](validation/menu-recovery-v1.0.6.json), [import handoff](validation/menu-import-v1.0.6.json), and [APK checks](validation/menu-package-v1.0.6.json).

- The tester's actual StarDat.mpq contains all eight original fonts at their normal names. Their installer encryption caused the old FONT decoder to reject them. The supplied StarCraft.mpq contains campaign artwork and no entries at the 16 supported font paths.
- Reproduced 1.0.5 falling back for all five menu font slots on these same archives. The new decoder passes 1,717 checks and matches an independent decoding of all eight fonts byte for byte. Exact original fonts are selected by the production menu renderer; malformed metadata/envelopes retain the readable fallback.
- The actual StarCraft.mpq passes the production import path: 31 maps and campaign artwork. The imported sparse MPQ feeds the native decoder and both campaign menus without a missing-font warning. BroodWar.mpq did not transfer and was not tested.
- 3,686 font checks, 41 asset checks, 13 fallback label/action checks and 33 synthetic import checks pass. Original-font substitutes, no-font fallback, partial imports and safe replacements remain covered. Credits invokes the original Diagnostics / credits screen.
- Extra menu reports, font inventories and repair banners are removed. General diagnostics, credits, Copy and network diagnostics remain. Existing imports load the fix automatically; ordinary future imports do too. No repair button.
- Host font renders inspected. These use the real bitmap fonts but an AWT Canvas shim and omit animated Smacker layers. No physical Android device test was performed.
- Release assembly and lint pass (0 errors, 10 existing warnings). Version 1.0.6/code 76, the original signing certificate and 16 KiB APK alignment verified. All 76 native-library and asset entries match 1.0.5 byte for byte; no original fonts, game archives or installation metadata are distributed.

# Historical validation: StarDroid 1.0.5 (font recovery, build 75)

Reports: [menu/font regression](validation/menu-recovery-v1.0.5.json), [import handoff](validation/menu-import-v1.0.5.json), and [APK checks](validation/menu-package-v1.0.5.json).

- Original fonts are preferred across all installed archive sources and both known font paths. Missing sizes reuse the closest readable original size, including optional font12/32/50, before using the installed Android font.
- 3,686 font checks, 41 asset checks and 13 fallback action/label checks pass. Coverage includes exact-font preference, imported and optional original-size substitutes, colors, cached glyph metrics, accents, wrapping and real dialog bounds.
- 33 production import checks pass. Palette-only normal imports are decoded through the real sparse MPQ/native reader and both menu classes retain artwork, render styled system fonts and omit artwork-repair warnings. Complete/partial original-font imports also pass.
- Before/after host previews inspected. Android sans-serif is represented by desktop sans-serif in the AWT shim; this is not an exact Samsung render.
- Release assembly and lint pass (0 errors, 10 existing warnings). Version 1.0.5/code 75, original release certificate and 16 KiB alignment verified. All 76 native-library/asset entries unchanged from 1.0.4.
- No reimport required for existing installations. Ordinary imports continue to reload the same font selection; no repair button added.
- The tester's actual archive was not supplied. Its report confirms no expected font entries in StarCraft.mpq but was generated before menu loading. No physical-device test was performed.

# Historical validation: StarDroid 1.0.4 (partial interface imports, build 74)

Reports: [partial import regression](validation/menu-import-v1.0.4.json), [menu recovery](validation/menu-recovery-v1.0.4.json), and [APK checks](validation/menu-package-v1.0.4.json).

- The supplied 1.0.3 diagnostic report confirms the incomplete-font validation error and a missing interface bundle. It does not name the missing font.
- 32 production import checks pass: full and partial imports, 31 maps, full-size PCX, missing unused font, missing menu font, palette-only imports, exact missing-file reporting, existing-file protection and fingerprints.
- Reproduced the 1.0.3 validator rejecting a valid background and all five menu fonts when font50 was absent. Baseline Java sources match hashes in the recorded 1.0.3 build manifest. The fixture is synthetic; it does not establish which font is absent from the tester's archive.
- Partial import, sparse MPQ reconstruction, native decoder and both campaign menu classes verified together. Both menus select the imported palette and all five menu fonts with no fallback despite absent font50.
- 33 asset regression checks and 13 fallback labels/actions pass using real external core archives and fault injection.
- Release assembly and lint pass (0 errors, 10 existing warnings). Original release signature, version 1.0.4/code 74, minimum API 26/target API 35 and 16 KiB alignment verified. All 76 native-library and asset entries unchanged from the intact 1.0.2 baseline; no native changes in 1.0.3 or this update.
- No physical-device test was performed. The tester's actual StarCraft.mpq has not been supplied. Fonts genuinely absent from the archive will still need a complete source; the fix retains available artwork and reports missing entries.

# Historical validation: StarDroid 1.0.3 (menu import and reports, build 73)

Reports: [import regression](validation/menu-import-v1.0.3.json), [menu recovery](validation/menu-recovery-v1.0.3.json), and [APK checks](validation/menu-package-v1.0.3.json).

- Reproduced 1.0.2 rejecting a valid 308,097-byte campaign background at its 256 KiB limit.
- Normal fresh import and reimport tested with 31 base maps, embedded Install.exe MPQ, alternate font paths, bounded oversize rejection, safe failed replacement and SHA-256 report output.
- End-to-end interface handoff: import, sparse MPQ reconstruction, native decoding and both campaign layouts using the restored palette and all five original-font slots. Synthetic assets exercise the interfaces without distributing game data.
- 33 asset checks and 13 fallback button labels/actions pass with real external core assets. Proportional fallback text and exact loaded/missing source reporting checked. Host Canvas renders inspected.
- Signed release assembly and lint pass (0 errors, 10 existing warnings). Application ID, version 1.0.3/code 73, original release certificate, minimum API 26/target API 35 and 16 KiB alignment verified.
- All 76 native-library and bundled-asset entries unchanged from 1.0.2; native engine not rebuilt.
- Physical Android installation, import picker, share/save UI and touch interaction remain untested. The affected tester's actual archive was not supplied. Their screenshot identifies palcs/backgnd.pcx as unavailable but does not identify the underlying archive version or confirm the size-limit cause on that device.

# Historical validation: StarDroid 1.0.2 (menu recovery, build 72)

Reports: [menu recovery](validation/menu-recovery-v1.0.2.json) and [APK checks](validation/menu-package-v1.0.2.json).

- Reproduced the old campaign-menu exception with real classic core archives missing the campaign palette.
- 30 asset checks pass, including missing palettes, bad patch entries, decoder exceptions, valid imported fonts, raw PCX and malformed bounds. All 13 main/campaign fallback labels and actions are checked using production rendering call sites.
- Interface metadata tests distinguish a font-only bundle from a bundle containing campaign artwork, and retain incomplete-font rejection.
- Main and campaign screens were rendered with the real NativeArt/NativeGlue code through an AWT Canvas shim and inspected. This is not an Android device render.
- Release assembly and lint pass: 0 errors, 10 existing warnings.
- APK version 1.0.2/code 72, application ID org.openbw.androidtest, minimum API 26 and target API 35 verified.
- Original release signing certificate and 16 KiB native-library ZIP alignment verified.
- All 76 native-library and asset entries match the supplied 1.0.1 source package byte for byte.
- No physical device test was performed. The affected person's actual archives and diagnostic report were not provided, so the exact failing file on that device remains unconfirmed.

# Historical validation: StarDroid 1.0.1 (minimap default, build 71)

Report: [minimap-default-v1.0.1.json](validation/minimap-default-v1.0.1.json).

- 14 focused preference assertions pass using the production ControlSettings class:
  fresh and missing settings, all three presets, saved true/false values,
  save/load round trips, and malformed-preference fallback.
- Release assembly and Android lint pass: 0 errors and 10 warnings.
- The signed APK has application ID `org.openbw.androidtest`, version 1.0.1,
  version code 71, minimum SDK 26, and target SDK 35.
- APK signature verification passes with the same signing certificate as version
  1.0. ZIP alignment checks pass, including 16 KiB native-library alignment.
- All 76 native-library and asset entries match version 1.0 byte for byte.
  Only the Java default and app version change; explicit saved choices remain intact.
- Physical-device installation and touch testing were not performed for this update.
  Earlier device/runtime evidence below remains historical, not a new test run.

# Historical validation: StarDroid 1.0 (placement scroll preference, build 70)

> Publication note: references below to paused GitHub publication record earlier development decisions. Current download information is in [the release notes](docs/RELEASE-1.0.1.md). Testing limitations remain as recorded.

Current reports: `placement-scroll-v1.0.json` and
`placement-package-v1.0.json`. Build 69 snapshots are preserved in
`NATIVE-BUILD.json`; its native memory report retains its original build number.

- 178,077 Java camera checks include activation 28, 36 and 47 logical pixels
  from the top/left/right, no activation outside the 48-pixel band, and the
  retained bottom threshold. Timing, equal directional speeds, diagonals,
  zoom/speed, 30–144 Hz, irregular frames and subpixel drag checks still pass.
- 13,116 touch/layout checks cover new/old-install defaults, persistence of both
  setting states, preservation of unrelated preferences, immediate stopping,
  re-enabling, retained ordinary/selection/target panning, Build confirmation,
  and menu bounds. All three race menu renders were inspected; the new label
  and rows fit without overlap. Existing placement-button tests include 1,728
  edge/zoom/control positions.
- This update changes Java input/settings only. All 76 native-library and asset
  entries match build 69 byte for byte, retaining the tested placement/selection
  buffer fix. Its guarded-buffer/AddressSanitizer results are retained evidence,
  not relabeled as a new native run.
- Signed release assembly and lint pass (0 errors, 10 warnings); version remains
  1.0, code 70. The package/signing identity supports updating build 69 in place.
  The 38 JNI methods and 16 KiB alignment checks pass.
- Physical-device touch/display confirmation remains pending. GitHub publication
  remains paused.

# Historical validation: placement scrolling, build 69

Current reports: `placement-scroll-v1.0.json`, `native-placement-v1.0.json`,
and `placement-package-v1.0.json`. Build 68 report snapshots are preserved in
`NATIVE-BUILD.json`; current filenames contain this build's new results.

- 174,467 Java camera checks cover 30, 60, 90, 120 and 144 Hz; four zoom levels;
  three speeds; equal opposite directions; normalized diagonals; irregular
  frame intervals; left-edge overshoot; release/reversal; long-frame limits;
  and symmetric fractional drag accumulation.
- 12,971 host touch/layout checks include 1,728 button positions and extracted
  production gesture handlers. They cover placement drags below the command
  bar, UI scale/width/zoom variants, fixed/following controls, confirmation,
  covered controls, held scrolling without new move events, release, Android
  cancellation, menus, transitions, pinch and selection/target edge scrolling.
- AddressSanitizer and guard pages pass 57,794 rectangle checks, 24,960 ghost
  draws across 65 building entries and 684 rendered frames. Of those frames,
  384 exercise host-owned pans in eight directions at four zoom levels, map
  boundaries, bottom-edge outlines and an idle confirmation target. No second
  native pan is added to the host's movement.
- The previously fixed rectangle renderer is byte-for-byte unchanged in the
  prepared source. This update changes the host camera integration and native
  ownership flag, not simulation rules or the multiplayer protocol.
- Signed release assembly and lint pass (0 errors, 10 warnings); all 38 JNI
  methods and 16 KiB load/APK alignment pass. Version is 1.0/code 69, and the
  signing identity matches build 68. All 72 assets and both decoder libraries
  are unchanged. Both engine libraries were rebuilt.
- These are host tests and package checks. Physical-device smoothness/touch
  confirmation, the separate Vivo closure and actual radio tests remain
  unverified. GitHub publication remains paused.

# Historical validation: placement crash fix, build 68

Current reports: `native-placement-v1.0.json` and
`placement-package-v1.0.json`.

- The retained ARM64 stack points to the bottom-border `memset` in
  `draw_placement_ghost` (PC `0x136d18` in the build 65–67 engine).
  The border helpers use exclusive rectangle ends but wrote the bottom row at
  `height`, one row beyond the clipped rectangle. At the bottom of the image
  this writes outside the allocated buffer.
- Both original indexed placement and RGBA selection outline renderers reproduce
  a write SIGSEGV with a protected page after the image. The fix writes the last
  row at `height - 1`; both reproductions pass after the fix.
- AddressSanitizer and guarded images pass 57,794 rectangle checks, 24,960
  placement-preview draws across 65 building entries, and 300 full frames.
  Coverage includes every edge, fully offscreen and empty/inverted rectangles,
  one-pixel dimensions, extreme coordinates, padded row strides, blocked/valid
  previews, refineries, flying-building/add-on previews, three display sizes,
  and zoom 0.5, 1, 1.4 and 3. Leak detection was disabled.
- Only `ui/ui.h` changed in the prepared engine; the other 423 prepared files
  match the pre-fix tree. Simulation rules and multiplayer protocol are unchanged.
- Both ARM64 and x86-64 libraries were rebuilt. All 38 JNI methods and 16 KiB
  ELF/APK alignment pass. The decoder source is unchanged; its rebuilt binary
  embeds the renamed project path in assertions. All 72 packaged asset entries
  match build 67, and no original game archives are bundled.
- Signed release assembly and lint pass (0 errors, 10 warnings). Display version
  is 1.0, version code is 68, and the signing identity matches build 67 for an
  in-place update. Android permissions are unchanged.
- The user's report also verifies that build 67 can retrieve a real retained
  Android tombstone. The timestamp identifies the older crash, not a new crash
  in build 67. Post-fix physical-device play is still pending, and the separate
  Vivo closure has not been diagnosed. GitHub publication remains paused.

# Historical validation: native trace diagnostics, build 67

Current reports: `native-crash-trace-v1.0.json`,
`native-trace-package-v1.0.json`, and `native-crash-investigation-v1.0.json`.

- 1,066 checks cover bounded Android tombstone decoding, correct faulting-thread
  selection, omitted zero-valued protobuf fields, signal/address/frame/build ID
  formatting, unknown fields, malformed/oversized inputs, exclusion of raw memory
  and logs, Android API guards, missing traces, and persistence across JVMs.
- Gradle release assembly and lint pass: 0 errors, 10 warnings. Version remains
  1.0; code 67 and the existing signing identity permit an in-place update.
- All 76 native-library and asset entries match build 66 byte for byte.
- Five host AddressSanitizer checks completed without a reported memory error,
  including 60,000-frame Terran and Protoss Hero Mode runs. The Zerg run exceeded
  the 240-second investigation limit and is incomplete, not a pass.
- The user's foreground single-player native SIGSEGV is confirmed by Android's
  exit report but has not been reproduced or located. This build retrieves the
  native stack if Android still retains it; it is not a claimed crash fix.
- Device execution and actual retained tombstone decoding remain unverified.
  GitHub publication is still paused.

# Historical validation: StarDroid 1.0 diagnostics, build 66

Current diagnostic reports: `diagnostics-v1.0.json` and
`diagnostics-package-v1.0.json`.

- 37 host checks cover exit classification, bounded reports and cause cycles,
  Android-version guards, scoped/empty/unavailable history, original crash-handler
  delegation, and report persistence across separate JVM processes.
- Gradle release assembly and Android lint pass (0 errors; 10 warnings).
- Signed APK identity matches build 65; version remains 1.0, code advances to 66.
- All 76 packaged native libraries and asset entries match build 65 byte for byte.
  Gameplay, the multiplayer protocol, and native engine are unchanged.
- Actual Android/Vivo process-exit records and physical-device behavior are not
  tested here. The reported Vivo X100 foreground shutdown is not reproduced and
  its cause is not confirmed. This is a diagnostic update, not a claimed fix.
- Source signing uses environment variables; an unconfigured contributor build
  uses Android development signing. The distributed APK retains the existing key.

Previous reports below are historical evidence for their recorded inputs.
They are not relabeled as reruns of the new Android diagnostic integration.

# Historical validation: StarDroid 1.0 upgrade cards, build 65

Current reports: `native-upgrades-v1.0.json`, `upgrade-ui-v1.0.json`,
`branding-v1.0.json`, `native-package-v1.0.json`, `placement-v61.json`,
`hud-v59.json`, `native-v55.json`, `room-v55.json`, `room-sockets-v55.json`,
`ui-v58.json`, `native-results-host-v56.json`, `tooltip-v56.json` and
`local-permissions-v55.json`.

- The baseline probe confirmed that all 16 three-level upgrade lines allow
  levels 2 and 3 with the relevant tech, but their icons disappear without it.
- Twenty configurations cover original/Brood War, custom Melee/FFA/teams,
  multiplayer FFA/teams, and Hero Mode off/on. Each covers all 16 lines plus
  both Spire producers: 1,080 real research completions and 21,820 assertions.
  Commands pass through the production command card and action packets; network
  cases use actual ordered multiplayer turns from player slot 3.
- Checks cover next-level icons and prerequisites, blocked clicks, uncompleted
  and enemy prerequisites, replacement tech buildings, retail unpowered Protoss
  tech counting, costs, duration initialization, duplicate research prevention,
  in-progress save/load and removal after level 3. Research timers are shortened
  before normal completion so this remains a bounded regression suite.
- Ten retained gameplay checks are rerun on the new native build: powered and
  unpowered buildings, heroes, hero merging, teams, old saves, victory, cargo,
  detection, add-ons and sound. The long AI economy matrix is not repeated.
- The new patch changes only `web/sandbox.h` in the prepared engine. Every other
  prepared file matches the recorded baseline, including simulation and AI.
  Multiplayer protocol build 60 is retained. Both native engine ABIs are rebuilt;
  the unchanged Smacker decoder binaries are retained.
- All 16 real native locked cards render through production HUD/tooltip methods
  and original artwork at two widths and button sizes. 704 checks cover grey
  palettes, fixed slots and required-building/level text. Renders are inspected.
  Existing tooltip tests cover 2,070 layouts, sizes and hover interactions.
- Current Java placement/menu/result/branding checks pass. Signed-package checks
  verify version 1.0, higher internal build code 65, the previous install identity,
  native exports, assets, library alignment and lint.

These are host checks. Physical Android installation, touch, sound and radio
confirmation remain pending. Original game archives and extracted artwork are
excluded from deliverables.

# Historical validation: StarDroid 1.0 build 64

Current reports: `branding-v1.0.json`, `native-package-v1.0.json`,
`placement-v61.json`, `native-v59.json`, `hud-v59.json`, `native-v55.json`,
`room-v55.json`, `room-sockets-v55.json`, `ui-v58.json`,
`native-results-host-v56.json`, `tooltip-v56.json` and `local-permissions-v55.json`.

- App Options uses the same screen for missing-file startup and menu access.
  The permanent file guide, single import action and installed-content inventory
  are retained; export, movie-help and control-help sections are removed.
  Cheats uses Force victory (end match), with the defeat button removed.
  Touch Controls retains its Comfortable defaults and saved preferences. Three
  original-font control-menu renders were inspected with the existing Canvas
  shim. Updated Android instrumentation sources compile; they were not run on
  a device.
- Branding checks cover the project and launcher name, version 1.0, setup and
  diagnostic text, exported filenames, and preserved upstream/ToadWarrior credits.
- Imported content is exercised under old and new names, including precedence
  when both exist and read fallback if renaming is unavailable. Original campaign
  data is exported, imported with the new name and exported again for comparison.
- Android permission tests are rerun against the updated activity. Existing
  room and encrypted-socket reports are retained against unchanged sources.
  Wi-Fi invitations and network keys are unchanged.
- Menu, results and placement-input harnesses are rerun against current sources.
  All retained reports are checked against their exact source hashes.
- The signed APK must identify as StarDroid 1.0, use a higher version code and the
  same application ID/certificate as the previous 1.0 build, and contain the same native libraries
  for both ABIs. JNI exports, assets, 16 KB alignment and lint are checked.

These are host tests. Physical Android installation, touch, sound and radio
validation remain pending. The native simulation is unchanged, so its bounded
0.59 checks are retained without rerunning the long simulation matrix.

# Historical validation: 0.61

Current reports: `placement-v61.json`, `native-package-v61.json`,
`native-v59.json`, `hud-v59.json`, `native-v55.json`, `room-v55.json`,
`room-sockets-v55.json`, `ui-v58.json`, `native-results-host-v56.json`,
`tooltip-v56.json` and `local-permissions-v55.json`.

- The placement harness executes the production touch handler and drawing,
  gesture-blocking and confirmation methods with Android/Canvas shims. It uses
  the real preference, placement, command-hover and font/art classes.
- Taps and holds on Build, Cancel and the gap are tested over underlying menu
  buttons, command icons and the minimap for all three races. Redrawing during
  the press replaces hit objects without losing the captured action.
- Gestures starting on exposed controls cannot activate them by releasing in
  the covered row. Entering and then leaving the row keeps the gesture consumed.
  Placement drags keep moving the target without pressing either button.
  Cancellation clears capture; underlying controls work again after placement.
- 1,728 edge/zoom/control arrangements keep the row below the visible preview
  and on screen, including positions overlapping the HUD. Original-art renders
  are inspected for readable overlapping controls and the settings layout.
- Existing menu/results checks are rerun for the changed Surface. Retained
  simulation, HUD, networking and tooltip reports have matching source hashes.
  The packaged native libraries remain byte-identical to 0.60. Protocol build
  60 is retained. The signed APK passes package, update-identity and lint checks.

These are host checks, not physical Android installation or touch tests. Radio,
sound and device performance remain unverified. Previous bounded gameplay-test
limitations still apply. Game archives and extracted artwork are not packaged.

# Historical validation: 0.60

Current reports: `placement-v60.json`, `native-package-v60.json`,
`native-v59.json`, `hud-v59.json`, `native-v55.json`, `room-v55.json`,
`room-sockets-v55.json`, `ui-v58.json`, `native-results-host-v56.json`,
`tooltip-v56.json` and `local-permissions-v55.json`.

- The focused placement harness checks default preferences, migration from an
  existing customized configuration, persistence through the actual settings
  callback, and independence from the confirmation preference.
- 1,728 arrangements cover three viewport widths, zoom from 0.5× to 3×,
  both control sides, two touch sizes and screen-edge placements. Confirmation
  buttons remain in bounds and clear of the supplied HUD obstacles.
- Extracted production drawing and callback methods verify that Build uses the
  original placement coordinates, Cancel sends Escape, finger offset and zoom
  are accounted for, and fixed mode retains the previous position. Real game
  artwork renders settings and placement examples for all three races; those
  renders are inspected. This is an AWT Canvas compatibility harness, not an
  Android touch-event or physical-device test.
- Command Settings touch targets fit within the panel and do not overlap.
  Existing menu and results checks are rerun against the changed Surface source.
  The package checker verifies current source hashes in all retained reports.
- Both packaged native libraries are byte-identical to 0.59 for both ABIs.
  Native simulation and multiplayer source hashes are unchanged, so their
  existing reports are retained without repeating the long simulation matrix.
  Multiplayer protocol build 60 is retained for compatibility with 0.59.
- The APK is checked for its higher version code, unchanged update certificate,
  complete JNI exports, 16 KB library alignment, asset integrity and Android lint.

Physical Android installation, touch, sound, radios and performance remain
unverified. Original game archives and extracted art are excluded from the source
package. Prior gameplay validation limitations continue to apply.

# Historical validation: 0.59

Current reports: `native-v59.json`, `hud-v59.json`, `native-v55.json`,
`room-v55.json`, `room-sockets-v55.json`, `ui-v58.json`,
`native-results-host-v56.json`, `tooltip-v56.json`,
`local-permissions-v55.json` and `native-package-v59.json`.
Report hashes identify the exact tested sources. Older report filenames in this
list are retained harnesses rerun where their sources changed.

- Eighteen 60,000-frame Hero Mode scenarios cover all three races, all three
  difficulties and both expansions from ordinary four-worker starts. Every
  scenario requires an early completed hero, all six hero types, multiple
  hero/upgrade buildings, overlapping hero production and upgrades, expansion,
  at least five upgrades, and byte-identical saved continuation over 48 frames.
  No extra resources are granted. Human starting units are healed to keep the
  bounded economy test running without ending the match.
- Eighteen ordinary 60,000-frame scenarios retain expansion, upgrade, advanced
  unit/detection, attack and saved-continuation checks with Hero Mode off.
  Three depleted-main scenarios retain resource recovery and fresh-base checks.
- All 18 hero times exactly match their normal counterparts in both expansions.
  Both Spire types reject level 3 air attack/armor without a completed Hive and
  accept them with one. Recycled visual-effect images clear stale frozen
  positions, preserving exact save continuation through later image allocation.
  Duplicate-loss guards are retained while a unit dies and released when its
  slot is recycled, so reused unit IDs cannot suppress later losses.
- Fixed hero slots are checked against every possible combination of remaining
  upgrades at all three producers, at two widths and two command scales. The
  HUD harness runs 4,958 checks using original command artwork and fonts.
  Status/Detector combinations stay within their row, expose full inspection
  text, preserve red Unpowered and leave kills/supply unobscured. Rendered
  command and Lockdown/Detector examples are inspected visually.
- Retained native cases cover hero costs, prerequisites, queued/living limits,
  death/rebuild, cancellation, Tassadar/Zeratul merging, Duke siege, team results,
  old saves, retail power/add-on rules, cargo, victory, detection and original
  selection/menu/score audio. First Strike and partial-larva feedback also run.
- Multiplayer checks retain two to eight simulated devices, encrypted desktop
  sockets, four team perspectives and fourteen ordinary native perspectives.
  Menu renders, tooltips, permissions, JNI exports, both rebuilt Android ABIs,
  16 KB library alignment, update signature and Android lint are checked.

These are host tests with original game data supplied separately. Physical
Android installation, input, sound, Bluetooth/Wi-Fi Direct and performance
remain unverified. Bounded maps cannot establish every map, campaign or combat
outcome; hero balance still needs playtesting. Original game archives and
extracted game assets are excluded from the source package.

# Historical validation: 0.58

Current reports: `native-v58.json`, `native-v55.json`, `room-v55.json`,
`room-sockets-v55.json`, `ui-v58.json`, `native-results-host-v56.json`,
`tooltip-v56.json`, `local-permissions-v55.json` and `native-package-v58.json`.
Report source hashes identify the code tested. Earlier version-specific reports
are history; unchanged tooltip/permission reports remain valid for identical code.

- All 18 heroes: six buttons at the correct producer, prerequisite handling,
  actual costs/supply, cross-producer queue limits, cancellation/refunds,
  completion, exact save/load and rebuilding after death. Hero Mode off retains
  original costs and disallows hero production.
- Actual Tassadar/Zeratul merge and completion, four-supply hero Archon, saved
  paired limits and release on death; Duke's Tank/Siege forms share a limit.
- Four native team perspectives compare initial hashes, shared vision, save/load,
  an eliminated teammate waiting for shared victory and both teams' results.
  Mismatched saved rules are rejected; previous schema 2 saves still restore.
- Eighteen 60,000-frame AI scenarios cover all three races and difficulties in
  original StarCraft and Brood War. They check expansion, upgrades, advanced
  units/detection, attacks and byte-identical 48-frame saved continuation.
- Three 30,000-frame depleted-main tests begin with only 75 minerals, no gas,
  and empty main mineral fields. They require new mining income and a completed
  base at another resource location, without additional resource grants.
- Campaign/custom reaction tests use available Overlords, Observers, Science
  Vessels and attached Comsats; scans spend energy and existing scripted movement
  is preserved. Campaign macro changes are excluded.
- All 13 power-dependent Protoss buildings and 17 prerequisite cases per
  expansion verify retail completed-tech counting alongside disabled production,
  original red status and sound, actual Pylon changes and exact saved power state.
- Six Terran add-ons retain real lift, neutrality, opponent landing capture,
  ownership accounting and saved continuation. Four transport types retain Load
  controls. Forty-eight ordinary custom/multiplayer victory cases are checked.
- Real imported score fill/end audio composes to 2,200 ms and stops with the
  counter clock. Original Ultralisk normal/annoyed sequencing and complete menu
  clips are retained. The Android score bridge now allows 8 MiB per audio file;
  network command payloads retain their 16 KiB limit.
- Room tests cover two to eight simulated devices with Hero Mode/teams, slot
  movement, transfer, chat, countdown, saved settings and reload. Eight desktop
  socket clients use fourteen authenticated encrypted lanes. Fourteen native
  ordinary-game perspectives compare 1,440 frames and saved/departure continuations.
- Thirteen production-menu renders include eight-slot teams, Hero Mode and both
  Player ID dialogs; hit areas remain in bounds and do not overlap. Six outcome
  themes, 24 result tabs and the tooltip layout suite retain their checks.
- Original First Strike triggers and partial-larva resource feedback are retained.
  Both Android ABIs are rebuilt. Package checks verify retained signing identity,
  current version/libraries/assets, JNI exports, 16 KB alignment and no lint errors.

These are host tests using the real engine and external original archives, with
AWT replacing Android Canvas and desktop sockets replacing Android radios.
Physical Android installation, keyboard/touch, sound, Bluetooth/Wi-Fi Direct and
performance remain unverified. Bounded scenarios do not prove every map or
campaign behavior, and the discounted hero costs need multiplayer balance testing.
No original game archives, extracted UI/sound assets or external decoder checkout
is included in the source package.

Build the engine harness with `python3 tests/build_native_host.py revision58`;
run `python3 tests/run_native58.py GAME_DATA`. The original-data menu checks use
`tests/run_ui58.py GAME_DATA` and `tests/run_results56.py GAME_DATA`.

# Historical 0.57 validation

Current reports: `native-v57.json`, `native-v55.json`, `room-v55.json`,
`room-sockets-v55.json`, `ui-v56.json`, `native-results-host-v56.json`,
`tooltip-v56.json`, `local-permissions-v55.json` and `native-package-v57.json`.
The reused harnesses are rerun against the current source; their source hashes
record this run. The prior `native-v56.json` is historical, not a current-run claim.

- All 13 power-dependent Protoss building types in original/Brood War: empty
  command cards, original red Unpowered text, original selection sound, blocked
  production/research/upgrades, and recovery when power returns.
- Unit, building and upgrade prerequisites; second powered provider; actual
  Pylon creation/destruction; exact saved power state. Nexus/Pylon/Assimilator
  exemptions come from the original DAT flags.
- All six Terran addons: actual lift-off, neutral owner, unavailable old-owner
  technology, opponent landing capture, restored new-owner technology and exact
  save round trip. These are real engine orders, not ownership assignments.
- All four original normal Ultralisk WAVs are byte-identical to StormLib's
  independent extraction and decode to exact source PCM at the original rate.
  Rapid/suppressed clicks do not silently advance annoyed voices; normal voice
  choices do not repeat immediately.
- Three 60,000-frame hard Brood War AI scenarios check expansions, upgrades,
  advanced units/detection, attacks and byte-identical saved continuation.
  Forty-eight original/BW, Melee/FFA and multiplayer result cases and all four
  transport types are retained in this run.
- Fourteen network player perspectives retain deterministic save/load and
  simulation hashes; room and authenticated-socket tests cover up to eight
  devices, slot changes, chat, countdown, transfer, handover and save/reload.
- Existing UI, results and tooltip render harnesses are rerun. APK checks verify
  both ABIs, JNI exports, 16 KB alignment, version, retained signing identity,
  ToadWarrior credit, absence of Google Play dependencies and lint errors.

The tests use imported archives outside the project. No game data, original
sound clips or independent decoder checkout is bundled. Physical Android,
Bluetooth/Wi-Fi Direct and listening checks remain pending. Bounded AI and
campaign scenarios do not establish correctness on every map.

Build the native harness using `python3 tests/build_native_host.py revision57`.
`tests/run_native57.py GAME_DATA` runs the regression suite. Its independent
waveform audit additionally expects a StormLib checkout/build in
`build-native/probe57/StormLib` and `build-native/probe57/storm-build`; compile
`tests/extract_storm_reference57.cpp` against that static library into
`build-native/probe57/storm-extract`. StormLib's bundled-dependency build option
is `STORM_USE_BUNDLED_LIBRARIES=ON`. Its exact revision is recorded in the report.
`tests/run_ui56.py GAME_DATA` prepares the original-asset extractor used by this
suite. Keep imported archives out of source packages.

# Historical 0.56 validation

Current reports include `native-v56.json`, `ui-v56.json`,
`native-results-host-v56.json`, `tooltip-v56.json` and `native-package-v56.json`.
The 0.55 room, socket, permission and native regression harnesses are rerun against
current production sources; their recorded source hashes identify this run.

- Forty-eight real-engine result scenarios cover StarCraft/Brood War,
  Melee/Free for All, three AI races and three difficulties, plus human and mixed
  multiplayer perspectives. Victory waits for the final opponent; losing local
  players receive defeat.
- Eighteen 60,000-frame AI scenarios cover every race and difficulty in both
  StarCraft and Brood War. They check
  expansions, upgrades, attacks, advanced units/detectors and byte-identical
  48-frame save continuations. AI starts with normal resources and pays normal
  costs; the human opponent is kept alive to allow the long observation period.
- Bunkers, Dropships, Shuttles and transport Overlords are checked empty, full
  and after unloading. Detection tests exercise the actual attack callback for
  custom and campaign contexts, Comsat energy and preserved scripted movement.
- Original Ultralisk voice IDs verify normal, annoyed and returned-to-normal
  selection. Original score audio produces exactly 2,200 ms of PCM with a
  completed fade; the playhead is checked. Independent entry/lock sounds survive
  a simulation reset and finish.
- Seven production-menu renders check bounds, non-overlapping hit targets,
  original assets, terrain previews, normal/hover colors and no pre-lobby slot
  controls. Six outcome themes and 24 result tabs check original score-bar assets,
  stationary backgrounds, slide motion and count timing. The complete Protoss
  Replay image moves with its panel.
- Tooltip checks render 2,088 layouts at multiple widths/scales and exercise
  hover, holds, gutters, early inspection and quick taps. The shared description
  excludes resource-shortage messages while actual command feedback remains.
- Existing tests cover 2–8 room participants, older-build rejection, slot/race
  changes, chat, countdown, pause/save/restore and departures. Eight instances
  use fourteen encrypted desktop socket lanes with independent handovers and
  fallback. Fourteen C++ perspectives compare 1,440 frames and saved/departure
  continuations. Original First Strike and partial-larva-order regressions run.
- Android permission/lifecycle cases cover API 26–36. Both native ABIs are rebuilt.
  Package verification checks versionCode 57, signature continuity from 0.55,
  all JNI symbols, current libraries/assets, 16 KiB alignment, no Google Play
  services classes and zero lint errors.

These are bounded host tests. Canvas uses an AWT shim; radio transport uses
actual desktop sockets rather than Android radios. There was no physical-device
installation, touchscreen/keyboard test, listening test or complete campaign
playthrough. AI success on the fixture does not imply success on every map.

Reproduce with original game archives outside the source tree:

```
python3 scripts/prepare_native.py
python3 tests/build_native_host.py revision56 --skip-prepare
python3 tests/run_native56.py /path/to/game-data
python3 tests/build_native_host.py revision55 --skip-prepare
python3 tests/run_native55.py /path/to/game-data /path/to/expterran01.mpq
python3 tests/run_room55.py
python3 tests/run_room_socket55.py
python3 tests/run_local_permissions.py
python3 tests/run_results56.py /path/to/game-data
python3 tests/run_tooltip56.py
python3 tests/run_ui56.py /path/to/game-data
python3 scripts/build_nearby.py --lint
python3 tests/check_nearby_package.py /path/to/OpenBW-Android-0.55.apk
python3 scripts/build_hero_report.py /path/to/output
```

Imported archives and extracted original assets are not included in the APK or
source package. The hero comparison stores numeric facts and proposals only.

# Historical 0.55 validation

Current reports: `validation/*-v55.json`.

- The production room protocol runs with two through eight simulated devices.
  Checks cover roster/race changes, host moves, chat, countdown cancellation,
  shared pause, live/fresh save restoration, departing guests and saving during
  departure. Delayed delivery does not create simulation catch-up bursts.
- Eight room instances use fourteen actual encrypted desktop TCP lanes. Each
  guest switches from its first lane to its second and falls back independently.
  Map transfer, chat, countdown, a paused save, guest departure and at least 740
  frames complete with matching state histories. The stream codec additionally
  checks pairing, authentication, replay/tamper rejection, queue bounds and EOF.
- Fourteen real C++ engine perspectives compare 360 checkpoints each: eight
  human positions in Melee and six human positions plus two computers in Free
  for All. Each trace covers 1,440 frames, with an additional saved continuation,
  cross-slot restore, departure/closed-slot restore and invalid-batch rejection.
  Starting slots match original map positions and the computers gather resources.
- Original mission 401 triggers verify that Duran and the Command Center are
  visible during the paused introduction, units remain stationary, and both
  become owned without moving the visiting unit closer. Actual unit data/audio
  verifies the normal Ultralisk selection range. Partial larva mineral, gas and
  supply shortages and supply-neutral replacement morphs are checked.
- Original assets and actual production render methods cover seven connection,
  discovery, lobby and custom-setup screens with bounded, non-overlapping touch
  targets. Six race/outcome themes and 24 result tabs verify stationary
  backgrounds and sliding UI; pixel comparisons allow 1/255 alpha rounding.
- Shared font and tooltip code renders 2,088 layouts at three widths, three text
  scales and two command scales. Glyph bounds and line separation are checked,
  including Hive, long descriptions, requirements and unbroken names. Hover,
  hold, gutter inspection, early sliding and quick taps are exercised.
- Production permission/lifecycle policy passes API 26–36 Host/Join, grants,
  denial, optional Wi-Fi, repeated and late callbacks, enable and visibility.
- Both Android ABIs are rebuilt. APK checks include versionCode 56, previous
  signing identity, every JNI method, current library/asset bytes, 16 KiB
  alignment, no Google Play services classes and zero Android lint errors.

The Canvas renderer uses an AWT compatibility shim. Room tests use a small
synthetic engine; the C++ engine is tested separately. Desktop TCP tests do not
exercise Android Bluetooth or Wi-Fi Direct radios. There was no physical-device
installation, touchscreen/keyboard test or complete campaign playthrough.

Reproduce with original game archives outside the source tree:

```
python3 scripts/prepare_native.py
python3 tests/build_native_host.py revision55 --skip-prepare
python3 tests/run_native55.py /path/to/game-data /path/to/expterran01.mpq
python3 tests/run_room55.py
python3 tests/run_room_socket55.py
python3 tests/run_local_permissions.py
python3 tests/run_results55.py /path/to/game-data
python3 tests/run_tooltip55.py
python3 tests/run_ui55.py /path/to/game-data
python3 scripts/build_nearby.py --lint
python3 tests/check_nearby_package.py /path/to/OpenBW-Android-0.54.apk
```

The eight-start fixture derives its terrain from the bundled Weave map; the
Duran fixture uses the original First Strike scenario. Neither imported archives
nor extracted original game assets are distributed in the source package.

# Historical 0.54 validation

Current results are recorded in `validation/*-v54.json`.

- Twelve real-engine host/guest pairs (all AI races, Melee/FFA, Classic/Brood War)
  compare every turn through 2,400 frames and a 240-frame saved continuation.
  Snapshots restore into either player role, preserving simulation and local fog
  identity. Three-computer solo save/load continuations are also byte-identical.
- Actual engine checks cover transport/bunker deselection, command cards for all
  six flying Terran structures, replacement of addon placement by Land, and
  continued AI play after the other human departs.
- The production match scheduler passes new setup/countdown/save/reload cases,
  including exact continuation with both accepted command batches retained.
  Existing protocol, encrypted-socket, permission, pacing and transfer suites pass.
- The production result renderer is compared pixel by pixel against a single
  translated screen. Original-artwork host renders cover connection, discovery,
  host/guest lobbies, countdown and both custom setup screens. Map previews use
  actual terrain data. Core-only installs use original lobby panel art when the
  optional CD interface panels are absent. FONT fallback is used when original
  font entries are unavailable in the test core archives.
- Both Android native architectures are rebuilt. APK validation checks JNI exports,
  current native bytes, 16 KiB alignment, signature continuity, versionCode 55,
  absence of Google Play services, and zero lint errors.

No physical Android or radio test was run. The Canvas checks use a desktop AWT
shim, protocol engines are synthetic except for the separately tested C++ engine,
and the native scenarios are bounded checks rather than complete playthroughs.

Reproduce with the original game archives outside the source tree:

```
python3 scripts/prepare_native.py
python3 tests/build_native_host.py revision54 --skip-prepare
python3 tests/run_revision54.py /path/to/game-data
python3 tests/run_nearby_protocol.py
python3 tests/run_match54.py
python3 tests/run_local_transport.py
python3 tests/run_local_permissions.py
python3 tests/run_nearby_pacing.py
python3 tests/run_nearby_efficiency.py
python3 tests/run_results54.py /path/to/game-data
python3 tests/run_ui54.py /path/to/game-data
python3 scripts/build_nearby.py --lint
python3 tests/check_nearby_package.py /path/to/OpenBW-Android-0.53.apk
```

# 0.53 validation

- Google-free production transport passed 545 checks over encrypted desktop
  sockets. An integrated match transferred an exact map through handover and
  ran 900+ deterministic frames, shared pause/resume, fallback and leave.
- Production permission/lifecycle flow passed 685 assertions with Android
  boundary test doubles across API 26–36 and Host/Join. Optional Wi-Fi denial
  retains Bluetooth; modern Android does not request location permission.
- Protocol (1,430 assertions), efficiency and host pacing suites pass. The
  scheduler is byte-identical to 0.52. Both peers remain free of multi-step
  bursts after settling in the reproduced synthetic late-start scenario.
- APK certificate/application ID match 0.52; versionCode increases to 54.
  No Google Play services classes or metadata are present. Both ABIs, all
  32 JNI methods, native-library identity, assets and 16 KiB alignment pass.
  Android lint reports zero errors and ten warnings.

These checks do not verify physical Bluetooth discovery, pairing dialogs,
Wi-Fi Direct group creation or phone performance. No current campaign,
original-art render or Android UI test is claimed. See [0.53 notes](docs/FIXES-0.53.md).
Current reports: `validation/*-v53.json`.

# Historical 0.52 validation

- The production 0.51 scheduler reproduces host-only bursts after a guest starts
  600 ms late: 89 multi-step updates over 15 seconds, up to four steps in one
  update, a 208 ms longest step gap and `Wait 100%`, despite near-full game speed.
  With the same synthetic link (60 ms RTT, +/-20 ms one-way jitter), 0.52 has no
  multi-step updates in the measured window, a 48 ms maximum step gap and full
  game speed on both peers.
- The pacing suite covers late starts on either peer, varied drawing cadence,
  a later stall, background pause/resume, absent input, bounded peer lead and
  matching state checkpoints. Its 302,368 assertions include repeated invariants,
  not that many independent scenarios. This is a deterministic host model, not
  a physical-phone test or actual native-rendering measurement.
- The existing efficiency suite passes (737,020 assertions), including map
  compression/cache validation and high-latency recovery. The 1,430 protocol,
  608 permission and 49 transport assertions also pass.
- Native game/video libraries are reused unchanged from 0.51. Historical native,
  campaign, original-art and Android reports have not been rerun. The automatic
  version heading is checked in the compiled APK as well as the package version.
- The APK passes update identity/signature checks against 0.51, permissions,
  asset/library correspondence, all 32 JNI methods, both ABIs and 16 KiB
  alignment. Android lint reports zero errors and nine warnings.

Current reports: `nearby-pacing-v52.json`, `nearby-efficiency-v52.json`,
`nearby-protocol-v52.json`, `nearby-permissions-v52.json` and
`native-package-v52.json` in `validation/`. See [0.52 notes](docs/FIXES-0.52.md).
Physical-phone confirmation remains pending; release readiness remains false.

# Historical 0.51 validation

- The production 0.50 and 0.51 Java match schedulers ran against the same
  deterministic lightweight engine and synthetic link for 60 virtual seconds
  per latency case. At 100 ms round-trip delay, simulation speed improved from
  69.86% to 99.89% of the Fastest target. A 1 MiB incompressible map became ready
  in 951 ms versus 6,551 ms. These are controlled host measurements, not physical
  radio, native game or rendering measurements.
- The efficiency suite checks ordered/exactly-once commands and matching state
  checkpoints; missing-input freezes; pause/resume; 600 ms RTT with jitter and
  recovery; bounded decoding; invalid metadata; verified cache hit, corruption,
  eviction and I/O failure. Its 737,042 assertions include repeated per-step
  invariants, not that many independent scenarios.
- All 1,430 protocol and 608 permission assertions pass. Another 49 assertions
  run the production transport with fake Android/Google boundaries, covering
  concurrent sends, out-of-order and duplicate completions, reordered receive,
  queue limits, failure and closing with messages in flight.
- The signed APK passes package/update identity checks against 0.50, versionCode
  52, version label 0.51, permissions, assets, all 32 JNI methods, both ABIs and
  16 KiB alignment. Benchmark baseline classes are absent from the APK. Android
  lint reports zero errors and nine warnings.
- Native game/video libraries are byte-identical to 0.50. Historical native,
  campaign and original-art render reports were not rerun and are not presented
  as current evidence. The new Network panel compiles but has not been visually
  or interactively checked on Android.

Current reports: `nearby-efficiency-v51.json`, `nearby-protocol-v51.json`,
`nearby-permissions-v51.json` and `native-package-v51.json` in `validation/`.
See [0.51 notes](docs/FIXES-0.51.md) for the complete benchmark table and commands.

Both phones must install 0.51. Physical installation, discovery, pairing, radio
handover and actual performance remain untested. Release readiness remains
false pending device testing. The one-turn buffer adds 168 ms of input buffering;
it does not increase the configured game speed.

# Historical 0.50 validation

- 608 permission/start-flow checks run the production NativeNearby class with
  fake Android and Google API boundaries across API levels 26, 28–36. They cover
  both Host and Join, an update from 0.49 with Nearby devices already granted,
  missing Location, partial grants, cancellation, precise-location upgrades,
  duplicate taps/callbacks and a lobby closed before a permission response.
- All 1,430 production Java protocol assertions pass for build 51.
- Android lint reports zero errors and nine warnings.
- The package verifier checks actual compiled location permission declarations,
  the 0.50 label, versionCode 51, the same application ID/signing certificate as
  0.49, all 32 JNI methods, both ABIs, assets and 16 KiB alignment.
- All four native game/video libraries remain byte-identical to 0.49, 0.48 and
  0.47. The older native paired-simulation results have not been rerun.

Current reports: `nearby-permissions-v50.json`, `nearby-protocol-v50.json` and
`native-package-v50.json` in `validation/`.

Physical Android permission dialogs, installation, discovery, pairing, radio
handover and latency remain untested. These host tests do not simulate a real
Google Play services installation. Both phones must use 0.50. Release readiness
remains false pending device testing.

# Historical 0.49 validation

- The Google Nearby APK was rebuilt with versionCode 50 and versionName 0.49.
  Its application ID and signing certificate match the 0.48 APK, whose
  versionCode is 49. This verifies package update compatibility; installation
  on a physical phone has not been tested.
- All 1,430 production Java protocol assertions passed, including version and
  data mismatches, bounded packets, map integrity, delayed/missing input,
  pause/resume, desync, surrender and disconnect handling.
- Package verification passed for both ARM64 and x86_64, all 32 JNI methods,
  APK signatures, assets, native library correspondence and 16 KiB alignment.
  The compiled APK contains Google Nearby and the 0.49 version label.
- Android lint reported zero errors and nine warnings.
- All four game/video libraries are byte-identical to 0.48 and 0.47. The save
  schema, save/settings code and native engine are unchanged. The earlier
  native peer and desktop lobby-render results below were not rerun.

Current reports: `nearby-protocol-v49.json` and `native-package-v49.json` in
`validation/`. The original 0.47 native report still matches the engine source.

Physical installation, Android UI, Bluetooth/Wi-Fi discovery, pairing,
handover, latency and mixed-device operation remain untested. Both phones
must use 0.49 and have Google Play services. Release readiness remains false
pending device testing. No new full campaign playthrough claim is made.

# Historical 0.47 validation

- Six independent native peer pairs ran 7,200 frames each. All 1,801 state
  checkpoints per pair matched, with different local camera, selection and
  rendering activity. All three races and both editions were covered.
- The guest loaded the actual Java-generated transferred scenario archive.
  Native checks include malformed commands, ordered turns, resource gathering,
  production, attacks, surrender, cheat blocking and return to solo save/load.
- Production Java protocol tests passed: bounded packets, map checksums,
  version/data mismatches, delayed and missing input, pause/resume, stale pause,
  desync, surrender, lost connection and finished-game exit.
- Six lobby states were rendered with the production drawing code on a desktop
  Canvas shim. Controls stayed within bounds, did not overlap, and were inactive
  during entry/exit animation. These are not Android screenshots.
- Native ARM64 and x86_64 libraries were rebuilt. The package keeps the existing
  application ID, certificate and solo save format.
- APK signatures, 16 KiB alignment, all 32 JNI methods, native library and asset
  correspondence, and current report hashes passed verification. Android lint
  reported zero errors and ten warnings.

Reports: `native-multiplayer-v47.json`, `nearby-protocol-v47.json`,
`nearby-lobby-v47.json`, `native-package-v47.json` in `validation/`.

Physical Android discovery/pairing, radio switching, latency, permissions and
mixed-device operation remain untested. Older campaign reports below are
historical; no full mission playthrough claim is made for this networking update.
Release readiness remains false pending device testing. This is an initial
nearby multiplayer test build. Weave's prior ground-unit bunching remains.

# Historical 0.46 validation

- **113 native automated scenarios passed**, including the 103 existing checks.
- Nine new Classic AI runs used High Noon for 60,000 frames, covering every race
  and difficulty. All gathered resources and attacked; none produced or queued
  Brood War units. The passive human is healed to keep each run alive; the AI
  receives no resource assistance. These checks do not measure game balance.
- A ruleset fixture checked all 18 Classic/Brood War race/difficulty combinations,
  Classic practice mode, restricted commands/AI production and exact save/load
  continuation after fresh initialization. Legacy setup defaults remain Brood War.
- The existing 64 campaign checks ran 2,400 opening frames and save continuation.
  They are startup checks, not full mission or victory playthroughs.
- The real Java NativeArt, NativeGlue and NativeResults classes were compiled
  against a small desktop Canvas shim. Six outcome themes and 24 tab renders
  passed inspection; checks cover transitions, input timing, long-name bounds,
  custom-menu panel grouping and palette-key transparency before/after recoloring.
  The supplied core FONT payloads use the readable fallback in this harness;
  imported original-font appearance still needs device verification.
- ARM64 and x86_64 engines and the APK were rebuilt. Package/signing/update-key,
  JNI exports, library/asset correspondence, adaptive/themed icon resources, ZIP
  integrity and 16 KiB alignment checks passed. The ordered source patch stack
  reconstructs identically from pinned input.

Physical Android touch, visual, audio, original-font and two-phone tests remain
pending. The broad release-readiness gate remains false and still fails on
missing current full campaign/device evidence. Older reports are historical.
Weave's known ground-army bunching limitation remains. Local multiplayer is a
feasibility assessment, not an implemented or tested feature of this build.

Current reports: `native-revision46-host-v46.json`, `native-results-host-v46.json`,
`native-patch-preparation-v46.json`, `native-package-v46.json` in `validation/`.

# 0.45 validation

- **103 automated scenario checks passed** with the supplied original game data.
- Five Zerg runs of 60,000 frames covered Easy, Medium and Hard on High Noon,
  plus Hard on Eldritch Lake and Weave. They verified normal resource gathering,
  expansion mining, tech progression, advanced unit production, attack waves,
  and exact save/load continuation after a fresh game initialization.
- Four Terran runs covered all three difficulties on High Noon plus Hard on
  Weave; six existing Protoss runs, including power recovery, also passed.
- All nine race/difficulty combinations selected their expected original script.
  A controlled spell fixture verified Ensnare, Dark Swarm, energy spending and saves.
- The 64 campaign checks covered 2,400 opening frames and save/load continuation.
  These are startup checks, not full mission or victory playthroughs.
- Eight map startup/economy checks and the prior command, audio-event, cloak,
  combat-alert, nuclear-strike and mission-permission regressions passed.
- Both Android ABIs were rebuilt. APK signature/update-key, JNI exports, library
  correspondence, assets, ZIP integrity and 16 KiB alignment were verified.
  A pristine rebuild of the ordered source patch stack was also verified.

The long AI tests heal the passive human opponent to keep the scenario running;
the AI receives no resource assistance. They do not measure competitive balance.
Weave still bunches some ground troops on its winding approaches. Air attacks
work there; High Noon and Eldritch Lake also exercised Lurker ground combat.
The Weave run does not claim that a Lurker met an enemy or burrowed there.
Physical Android visual/audio/touch checks remain pending. The broad release
readiness gate remains false; no older device report is presented as current.

Current evidence: `validation/native-revision45-host-v45.json`,
`validation/native-patch-preparation-v45.json`, and `validation/native-package-v45.json`.

# Current revision: 0.44

The native suite covers 94 original-data cases. Six new groups check:

- Race-specific placement and landing voices, interrupted landing, building
  and addon completion notifications, and actual siege/unsiege transitions.
- No attack alert for burning, self/allied or zero damage; alerts for real
  enemy damage and shield hits from projectiles whose owner has died. Active
  pings keep their original lifetime and subsequent hits can ping after expiry.
- Immobile touch selection, explicit rally targets, reveal-map detection,
  addon command disappearance/restoration and mixed-race supply-cost metadata.
- Actual silo missile training, Ghost command enablement, the original icon,
  command-driven launch, save/restore during flight, explosion damage and the
  spent-missile disabled command. Save continuation is compared byte for byte.
- Animated cloak refraction using original GRPs, translucent detected units,
  actual-vision limits with the map cheat, burrow suppression and edge clipping.
- Drawing of the Web's original Queen/combat-air/transport restrictions.

The 88 existing cases are rerun: 64 mission openings at 2,400 frames with save
continuation, eight map/economy checks, eight focused regressions and eight
60,000-frame Terran/Protoss simulations. The passive human is healed in long AI
runs; the AI receives no resource assistance. These are automated simulations
and campaign startup checks, not completed human campaign playthroughs.

The host JVM also checks Science Facility and Ghost slots and cost text.
Package checks cover both architectures, the retained update certificate, JNI
exports, library correspondence and 16 KiB alignment. Fresh patch application
is repeatable. Reports record outcomes and the tested source hashes.

No 0.44 Android device visual/audio run was performed. App/instrumentation
compilation does not establish that coverage. The broad production-release
gate remains false without current device and full-campaign evidence.
See docs/FIXES-0.44.md, NATIVE-BUILD.json and validation/*-v44.json.

# Historical revision: 0.43

The current native suite covers 88 cases using original game assets:

- Six 60,000-frame Protoss matches: Easy/Medium/Hard on High Noon, Hard on
  Weave and Eldritch Lake, and a High Noon run that destroys all AI Pylons at
  frame 18,000 to check power recovery. Tests require expansions, multiple
  Assimilators, sustained gas harvesting, attack waves that damage the opponent,
  advanced units, Carrier/Reaver ammunition and exact save continuation after
  closing and reinitializing the game. Each starts with 50 minerals and zero
  gas; the AI receives no resource assistance. The passive human is healed to
  keep the test running. This is a simulation check, not an even competitive match.
- Two 60,000-frame Terran matches check advanced units, expansion mining,
  repeated waves and save continuation on High Noon and Weave.
- Eight map startup/build-space checks, seven existing command/visibility/
  placement/ammunition/merge/cargo/warning checks, and a retired-bot save check.
  The latter verifies rejection without mutating the running world and confirms
  that human Zerg gameplay remains available.
- All 64 campaigns run 2,400 opening frames, render and round-trip their saves
  with exact short continuation. These are startup checks, not full playthroughs.
- Fresh native patch reconstruction is repeatable. Package validation checks
  both ABIs, signatures, update certificate, JNI exports, ZIP CRC, 16 KiB
  alignment, source/library correspondence and absence of retired bot inputs.

The reports record actual pass/fail results and source hashes. Android app and
instrumentation compilation does not establish device visual/audio behavior.
No 0.43 Android device UI run or unassisted full campaign playthrough was performed.
The broad production release gate remains false when its older comprehensive
Android/campaign evidence does not match this source; it has not been weakened.

See docs/FIXES-0.43.md, NATIVE-BUILD.json and validation/*-v43.json. Exact retail
AI parity, island transport strategies and exhaustive spell use remain outside
this revision's coverage. Old external Zerg-bot skirmish saves cannot resume;
campaign, practice and Terran saves retain their schema.

# Historical revision: 0.42

The original-data native suite passes all 84 cases:

- Seven command, visibility, placement, ammunition/research, merge, cargo and
  warning cases. These check innate Feedback, group Carrier/Reaver production,
  both merge pair requirements, actual Shield Battery charging with icon 308,
  unavailable cargo buttons, cloak detection/selection and initial fog snapshots.
  Invalid terrain, missing creep/power/geyser warnings retain the placement preview.
- Eight imported skirmish maps run for 6,000 frames, checking usable terrain,
  AI construction/training and exact save continuation.
- Five Terran AI runs last 60,000 frames each: Easy/Medium/Hard on High Noon,
  plus Hard on Weave and Eldritch Lake. Each produces Medics, Ghosts, Science
  Vessels and Battlecruisers, completes multiple bases/refineries, gathers from
  the expansion economy, launches repeated attacks and passes exact same-instance
  save continuation. The AI starts with ordinary
  50 minerals/zero gas and receives no resource assistance. The passive human
  player is healed to keep the long tests running.
- All 64 original campaign maps run 2,400 opening frames, render and pass exact
  snapshot/continuation checks without script errors. These are startup checks,
  not full campaign playthroughs; an unattended mission can end in defeat.
- Fresh patch reconstruction is byte-identical and repeatable.
- Reused projectile motion targets are reset before initialization; this fixes
  the save-continuation discrepancy caught in two Brood War Zerg mission checks.

Both ARM64 and x86_64 native libraries were freshly compiled, as were the Java
app and Android instrumentation APK. APK structural checks pass: the update
certificate matches previous versions, packaged assets/libraries match their
build inputs, ZIP CRC and 16 KiB alignment are valid, and all 26 JNI methods
exist in both architectures.

The 0.42 Android visual/instrumentation suite was not executed. Device-rendered
menu animation, title artwork, enlarged hit regions, tooltip layouts and audio/
touch behavior still need Android testing. Earlier Android results are historical,
not current evidence. The broad production release gate remains false because
matching Android and older comprehensive campaign/presentation evidence is
missing; none of its requirements has been weakened.

See docs/FIXES-0.42.md, NATIVE-BUILD.json and validation/*-v42.json. This revision
preserves the signing key, package ID and save schema. The AI uses original
campaign scripts plus an OpenBW melee manager, without claiming exact retail
AI behavior or complete support for every map's terrain and transport strategy.

# Historical revision: 0.41

The original-data host suite passes all 15 cases:

- Ammunition capacity: Carrier/Gantrithor 4/8 and Reaver/Warbringer 5/10;
  completed ammunition, queued ammunition, destruction and cancellation.
- Research gates, low-energy button brightness, scenario-disabled technology,
  and original resource/energy/supply warning text and advisor sound lookup.
  Mixed-race supply warnings name the correct Overlord/Depot/Pylon provider.
- Both Archon types advance from 0 to 99 percent, finish summoning, and emit
  exactly one completion voice. Progress is present during the transitional
  collision-reset order. Snapshots and continuation match exactly.
- Real cargo capacity and nonempty original wireframe pixels for a Tank,
  Vulture, Marine and Firebat; exact snapshot and continuation.
- All eight added maps load original terrain and run 6,000 AI startup frames
  with functional construction/training. Snapshots and continuation match.
- Original Easy/Medium scripts run 80,000 frames; Hard runs 140,000 frames.
  Nine/eight/five attack waves are observed respectively. Hard produces Ghosts,
  Science Vessels, Valkyries and a Battlecruiser, with both Science Facility
  add-ons. The passive human side is healed to preserve the test; the AI gets
  no resource assistance. These tests also check exact save continuation.
- Fresh patch reconstruction is byte-identical and repeatable.
- The exact Java map importer passes ZIP/single-file imports, persistence,
  deduplication, path isolation, 128-map limits and temporary-file cleanup.

The ARM64 and x86_64 libraries and Java app were freshly built. APK structural
checks pass: signing key matches prior versions, ZIP CRC and asset bytes match,
16 KiB alignment is valid, and all 26 JNI methods exist in both architectures.
The app and Android instrumentation compile. The Android visual suite did not
execute: emulator first-boot/userdata setup repeatedly failed or stalled, with
storage exhaustion on retries. Rendered Android command tints, warning position,
merge/cargo panels and ZIP-import interaction remain unverified in this build.
The full release gate remains false because that check and matching evidence
for older broad campaign/Android suites are missing; its requirements are intact.

Current reports are listed in NATIVE-BUILD.json. Earlier broad campaign and
Android reports below remain historical evidence. This revision does not claim
fresh full campaign playthroughs or physical-device audio/touch testing.

# Historical revision: 0.40

Both native libraries were freshly rebuilt for ARM64 and x86_64. Original game
archives and exported maps remain external test inputs, excluded from the
APK and source distribution.

- Emperor's Flight runs 6,000 opening frames with its original triggers. All
  five reinforcement buildings are airborne before movement and transfer to the
  player in the southwest. Its opening computer tanks siege. The snapshot and
  240-frame continuation match exactly.
- All six traps remain hidden for 90 frames before activation. With map reveal,
  framebuffer pixels match explicitly hidden trap artwork. Proximity then
  exposes their opening animation and their real weapons damage a passive target.
- Actual rendered camera boundaries match the center console at four viewport
  sizes: 640x480, 1280x960, 960x480 and 427x320.
- The original Brood War TLOx Terran Easy script runs for 60,000 frames from
  ordinary 50-mineral/zero-gas starting resources. It mines minerals and gas,
  builds Barracks, Factory, Starport and Machine Shop, sends six attack waves,
  and fights the human player's units. The passive human units are healed each
  frame to keep this test running; the AI receives no resource assistance.
  Snapshots and 240-frame continuations match after both same-instance restore
  and fresh game initialization. The longer run also checks casualty counters
  after restore, catching a discarded-future duplicate-death guard.
- 64/64 original-map startup/render/save checks pass after 4,800 frames, followed
  by fresh initialization, exact snapshot restore and 240-frame continuation.
  These are unattended checks; a mission can end in defeat. They are not full
  unassisted campaign playthroughs. The previous revision's assisted victories
  remain historical evidence, not fresh 0.40 playthroughs.
- Patch-stack reconstruction from the pinned upstream archives is repeatable.
- Android controls checks use the final APK and cover the new attack/move
  button on both sides, original changing icons, spacing, optional hiding and
  preference persistence. Ground-order opt-in remains independent. Resource
  size options, higher group controls and the actual rendered bottom map edge
  are checked alongside existing gestures, advisor error PCM, command slots
  and all 36 splash stress layouts. The final HUD capture is visually inspected.
- APK signatures, update certificate, both native architectures, JNI exports,
  packaged library/asset bytes and 16 KiB alignment are verified.

Reports are in validation/*-v40.json. The broad full-release gate stays strict
and is not claimed as passing: earlier comprehensive parity, presentation,
import, briefing and objective suites were not all repeated for this build.
No physical Android device was tested.

The Terran opponent uses the original campaign Easy script with the native
manager, not the original melee script or full retail AI behavior. Expansions,
island transport tactics, and all race/difficulty choices remain future work.
Original opening text and campaign speech are absent from the supplied exports;
font parity and the seven previously documented leaderboard displays remain
limited. See docs/FIXES-0.40.md for the changes and scope.

# Historical revision: 0.39

Both native libraries were freshly rebuilt for ARM64 and x86_64. Original game
archives, all 64 exported maps and extracted art remain external test inputs.

- 233/233 original-data native gameplay checks pass. The nine new checks cover
  off-map framebuffer clearing at four viewport sizes, casualty selection and
  64-pixel survivor wireframes, group assignment/recall/centering/pause/save state,
  all six beacon types against ordinary units and Infested Kerrigan, direct/spell
  damage and explicit attack orders, scripted removal/ownership transfer, and a
  destructible Protoss Fleet Beacon.
- 64/64 original-map startup/render/save checks pass after 4,800 frames, followed
  by exact snapshot restore and 240-frame continuation comparison. These are
  unattended checks: an unattended mission can end in defeat.
- 64/64 assisted objective traversals reach original victory triggers, starting
  assists after 24 frames so unattended combat cannot end the mission beforehand.
  No direct victory or switch edits are used. These are diagnostic traversals,
  not unassisted playthroughs.
- Original map records contain 57 ordinary beacons across the three races and no
  flag beacons. Flag-pad combat tests use stationary orders; capture-the-flag
  mode's existing CTFCOPInit order is outside the supported campaign scope.
- Patch-stack reconstruction is repeatable from the pinned upstream archives.
- APK signatures, the existing update certificate, both native architectures,
  JNI exports, ZIP bytes and 16 KiB alignment are verified.

Android checks pass on the final APK for settings/persistence, left cursor defaults,
optional group-button touch gestures, cancellation, both cursor sides, resource
errors/PCM, original Load/Unload icons and the reference Kerrigan slots. All 36
splash stress layouts fit; short openings retain their larger shaded green font.
The selection settings and complete gesture guide are visually inspected.

All three original briefing rooms pass animation/hover pixel checks. Terran
captures cover entry, idle, hover, animated hover, projector looping and exit;
the projector stays behind the planet and remains fixed on hover. Zerg/Protoss
Replay support and hover checks continue to pass. Captures are inspected.
The first emulator attempt lost its system package service before app install;
a reboot with two virtual CPUs recovered it. Final APK checks then passed.

The broad full-release gate remains separate and strict; historical comprehensive
suites and the earlier foreground gate are not presented as current matching
evidence. Their assertions have not been weakened.

Original opening text files and campaign speech are absent from the supplied
exports. Splash fitting is tested with varied lengths and line breaks, not all
64 original opening texts. Supplied font data uses the readable fallback, so
original FONT visual parity remains unverified. No physical device was tested.
Seven maps' leaderboard displays and exact retail AI parity remain outside this
revision. See docs/FIXES-0.39.md and validation/*-v39.json.

# Historical revision: 0.38

Both native ABI libraries are rebuilt from the current sources. Original core
archives and all 64 exported maps are external inputs, excluded from the APK
and source archive.

- 64/64 original-map startup/render/save checks pass after 4,800 frames, followed
  by exact snapshot restore and 240-frame continuation comparison.
- 64/64 assisted objective traversals reach original victory triggers, including
  all four previously unresolved missions. No direct victory, switch or capture
  score edits are used. Movement, healing/invulnerability, resource changes,
  enemy removal, countdown advances and unit-creation assists are documented.
  These are diagnostic traversals, not unassisted human playthroughs.
- 8/8 focused original-mission checks pass. Eye of the Storm verifies the actual
  Command Center, SCV mineral returns and new construction, independent Terran
  and Protoss supply, Gantrithor/Interceptor combat, and its original ending.
- 224/224 native gameplay checks pass with original core data. New cases cover
  foreign and Mind Controlled workers, separate supply, all transport types,
  Nydus entry/exit controls, and disabled ground-tap orders with explicit commands.
- Android checks pass for new settings/persistence, the one-shot selection button
  on either side, actual gesture dispatch, the Miscellaneous/defender setting,
  resource-error text and PCM, tooltip behavior and the larger green splash font.
- Original Zerg and Protoss briefing artwork is tested on Android: stationary
  Replay supports, moving frames, background motion, actual Start hit regions,
  and hover pixels compared with the original decoded animation. Captures are
  visually inspected. The Ghost/hero layout checks pass.
- Actual Android world snapshots survive a fresh process and continue identically;
  all 64 original mission archives also pass save/load and native map readback.
- Patch reconstruction, snapshot schema 1 compatibility, schema 2 save/defense
  state, mission/feedback regressions, archive decoding, map references, signatures,
  JNI exports and 16 KiB library alignment pass.

The Android foreground check was blocked by a System UI ANR dialog. Closing it
and disabling emulator animations allowed window/accessibility dumps to verify
the app foreground, but the unchanged revision suite hit another System UI ANR
on retry. The system log identifies a TIME_TICK broadcast timeout. Both failed
attempts are retained; the revision suite's foreground/screenshot gate remains
incomplete. Its app/hero/briefing logic checks pass.

Original campaign voice recordings are unavailable. Supplied core font payloads
are not readable FONT data; the readable fallback is tested, while original-font
visual parity remains unverified. Seven maps' leaderboard displays are still
unimplemented. No physical Android device was tested. Full unassisted campaign
playthroughs and exact retail AI parity are not claimed. The broad full-release
gate remains incomplete because the older comprehensive presentation, import,
parity and Android suites do not have current matching evidence, and the revision
foreground gate is blocked as described above. Those checks have not been weakened.

See docs/FIXES-0.38.md and validation/native-*-v38.json. Earlier sections below
are historical evidence and do not describe the current mission results.

# Historical revision: 0.37

Both native ABI libraries are rebuilt from the current sources. Original core
archives and all 64 exported maps are external inputs and are excluded from the
APK and source archive.

- 64/64 original-map startup/render/save checks pass after 4,800 frames, followed
  by exact snapshot restore and 240-frame continuation comparison.
- All 64 assisted objective attempts pass the engine/save checks; 60 reach the
  original victory triggers. These are assisted diagnostic traversals, not
  unassisted human playthroughs. Every intervention is described in the runner.
- 8/8 focused mission checks pass, including Eye of the Storm's actual Command
  Center, SCV cargo returns, Gantrithor combat, Interceptor losses/replacement,
  Overmind destruction and the original finale victory sequence.
- 212/212 real-data gameplay checks pass, including all three races' refinery
  removals, loaded turret-unit deaths and hero fighter lifetimes.
- Android checks cover real world saves and fresh-process continuation,
  all 64 original mission archives, resource-error text/PCM, control presets,
  customization/persistence, gesture dispatch, hover behavior and splash font.
- Patch reconstruction, snapshot schema 1 compatibility, schema 2 defense state,
  synthetic feedback/mission regressions, static map references, signatures,
  JNI exports and 16 KiB alignment pass.

## Victory attempts still unresolved

| Mission | ID | Result |
| --- | --- | --- |
| The Dylarian Shipyards | expterran02 | Running after the assisted attempt |
| Ruins of Tarsonis | expterran03 | Running after the assisted attempt |
| Vile Disruption | expzerg01 | Running after the assisted attempt |
| To Slay the Beast | expzerg08 | Running after the assisted attempt |

These stalled attempts are not proof of broken missions. Their objective chains
still need directed play, including rescue/capture sequences and custom scores.
No attempt directly edits victory, switches or original trigger code. Diagnostic
assists include movement, enemy removal, resource/countdown changes, ordinary
unit creation and player invulnerability/healing.

Original campaign recordings and complete menu/briefing artwork are unavailable.
The supplied core font payloads are unreadable FONT data; the Android check uses
the readable fallback, while original-font visual parity remains unverified.
Seven maps' leaderboard displays remain unimplemented. No physical device was
tested. The strict full release gate remains incomplete; raw results and any
accessibility failure are preserved. The emulator's System UI stopped responding;
after restarting it, the foreground accessibility connection still did not attach.
The revision suite's UI logic checks pass, but its foreground/screenshot check
remains incomplete. See docs/FIXES-0.37.md and the current
validation/native-*-v37.json reports. Earlier sections are historical evidence.

# Historical revision: 0.36

Both native ABI libraries are freshly rebuilt. The uploaded original core data
and 64 exported campaign maps are now used by executable checks, and are excluded
from the downloadable APK and source archive.

- 64/64 unattended mission startup, render, complete snapshot round-trip and
  240-frame exact continuation checks pass (up to 4,800 initial frames).
- 7/7 focused mission checks pass: chrysalis hatch/Kerrigan death, True Colors
  Lurkers and replacement larvae, both Korhal routes, Kel-Morian minerals,
  Khalis pickup and Duran's entrance. Objective checks use documented diagnostic
  actions; Duran's entrance runs without intervention.
- 202/202 gameplay matrix checks pass with original core data.
- Android production JNI saves and restores real zerg04 and expzerg05 world
  states, compares continuation and resaves their loaded maps. True Colors also
  passes after a separate process restart. The two saves are approximately
  128 KiB and 315 KiB, respectively, without sparse archive padding.
- All 64 original mission imports again pass Android save/load and native CHK
  byte comparison. Atomic overwrite, corruption rejection, legacy format,
  command slots, hover controls and mission export checks are retained.
- Patch reconstruction, native save/feedback/mission regressions, the static
  64-map trigger audit, package signatures, JNI exports and 16 KiB alignment pass.

These are not full campaign playthroughs. Original mission recordings and full
menu/briefing artwork are absent from the map-only export and supplied core
archives. Seven missions' leaderboard displays remain unimplemented. No physical
device was tested. The stricter full release gate remains incomplete; its
original requirements and the actual accessibility results are preserved.

See docs/FIXES-0.36.md and validation/native-*-v36.json. The following sections
are historical results, not additional fresh 0.36 evidence.

# Historical revision: 0.35

Save archive and campaign-ID validation bugs are fixed. Both Duran variants have
Cloak/Decloak bottom left and Lockdown bottom centre. Native world serialization
and simulation are unchanged; both signed ABI libraries are retained from 0.34.

64 original campaign imports now pass Android save/load and native CHK readback,
including True Colors resaving without its original import bundle. Existing
raw-map saves remain supported; process-restart persistence is checked separately.
The native snapshot, feedback and mission suites pass. The expanded mission
suite performs 8,414 condition dispatches over all 13 types used by the maps.
The static audit checks all 64 maps, 1,869 triggers and branching mission routes.
Package signature, JNI, APK ZIP integrity and 16 KiB alignment checks pass.

These checks do not certify full campaign playthroughs. Original AI scripts and
core unit, terrain, artwork and audio data are absent, and no physical device was
tested. Seven maps use leaderboard displays that remain unimplemented; their
objective triggers are separate. The older Android revision suite retains its
actual accessibility result, including a failure if Android foreground detection
fails. Full release gates are not weakened and remain incomplete.

See docs/FIXES-0.35.md and validation/native-*-v35.json. The following sections
are historical evidence, not additional fresh 0.35 results.

# Historical revision: 0.34

Both native architectures were freshly compiled. The signed APK preserves the
update certificate and passes ZIP integrity, JNI exports, architecture and
16 KiB alignment checks. Save/load schema 1 is now implemented with six atomic
slots. Both live-game menus and the Single Player Saved Games button are wired.

Current checks: four native snapshot groups, a fresh-process snapshot read,
twelve native feedback groups, five original-mission groups (64 CHKs), six
Android save/persistence/menu groups, six Android hover/intro groups and eight
Android export checks pass. Snapshot tests cover relocated references, pools,
orders/production, creep, resources/research, mission/AI state, fog, replay,
trigger waits, corruption and map mismatch. The Android process is stopped
between writing and reopening a saved file. Android file tests use synthetic
payloads; they do not constitute an original-data campaign save/load test.

The complete release gate remains incomplete. Original core assets/audio,
full campaign save/load playthroughs, custom-bot continuation, original-art
comparisons and physical-device testing are unavailable. The older Android
revision suite's actual result and any foreground accessibility failure are
retained in its report. This APK is a feedback candidate.

See docs/SAVES-0.34.md and validation/native-*-v34.json. APK/test APK hashes bind
Android evidence; source hashes bind host and patch checks. The sections below
are historical and are not fresh 0.34 evidence.

# Historical revision: 0.33

Both Android native architectures were rebuilt from pinned source and the full
ordered patch stack. The signed APK retains the existing update certificate and
passes ZIP, JNI, architecture and 16 KiB alignment checks.

Current checks: five original-mission groups (64 CHKs), eleven synthetic native
feedback groups, six Android hover/intro groups and eight Android export checks
pass. The True Colors check exercises the original Give Units action for both
neutral Hatcheries, then checks initialization, production timers/retry, the
three-larva cap and resumption. Original creep placement and a full mission
playthrough are not claimed. Android hover checks use shipped UI classes and
synthetic hits; intro choices are checked through the actual chooser callbacks.
Original chooser artwork and cinematic playback are not tested.

The older Android revision suite passes its ten logic checks, including JNI and
mixer loading, then fails the foreground-window check because accessibility
reports the Android system window. The whole suite remains recorded as failed.
The full release gate is incomplete; this build is a feedback candidate.

See `docs/POLISH-0.33.md` and the current `validation/native-*-v33.json` reports.
APK/test APK hashes bind Android evidence; source hashes bind native checks.
Original core assets, original-art comparisons, full campaign playthroughs and
physical-device sound/input checks remain outstanding. Historical sections below
are not fresh 0.33 results.

# OpenBW Android 0.28 validation

This release rebuilds both native ABIs and changes Android presentation,
audio lifetime, campaign movie flow, map camera bounds and placed add-on linking.
The native gameplay matrix was rerun for this release; its results are not
inherited from 0.26 or 0.27.

## Current release checks

All five Android suites passed on the final APK. The release gate verifies their
results against the exact packaged APK and test-APK SHA-256 values. No app errors
appeared in the collected AndroidRuntime/OpenBW error log:

| Report | Scope |
| --- | --- |
| `validation/native-feedback-v28.json` | Continuous title music; logo chooser; letterbox clipping; tutorial/movie order; silent splash taps; voice-clock captions; Hatchery rally and Lair; unarmed command cards; build and Egg Cancel; Den/Colony slots; tips; same-type portrait transition; pressed Menu button; resource panels; intermission-to-next-mission flow |
| `validation/native-android-v28.json` | Campaign chooser and briefing; disabled Mutalisk prerequisite label; Egg production; Lair morph; native mixer and AudioTrack; results; custom games; HUD; portraits; background/resume and introduction |
| `validation/native-polish-v28.json` | Independent audio channels; focus loss/resume; mute/background handling; phase-aware music; dialogue ducking; modal isolation; smooth menu movement/list inertia; slider touch; command drag cancellation and App Options |
| `validation/native-parity-v28.json` | Classic menu layout/navigation; custom-map validation/start; practice and computer-slot selection; briefing speech; settings; real touch gestures and placement confirmation/cancellation |
| `validation/native-gameplay-android-v28.json` | Busy Lift Off; blocked landing/add-on placement; completed Machine Shop; Nydus entrance and exit through Android command-card touches |
| `validation/native-package-v28.json` | Version/signature/update key; JNI bindings; both ABIs; asset bytes; 16 KiB alignment; current test identities; no browser runtime |

Tests use Android 9/API 28 x86_64, emulator 37.2.12 at 960 × 640,
software CPU emulation and SwiftShader without KVM. Real MotionEvents exercise
menus, command cards and placement. Direct unit selection, resource grants,
accelerated simulation and forced outcomes are test fixtures. Screen captures
are checked against the user's supplied original-game references.

Audio checks verify nonzero PCM, independent voices and an active Android
AudioTrack. Focus callbacks are invoked directly to test interruption/recovery.
The emulator has no host speaker output. Physical speakers, Bluetooth routing,
other apps' focus requests, Android 15 behavior and phone frame rate are not
established by these runs.

## Fresh native and import checks

`validation/native-gameplay-v28.json` records 202 passing checks and zero failures:
all 50 standard structure types, 39 train/morph unit types, both Templar merges,
both ammunition types, all 24 research items and all 50 upgrade types through
their maximum levels (82 upgrade completions), plus prerequisites, cancellation
and construction edge cases. `docs/GAMEPLAY-TESTS-0.26.md` describes the matrix
fixtures and coverage; the matrix executable was freshly compiled and rerun.

`validation/native-presentation-v28.json` checks original Terran 3 speaker camera
movement and both bunker pings, two Factory/Machine Shop connections in Brood War
Zerg 2, bottom-map visibility at four viewport/zoom combinations, unarmed command
eligibility, producer-only rally (including mission-restricted Hatcheries),
Escape without a scan code, music surviving game cleanup, and native
playback with sound of the greater-than-64 MiB Brood War introduction.

`validation/native-import-v28.json` records fresh combined imports of 31 original
maps, 33 expansion maps, 13 original cinematics and 4 expansion cinematics. The
new expansion movie bundle is independent of the original movie bundle. Original
archives remain external; reimport the campaign archives once to add the movies.

`validation/native-patch-preparation-v28.json` starts from the pinned pristine
engine archive, verifies gameplay-patch detection/application, checks coexistence
with presentation changes and proves a second preparation is byte-identical.
The previous reverse dry-run could autodetect the wrong patch direction and
silently skip gameplay fixes. Forced direction fixes this; both release ABIs were
rebuilt after the correction. The first fresh gameplay run exposed four failures;
the corrected fresh run passed all 202 checks.

## Comparison and scope

The current comparison uses the user's supplied original-game screenshots and
new Android captures. Retained browser captures and earlier browser execution
remain in `validation/browser-reference-v25.json` and
`validation/campaign-v22-parity.json`; the browser was not rerun in this pass.

All 64 catalog maps retain earlier startup/advance evidence in
`validation/native-campaigns-v23.json`. This is not full campaign-playthrough
coverage. Existing imports are preserved by the unchanged package/signing key.

Briefing lines follow the playing voice clock. Line boundaries are estimated from
transcript length and punctuation because the CHK/WAV files contain no exact word
timestamps. This avoids showing the whole upcoming transcript, but does not claim
word-perfect alignment. Selection-transition static is synthesized; original
portrait borders, progress bars, fonts, tips and sounds come from local imports.

## Repeat the checks

Build the application before the separate test APK:

```sh
python3 scripts/build.py
python3 tests/build_instrumentation.py
adb install -r dist/OpenBW-Android-0.28.apk
adb install -r build-native/instrumentation/native-tests.apk
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativeFeedbackInstrumentation
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativeInstrumentation
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativePolishInstrumentation
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativeParityInstrumentation
adb shell am instrument -w org.openbw.androidtest.validation/org.openbw.androidtest.NativeGameplayInstrumentation
python3 tests/native_patch_preparation.py
python3 tests/build_native_host.py gameplay
build-native/host/native-gameplay /path/to/private/game-files app/src/main/assets/native/weave.scx validation/native-gameplay-v28.json
python3 tests/build_native_host.py presentation
build-native/host/native-presentation /path/to/private/game-files
python3 tests/native_package.py
```

The device needs the user's imported game files, including the cinematics for the
feedback suite. `--skip-engine` on the application build reuses included native
libraries. Record pulled Android reports and tested APK/test-APK hashes in the
corresponding `validation/` files before the package gate. The native report
wrappers also record SHA-256 values for their tested source files. No test classes
or private original game files are included in the application APK.

## Remaining limits

Campaign AI still lacks complete multi-town behavior, coordinated transports and
tactical spellcasting. Some mission behavior remains incomplete. Custom games
support one native computer opponent. Save/load, replay loading and multiplayer
are unsupported. Replay export for custom games remains available; testing cheats
disable it. Campaign cinematic slots and progression are now implemented.

Every combat matchup, spell target, long match, full campaign playthrough and
Activity recreation scenario has not been tested. Physical-device audio,
performance and large-import testing remain necessary. Original MPQs, campaign
maps, voices, artwork and test screenshots are excluded from the APK/source
package. The freely licensed Weave test map is included.

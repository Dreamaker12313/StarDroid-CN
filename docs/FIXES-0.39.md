# OpenBW Android 0.39

- Clear the indexed world framebuffer before every terrain render. Camera bounds
  still use the visible map area above the console; blank areas past the map no
  longer retain the preceding frame. The minimap remains a separate overlay.
- Prune dying and invalid selection IDs before rendering the card and wireframes.
  A group reduced to one survivor immediately gets the 64-pixel single wireframe.
- Default the selection cursor to the left. Migrate the old preset's right-side
  default while preserving an explicitly customized side.
- Add ten optional control group buttons, 1–9 and 0, disabled by default. Hold to
  assign, tap to recall, double tap to center. Input respects pause/control locks;
  dead units are excluded, and the existing snapshot group state is reused.
- Use Load frame 309 and Unload frame 312 from the supplied Brood War orders.dat
  highlight fields and cmdicons.grp. Slots remain bottom left and bottom right.
- Fit every opening-text page within x=32…608 and y=32/52…448. Short pages retain
  the requested 1.5× green font; long pages shrink only enough to fit, recalculating
  wrapping and respecting explicit line breaks. Lower-left pages remain bottom
  aligned. Layout is cached per page.
- Infested Kerrigan: Consume middle right, Cloak/Decloak bottom left, Ensnare bottom
  middle, Psionic Storm bottom right whenever that technology is available. Other
  Ghost and Ghost-hero slots retain Cloak left / Lockdown middle on the bottom row.
- Treat all six mission beacon types as invincible for combat targeting and damage,
  including ordinary, hero, direct weapon and spell damage. Scripted removal and
  ownership transfer remain available. The Protoss Fleet Beacon tech building is
  deliberately outside this marker-type range.

The Terran ready room is checked alongside Zerg and Protoss using original decoded
SMK frames, animation timing and production hover hit testing. Its existing
projector-under-planet ordering and hover alignment are retained where verified.

Validation results are recorded in VALIDATION.md and validation/*-v39.json.
Original game archives, extracted maps and original-art captures are external test
inputs and are not included in the source or APK. The supplied exports do not
contain original mission opening text or campaign speech. Exact mission-by-mission
splash/font parity and unassisted campaign playthroughs remain unverified.

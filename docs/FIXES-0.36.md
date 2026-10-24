# 0.36 — Original-data campaign checks

This build retains the sparse mission save fix and Duran command layout from
0.35. Both Android native libraries are rebuilt from the pinned engine and patch
stack. The save formats and signing key are unchanged.

Testing with the supplied StarDat, BrooDat and patch archives exposed five more
problems:

- A missing campaign recording could match a deleted MPQ hash-table entry and
  crash the mission. Deleted entries now preserve lookup chains without being
  treated as readable files; empty tables also return a clean miss.
- Transmissions without recordings completed immediately. They now use the
  original map's recorded duration. Present recordings still determine timing.
- Reused unit/projectile slots retained dormant movement values. Initialization
  now clears these values, so loading a save continues identically to an
  uninterrupted game. Four of the 64 maps exposed this difference before the fix.
- The location-based Ally/Enmy scripts incorrectly targeted the human player.
  They now change the relationship between the triggering player and owners of
  units in the specified region. This restores the entrance fight and Duran's
  arrival in Patriot's Blood. Campaign AI remains an OpenBW implementation,
  without a claim of frame-perfect original-engine parity.
- Doors reached their final animation frame but retained a non-interruptible
  order. Completion now releases that order before returning to idle, allowing
  later close/open triggers to work. The regression uses delayed animation
  signals and the original non-interruptible order behavior for all four doors.

## Validation scope

All 64 original missions run unattended for up to 4,800 simulation frames,
render, save, reload into a fresh mission instance, and compare both the complete
restored snapshot and 240 frames of continuation byte for byte. AI errors are
checked. A mission can legitimately lose while unattended; outcomes are recorded.

Seven additional checks exercise the chrysalis hatch and Kerrigan death,
True Colors' three burrowing Lurkers and replacement larvae from transferred
Hatcheries, both Assault on Korhal branches, the Kel-Morian resource objective,
the Khalis pickup, and Duran's opening. These keep original triggers but use
documented diagnostic interventions for the objectives. Duran's opening runs
without intervention. They are not full combat playthroughs.

Android additionally verifies real chrysalis and True Colors saves through the
production JNI/file path, identical continuation, resaving the loaded map and
True Colors persistence across a process restart. The tested saves occupy
131,062 and 322,980 bytes. The original-data gameplay matrix passes all 202
checks. All 64 exported map archives also pass Android save/load/readback.

The source includes the raw validation reports and reproducible harnesses.
Original game archives and campaign maps remain external inputs and are not
included in this download.

Remaining limits: full campaign completion, mission voice playback from the CD
archives, original menu/briefing artwork comparisons, physical-device audio and
touch, and seven maps' leaderboard displays. The stricter full release gate
continues to report incomplete evidence rather than treating these as passed.

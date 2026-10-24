# 0.44 — Terran feedback and nuclear strikes

- Placement errors resolve the original Drone, SCV and Probe sounds by filename.
  Protoss power errors use the separate Probe error; invalid Terran landing uses
  the advisor's landing-zone line. A landing obstructed after the order uses
  the separate landing-interrupted line. No cross-race sound-table offsets.
- Siege Tanks announce readiness after their siege/unsiege animation finishes.
  Completed Terran structures use the SCV construction-complete line; addons use
  the advisor's addon-complete line. Startup and rescued structures stay quiet.
- Attached addons remove the parent's addon construction buttons. Detaching an
  addon restores the choices. Covert Ops and Physics Lab occupy the Science
  Facility's bottom-left and bottom-middle command slots.
- Unit cost tooltips include the original supply glyph for the produced unit's
  race, including mixed-race armies and half-supply costs.
- Undetected cloaked enemies show a faint animated background refraction inside
  actual vision, using their original GRP silhouette and tileset cloak ramp.
  Friendly/detected cloaks use the original trans50.pcx transparency table.
  Shimmer does not expose selection circles, health bars, minimap dots or unit
  targets. Revealing terrain does not extend cloak sight or detection. Burrowed
  units and hidden traps remain concealed. This implements the original style;
  exact retail pixel-for-pixel distortion has not been established.
  Reference: https://classic.battle.net/scc/terran/tspecial.shtml (Cloaking).
- Attack notifications originate from hostile damage, including shield hits,
  missiles whose firing unit has died, and the application of enemy Plague.
  Burning structures, Stim/self damage, allied damage and direct trigger health
  changes no longer generate false attack notifications. Base and forces use
  their respective advisor lines. A repeated hit cannot restart an active ping;
  nearby hits share that ping, while separate fights can alert independently.
- With a selection that has no Move button, tapping another unit selects it.
  Explicit Rally Point targeting is still available from the command button.
- Ghost Nuclear Strike uses the public NukePaint order and original mushroom-
  cloud icon (cmdicons.grp frame 311). It remains visible but grey without a
  completed missile in a ready silo. Launch consumes that missile. The internal
  unit-targeted painting path also retains the actual target instead of aiming
  at the Ghost itself.
- Verified Drawing of the Web against the original CHK: the human player has
  Queens explicitly enabled. Mutalisks, Guardians, Devourers, Spires and Greater
  Spires are disabled, and Ventral Sacs has maximum level zero. Those intentional
  mission restrictions are preserved.

The package ID, signing key and save schema are unchanged. See VALIDATION.md and
the version 44 reports for the executed checks and device-testing limitations.

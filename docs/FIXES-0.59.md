# OpenBW Android 0.59

Install `OpenBW-Android-0.59.apk` over the existing app on every participating
device. Do not uninstall. Imports, preferences and saves are retained.
Multiplayer build 60 rejects older simulation builds before map transfer.

## Hero commands and timing

- Every hero has a fixed command-card slot. Finishing an upgrade leaves its
  original space empty without shifting any hero icons. Engineering Bay heroes
  occupy slots 2–7, with upgrades at 0–1 and Lift Off at 8. Forge and Evolution
  Chamber heroes occupy 3–8, with upgrades at 0–2 (zero-based slot numbers).
- Build time is taken directly from the normal counterpart's original data.
  Duke's Tank/Siege forms share the normal Tank build time. Hero costs, supply,
  statistics, prerequisites and one-per-player limits are unchanged.

## Hero Mode computers

- Easy, Medium and Hard all pursue their race's six heroes. The old Hard-only
  12,000-frame delay is removed. Opening hero preparation starts after 600
  frames once six workers are complete.
- Pending building orders retain their construction funds while the worker
  walks to the site. The opening goals are Devouring One, Raynor (Marine) and Fenix (Zealot).
  The AI saves for their required buildings instead of continually spending
  that budget on workers and unrelated production.
- After queuing the first hero it pursues the other heroes' technology. It
  adds a second hero/upgrade building as workers grow, and a third after
  expanding. A free producer and a resource budget keep ordinary upgrades
  from indefinitely delaying heroes. Additional buildings can upgrade while
  heroes train. Existing expansion budgets and actual resource costs apply.
- These changes only apply to custom and multiplayer games with Hero Mode on.
  Campaign build orders and Hero Mode-off strategy are unchanged.

## Selected-unit text

- Status and Detector text share a bounded line. The normal font is retained
  when it fits; longer combinations use the smaller original font and trim
  within the panel. Inspecting the line shows the full text.
- The original status colors, including red Unpowered, are preserved. Kills,
  supply and other detail rows retain their own space.

## Spire requirements

Level 3 Zerg air attack and carapace require a completed Hive. Both an ordinary
Spire and a Greater Spire can research them. No Greater Spire requirement is
added, and the original rules are tested in both expansions.

A reused visual-effect image now clears its old frozen position, fixing a
long-match saved-continuation discrepancy found by the Hero Mode tests.
Loss tracking also clears the old unit ID when its pool slot is recycled, so
a later unit with the same wrapped ID is counted correctly.

See `VALIDATION.md` for test scope and remaining physical-device checks.

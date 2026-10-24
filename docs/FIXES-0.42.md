# 0.42 — Commands, visibility, interface and Terran economy

Feedback is an innate Dark Archon spell. The unused Feedback research entry no longer appears at the Templar Archives; Mind Control and Maelstrom remain researchable.

## Commands and visibility

- Undetected enemy cloaked/burrowed units are excluded from world rendering, minimap rendering and tap/drag selection. Detection still reveals them; the player's own cloaked units remain visible.
- Mission-start explored terrain gets an initial snapshot of its existing buildings and resources. Current vision is still required for mobile units, and later construction in fog is not exposed.
- Carrier and Reaver ammunition buttons check every eligible selected producer. A full primary unit no longer hides the button from another selected producer with space.
- Shield Batteries have Recharge Shields in the top-left command slot, using original command icon 308. The command targets a unit or location; an empty battery reports insufficient energy.
- Both Archon merge commands are grey until at least two eligible matching Templars are selected.
- Load is hidden when cargo capacity or the transport upgrade is unavailable. Unload is hidden when empty. Linked Nydus loading requires a completed exit.
- Move, Attack, Patrol and other targeted commands show a target prompt until the order is issued or cancelled.
- Invalid placement keeps the placement preview active and reports the original stat_txt warning, with original worker error audio, for blocked terrain, missing creep/power, missing geyser, unexplored/out-of-bounds locations and unreachable sites. The touch confirmation button accepts invalid attempts so the reason can be explained.

## Interface

- The original title artwork precedes the main menu. Tap it or press Back/Escape to continue.
- Labels belonging to sliding menu panels appear only after entry completes and disappear as exit begins.
- Resource/energy/supply/placement errors use the original blue font ramp above the console.
- Tooltip mineral and gas costs use their original resource icons beside the numbers.
- Skirmish map import moves into the map-list header. Five map rows and pagination fit above the original game-type and player-slot controls. Difficulty occupies the unused subtype row.
- Video Options has an Interface Sizes page: resources, command buttons, descriptions/messages, and selection/move buttons. Settings persist, and command hit regions scale with their artwork. Command enlargement is capped at 120% to preserve the adjacent portrait/menu area.
- The redundant normal-production/reset-speed cheat action is removed. Instant production has one checkbox; game speed remains on its existing options page.

## Terran skirmish AI

The original TLOx/TMEx/THIx script data still controls scripted attacks. The melee manager now adds the economy and support work those campaign scripts assume:

- Worker allocation across all completed depots and nearby active mineral/refinery lines, with three gas workers per refinery. Tighter resource-line limits avoid assigning workers to distant patches across cliffs.
- New Command Centers near available resource groups, scouting before construction, extra refineries and worker transfers. Mining and production preserve the scout's movement order; unsuccessful approaches retry other resource groups.
- Building placement keeps wider SCV passages, preserves resource approaches, reserves add-on room and searches around additional bases as they complete.
- Replacement workers, resumption of abandoned unfinished buildings, and retries for local building orders that never begin construction.
- Medic support, Ghost/Science Vessel technology, and Battlecruiser production at difficulty-dependent stages, using normal resource and technology requirements.
- Resource reservations prevent cheaper continuous production from starving ready advanced-unit requests.
- Medics and Science Vessels accompany attacking troops. Sieged tanks count toward tank requests.

This is an OpenBW melee manager around original script data, not a claim of frame-perfect Blizzard AI parity. It does not grant the computer bonus resources.

## Save continuation

Reused projectile/unit motion objects clear their prior movement targets before initialization. This fixes a continuation mismatch when successive shots reuse a slot at the same position; save schema 2 remains unchanged.

## Verification

See VALIDATION.md and the versioned JSON reports for the checks actually run. Campaign startup/render/save-continuation checks are not full mission playthroughs. Device UI, audio routing and touch behavior require testing on Android hardware before calling this a production release.

# OpenBW Android 0.41

## Commands and feedback

- Normal and hero Carriers/Reavers hide their ammunition button when completed
  plus queued Interceptors/Scarabs reach the original DAT capacity. Losing or
  cancelling ammunition exposes the button again.
- Scenario-available, unresearched abilities remain visible and grey. Scenario-forbidden targeted spells, cloak and burrow remain hidden. Research enables the button regardless
  of current energy; attempting an unaffordable spell gives the energy warning.
- Both Archon merges show their original build-time progress. The intermediate
  collision-reset order is included, so the ready voice cannot fire before the
  merge. The voice plays once when the summon finishes.
- Transport panels use tranwire.grp, original command-frame borders, statdata.bin
  positions and units.dat cargo space: infantry one cell, medium units a tall
  two-cell frame, Tanks four cells. Tapping a passenger unloads that passenger.
- Resource, energy and supply warnings use the original stat_txt.tbl messages as
  red game text with a shadow, centered above the console. No tooltip panel is
  drawn. The original advisor lines are retained, including AdErr06 for energy.
  Supply messages/sounds follow the race being produced in mixed-race armies.

## Terran skirmishes and maps

The previous opponent used the original TLOx Easy campaign script. New games
can select Easy (TLOx), Medium (TMEx) or Hard (THIx). The imported aiscript.bin
and bwscript.bin still decide army composition and attack timing. These are
campaign scripts adapted to a normal four-SCV melee start, not a claim of exact
retail melee AI behavior. The manager supplies prerequisites and maintains a
16-SCV economy, with separate Science Facilities for Covert Ops and Physics Lab.

A producer cannot train while its add-on placement/build order is in progress.
Building placement reserves the structure and add-on area for both existing
buildings and queued SCV construction orders. This prevents production from
stalling or later facilities from occupying another building's future add-on.
The placement search extends farther from the starting base on larger maps.

Custom Game stores imported maps by content hash, deduplicates them, remembers
the selected map, and pages through the collection. Choose individual SCM/SCX
files together or import a ZIP. Imports validate the scenario and are bounded
to 128 maps, 64 MiB per map and 256 MiB uncompressed per batch. ZIP paths are
never used as destination paths.

The separate eight-map pack contains unchanged maps from Blizzard's official
map archive. Its README includes the download source and import instructions.

## Scope

The 15 host checks pass. Android visual verification is pending because the
emulator could not complete setup. See VALIDATION.md for exact evidence.

The Terran manager still uses one base economy; it does not implement a full
expansion strategy or transport-based island attacks. New difficulty affects
new matches; saved games retain their original script threads and difficulty.
Previous campaign fixes and save format compatibility remain in place. This
revision does not claim fresh unassisted playthroughs of every campaign.

Reference data: original installed game archives; Blizzard's Carrier, Reaver
and Dropship unit pages; GPTP's transport status and cloak energy-error hooks:
https://github.com/BoomerangAide/GPTP
https://classic.battle.net/scc/protoss/units/carrier.shtml
https://classic.battle.net/scc/protoss/units/reaver.shtml
https://classic.battle.net/scc/terran/ud.shtml
https://classic.battle.net/scc/OS/1298.shtml

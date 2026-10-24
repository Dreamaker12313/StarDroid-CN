# OpenBW Android 0.40

Install over the existing app to retain imports, settings and saves. Restart
Emperor's Flight to replay its corrected opening; an old save cannot recreate
reinforcements already lost by its opening triggers.

## Changes

- **Emperor's Flight:** CHK/UPRP's lifted-building property now makes the five
  reinforcement buildings airborne before the original move/give triggers run.
  The Command Center, Barracks, Factory, Starport and Engineering Bay can reach
  the southwest staging area and transfer to the player.
- **Computer tanks:** computer-controlled tanks siege against visible ground
  targets within siege range. Scripted Move orders are preserved. Attack-wave
  tanks unsiege to continue moving when no ground target remains in range.
- **Map edge:** the world viewport and its bottom camera clamp end at the center
  console's top, logical y=376, across zoom and widescreen settings. World pixels
  are clipped before drawing the console; the minimap remains independent.
- **Control groups:** the optional numbered bar is at the top left. It remains
  disabled by default and leaves room for enlarged resource counters. Mission
  countdowns move below the top row when needed to avoid overlap.
- **Resource size:** Game Menu → Options → Video has 100%, 125% and 150% sizes.
  Minerals, gas and all active races' supply icons/text scale together. The
  preference survives restarting the app.
- **Attack/move toggle:** an original command-icon button sits above the selection
  cursor, with a 16-pixel gap. It follows the cursor's Left/Right placement and
  changes army ground taps between attack-move and move. Hide it in Touch Controls
  → Command settings. Ground-tap orders remain disabled by default; changing
  modes does not override that separate setting.
- **Traps:** physically retracted traps are hidden until their RevealTrap opening
  starts, including when map-reveal/shared vision exposes their terrain. All six
  trap types use the same state-based visibility rule. Doors are unaffected.
- **Terran skirmish AI:** choose Terran in the computer race field of Custom Game.
  This first Easy opponent executes the original Brood War `TLOx` script from
  the imported game data. Its native manager supplies prerequisite buildings,
  mining, production, supply, add-ons, base defense and attack orders. Starting
  resources stay at the ordinary 50 minerals and zero gas. The existing Zerg
  opponent remains selectable. AI state is saved with the game.
- **AI construction:** stale worker reservations after failed placements are
  released so supply can be retried. Builders are excluded from gas reassignment.
  The skirmish manager leaves walking corridors and room for future add-ons.
- **Loading saves:** the duplicate-death guard is rebuilt from the restored
  world so casualties after reloading are counted correctly. Existing save
  formats remain compatible.

## Scope and verification

See VALIDATION.md and the current `validation/*-v40.json` reports for the executed
checks and their exact inputs. Original game assets and maps are external test
inputs and are excluded from the APK/source distribution.

The Terran opponent is an initial ground-map implementation using an original
**campaign Easy** script, not the original melee script or a complete recreation
of Blizzard's AI manager. Expansion management, island transport tactics, all
race/difficulty choices and exact retail parity remain future work.

Automated campaign startup/restore checks and assisted route checks are not
unassisted human playthroughs. Original mission opening text and campaign speech
are still absent from the supplied data, font parity remains limited by the
fallback font, and the seven previously documented leaderboard displays remain
unimplemented. This is a feedback build, not a claim of complete retail parity.

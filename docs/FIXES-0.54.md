# OpenBW Android 0.54

Install the APK over the existing app on both phones. The package and signing key
are unchanged; no uninstall is needed. Both phones must run 0.54 for multiplayer.
Google Play services and internet access remain unnecessary.

## Controls and results

- The entire victory/defeat screen slides in from the left, including its background.
- Passengers are deselected when loaded into a transport or bunker. Recalling a
  control group does not select passengers still inside a transport.
- Land replaces a pending addon placement with ordinary landing placement.
- Airborne structures hide their training, research and upgrade controls. Addon
  and Land controls remain available as appropriate for that structure.
- Multiplayer results return to the main menu, including after the other human
  leaves and the surviving player continues against computers.

## Game setup

Custom games support a computer in each available nonhuman slot, with independent
race choices, shared difficulty, and Melee or Free for All. In Melee the computers
are allied with one another; in Free for All every player is an opponent. Map
starting locations limit the number of slots (up to eight).

The map browser scrolls by dragging the list, using its arrows, or dragging the
original GRP scrollbar. It has no map pages. The import button has a frame. Both
solo and multiplayer map selection show a terrain thumbnail, with resources and
starting locations, sampled from the original tileset graphics. The lobby also
shows the map thumbnail.

Multiplayer uses the original connection-selection and lobby artwork and layouts:

1. Choose Bluetooth + Wi-Fi Direct or Bluetooth, your race and the game edition.
2. Choose Host Game or Join Game. Brood War is the multiplayer default.
3. The host selects a map, Melee/Free for All, computers, difficulty and game speed
   before creating the lobby. A second human slot is reserved for the other phone.
4. The host can also change computer slots and races in a new-game lobby. Both
   peers reload the agreed setup before Start becomes available again.
5. Start counts down five seconds, playing the original countdown sound each
   second. Changing away from the host app during the countdown cancels it.

There are two human phones, plus computers in the remaining map slots. Wi-Fi
Direct upgrades and Bluetooth fallback from 0.53 remain in place.

## Multiplayer saves

The host can use Save Game and Load Game from the in-game menu. Multiplayer has
six separate save slots so campaign and solo saves are preserved. To continue a
saved match later, choose Multiplayer > Load Saved Game and have the guest join.
Loading during a connected match returns both phones to the lobby automatically.
The saved map, rules, races, computer scripts, resources, world state and accepted
pending commands are restored on both peers before the countdown can start.

Saves are taken at a complete input-turn boundary, including when the game menu
is paused. Transfers are bounded, compressed when useful, checksummed, and checked
for matching core assets and restored simulation hashes. Each phone keeps its
own player identity and fog perspective; host-only display state is not copied
to the guest. Saved-game lobby settings are fixed to the saved match.

Existing single-player saves retain their earlier snapshot format. Legacy
single-computer setup is migrated when an old save is loaded and saved again.

## New-install defaults

Allow zoom out is enabled, and Disable ground-tap orders is unchecked. Explicit
settings already stored by an existing installation are preserved.

## Validation scope

The source includes reproducible desktop protocol, socket, native-engine and
original-artwork rendering checks. Twelve independent native host/guest pairs
cover both game modes, both editions and all computer races; their turn hashes
and saved-game continuations match. Network tests cover countdowns, paused saves,
accepted commands, in-session reloads, fresh-lobby restores, malformed snapshots,
and departure of an eliminated human while computers remain.

These are automated host checks. Physical-phone installation, touch interaction,
radio behavior, audible countdown timing and a complete multiplayer match still
need device confirmation. Original game data stays external to the APK/source.

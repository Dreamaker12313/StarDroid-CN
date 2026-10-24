# OpenBW Android 0.58

Install `OpenBW-Android-0.58.apk` over the current app on every participating
device. Do not uninstall. Existing imports, preferences and saves are retained.
Multiplayer build 59 rejects older simulation builds before map transfer.

## Custom and multiplayer games

- Choose **Melee**, **Free for All** or **Teams** under Game Type. Melee uses
  ordinary alliance rules, with computers allied by default; FFA makes every
  active slot an opponent. Teams fixes
  allies in the lobby: matching T1–T8 numbers share vision and victory, while
  keeping separate units, resources and technology. This is preset alliances,
  not classic Team Melee's shared economy/control.
- The host assigns teams beside player slots. Custom games support human/CPU
  teams. At least two opposing sides are required. An eliminated teammate waits
  for their side's result. Moving a player to another start moves their team
  with them. Saved games retain teams; loading cannot change their rules.
- **Hero Mode: On/Off** appears above the map name. It defaults off and is
  synchronized with all joining devices and saved matches.
- Engineering Bays, Evolution Chambers and Forges train six heroes each.
  Normal upgrades share the same building's production time. Heroes require
  their normal counterpart's technology, cost the discounted amounts in
  `campaign-heroes.json`, and consume their normal counterpart's supply.
- One living or queued instance of each hero form is allowed per player across
  all producers. Canceling or losing it releases the slot. Duke's Tank/Siege
  forms share a limit. Edmund Duke's tank replaces Norad II in the chart.
- Select Tassadar and Zeratul together and use **Merge Heroes** to create the
  original Tassadar/Zeratul Archon. It uses four supply and keeps both hero
  slots reserved until it dies. Ordinary Templar merges are unchanged.
- Heroes are optional custom/multiplayer content in either expansion. Campaign
  hero statistics, costs and scripts are unchanged. Prices are starting balance
  values, not results of multiplayer balance testing.

## Economy and original behavior

- A depleted main can send workers to reachable fresh mineral fields even when
  the computer cannot yet afford a new base. It avoids fields beside enemy
  bases, redistributes workers, and keeps harvesting depleted geysers.
- Expansion funds stay reserved while the builder approaches and places the
  new base. Empty old bases no longer prevent further expansion. Hard AI grows
  production capacity and attacks more often; it can purchase limited heroes
  when Hero Mode is enabled. Normal resource costs still apply.
- These macro changes apply to custom/multiplayer AI. Campaign build orders
  remain unchanged; the previous reactive detection support is retained.
- Restores retail Brood War Protoss prerequisite counting: a completed but
  unpowered tech structure still provides its prerequisite. The unpowered
  structure itself cannot train, upgrade or research and keeps its original
  red status, selection sound and empty command card. Terran add-ons still
  require attachment and can be claimed by another Terran by landing on them.

## Interface and sound

- Score-fill audio now accepts the original sound files instead of rejecting
  them at the smaller network-command size limit. Counters and composed fill/
  ending audio continue using the same 2.2-second playback clock.
- New/delete Player ID uses the main menu artwork with a translucent dark,
  rounded red dialog. Name entry uses the device keyboard, with Enter/Done,
  deletion, Cancel and Back handling.
- Hero/team controls use normal and hover menu colors, rounded red borders,
  fitted labels and bounded hit areas. Eight-slot layouts and both dialogs
  are rendered by the automated UI harness.
- The simple wireframe Pylon icon now has a surrounding ring with rear and
  front arcs. ToadWarrior's credit is retained.

See `VALIDATION.md` for the actual test scope. Physical Android input, audio,
Bluetooth/Wi-Fi Direct and performance confirmation remains pending.

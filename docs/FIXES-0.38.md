# OpenBW Android 0.38

## Missions and mixed-race armies

- Raid on the Dylarian Shipyards uses Player 4's custom score for its last
  platform, although that player slot is unused. Scenario counters now include
  explicitly named unused slots. Capturing the final ships can advance the mission.
- Ruins of Tarsonis's rescue highlights explicitly use a zero wait. The engine
  incorrectly waited for each rescue sound, allowing the departing dropship's
  cleanup trigger to remove the infantry and SCVs before they transferred.
  Transmission Set To/Add/Subtract timing now follows the map's timing fields;
  zero-wait highlights do not block behind unrelated dialogue.
- Vile Disruption is checked by visiting all seven Hives, observing the map's
  own counter and final waves, then reaching its original victory trigger.
- To Slay the Beast is checked with a Dark Templar attacking the Overmind and
  the original Raszagal ending. The Overmind's resurrection without a Dark
  Templar is an intentional mission rule.
- Building placement uses the building's race rather than the player's starting
  race. This fixes Eye of the Storm SCVs and captured/Mind Controlled workers.
- Supply totals are displayed independently for every race in the player's army.
  Worker build-menu icons also use the selected worker's race.

The mission checks use documented movement, healing/invulnerability, countdown,
resource and enemy-removal assists. They preserve the original triggers and do
not directly write victory, switches or capture counters. They are not unassisted
human playthroughs. Starting a fresh mission is recommended when testing an opening
that has already run incorrectly in an older save.

## Commands and controls

- Ghost, Sarah Kerrigan, Stukov, Duran and Infested Duran use Cloak/Decloak in
  the bottom-left slot and Lockdown in the bottom-middle slot. Duran's layout
  is retained. Infested Kerrigan keeps her separate spell layout.
- Touch Controls > Selection settings adds an optional cursor button: Off,
  Left or Right. It defaults to Right. Tap it, then drag once to select units
  without waiting for a long press. It disarms after that selection.
- Touch Controls > Command settings adds Disable ground-tap orders, checked
  by default, including for existing preferences. Explicit command targets and
  unit/transport targets still work. Minimap orders retain their own setting.
- Miscellaneous contains the testing cheats and Nearby enemies defend their
  base. Turning that off stops the added reinforcement response; original
  mission attack scripts continue normally.
- Eligible selected ground units enter a friendly Bunker, Dropship, Shuttle or
  upgraded Overlord when it is tapped. Zerg ground units can enter a linked Nydus.
- Transports expose Load at bottom left and Unload at bottom right. Bunkers
  unload immediately; flying transports ask for a landing location. Passenger
  icons occupy the cargo panel and can be tapped individually to unload.
- A linked Nydus exposes Load and View Exit. Units emerge immediately at its
  linked end, so it does not hold an unloadable passenger queue.

## Briefing presentation

- The Zerg room's background drip stays fixed during control-panel movement.
- The decorative support below Replay is separated from the sliding button.
- Zerg Start displays its hover animation without the idle animation covering it.
- Protoss Start blends the original movie with its matching room scenery;
  the old screen blend doubled the background and washed out the crystal.

Save schema 2 and existing import/save locations remain compatible. Original game
archives and mission files are external inputs and are not included in this build.
Exact validation results, asset limitations and physical-device status are in
VALIDATION.md and validation/native-*-v38.json.

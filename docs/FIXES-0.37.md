# OpenBW Android 0.37

Install over the existing app to preserve imported data, preferences and saves.
Restart Eye of the Storm from its beginning to get the corrected opening base;
a save made after the failed creation retains that old mission state.

## Gameplay fixes

- Eye of the Storm: original opening triggers can create Raynor's Command Center
  and depots before the first fog update. SCVs can return their mineral cargo.
- Gantrithor and Warbringer correctly detach destroyed Interceptors/Scarabs from
  their hangars, including fighters destroyed while inside. Replacement fighters
  can be trained and launched without corrupting the hangar lists.
- Hidden tanks/Goliaths complete parent death before processing their turrets.
- Scripted refinery removal leaves a valid neutral geyser. This fixes a crash
  during the scene transition in both Emperor's Fall variants.
- Provoked neutral campaign units enter ordinary guard behavior instead of
  aborting with an unsupported-AI error (seen in Escape from Aiur).
- Unaffordable unit/building commands reach the original error handler and play
  the race-specific advisor response with the on-screen resource message.
- Campaign bases recruit nearby idle defenders after attacks on their buildings
  or nearby harvesters. The response respects alliances, visibility, weapon
  targets and scripted orders. It uses a short delay and a limited local group;
  exact retail AI parity is not claimed.
- Native snapshot schema 2 preserves pending defensive responses and accepts
  older schema 1 world snapshots. The portable map/save container is unchanged.

## Controls and presentation

Use Game Menu > Options > Controls. Comfortable, Precise and Drag to select
presets can be customized and are saved independently of mission save slots.

| Group | Settings |
| --- | --- |
| Selection | Drag behavior, hold duration, tap tolerance, hold-tap selection, double-tap selection and its timing |
| Camera | Pan speed, pinch sensitivity, pinch zoom, reverse drag, minimap orders and hold timing |
| Commands | Ground-tap move/attack move, descriptions, description delay, placement confirmation and finger offset |

The gesture guide reflects the current settings. Mission opening text uses a
larger green font. Readable original FONT assets retain their shading; when
font payloads are unreadable, the UI falls back cleanly instead of failing.
The archive reader also supports checksum-enabled sector tables, including the
font entries in the supplied StarDat archive.

## Validation scope

Current results are recorded in VALIDATION.md and validation/native-*-v37.json.
The real-data campaign runner executes the original maps and triggers, renders,
saves, reloads and compares subsequent simulation snapshots. Its objective mode
uses documented assistance: moving units, removing objective enemies, granting
resources, advancing countdowns, creating required ordinary units, and protecting
player units. It never directly sets victory or changes switches/trigger code.
These checks are not unassisted human playthroughs. Unresolved objective attempts
are listed separately from engine or save failures.

The finale combat case sends Gantrithor into original anti-air defenses, loses
and replaces real Interceptors, then attacks the original Overmind and waits for
the original victory sequence. Minerals, hero invulnerability, movement and
nearby-defender removal are explicit test assists.

Original campaign recordings and complete menu/briefing artwork are absent
from the supplied core archives and map-only export. Seven mission leaderboard
displays remain unimplemented. Physical-device audio/touch and full campaign
playthroughs remain unverified. The strict release gate retains these limits.

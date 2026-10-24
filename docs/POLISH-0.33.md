# OpenBW Android 0.33

## Changes

- Campaign Give Units now uses the engine's ordinary trigger transfer path.
  True Colors starts both Hatcheries under a neutral controller. The old shortcut
  assigned their new owner and `return_to_idle`, skipping `InitCreepGrowth`.
  The normal path restores that initialization, starts the creep/larva secondary
  order, and updates sprite ownership, unit counts and the ownership notification.
- Mouse/stylus hover resolves the current command card every frame, so prices,
  requirements and descriptions remain current after selection or research changes.
  Touch inspection starts after 280 ms, supports sliding across buttons, and
  never executes an order on release, including when rendering is delayed.
  Short taps still activate commands; early drags and changed commands cancel.
- Unit production buttons include their actual scenario mineral/gas costs and
  supply. Supply is the resulting unit's total, rather than the extra supply of
  a morph. Two-unit eggs show the pair's cost and supply. Descriptions use engine
  type properties; actions, research and upgrades have explanatory text. Stat,
  production-cancel and More buttons also support inspection.
- Main-menu Play Introduction opens the existing Original/Expansion artwork and
  button layout. The choices target `smk/starintr.smk` and `smk/starxintr.smk`.
  Cancel returns to the menu; choosing an intro leaves the campaign preference
  untouched. Missing movies retain the existing archive-import guidance.

## Validation scope

Both native architectures are rebuilt. The original 64 CHKs are external test
inputs and are excluded from the APK/source distribution. The mission harness
uses the real True Colors Give Units action and both placed neutral Hatcheries,
then verifies ownership, initialization, production timer/retry, the three-larva
cap and resumption when a larva leaves. Unit graphics and terrain are synthetic;
this is not a full original-data campaign playthrough or a real-creep placement
check. Prior alliance, Lurker, trigger, trap, door, hero, sound and selection
regressions are retained. A native metadata check uses customized prices and
paired supply to catch hardcoded costs.

Android checks exercise the shipped tooltip and touch-inspection classes and
intro chooser callbacks with asset-independent state. Original chooser artwork
and movie playback require the user's imported archives. Current reports bind
the APK and test APK hashes; failed or absent checks remain failures. Full
campaign, original-art and physical-device audio validation remain outstanding.

## Next useful work

Save/load remains unimplemented, making it the largest practical gap for long
campaign missions. Original-data playthroughs should next verify the True Colors
opening and Hatchery, Agent of the Swarm's hatch sequence, and the reported door,
trap, briefing-font and Replay artwork issues on the device.

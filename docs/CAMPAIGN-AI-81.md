# Campaign AI audit — Revolution and original campaign startup

“Revolution” is original StarCraft Terran mission 5, catalog code `5`, archive path
`campaign/terran/terran05/staredit/scenario.chk`.

The Confederate AI is intentionally inactive at the beginning. The original map
starts most of its base already built, then activates the economy and attack
scripts after a mission event. It is not supposed to remain inactive forever.
No mission triggers, original AI bytecode, economy rules or combat behavior were
changed for this audit.

## Original map evidence

Trigger numbers below are zero-based CHK record indexes.

- Trigger 1 starts the Antigan rebellion when the player's Kerrigan reaches the
  Command Center. Trigger 11 runs the dialogue and handover; trigger 8 runs the
  original rescue script for the Antigan force.
- Trigger 9 sets switch 6 when a player unit enters location 18, the southern
  “Activate Computer -- Town” region. That location's exclusion mask is `7`,
  excluding all three ground elevations: this path requires an aircraft.
- Trigger 16 also sets switch 6 after the Confederate buildings in location 20,
  “Clear Combat,” have been cleared near the Antigan base.
- Trigger 10, owned by the Confederate force, waits for switch 6. It grants the
  original 6,000 minerals and gas, then starts `Ter5` at location 4, “Combat Town,”
  and `Te5H` at location 17, “Harvest Town.”
- The imported `Ter5` AI script maintains its existing Command Center, SCVs,
  Barracks, Factory, Starport, Academy and add-ons. It waits 6,000 AI frames before
  assembling the first four-Firebat attack, then waits a further 500 frames before
  ordering that wave. Assembly can take additional time. `Te5H` maintains the
  harvest base. These waits are simulation frames, not a fixed wall-clock promise.

Consequently, watching the enemy immediately after mission start is not a useful
production check. Both the original activation event and the script's delay need
to occur. Existing requested buildings also need not be rebuilt unless lost.

## Executed checks

`tests/native_campaign_ai81.cpp` uses the actual engine and caller-owned game
archives. Its focused Revolution case checks:

1. No Confederate production before activation; a ground unit in the southern
   region does not incorrectly activate its aircraft-only trigger.
2. Original Kerrigan rescue and Antigan rebellion/handover.
3. Both activation paths: clearing the original Confederate guard buildings and,
   separately after snapshot restoration, moving the rescued original Wraith
   into the southern trigger region.
4. The original first-attack delay, actual construction and training, mineral and
   gas collection beyond the map's 6,000-resource grant, and an attack wave.
5. Replacement of a destroyed original Barracks through the existing build
   request, followed by an exact snapshot/continuation comparison.

The focused run recorded two construction orders, four training orders and one
attack by frame 17,440; the first attack occurred at frame 14,972. Its resource
counters were 7,514 minerals and 6,432 gas, including the original 6,000 grant of
each, proving additional collection. The destroyed Barracks was rebuilt without
adding AI resources or injecting AI instructions.

`tests/run_campaign_ai81.py` also resolves every enabled AI-start action in all
64 original campaign maps against the installed original/expansion AI indexes,
and runs each original map for up to 4,800 simulation frames with its normal
startup triggers. All 609 enabled AI-start actions (172 distinct script IDs)
resolved, and all 64 startups finished without an AI interpreter error. The
unattended player lost in The Trump Card at frame 1,440 and The Swarm at frame
3,367; those runs stopped at the outcome. Both maps also had unattended defeats
in the previous v40 startup report. The other 62 ran all 4,800 frames. Per-map
outcomes, AI activity and script references are saved in
`validation/campaign-ai-v81.json`.

Run with local, owned archives:

```sh
python3 tests/run_campaign_ai81.py CORE_DIR StarCraft.mpq BroodWar.mpq --skip-prepare
```

`CORE_DIR` contains `STARDAT.MPQ`, `BROODAT.MPQ`, and `patch_rt.mpq`. Omit
`--skip-prepare` when the native engine has not already been prepared. The runner
builds its host executable and extractor, and keeps extracted data only in the
ignored `build-native` directory.

## Limits

These are controlled native regression tests and a bounded startup audit, not
64 full playthroughs, physical Android tests or proof of every later AI branch.
The focused case relocates original units, protects objective heroes and trigger
entry units from damage, and destroys selected original buildings to exercise
specific branches. Original triggers, AI bytecode and AI resource grants remain
intact. Some other missions intentionally lack an active production town during
this startup window. An original defeat during unattended startup is recorded
separately from an AI interpreter error.

The port's AI manager is not asserted to reproduce Blizzard's implementation
frame for frame. The tested Revolution behavior does not justify changing its
mission scripting or enabling its armies before the original activation event.

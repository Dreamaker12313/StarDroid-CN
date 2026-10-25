# AI production fixes (build 80)

Campaign Carriers and Reavers could remain empty because ammunition purchases ran only inside the Protoss melee town manager. The shared computer-player tick now replenishes Interceptors and Scarabs in campaigns and custom games, including Gantrithor, Warbringer, and captured units owned by another race. An active town is unnecessary. This uses the ordinary paid production action and capacity checks. It preserves the unit's movement/attack order, obeys map unit availability and disabled/hallucinated states, and never buys ammunition for the human player. Scene pause/control locks remain authoritative.

A second bug could stall a legal Carrier request with four or five supply free: the AI's fixed low-supply threshold was four, while a Carrier needs six. Supply planning now considers pending, permitted production requests whose producers and prerequisites exist. It also respects the 200-supply ceiling. This covers other expensive units such as Battlecruisers without changing campaign army composition or granting technology.

The existing custom Protoss AI already requested Carriers and their prerequisites. A natural-economy Hard AI run on Weave v1, starting at 50 minerals and zero gas, completed a Carrier at frame 29124, its first Interceptor at 29436, a Reaver at 31554, and a Scarab at 31665. The human side was kept alive to allow the test to continue; the AI received no resource boosts.

## Validation

`validation/ai-production-v80.json` records two reproduced failures against the release 1.0.9 source and the isolated fixed results. `validation/ai-production-final80.json` records the current integrated native stack and exact source hashes. Thirteen controlled checks cover paid ammunition, replacement, normal/hero/upgraded capacities, primary-order preservation, availability and human-owner restrictions, mixed-race ownership, deterministic save continuation, and actual Pylon → Carrier → Interceptor production. The additional natural-economy run checks the complete custom-game production path.

Run after preparing native sources:

```
python3 scripts/prepare_native.py
python3 tests/run_production80.py CORE_DIR BROODWAR_MPQ
```

Original data is supplied locally. These checks are host simulations, not device tests or complete campaign playthroughs. No save-state fields were added.

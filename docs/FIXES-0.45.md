# 0.45 — Zerg skirmish AI

- Zerg joins Terran and Protoss in the computer race selector. All three races
  use the same Easy, Medium and Hard selector.
- Zerg loads the original Brood War ZLOx, ZMEx and ZHIx scripts from the user's
  imported MPQs. No game data or retired external bot is bundled.
- The native manager adds the economy and prerequisites needed for a normal
  four-Drone start: larva production, Drone replacement after construction,
  Overlord supply, creep-aware placement, gas mining and fresh-resource expansions.
- The roster develops from Zerglings and Hydralisks through Mutalisks, Lurkers,
  Queens, Scourge, Ultralisks, Defilers, Guardians and Devourers. Production,
  morphing and research use normal resource, supply, tech and time checks.
- Lurkers burrow in combat. Some Overlords escort the army for detection;
  Queens can Ensnare clusters and Defilers can cover melee troops with Dark Swarm.
- Terran already used TLOx, TMEx and THIx for Easy, Medium and Hard. These also
  change the supplemental manager's tech and expansion timing. This release
  verifies all three Terran levels, alongside all three Zerg levels.
- New Zerg matches use the current portable save system. Saves from the retired
  external Zerg bot remain unsupported; current campaign, Terran and Protoss
  saves keep their format.

This is an OpenBW manager around original script data, not frame-perfect retail
AI. Island transport strategies and exhaustive spell use are not covered.
The existing engine can bunch ground armies at Weave's winding approaches; air
attackers still engage. This revision does not claim that routing issue is fixed.
See the current validation report for executed checks and remaining device testing.

# 0.43 — Protoss skirmish AI

- Original Brood War Protoss campaign scripts PLOx, PMEx and PHIx supply the
  Easy, Medium and Hard build/wave definitions. They are read from the user's
  imported MPQs, never redistributed with the app.
- A native melee manager supplies prerequisites, normal Probe mining, gas
  saturation, additional Nexuses and Assimilators, Pylon power/supply placement,
  power recovery, safe building spacing and stuck placement retries.
- The army grows from Zealots/Dragoons into Dark and High Templars, Archons,
  Observers, Reavers, Corsairs, Scouts, Carriers and Arbiters. Production uses
  actual resource, supply, tech and construction-time checks. Special units
  already fighting count toward maintained army targets, preventing them from
  starving later tech. Reserve defenders remain home during supplementary waves.
- Observers and Templars accompany attackers. High Templars use researched
  Psionic Storm against visible clusters while avoiding friendly concentrations.
  Reavers and Carriers purchase ammunition normally and join attacks.
- Original campaign script execution and Zerg campaign support are retained.
  This is an OpenBW manager around original script data, not an assertion of
  frame-perfect retail AI behavior. Island transport strategies and exhaustive
  spell use are outside this revision's coverage.
- Removed ZZZKBot/BWAPI source archives, native adapter and compiler hooks,
  historical bot WASM, and web/bot from the retained upstream archive. The
  filtered source archive is pinned with its new checksum and original provenance.
  Historical reports/docs still describe the versions they tested.
- One opponent can be Terran or Protoss, with the same difficulty control for
  both. New saves record opponentRace explicitly. Campaign and Terran saves
  keep their format. Old external Zerg-bot matches cannot resume after removal;
  the app explains this before discarding the current game.

Validation details and limits are recorded in VALIDATION.md and the v43 reports.

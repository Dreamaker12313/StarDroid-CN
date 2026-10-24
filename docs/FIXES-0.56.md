# OpenBW Android 0.56

Install `OpenBW-Android-0.56.apk` over the existing app on every participating device. Do not uninstall. The application ID and signing certificate are unchanged. The multiplayer build check rejects older simulation versions before transferring a map.

## Interface and sound

- Ultralisk selection uses the original four normal voices. Repeated selection plays the original annoyed sequence, then returns to normal; the old sequence stayed annoyed indefinitely. The reversed original DAT range remains normalized.
- Score counters run for 2.2 seconds after the UI finishes entering. Original fill and finish audio are composed into that same interval, and counters follow the audio playhead. Bars use the original `iscore.grp` frames, with their colored segments, empty portions and caps. The background remains stationary.
- The complete Protoss briefing Replay button, including its base, moves with the briefing UI.
- Added menu controls use the same normal green, bright hover and disabled colors as the original controls. Fine red outlines have inset rounded corners. Import and Send labels fit their buttons.
- Lobby roster refreshes no longer replay the entrance transition. Entry and locking sounds have independent channels and survive simulation/lobby restoration, allowing each sound to finish.
- Multiplayer opens the player registry first, followed by expansion selection and connection selection. Race selection remains in the lobby.
- Host map selection shows map capacity and open player slots. Player/Computer/Closed configuration and slot movement become available after creating the lobby.
- Lobby status wraps inside its panel. The chat field and Send button fit the original bottom input strip.
- The isometric wireframe Wraith icon has a narrower forward nose.

## Controls and match results

Empty Bunkers and eligible Dropships, Shuttles and transport Overlords enable Load. Full transports hide Load; unloading restores it. Tooltips retain costs and technology requirements without resource, energy or supply shortage messages. Actual failed commands still play the appropriate error.

Competitive games using the campaign AI wrapper now run the competitive elimination checks. An alliance-aware last-opponent check awards victory after every living enemy has been eliminated. It ignores units already dying and defeated players, and does not run in story campaigns. Tests cover StarCraft/Brood War, Melee/Free for All, all three AI races and difficulties, and human/mixed multiplayer perspectives.

A long AI save test also exposed a recycled-unit initialization bug. Unfinished units now initialize their strength fields consistently, so producing a new Scarab after loading matches uninterrupted play. The save format is unchanged.

## Computer opponents

Custom and multiplayer managers reserve resources for expansions and eligible upgrades instead of repeatedly spending the savings on replacement armies. All three races request their normal technology and combat upgrades, advanced units and detection. The Zerg progression reaches Hive, Ultralisk Cavern and Ultralisks. Terran progression includes Comsat Stations and Science Vessels; Protoss progression includes Observers.

Blocked worker placement orders are retried. Nearby combat units can clear a visible, destructible neutral building obstructing an expansion worker; invincible objects and resources are excluded. Building placement preserves worker access around the footprint, original resource routes and Terran addon space. The terrain clearance check uses the actual eight-pixel walkability cells, including partially walkable cliff edges.

Campaign construction, army composition and upgrade requests are unchanged. Detection reactions use only an existing, available Comsat or nearby idle/escorting Science Vessel, Observer or Overlord. They react to an actual undetected attacker; they do not search the hidden map. Scans spend energy and respect the mission's technology availability. Scripted movement is retained. This restores the original AI's reactive-detection behavior without adding detectors or unlocking technology in campaign missions.

## Hero reference

`docs/campaign-heroes.json` contains stock comparisons for 15 directly playable campaign hero forms. `scripts/build_hero_report.py OUTPUT_DIRECTORY` produces searchable HTML and CSV with original unit costs and explicitly proposed one-at-a-time prices. The roster was checked against ownership and transfer triggers in all 64 original campaign scenarios. The proposed prices do not add hero production or alter gameplay.

## Verification limits

See `VALIDATION.md` and the recorded reports. Host tests exercise real engine simulations, original assets, score audio PCM, menu rendering, encrypted socket transport and Android packaging. Physical-device installation, radio groups, touch/keyboard behavior and listening confirmation remain pending. AI scenarios are bounded tests, not a guarantee of every map or a full campaign playthrough.

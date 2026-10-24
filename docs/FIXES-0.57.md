# OpenBW Android 0.57

Install `OpenBW-Android-0.57.apk` over the existing app on every participating device. Do not uninstall. Application identity and signing certificate are unchanged; multiplayer simulation build 58 requires every device to update.

## Selection audio

The four `ZUlWht00..03.wav` normal Ultralisk clips were compared byte for byte with an independent StormLib extraction of the supplied StarDat archive. All match. Their 22,050 Hz mono PCM samples also pass the app's decoder unchanged.

The remaining selection path advanced the annoyed-sound counter even when playback was suppressed by an already-playing acknowledgement. Rapid taps could therefore skip normal voices without the player hearing them. The counter now advances only after an actual sound start, uses the original ten-tick selection debounce, avoids immediate repeats among normal voices, plays annoyed voices in sequence, then returns to normal. Voice choice uses local UI state, never simulation randomness. Physical-device listening is still needed to confirm the user's audible report.

## Protoss power

Completed power-dependent buildings have an empty command card when unpowered. Their description displays original `stat_txt.tbl` entry 829, including its red color control, and selection plays original sound 116 (`Misc/PPwrDown.wav`). Power dependence comes from the original unit flags: Nexus, Pylon and Assimilator do not require it. An unpowered Photon Cannon no longer displays an active Detector label. Restoring power restores normal controls and feedback.

As requested, an unpowered tech building no longer unlocks its dependent units, structures or upgrade levels. One completed, living, powered provider of that type is sufficient, so an unpowered Fleet Beacon does not block Carriers if another powered Fleet Beacon exists. Actual unit counts used by mission triggers, victory and statistics remain unchanged. Producers already pause their own work without power. Losing a prerequisite blocks new requests; already accepted queues are not erased or refunded.

This powered-prerequisite requirement is an intentional rule change from classic Brood War's completed-building tech counting, not a claim of exact retail behavior. The same requirement checks are used by human orders and AI production. Campaign scripts and build orders are not rewritten.

## Terran addons

An addon used as a prerequisite must be completed, living, owned by the producer's player and attached to a compatible grounded parent. Orphan addon buildings cannot independently produce, research, upgrade or use Comsat technology. Neutral addons do not display Protoss Unpowered text.

The existing lift-off/neutralization/capture path was exercised for Comsat Station, Nuclear Silo, Machine Shop, Control Tower, Covert Ops and Physics Lab. An opposing Terran player can land at the compatible empty socket, claim the addon and use its prerequisites; the previous owner loses access. No enemy ownership restriction is added to a genuinely abandoned neutral addon. A dying addon cannot be reattached. Save/load preserves the connection and ownership.

## Icon, credits and hero proposal

The launcher uses a simple vector wireframe Pylon. Diagnostics / credits includes `Put together by ToadWarrior.` and retains existing project and asset attribution.

The chart contains six hero forms per race. Torrasque, Devouring One and Kukulza (Mutalisk) are proposed Zerg additions, explicitly distinguished from the previous directly playable campaign roster. Prices use two thirds of an explained regular-unit equivalent, rounded to five resources. Raynor Marine costs 100 minerals, zero gas. Caster and Carrier equivalences are estimates, not exact DPS measurements. Hero production is not added to the app.

Generate HTML and CSV with `python3 scripts/build_hero_report.py OUTPUT_DIRECTORY`.

## Validation

See `VALIDATION.md`. Host behavior, original data, multi-device protocol and Android package checks are automated. Physical-device installation, Bluetooth/Wi-Fi Direct radio groups and listening remain unverified.

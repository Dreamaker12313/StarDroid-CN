# 0.28 feedback pass 

Reference: user's October 18/19 screenshots and feedback, following 0.27.

## Changes

- Preserve title music through menu navigation; silent mission splash/cinematic taps.
- Moderate 620 ms ease-out menu entrances, 340 ms exits; clip to logical viewport.
- Place Original/Expansion labels below logos using original bottom-aligned widgets.
- Original race-specific command BIN coordinates, conover portrait masks, PCX progress bars.
- Creep Colony morph slots 6/7, Hydralisk Den slot 6, Hatchery/Lair/Hive rally slot 1.
- Rally only on unit producers; no colony/spire rally, and mission-restricted Hatcheries keep it.
- Escape routes correctly from touch Cancel; no targeting Cancel for ordinary unit orders.
- Unarmed units do not expose Attack or get automatic attack taps.
- Selected resource amounts in right info panel; Vespene Gas label.
- Portrait tuning noise triggered by selection identity, including same-type units.
- Translucent blue in-game dialogs, original font sizing, tips browser.
- All original cinematic slots and tutorial in campaign history and progression.
- Speech-timed briefing scrolling without revealing upcoming text.
- Initial addon connections resolved after UNIT loading.
- Camera bounds/centering/minimap rectangle exclude HUD-covered bottom area.
- Mission 3 scripted camera/ping regression against actual CHK actions.

## Validation

Fresh host validation passes all 202 gameplay cases and the presentation checks:
original Terran 3 camera/transmissions/bunker pings, Brood War Zerg 2's two Factory
addons, bottom-edge coverage at four view sizes, unarmed command cards, producer-only rally, Escape,
menu music continuity and native playback of a >64 MB Brood War cinematic.

The complete combined importer validates 31 original maps, 33 expansion maps,
13 original movies and 4 expansion movies. A pristine-source regression test
checks both patch application and repeatability. The earlier dry-run patch check
could silently treat an unapplied patch as applied; it now uses forced direction.

All five Android suites passed on the final APK: feedback, campaign/HUD, audio/motion,
navigation/gestures and construction. The collected runtime error log was empty.
Android evidence and package identity are recorded separately in `validation/`.
Caption line timing uses the decoded voice clock plus estimated transcript timing;
no exact word timestamps are present in the original CHK/WAV data.
Monitor static is synthesized; all other original artwork/audio stays in local imports.
Original game files and reference images remain external to distributed files.

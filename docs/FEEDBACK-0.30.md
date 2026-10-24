# 0.30 feedback update

This revision uses the supplied 0.29 source. Original game archives are external
inputs and were not included. The changes below are implemented; the current
synthetic/Android checks cannot establish a complete original campaign playthrough
or an exact artwork/audio comparison. Both native architectures are rebuilt.

## Changes

| Report | Change |
| --- | --- |
| Distant selected units are silent | Selection and command acknowledgments use global volume, retaining the unit's voice identity. World combat sounds keep their normal positioning. |
| Campaign allies attack one another | CHK force alliance, allied-victory and shared-vision flags now apply to computer players before preplaced units load. Trigger queries for Allies include allies without shared victory. |
| Raynor's buildings / early Chrysalis ending | Preplaced and trigger-created unit properties now honor invincibility, cloak and burrow flags. These and the alliance correction address plausible causes. The reported mission ending and destroyed/reappearing buildings are **not yet confirmed fixed** without its original map and assets. |
| Computer Lurkers stay above ground | Computer Lurkers burrow near a visible ground enemy. Buried attackers can unburrow when no target remains nearby, and ordinary idle-wave retasking leaves buried Lurkers in place. Allied units do not provoke combat burrowing. |
| Critters | A single selected neutral critter plays its original selection/annoyance sounds. Critters have no combat-stat/armor placeholder. Neutral doodads cannot index a nonexistent race supply array. |
| Hidden traps | Six actual trap types are distinguished from doors. Reveal/hide animations run with the unit and flingy context, and completed reveal transitions to an armed attack order. Hidden acquisition avoids the generic stationary-unit timer reset. |
| Gate animations | Stationary doodad images can run their original Enable/Disable animation. Repeated trigger actions do not restart an ongoing gate animation. Collision clears when opening completes and returns when closing starts. |
| Hero abilities and slots | Hero-aware ability eligibility remains in use. Ghost heroes keep Lockdown in bottom-left and Cloak in bottom-middle. Infested Kerrigan uses Cloak at middle-right and Storm/Ensnare/Consume across the bottom. Defiler Burrow stays clear of its spell row. Hero Ghosts do not receive the normal Ghost's Nuclear Strike button. Mission restrictions and energy costs remain effective. |
| Easier selection | Hold before dragging is 200 ms, down from 350 ms. A tap slightly outside a visible unit selects the nearest eligible unit within 22 logical pixels, adjusted for zoom. Explicit spell/attack targeting and building placement retain their exact coordinates. Context taps on owned gas structures retain gathering. |
| Research and upgrade voices | Actual successful completion queues the correct race's advisor recording. Multiple completions are serialized. Cancelled, absent, already-completed and other-player work does not produce a new announcement. |
| Hover information | A dark, bordered tooltip above the command grid shows the label, positive costs, existing effect descriptions for all 50 upgrades and all researchable technologies, and requirements. Weapon upgrade blurbs no longer promise a universal +1 damage. Mouse hover displays it; holding a command for 280 ms inspects it without issuing it on release. |
| Dialogue motion | Ready-room dialogue holds the first screen for reading, then scrolls continuously across the remaining speech time. Per-line pause/jump easing is removed. Manual reading remains available. |
| Zerg Replay artifact | The moving panel mask compares RGB independently of palette alpha. Replay/Cancel panels and their movie layers are clipped to their BIN bounds; signed movie offsets are decoded correctly. Original-art verification remains required. |
| Mission pre-text font | Uses the original 16 font and the story's color ramp/background palette. The wide 16x font and forced solid green recoloring are removed, preserving shaded glyph edges. |
| Briefing leaks into paused mission | Starting a mission clears briefing messages, portraits, timing and the briefing voice immediately, before Tips can pause polling. |
| Main-menu hover audio | Entering an original menu button uses `sound/glue/mouseover.wav`. Touch highlight entry uses the same feedback. |

## Validation and limits

Current evidence is in `validation/*-v30.json`; older reports are retained as
history. Ten native regression groups and eleven Android checks pass. The host
harness tests synthetic state and decoded synthetic iscript,
including the trap's transition through reveal into firing animation/cooldown.
It does not execute original trap projectile artwork or damage against a full map.
Completion checks call the real research/upgrade success paths and record their
queued sound IDs; original WAV audibility still needs a device check.

The Android revision suite checks command hints, hero slots, continuous scrolling,
briefing cleanup while polling is paused, panel masking, native library loading,
and the import/options surface. Package validation checks the exact APK/test-APK
identities, update signing key, both ABIs, JNI symbols and 16 KiB alignment.

The full original-data release gate stays enabled. `tests/native_package.py`
records package integrity separately from `releaseReady` and exits nonzero while
the original-data campaign/gameplay/presentation/import suites are missing.
This build remains a feedback candidate, not a claim that those suites passed.

## Device checks still needed

1. Start the Chrysalis mission: verify Raynor's base is intact during dialogue,
   allied forces do not fight, and the mission continues through the hatch event.
2. Check the reported Brood War Zerg mission with Fenix: enemy alliances and
   Lurker combat burrowing, including a wave that moves onward afterward.
3. Trigger installation traps and open/close each gate in an original mission.
4. Check the Zerg Replay animation and mission pre-text against original artwork.
5. Listen to critter clicks, distant-unit commands, menu hover, and each race's
   research/upgrade completion sounds using the installed game archives.

## Rebuild

```sh
python3 tests/native_patch_preparation.py
python3 tests/build_native_host.py feedback
build-native/host/native-feedback
python3 scripts/build.py
python3 tests/build_instrumentation.py
```

The revision is carried by `patches/native-revision.patch`, after the previous
campaign/gameplay/presentation/feedback changes. Fresh reconstruction is tested
for byte-identical output. Original MPQs, tool caches, emulator data and generated
engine trees are excluded from the source ZIP. The package ID and signing key
are unchanged; install the APK over the existing app to retain imported data.

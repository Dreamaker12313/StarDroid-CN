# 0.29 native feedback candidate

This revision was rebuilt from the recovered 0.28 source. Original StarCraft
game archives are external inputs and were not available in the restored test
workspace. Synthetic fixtures validate individual code paths; they do not stand
in for an original campaign playthrough or a visual comparison using its assets.

| Report | Change / status |
| --- | --- |
| Traps visible before revealing or in fog | Trap visibility now respects detection and current vision. Traps no longer retain a building silhouette in explored fog. |
| Trap armor placeholder | Trap detail panels omit armor; their actual weapon information remains. |
| Missing hero abilities | Command cards use the engine's hero-aware technology eligibility. Infested Kerrigan can cloak, use Storm, Ensnare and Consume when permitted by the map. Other hero spell, Stim, Siege, mine and Burrow variants use the same rules. Energy shortage disables spells. |
| Gate animation/collision disagreement | Door orders begin before iscript, with the correct unit/flingy context for completion signals. Closing blocks immediately; opening releases collision on completion. Original-map pathfinding and animation still need comparison. |
| Replay carries background during entrance | Sliding Replay/Cancel panels remove edge-connected pixels that match their fixed background. Original assets are needed to verify this against the supplied screenshot. |
| Dialogue scrolling | Restored the complete drawn transcript. A smooth row scroll starts shortly before the next hidden line's estimated spoken time. No line-by-line text truncation. Timing remains an estimate. |
| Chrysalis hatching mission wins early | **Unresolved.** No mission-specific workaround was added without reproducing the trigger sequence. Need original Zerg 3 / StarCraft.mpq and core MPQs to investigate the premature dialogue and victory. |
| Start hover and Terran projector | Loads the previously skipped projector intro/loop, layers it below the start graphic, avoids duplicate hover streams, and keeps the base button if hover art is absent. Original assets are needed for visual confirmation. |
| Worker voice on build | Placement retains the build sound and no longer also plays a worker command response. Landing still uses its own response. |
| Drone taps on Extractor | Completed owned gas structures accept worker context orders before normal unit selection. Applies to Drone/Extractor, SCV/Refinery and Probe/Assimilator. |
| Slightly slower menu/briefing slides | Entrance 670 ms (was 620), exit 365 ms (was 340); cubic easing and viewport clipping retained. |
| Movie import explanation | App Options explains both campaign archives and Install.exe, reimporting older bundles, automatic intermissions, and installed movie counts. Counts ignore missing payloads. |
| Large green mission splash | Uses the wide 16x original font and explicit pale-green text, retaining dark glyph shadows. Requires a visual check with original story art. |
| Zero-cost / cramped hints | Free actions show only their names. Positive minerals, Vespene Gas and energy costs have spacing; zeros are omitted. Disabled spells explain their energy requirement. |

## Validation

Current checks completed for this candidate:

- Five native fixture groups pass: traps, hero commands and actual Kerrigan
  cloak/decloak activation, worker gas orders, doors, and delayed trigger timing.
- Eight Android checks pass on the final APK, on Android 9 / API 28 x86_64,
  emulator 37.3.4 at 1280 × 720 using software CPU emulation and SwiftShader.
  App Options and movie guidance screenshots were inspected. An initial Android
  System UI stall obscured captures; it was dismissed and the run repeated with
  a foreground-window check. No app errors appear in the final collected log.
- Patch reconstruction passes. APK identity, update certificate, v2/v3 signatures,
  both native architectures, JNI symbols and 16 KiB alignment pass. No WebView,
  JavaScript or WebAssembly runtime is packaged.

The current evidence lives in `validation/*-v29.json`. Earlier v23–v28 reports
remain historical. Full original-data gameplay/import/presentation suites must
be rerun before marking this build fully verified. The existing release gate
continues to require those suites; it is not waived by the synthetic checks.
`tests/native_package.py` therefore records `packageIntegrityPassed: true` and
`releaseReady: false`, then exits nonzero for the missing original-data evidence.
The Android mixer check confirms JNI loading only, not audible game samples.

`tests/native_feedback.cpp` exercises six trap types, hero variants and mission
technology limits, all three worker/refinery pairs, four door types with synthetic
iscript completion, and a synthetic wait/countdown sequence. The countdown check
does not claim to fix or reproduce Zerg 3.

`tests/NativeRevisionInstrumentation.java` runs Android checks without game files:
App Options, import guidance/counts, readable cost hints, continuous speech-clock
scrolling, background-mask preservation, menu timings, and native JNI/mixer loading.

## Reproduce

```sh
python3 tests/native_patch_preparation.py
python3 tests/build_native_host.py feedback
build-native/host/native-feedback
python3 scripts/build.py
python3 tests/build_instrumentation.py
```

For an original-data run, provide STARDAT.MPQ, BROODAT.MPQ, patch_rt.mpq,
StarCraft.mpq and BroodWar.mpq locally. Do not put these archives in the source ZIP.
The existing campaign, gameplay, presentation and Android suites can then run with
those inputs. The emulator helper uses official SDK files under `.tools/sdk` and
software CPU emulation when no hardware accelerator is available.

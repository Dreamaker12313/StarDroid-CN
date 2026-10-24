# OpenBW Android 0.26 gameplay test results

The compiled native gameplay suite passed **202 checks** with zero failures.
It issues the normal command-card actions and verifies the resulting simulation
state, resource charges, refunds, prerequisite gates and production results.

| Area | Coverage and result |
| --- | --- |
| Buildings | All 50 standard structure types: 39 worker-built types, six Terran add-ons and five Zerg building morphs |
| Unit production | 39 trained or morphed unit types, including a nuclear missile and an Infested Terran after actual infestation |
| Protoss special production | Both Templar merges; Carrier Interceptors and Reaver Scarabs, including costs and upgraded capacity limits |
| Research | All 24 research items: start, exact cost, cancellation/full refund, completion and removal of the completed research command |
| Upgrades | All 50 upgrade types through their maximum levels: 82 level completions, with cost and cancellation/refund checks at every level |
| Requirements | Missing technology, missing creep/power, power loss/restoration, local Machine Shop attachment, minerals, gas and supply rejection |
| Queues | Five-slot limits, cancellation from the middle, cancellation of the active item, invalid cancellation indexes and refunds |
| Construction behavior | Drone consumption; SCV/Probe preservation; construction cancellation and 75% refunds for a representative building of each race; SCV halt/resume |
| Morphs and abilities | Hatchery/Lair/Hive, Greater Spire, Sunken/Spore Colony, Lurker/Guardian/Devourer, Siege/Unsiege, Burrow/Unburrow, infestation and building-morph cancellation |
| Nydus | Entrance construction, free exit placement and bidirectional endpoint links |

## Problems found and fixed

- **Busy Lift Off button:** the command-card refresh overwrote the busy state.
  It now keeps Lift Off disabled while the building is producing or otherwise busy.
- **Blocked landing confirmation:** the placement query accepted every landing
  location. It now checks the footprint before enabling confirmation.
- **Blocked add-on confirmation:** the placement query now checks both the parent
  building and the add-on footprint, matching the preview and simulation.
- **Missing Nydus exit:** completed, unlinked canals now offer **Build Nydus Exit**.
  The exit uses the existing simulation order, requires valid creep and costs no
  additional resources. A linked canal does not offer another exit.
- **Diagnostic crash:** inspecting a unit without a ground weapon could dereference
  a null weapon. The diagnostic readout now handles that case.

## Test conditions

The construction matrix uses the included Weave map and externally supplied
original game archives. It starts each race separately and builds its technology
tree through normal orders. Extra resources and accelerated production make the
run practical; ordinary placement, prerequisites, supply, costs, morph animations
and completion logic still run. Timing is temporarily restored for cancellation,
queue and halted-construction tests. Workers are repositioned beside test sites.
A damaged enemy Command Center is created solely as the infestation prerequisite.

Several early failures were test setup issues, not game defects: crowded worker
paths, larvae moving into a proposed footprint, selecting the same Templar twice,
rebuilding a Pylon outside the Gateway's power range, and exhausting larvae before
their normal replenishment interval. The fixtures were corrected. The game still
rejects occupied construction sites and requires actual power and larvae.

The original campaign controls/audio regression suite also passed: Zerg mission 2
Lair, mission-allowed disabled technology, Egg target, Extractor health/gas,
Chrysalis details, original build sound, silent beacon transfer, victory PCM,
touch/resize cancellation and original introduction decoding.

## Android results

The campaign/audio suite and menu/touch parity suite both passed on Android 9
in an x86_64 emulator. The new construction checks also passed: busy Lift Off
stays disabled, blocked landing/add-on sites cannot be confirmed, a valid
Machine Shop completes, and Build Nydus Exit creates the second endpoint.
The runs captured 46 scenes; selected HUD, menu and construction scenes were
inspected visually. No OpenBW or AndroidRuntime errors were logged by the final
test processes.

The construction report combines two passed sections on the same APK. After
the Terran section passed, the first Zerg attempt stopped because its fixture
assumed a Spawning Pool already existed. The corrected section built the Pool,
Lair, Queen's Nest and Hive normally, then passed the Nydus touch checks.

The emulator uses software CPU emulation and SwiftShader. Its timing is not a
phone performance measurement. ARM64 libraries were compiled and packaged, but
were not run on a physical ARM phone. The earlier browser reference was retained;
this pass reran the native parity tests, not the browser itself.

## Limits

These checks do not certify every campaign as completable, every combat matchup
or spell-targeting combination, long matches, physical Android performance, or
speaker/Bluetooth behavior. Construction cancellation was sampled across races;
it was not repeated for every structure. Nydus endpoints were checked, but a full
transport/combat scenario was not.

Campaign AI still has the previously documented multi-town, transport and tactical
limitations. Custom games still support one native computer opponent. Save/load,
replay loading, multiplayer and full cinematic sequencing remain unsupported.

Machine-readable results: `validation/native-gameplay-v26.json`.
Reproduction: `python3 tests/build_native_host.py gameplay`, then
`build-native/host/native-gameplay /path/to/game-files app/src/main/assets/native/weave.scx report.json`.

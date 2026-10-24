# OpenBW Android 0.52 — Host frame pacing

Fixes a multiplayer timing bug that matches the reported host-only jumps:
full game speed and 100% waiting on the host, while the guest looks smooth.

## Cause and fix

In 0.51, the earlier phone kept accumulating elapsed time while waiting for the
other phone's next command batch. When that batch arrived, it advanced several
simulation frames in one display update. It then reached another empty batch
and waited again. A startup delay could leave the host in that cycle for the
whole match, even though its average game speed was 100%.

Tabbing out and returning pauses/resumes the match and resets timing, which
explains why it can clear this pattern. That workaround is no longer needed for
this reproduced bug. After a network stall, 0.52 keeps one due simulation frame
and resumes normal pacing instead of trying to repay time spent waiting. No
simulation steps or player commands are skipped. A slow or disconnected phone
still stops progress when input runs out.

Pause transitions now reset timing immediately, including while a backgrounded
phone has no drawing callbacks. The reset leaves units, orders, pending command
batches and state checks untouched. Fastest remains 42 ms per simulation frame,
with the same one-turn / 168 ms input buffer from 0.51.

## Diagnostics

The report now includes the maximum simulation steps per drawing update,
multi-step update count, longest simulation-step gap and automatic pacing
recoveries. Wait accounting ends when the missing packet reaches the game
worker. Pause menus preserve the last active pacing sample.

The old `0.41 Native (42)` heading was stale text, not the installed package
version. Both visible version labels now come from the build configuration.
This APK reports `0.52 Native (53)`. The previous "Worst draw work" field is
renamed "Worst frame work" to match what it actually measures.

## Verification

A controlled reproduction runs the production 0.51 and 0.52 schedulers with the
same deterministic engine. The guest starts 600 ms late; round-trip latency is
60 ms with up to 20 ms jitter in each direction. After a three-second settling
period, the following measurements cover 15 seconds with a 16 ms display cadence.

| Metric | 0.51 host | 0.52 host | 0.52 guest |
| --- | ---: | ---: | ---: |
| Game speed versus Fastest | 99.68% | 99.96% | 99.96% |
| Updates advancing multiple game frames | 89 | 0 | 0 |
| Maximum game frames in one update | 4 | 1 | 1 |
| Longest gap between game steps | 208 ms | 48 ms | 48 ms |

The old host also reproduces `Wait 100%`; the fixed host settles at `Wait 0%`.
These are simulated link and pacing measurements, not physical Android screen
captures or radio benchmarks. The simulation target is about 23.81 frames/s;
the display may draw more often without advancing a game frame.

Additional checks cover either phone starting late, 8/16/33 ms drawing cadences,
a later loading stall, background pause/resume, missing input, state equality and
exactly-once command ordering. Existing protocol, permission, transport, map
transfer/cache and high-latency recovery suites also pass. The 0.51 throughput
and map-transfer improvements are retained.

The APK uses the same signing key, application ID, save format and native game
libraries as 0.51. The package verifier checks upgrade identity, the compiled
diagnostic heading, permissions, all JNI methods, both ABIs and 16 KiB alignment.
Physical-phone confirmation remains pending. No new campaign checks were run.

## Install and reproduce

Install over the existing app on **both phones**. Do not uninstall if you want
to keep imports, settings and saves. The build number increases to 53, and the
multiplayer handshake requires matching app versions.

Use **Game Menu → Options → Network → View / copy diagnostics** for pacing data.

```sh
python3 tests/run_nearby_pacing.py
python3 tests/run_nearby_efficiency.py
python3 tests/run_nearby_protocol.py
python3 tests/run_nearby_permissions.py
python3 scripts/build_nearby.py --skip-engine --lint
python3 tests/check_nearby_package.py /path/to/OpenBW-Android-0.51.apk
```

The 0.51 scheduler/protocol fixtures are renamed copies from the previous source
release and are not included in the APK. Reports are in `validation/*-v52.json`.

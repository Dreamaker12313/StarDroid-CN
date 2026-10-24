# OpenBW Android 0.51 — Multiplayer efficiency

Google Nearby multiplayer now sends commands ahead, allows concurrent packet
delivery, and transfers maps in larger windows with compression and a verified
cache. Network and rendering diagnostics help distinguish connection delays
from slow simulation or drawing.

## Install and use

Install 0.51 over the existing app on **both phones**. The application ID and
signing key match 0.50; versionCode increases from 51 to 52. Keep the app installed
to preserve imported files, saves and settings. Google Play services is still
required. The foreground-location permission fix from 0.50 is retained.

During a multiplayer match, open **Game Menu → Options → Network**. Enable
**Show network overlay** for ping, game speed, network wait, display FPS and
drawing time. **View / copy diagnostics** opens the detailed report, including
simulation time, traffic, map transfer size/time and the transport queue. Menu
pauses preserve the last active timing sample. The overlay starts disabled.

## Changes

- Commands are collected and sent one four-frame turn ahead. The phones can
  simulate the current turn while the next inputs travel. Fastest remains
  42 ms per simulation frame; the added input buffer is 168 ms. This trades some
  command response time for fewer simulation stalls. It does not predict input
  or roll back the game. Missing commands still stop progress safely.
- The scheduler preserves unused elapsed time across frame and turn boundaries,
  with bounded catch-up after a delay. It no longer discards time at every batch.
- Google Nearby can send four payloads concurrently. Sequence numbers restore
  delivery order, and duplicate/completion handling and queue bounds prevent
  unbounded backlog. Closing a connection briefly drains final messages.
- Map transfer permits eight 16 KiB chunks before waiting, with cumulative
  acknowledgements every four chunks. Deflate compression is used only when it
  saves at least 256 bytes and 10% of the map. Declared lengths, decompression
  output and the final SHA-256 digest are checked before initialization.
- Up to four verified maps (32 MiB total) are cached privately on each phone.
  Reusing a cached map skips its transfer. Corrupt entries are discarded, and
  cache read/write failures fall back to normal transfer. The map limit remains
  8 MiB uncompressed. Android can evict cache files without affecting imports.
- Ping/jitter, simulation rate, network waiting, engine work, drawing work,
  packet queues and transfer statistics are now available separately.

Both phones must use 0.51 because the wire protocol changed. Multiplayer remains
two-player; reconnect, multiplayer saves, AI slots and campaign co-op are not
added in this update. Native game and video libraries are unchanged.

## Verification

The production 0.50 and 0.51 match classes ran side by side for 60 virtual seconds
with a lightweight deterministic engine, an ordered simulated link and a 16 ms
display cadence. The map was 1 MiB of incompressible test data, so these transfer
results measure the window improvement without a compression advantage.

| Simulated round-trip delay | 0.50 game speed | 0.51 game speed | 0.50 map ready | 0.51 map ready |
| --- | ---: | ---: | ---: | ---: |
| 0 ms | 87.43% | 99.96% | 1 ms | 1 ms |
| 20 ms | 87.43% | 99.96% | 1,311 ms | 191 ms |
| 50 ms | 80.64% | 99.89% | 3,276 ms | 476 ms |
| 100 ms | 69.86% | 99.89% | 6,551 ms | 951 ms |
| 200 ms | 58.17% | 99.75% | 13,101 ms | 1,901 ms |

100% means the target simulation speed, not rendering FPS. These are controlled
scheduler measurements, not phone or radio benchmarks. Real performance still
depends on both phones, the connection and rendering workload.

Regression checks cover matching state/command order, pauses, missing input,
600 ms latency with jitter and subsequent recovery, compressed and malformed
maps, cache hits/corruption/eviction/I/O failure, concurrent sending, reordered
completion, duplicate packets and close/failure paths. The existing 1,430
protocol and 608 permission assertions pass, along with 49 transport assertions
and the new efficiency suite. APK upgrade identity, signatures, native library
correspondence, all 32 JNI methods, both ABIs and 16 KiB alignment pass. Android
lint reports zero errors and nine warnings.

Physical two-phone testing and Android visual/interaction checks remain pending.
No new campaign playthrough or native-engine performance claim is made.

## Reproduce

```sh
python3 tests/run_nearby_protocol.py
python3 tests/run_nearby_permissions.py
python3 tests/run_nearby_efficiency.py
python3 scripts/build_nearby.py --skip-engine --lint
python3 tests/check_nearby_package.py /path/to/OpenBW-Android-0.50.apk
```

The efficiency fixture contains renamed copies of the 0.50 production match and
protocol classes. They are compiled only by the benchmark and are absent from
the APK. Current reports are in `validation/*-v51.json`.

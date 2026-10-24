# OpenBW Android 0.53 — Multiplayer without Google Play services

Replaces Google Nearby with Android Bluetooth Classic and Wi-Fi Direct. The APK
contains no Google Play services dependency or Google Nearby classes. No Google
account, internet connection, router or server is required for a local match.

## Connect two phones

1. Install **OpenBW-Android-0.53.apk** on both phones over the existing app.
   Do not uninstall; the package ID and signing certificate are unchanged.
2. Turn on Bluetooth and Wi-Fi. Open **Multiplayer** on both phones and leave
   **Bluetooth + Wi-Fi Direct** selected.
3. Choose **Host Game** on one phone and allow Android to make it visible.
4. Choose **Join Nearby** on the other phone, then select the host's **phone
   name**. The list may include other nearby or previously paired phones.
   Arrows show more phones; **Search again** restarts discovery.
5. Accept Android's Bluetooth pairing prompt, if shown. Confirm that the
   six-digit OpenBW pairing codes match on both phones.
6. The map transfers automatically. The host chooses **Start Game** when ready.

Wi-Fi Direct upgrades the connection automatically. Bluetooth stays connected
as a fallback. Choose **Bluetooth only** before hosting/joining to disable the
upgrade. Both phones need this build and matching imported core game files.
The Google Nearby connection in 0.49–0.52 cannot join this version.

Android 12+ uses Nearby devices permissions for Bluetooth. Earlier versions use
Location permission for discovery. Wi-Fi Direct needs Android 10+, compatible
hardware and Wi-Fi enabled. On Android 10–12 it also needs Location permission;
Android 13+ uses Nearby Wi-Fi devices permission. Denying optional Wi-Fi access
keeps Bluetooth available. No location permission is requested on Android 13+.

## What is preserved

The production `NearbyMatch.java` is byte-identical to 0.52. Its automatic
recovery from host frame bursts, immediate pause timing resets, Fastest game
speed, one-turn / 168 ms input buffer and diagnostics are retained. Map
compression, the eight-chunk transfer window, SHA-256 verification and verified
map caching are unchanged. Native game and video libraries, save handling and
solo gameplay are unchanged.

## Connection details

Secure Android RFCOMM handles bonding and exchanges a fresh session secret.
Both players confirm the pairing code before the game or Wi-Fi invitation is
accepted. Wi-Fi credentials travel over the encrypted Bluetooth connection.
The Wi-Fi handshake proves possession of the session secret. Both streams use
AES-GCM with separate directional keys and bounded frames.

Ordered packet numbers, acknowledgements and retransmission of unacknowledged
packets preserve commands during a connection switch. Wi-Fi setup failures keep
Bluetooth usable. A silent Wi-Fi stall falls back after four seconds without
acknowledgement progress. A Wi-Fi send failure also falls back if its writer
stops before the disconnect callback runs. A late Wi-Fi invitation cannot end a
healthy Bluetooth match. Loss of both connections stops the match.

The lobby shows the transport separately from map progress, includes the
Bluetooth-only option and restores discovery pagination/rescan. Network
diagnostics identify the transport and pending acknowledgements. Background
Location is never requested. Bluetooth/Wi-Fi hardware is optional for solo play.

## Verified in this build

- Production local stream tests: 545 assertions covering encrypted real desktop
  sockets, authentication, tamper/replay rejection, bounded queues, ordering,
  in-flight handover, silent stalls, send-failure fallback and final-message EOF.
- Integrated production match + stream test: exact map transfer during handover,
  900+ deterministic engine frames with matching states, Wi-Fi loss, Bluetooth
  fallback, shared pause/resume and deliberate leave. These are desktop TCP
  sockets standing in for radio connections, not physical Android radio tests.
- Production permission and lifecycle flow: 685 assertions across API 26–36,
  Host/Join, both connection modes, existing/partial/denied grants, optional Wi-Fi,
  duplicate starts, late callbacks, Bluetooth enable and host visibility.
  Android system calls/dialogs are test doubles.
- Protocol regression: 1,430 assertions. Pacing and efficiency suites also pass,
  covering late startup, stalls, pause/resume, compression, cache and latency.
  In the reproduced 60 ms RTT/late-guest case, both peers have zero multi-step
  draws after settling, versus 89 host bursts in the 0.51 baseline. This measures
  a synthetic link and lightweight engine, not phone display/radio performance.
- APK verification: same application ID/certificate as 0.52, higher versionCode
  54, visible 0.53 diagnostics, no GMS classes/metadata, all 32 JNI methods,
  byte-identical native libraries, both ABIs, assets and 16 KiB alignment.
  Android lint: zero errors, ten warnings.

Physical installation, Bluetooth discovery/bonding, Wi-Fi group creation and
performance on two phones still need confirmation. No new campaign or artwork
verification is claimed. Multiplayer remains two-player melee without campaign
co-op, AI slots, saves or reconnect after complete disconnection.

## Rebuild and checks

```sh
# Bootstrap pinned tools and rebuild native libraries:
python3 scripts/build.py
# With tools and the included native libraries already present:
python3 scripts/build_nearby.py --skip-engine --lint
python3 tests/run_nearby_protocol.py
python3 tests/run_local_permissions.py
python3 tests/run_local_transport.py
python3 tests/run_nearby_efficiency.py
python3 tests/run_nearby_pacing.py
python3 tests/check_nearby_package.py /path/to/OpenBW-Android-0.52.apk
```

The protocol runner uses the prepared native source/toolchain to build its map
extractor, or accepts an existing tool via `OPENBW_MAP_EXTRACTOR`. Gradle accepts
`--offline` when its dependencies are cached. The build tools are still standard
Android SDK tools; the installed app has no Google Play services dependency.
Current reports are `validation/*-v53.json`. Earlier reports are historical and
must not be presented as current radio or UI validation.

Platform references:
- https://developer.android.com/develop/connectivity/bluetooth/bt-permissions
- https://developer.android.com/develop/connectivity/wifi/wifip2p
- https://developer.android.com/reference/android/net/wifi/p2p/WifiP2pConfig.Builder

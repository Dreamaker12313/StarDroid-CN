# OpenBW Android 0.47 — Nearby multiplayer

Two Android phones can host and join a one-versus-one melee game through Google
Nearby Connections. The SDK coordinates Bluetooth, BLE and Wi-Fi and upgrades
the connection when a faster supported link is available. Gameplay requires no
internet server. Both phones need Google Play services, this app version, and
the same three imported core MPQs.

## Play

1. Install 0.47 over the existing app on both phones. Imports and solo saves remain.
2. Turn on Bluetooth and Wi-Fi. Open **Multiplayer** from the main menu.
3. On the host, choose a race, map and StarCraft/Brood War edition; tap **Host Game**.
4. On the other phone, choose a race, tap **Join Nearby**, then select the host.
5. Grant Android's nearby-device permissions. Compare the pairing code on both
   phones and tap **Codes match** only if they agree.
6. The map transfers automatically. The host taps **Start Game** when both are ready.

Import additional maps through Custom Game first. Nearby play supports melee
maps with at least two starts and a scenario up to 8 MB. The host's map and
edition override the guest's local choices. Received maps are temporary and
do not replace the guest's installed collection. No campaign co-op or computer
opponents are included in this initial two-player mode.

Android 12 and earlier can also request Location permission for nearby discovery.
If discovery fails there, check that Location is enabled. No account or login
screen is added by the game.

## Match behavior

- Commands are exchanged in four-frame batches at the normal Fastest game rate.
  Both phones apply player 1 then player 2 at the same simulation frame.
- A late packet stops simulation advancement until its commands arrive. Camera,
  zoom, selection, rendering rate and audio remain local to each phone.
- Opening the game menu or backgrounding a phone pauses the shared match.
  Closing the menu or returning resumes after both phones are ready.
- Game version, entire core archives, initial state and map checksums must match.
  State checks run at every command batch and stop a divergent match.
- Save/load, testing cheats, speed changes and AI-defense settings are unavailable
  during multiplayer. Existing solo controls, settings and saves remain usable.
- Leaving a live match deliberately is a surrender. A broken connection stops
  the match and shows an explanation; it does not manufacture a victory.
- Reconnection and multiplayer saves are not included. Start a new lobby after
  a lost connection. Results exit is distinguished from surrender.

## Implementation and build

`NativeNearby` owns the permission-gated, authenticated P2P connection and bounded
ordered payload queue. `NearbyMatch` owns map transfer, lobby and turn scheduling
on the existing simulation worker. JNI methods in `native/multiplayer.h` enforce
turn boundaries, validate command batches and keep local input out of solo stepping.

`python3 scripts/build.py` bootstraps the pinned Android tools and builds both
native ABIs. The final packaging stage now uses Gradle 8.9 / Android Gradle Plugin
8.7.3 to merge Nearby 19.3.0 and its transitive resources/manifests correctly.
`python3 scripts/build_nearby.py --skip-engine` repackages after Java-only changes
when the Android tools and both native libraries are already present.

The same package ID and signing certificate are retained. The app declares
network permissions for local connections. Nearby runs through Google Play
services; its diagnostics follow the device's Google usage/diagnostics setting.

Reference APIs:
- https://developers.google.com/nearby/connections/overview
- https://developers.google.com/nearby/connections/android/get-started
- https://developers.google.com/nearby/connections/android/manage-connections
- https://developers.google.com/nearby/connections/strategies

## Verification limits

Six paired native scenarios cover Zerg/Terran, Terran/Protoss and Protoss/Zerg in
both editions. Every pair runs 7,200 frames, with different selection, camera and
render timing. The guest loads the actual Java-generated transferred-map archive.
State checks match at all 1,801 checkpoints per pair. Normal resource gathering,
worker production, attack commands, surrender, malformed-input rejection, cheat
blocking and a subsequent solo save/load are exercised.

The production Java protocol tests cover delayed/missing input, map corruption,
version/data mismatches, pauses, desyncs and disconnects. These are desktop tests.
Six lobby states also passed desktop rendering, bounds, overlap and animation
input checks. APK identity, native libraries, assets, JNI exports and 16 KiB
alignment passed verification; Android lint reported no errors.
Physical Android Bluetooth/Wi-Fi discovery, radio upgrades, permissions, latency,
disconnect behavior and mixed-phone/ABI operation still need two-phone testing.
This is an initial test build, not a claim of hardware verification or campaign
playthrough coverage. The previous Weave pathfinding limitation remains.

To reproduce focused checks after preparing the native source:

```sh
python3 tests/run_nearby_protocol.py
python3 tests/build_native_host.py multiplayer --skip-prepare
python3 tests/run_multiplayer.py /path/to/core-mpq-directory
python3 tests/run_nearby_ui.py
python3 scripts/build_nearby.py --skip-engine --lint
python3 tests/check_nearby_package.py /path/to/OpenBW-Android-0.46.apk
```

The core directory must contain `STARDAT.MPQ`, `BROODAT.MPQ`, and `patch_rt.mpq`.
For the lobby render check, also make those files available in
`build-native/game-data/` (copies or symbolic links).

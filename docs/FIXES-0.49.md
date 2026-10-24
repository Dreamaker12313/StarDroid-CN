# OpenBW Android 0.49 — Google Nearby update

Restores Google Nearby Connections multiplayer and installs as an update over
the Google-free 0.48 release. Android versionCode is 50, above 0.48's 49.
The application ID and signing certificate stay the same. Existing imports,
solo saves and settings remain in the same app storage; no data migration or
reset is performed.

Install 0.49 on both phones. Turn on Bluetooth and Wi-Fi, open **Multiplayer**,
then choose **Host Game** on one phone and **Join Nearby** on the other. Grant
Nearby permissions and confirm that the pairing codes match. Both phones need
Google Play services and matching imported game data. The map transfers before
the host starts the match.

This release uses the original 0.47 Google Nearby transport and its two-player
lobby. It does not include 0.48's framework-only Bluetooth/Wi-Fi Direct transport
or Bluetooth-only switch. Multiplayer remains at Fastest, with four-frame
command batches. Campaign co-op, AI slots, reconnect and multiplayer saves are
not added. There is no claim of improved frame rate or lower latency.

The four native game/video libraries are reused byte-for-byte from 0.48 and
were also verified identical to 0.47. Save schema 2 and the Java save/settings
code are unchanged. The Java app and Google dependencies are rebuilt using
Gradle, including the new lobby build identifier and visible version label.

Validation checks the compiled APK's identity, higher versionCode, signing key,
Google Nearby classes/manifest, native libraries, assets, JNI exports and 16 KiB
alignment. The production Java protocol suite is rerun for this release.
Earlier native simulation and lobby-render results are historical evidence for
the unchanged implementation, not new phone tests. Physical installation,
Bluetooth/Wi-Fi discovery, pairing, handover and performance still need device
testing.

Build from source with `python3 scripts/build.py`. To reuse prepared native
libraries, run `python3 scripts/build_nearby.py --skip-engine --lint`.
Run `python3 tests/run_nearby_protocol.py` and verify the update with
`python3 tests/check_nearby_package.py /path/to/OpenBW-Android-0.48.apk`.

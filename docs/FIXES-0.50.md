# OpenBW Android 0.50 — Nearby location permission fix

Fixes the immediate `MISSING_PERMISSION_ACCESS_COARSE_LOCATION` error when
starting Host Game or Join Nearby. In 0.49, the manifest excluded both location
permissions above Android 12L and the runtime request skipped them on Android
13+. The Google Nearby service on the reported phones still required location.

Both foreground location permissions are now available on newer Android versions.
Host/Join requests coarse location, plus fine location on Android 10 and newer,
alongside the applicable Bluetooth and Nearby Wi-Fi permissions. Fine location
requests always include coarse location, even if Approximate location was
already granted. No background location permission is requested.

The app waits for permission and rechecks all actual grants before contacting
Google Nearby. Partial grants and cancelled dialogs produce instructions rather
than starting discovery. Late callbacks cannot restart a closed lobby, repeated
taps cannot replace a pending request, and service permission errors identify
the setting to change.

## Install

Install 0.50 over the existing app on both phones. The package ID and signing
key are unchanged; versionCode 51 is above 0.49's 50 and 0.48's 49. Keep the app
installed to retain imports, saves and settings.

Open Multiplayer, choose Host Game or Join Nearby, and allow Location **while
using the app**, with **Precise location** enabled, plus **Nearby devices**.
If previously denied, change those options in Android Settings > Apps > OpenBW
> Permissions. Turn on Bluetooth and Wi-Fi. If discovery finds no phones, also
check the phone's Location switch. Both phones still need Google Play services.

## Verification

- 608 checks execute the production NativeNearby class against fake Android and
  Google service boundaries for API levels 26, 28–36. They cover Host/Join,
  existing grants, the 0.49 upgrade state, denial/cancellation, partial grants,
  Approximate-to-Precise upgrades, duplicate taps/callbacks and closed lobbies.
- The 1,430 production protocol assertions pass for build 51.
- APK checks verify the compiled location declarations have no maxSdkVersion,
  signing/update identity, library and asset correspondence, JNI and alignment.
- Native game/video libraries are reused byte-for-byte from 0.49. Gameplay,
  multiplayer timing and save schema are unchanged.

These are automated host and package checks. Android permission dialogs,
physical installation, discovery, pairing and Bluetooth/Wi-Fi performance have
not been tested on two real phones.

Build: `python3 scripts/build.py`, or reuse the included native libraries with
`python3 scripts/build_nearby.py --skip-engine --lint`.
Checks: `python3 tests/run_nearby_permissions.py`,
`python3 tests/run_nearby_protocol.py`, then
`python3 tests/check_nearby_package.py /path/to/OpenBW-Android-0.49.apk`.

Android's paired coarse/fine permission rule:
https://developer.android.com/develop/sensors-and-location/location/permissions/runtime

Google Nearby permission error definitions:
https://developers.google.com/android/reference/com/google/android/gms/nearby/connection/ConnectionsStatusCodes

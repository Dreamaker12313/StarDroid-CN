# OpenBW Android 0.46

- Victory and defeat score screens use the six original race/outcome backgrounds,
  score panels, tabs, palette ramps and gluscore.bin geometry. Corrected letter
  spacing, text bounds, long-name truncation, elapsed-time/button overlap, hover
  feedback and score-bar shading. The original font is used when imported; the
  readable fallback now uses the correct original palette colors too. Both
  252-magenta and 255-magenta transparency keys are handled without pink pixels.
- Victory and defeat panels slide in and out with the menu swish sounds. Text
  and controls appear after entry and disappear as exit starts. Counts begin
  after assembly. OK and Android Back both complete the exit before navigation.
- Custom Game now slides in and out, including OK, Cancel and Android Back.
  Controls move with their parent panels; content and touch targets wait for the
  panels to settle. The title identifies StarCraft or Brood War.
- Choosing StarCraft enforces Classic melee unit, upgrade and technology
  availability for all owners, including computer opponents and practice games.
  Imported terrain maps remain usable with the selected gameplay rules.
  Classic AI uses TLOf/TMED/THIf, ZLOf/ZMED/ZHIf, PLOf/PMED/PHIf from the supplied
  original scripts. Unavailable requests cannot reserve AI resources or spawn
  expansion units. Brood War retains its expansion scripts and units.
- New saves record the actual skirmish rules. Existing saves from 0.45 or earlier
  retain the Brood War rules they were played with, even if the old menu said
  StarCraft. The portable snapshot schema remains version 2. Replay headers now
  identify the match's Classic/Brood War mode.
- Original green Wraith wireframe Android launcher icon, drawn as vector paths
  for this project, including adaptive masking and Android 13 themed icons.
  Editable illustration: artwork/wraith-launcher.svg. No retail sprite is copied.

## Local multiplayer feasibility

The simulation already exposes command batches and peer initialization in
web/wasm_main.cpp (openbw_init_mp, openbw_out_*, openbw_apply). The native Android
adapter currently consumes local input directly, and has no peer transport or
lobby. Offline play is feasible, but is not implemented in 0.46.

A first version should use two phones on the same Wi-Fi network or a phone's
local-only hotspot; Wi-Fi Direct is another supported option. Bluetooth Classic
RFCOMM is feasible as a separate transport, but needs latency/jitter testing.
Both require a host/join lobby, matching map and rules, synchronized frame
batches, deterministic seeds, desync checks, pause/disconnect behavior and tests
on two physical phones. The existing engine hooks reduce the work; they are not
evidence that end-to-end multiplayer already works.

Android references checked 2026-10-23:
- https://developer.android.com/develop/connectivity/wifi/localonlyhotspot
- https://developer.android.com/develop/connectivity/wifi/wifi-direct
- https://developer.android.com/develop/connectivity/bluetooth/connect-bluetooth-devices

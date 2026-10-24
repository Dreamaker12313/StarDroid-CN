# StarDroid player guide

[Back to the project](../README.md)

## Importing and updating

Follow the [installation instructions](../README.md#install) to import the three core MPQs and the campaign/media archives. **App Options** is also the screen shown when game files are missing. It has one import action, the file guide, and **Installed content** counts.

Importing copies content into private app storage. Keep the original archives elsewhere: uninstalling StarDroid or clearing Android app data removes local imports, settings, and saves. Android backup is disabled for this app. Update by installing the matching signed APK over the existing app.

Use **Import maps / ZIP…** in the custom-game or host map selector for `.scm`, `.scx`, and ZIP map collections. Campaign bundles belong in **Import game files**. The included community map is **Weave**; additional game maps are not bundled.

## Touch controls and settings

Open **Menu → Options → Touch Controls** during a match. Its **Gesture guide** reflects your current preferences. The [README gesture table](../README.md#touch-controls) describes fresh-install defaults.

### Selection

- **Drag to pan / hold to select** is the default. Start dragging immediately to move the camera; hold briefly first to draw a selection box. The default selection hold is about 180 ms.
- You can switch to **Drag to select / two fingers pan** under **Selection settings**.
- **Hold tap always selects** helps distinguish selection from a ground order.
- The selection-mode button arms selection when you need it. It can be moved to the other side or hidden.
- Double-tap selects units of the same type. Its timing window and selection tap tolerance are adjustable.

### Camera

- Two fingers always pan, even when pinch zoom is disabled.
- Pinch zoom and **Allow zoom out** are on by default. Existing saved preferences take priority when updating.
- Tap or drag the minimap to move the camera. Holding there issues an order when **Minimap hold issues orders** is enabled; the default hold is about 450 ms.
- **Camera settings** includes pan speed, pinch sensitivity, reverse drag, and minimap hold timing.

### Orders and descriptions

With an army selected, tapping open ground issues attack move by default. Use the attack/move toggle for ordinary movement, or choose commands directly from the command card. Workers use context-sensitive orders.

For explicit command-button control, enable **Disable ground-tap orders** in **Command settings**. It is unchecked by default. Hold a command icon to read its description; a description hold does not issue that command on release. Lower **Description hold** if the popup feels slow. A finger can use a short hold without hover-capable hardware.

Tap a production-queue icon to cancel that queued unit. Android **Back** cancels targeting, dismisses a dialog, or opens the game menu.

### Building placement

Choose a building, position the preview, and tap **Build**. **Cancel** abandons placement. **Build buttons follow placement** keeps both buttons below the preview, including when they overlap the interface. Covered controls cannot receive taps.

While dragging a building preview, hold your finger near an edge to scroll the
map. You can keep dragging beneath the command bar or over the minimap to scroll
down; the drag does not press those controls. The preview stays in the visible
world. Lift your finger to stop, then tap **Build** or **Cancel**. Scrolling works
in all eight directions, uses the camera pan-speed setting, and has the same
speed at different display rates. Scrolling starts farther from the top and side
edges. **Camera settings → Scroll while placing** enables or disables placement
edge scrolling and is on by default. Your choice is saved. Small one-finger and
two-finger pans preserve fractional movement.

Turn **Build buttons follow placement** off for a fixed button position. **Command settings** also controls the finger offset and confirmation; with confirmation disabled, releasing your finger places the building.

### Control groups and interface size

Enable **Show control-group buttons** under **Selection settings**. Hold a numbered group to assign the current selection, tap to recall it, and double-tap to center the camera.

Interface-size options adjust resources, command buttons, descriptions, and selection/move controls. Sound options control effects and music separately. **Miscellaneous → Cheats** contains the single-player cheat controls, including **Force victory (end match)**.

## Local multiplayer

### Preparing devices

Use the same release APK and compatible classic data on every device. Enable Bluetooth and grant the requested nearby-device permissions. The combined mode also needs Wi-Fi Direct support and any permissions Android requests for it. Older Android versions can require Location permission and the system Location switch for discovery.

### Hosting

1. Open **Multiplayer**, select or create a player name, and choose the expansion. Brood War is the default expansion choice.
2. Select a connection mode, then **Host Game**.
3. Choose a map, speed, difficulty, game type, and Hero Mode. This screen shows player capacity; slot editing is in the lobby.
4. Create the lobby. Accept Android's discoverability/connection prompts and compare the pairing codes as devices join.
5. Tap unoccupied slots to choose **Player**, **Computer**, or **Closed**. Tap an occupied player's name, then a destination slot to move that player. Slot order affects map starting positions.
6. Set races and, in Teams mode, team numbers. Matching numbers share vision and victory, with separate armies and resources. Joining players can change their own race.
7. Tap the chat input to type and **Send** to chat. Start when the lobby reports readiness; the five-second countdown leads into the match.

### Joining

Open **Multiplayer**, choose your name and the matching expansion/connection mode, then **Join Game**. Select the host and tap **Join**. Use **Search Again** if it has just opened its lobby. Accept Android pairing prompts and confirm only matching in-app codes. Wait for the map transfer, choose your race, and wait for the host to start.

The selected map transfers automatically. Core game archives do not transfer. The combined mode begins over Bluetooth and can switch connections to Wi-Fi Direct on supported devices. Try Bluetooth-only mode if Wi-Fi Direct is unreliable.

There are up to eight map slots, including the host and computers. Connected-device capacity also depends on hardware and Android radio support. There is no Battle.net integration, internet lobby service, host migration, or mid-match rejoin flow. Keep the host active during play.

### Multiplayer saves

The host uses **Save Game** from the match menu. To continue later, the host chooses **Multiplayer → Load Saved**, selects the save, and opens its resumed lobby. Other devices rejoin, and the host arranges players in the saved human slots before starting. Saved match settings and computer slots are retained.

Use the same release build and compatible game data to resume. Saves are stored on the host device; this is not cloud saving or automatic reconnect.

## Hero Mode

Enable Hero Mode for a custom or multiplayer match. Heroes train at Engineering Bays, Evolution Chambers, and Forges, alongside their normal upgrades. Their command-card positions stay fixed.

Each player may have one of each hero form alive or queued, across all producers. A hero can be rebuilt after death. Training occupies its producer, so build extra upgrade buildings to train heroes and upgrade separately. Computers can use heroes on Easy, Medium, and Hard.

Heroes still require their relevant technology. Infested Duran needs a Lair or Hive and a Hydralisk Den; Infested Kerrigan needs a Hive and Queen's Nest. Tassadar and Zeratul can merge, but neither can be rebuilt until the resulting hero Archon dies. The [hero chart](campaign-heroes.json) records the roster, prices, and comparison stats. These optional rules do not change campaign units.

## Troubleshooting

| Problem | Check |
| --- | --- |
| Import screen keeps appearing | All three core archives must show as installed. Let each import finish. |
| Missing mission or movie | Import the corresponding original installation-media archive and check Installed content. |
| Grey upgrade icon | Read the description for the next level's technology requirement; also check resources, power, and whether another producer is researching it. |
| Camera moves instead of box selection | Hold before dragging, or change the drag preference. |
| Accidental ground orders | Use the selection-mode button, hold to select, or disable ground-tap orders. |
| Host is not visible | Check discovery permissions, Bluetooth discoverability, connection mode, and Search Again. |
| Wi-Fi Direct connection fails | Retry with Bluetooth-only mode on the devices. |
| APK update rejected | Check architecture and signing identity. Avoid uninstalling while troubleshooting if you need saved data. |

For unresolved problems, [report a bug](../../../issues/new/choose) with the device, Android version, release build, map or mission, settings, and steps. Do not attach MPQs or installation archives.

## Reporting an unexpected close

Version 1.0 includes local diagnostic evidence and native call stacks. After
the app closes unexpectedly, reopen it and choose **Credits** from the main menu, then
**Copy** in Diagnostics / credits. Share that text with your bug report.

Android 11+ can report previous process exits, including native/Java crashes,
ANRs, and low-memory kills. An update or requested stop is not itself a crash;
a SIGKILL without a specific reason does not identify memory pressure or a
vendor battery policy. Current memory figures are labeled separately from
historical exit records. Saved Java/renderer reports retain their timestamp.
Reports are local and are not sent automatically.

On Android 12+, the report also attempts to read the last native crash's
faulting thread and backtrace. Android can discard old traces, so copy the
report promptly. An update may retrieve a retained crash from the previous
build without another reproduction. The decoded stack stays local across
restarts; raw memory dumps and app log buffers are not copied.

Technical reference: [Android native exit traces](https://developer.android.com/reference/android/app/ApplicationExitInfo#getTraceInputStream()).

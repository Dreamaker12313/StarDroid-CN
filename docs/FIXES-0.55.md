# OpenBW Android 0.55

Install `OpenBW-Android-0.55.apk` over the existing app on every participating device. Do not uninstall. The application ID and signing certificate are unchanged, preserving imported files, preferences and saves. All players must use this version.

## Multiplayer

Choose StarCraft or Brood War after pressing Multiplayer in the main menu. The connection screen now contains connection modes, Host Game, Join Game, Load Saved and Cancel. Pick races in the lobby. Host and Join fit the original panel; new controls have simple red borders.

The host can create up to eight participant slots, within the selected map's starting-location limit. Tap empty slots to cycle Closed, Player and Computer. Tap an occupied player, then a destination slot to move or swap them, including the host. Slot numbers correspond to the map's original starting locations. Guests can choose their own race. Settings and readiness are redistributed after each change. The five-second countdown uses the original beep and cancels if a device backgrounds.

The lobby has larger bordered player rows and functional chat. Tap the message field to open the keyboard; Send or the keyboard's Send action broadcasts the message. Names and long messages are constrained to their panels. Game type, difficulty, speed and instructions fit inside the original artwork.

Connections use a host relay with an independent encrypted Bluetooth connection and optional authenticated Wi-Fi Direct lane for each guest. Seven guests are supported by the protocol; actual device radio limits can be lower. Each connection can fall back separately to Bluetooth. A guest leaving an active match is removed through the synchronized command stream. The remaining devices continue. Leaving as host ends the match; there is no host migration or mid-match reconnection.

Host-controlled saves retain all eight accepted command buffers and the host's assigned slot. Saving while someone leaves waits for the departure to apply, then closes that slot in the saved setup. A save needing fewer player slots than the currently connected devices is rejected before replacing the running match. Existing 0.54 multiplayer snapshots remain readable. Resuming keeps the saved setup; connected devices can be assigned among its human slots.

## Interface and controls

- Tooltips lay out each wrapped description and requirement once, allocate enough height and fit within the available screen area. Long unbroken words wrap. Shared font drawing prevents line spacing smaller than the font's height.
- New installs use a 220 ms description hold. Existing hold preferences remain unchanged. Hover responds immediately, small command gutters remain inspectable, and an early slide across commands enters inspection without issuing an order on release.
- Only the victory/defeat UI slides from the left. The background remains stationary on entry and exit.
- Map import and multiplayer controls use red outlines. Import is labeled **Import maps/ZIP**. The map scrollbar retains the original arrows and thumb with transparent surrounds and no rectangular track.
- Connection text uses “device”; the services/internet slogan and redundant race/expansion selectors are removed.
- The launcher uses a redrawn isometric Wraith silhouette and green wireframe, including swept wings, twin rear booms and the split forward body.

## Gameplay

- Mass larva morphing queues the affordable portion and gives one appropriate mineral, gas or supply error for the remainder. Replacement morphs retain their supply exemption.
- The original Ultralisk and Torrasque selection-sound range runs backward. Normalizing that range restores normal selection voices before repeated clicks reach the annoyed responses.
- In the original Brood War Terran mission First Strike, trigger-created map revealers refresh vision while dialogue pauses units. Duran and his base are visible during the introduction. Completed player buildings can perform the normal nearby rescue, allowing the newly transferred Command Center to bring Duran under player control without another approach. Movement and orders remain paused during the dialogue; the rescue radius is unchanged.

The 0.54 transport/bunker deselection, flying-building command cards, addon-to-normal landing switch, multiple computers, Free for All, terrain previews, scrollable map lists, host-selected speed, multiplayer return to main menu and new-install defaults remain included.

## Validation scope

`VALIDATION.md` and `validation/*-v55.json` describe the automated checks. Both Android native architectures were rebuilt and the APK signature, JNI methods, packaged libraries, alignment and lint results were checked. These are host-side engine, transport, rendering and Android boundary tests. Installation, real Bluetooth/Wi-Fi Direct groups, touchscreen hover behavior, on-device keyboard behavior and complete matches still need physical-device confirmation.

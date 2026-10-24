# StarDroid 1.0

## Earlier edge scrolling and placement preference (build 70)

- Expand the top, left and right edge activation bands from 24 to 48 logical
  pixels. Keep the bottom threshold, maximum speed and timed smoothing.
- Add **Scroll while placing** to **Touch Controls → Camera settings**, enabled
  by default for new and existing installs. Persist both enabled and disabled
  choices while preserving the other controls.
- Disabling the option stops placement edge movement immediately and still
  allows ordinary panning, selection/target scrolling and building confirmation.
- Fit the new checkbox into the existing camera panel and check all three race
  interfaces. The tested native engine and renderer crash fix are unchanged.
- Keep version 1.0, now internal update code 70.


## Placement scrolling and camera motion (build 69)

- Keep scrolling while a captured placement drag moves beneath the command bar
  or over the minimap. Keep the preview inside the visible world, accounting
  for zoom, command-button size and finger offset. Covered controls still do
  not receive the drag.
- Integrate edge movement by elapsed display time with a short acceleration
  ramp, equal directional speeds and normalized diagonals. Use the pan-speed
  preference and preserve fractional movement for regular and two-finger pans.
- Stop edge movement on release, leaving the edge, cancellation, a modal or
  transition, and pinch gestures. Overshooting the left edge no longer loses
  edge movement. Android owns the camera integration, preventing an additional
  native edge step in the same frame.
- Retain the build 68 buffer-overrun fix. Re-run the guarded-buffer and
  AddressSanitizer regression with moving-camera and map-limit cases.
- Keep version 1.0, now internal update code 69. Both Android native libraries
  are rebuilt; physical touch/display confirmation remains pending.


## Placement-preview native crash (build 68)

- Fix a one-row buffer overrun when a building-placement outline reaches the
  bottom of the image. The device's retained native stack identifies this exact
  drawing operation, and the old renderer reproduces a write SIGSEGV on a host
  with a guarded image buffer.
- Fix the same off-by-one error in the RGBA outline used for drag selection.
  Both helpers now keep their bottom border inside the clipped rectangle.
- Verify blocked/valid previews, buildings from all races, add-ons, refinery and
  landing previews, scrolling positions, screen edges, resize and zoom paths.
- Keep version 1.0, increase the internal update code to 68, and rebuild both
  supported native architectures. Preserve the installation/signing identity,
  content, settings, saves, simulation rules and multiplayer protocol.
- Automated memory and packaging checks pass. Physical-device confirmation is
  still needed; the Vivo closure is not proven to have the same cause.


## Native crash stacks (build 67)

- A device report confirmed a foreground native SIGSEGV in single-player play.
  Its older background excessive-CPU exit is a different event. Restarted
  memory statistics do not establish memory usage at the crash.
- Read Android 12+ native tombstones through the supported exit-history API,
  retaining the faulting thread, signal/code/address, library PCs, function
  names and build identifiers. Do not copy memory dumps or app log buffers.
- Bound trace input and output, handle missing/overwritten Android traces, and
  retain the latest decoded native stack locally across app restarts.
- Keep the existing Credits → Copy workflow, version 1.0, package/signing
  identity, native libraries, game assets and multiplayer protocol.
- The crash is not reproduced or fixed. The next diagnostic report is needed
  to locate the failing native code. See [release notes](RELEASE-1.0.md) for current download information.


## Unexpected-close diagnostics (build 66)

- Keep version 1.0 and the existing signing/application identity.
- Diagnostics now includes Android 11+ process exit history: Java/native crash,
  ANR, low-memory termination, updates, and other reported exit reasons. A
  SIGKILL alone is not classified as a memory or battery-policy problem.
- Persist the latest Java/renderer error with a bounded stack and session
  context; include current memory figures and memory-pressure callbacks.
- Reports stay on the device and use the existing Copy action. No telemetry
  service, new permission, battery exemption, or gameplay change was added.
- The reported Vivo X100 foreground shutdown has not been reproduced or fixed.
  Collect its post-close Diagnostics before attributing the cause.


## Upgrade command cards (build 65)

- Kept version 1.0. The next upgrade level stays in its original command slot,
  greyed out while its prerequisite is missing. Its tooltip names the next level
  and required building. Fully completed or map-disabled upgrades stay hidden.
- Reproduced the apparent level-1 cap: the previous UI removed next-level
  commands whenever the Science Facility or equivalent tech was missing.
  Actual level-2 and level-3 eligibility and simulation rules are unchanged.
- Verified all 16 weapon, armor and shield lines through real research commands,
  including both Spire types, custom Melee/FFA/teams, multiplayer, both expansions
  and Hero Mode on/off. Existing campaign restrictions and Protoss completed-tech
  counting are preserved.
- Removed the Cheats replay-export note. Replay playback is not implemented and
  the current Android replay-save button remains disabled.


## Settings cleanup (build 64)

- Kept the displayed version at 1.0 and advanced only Android’s internal build
  code to allow an in-place update.
- App Options and the missing-files startup screen now show a permanent file
  guide, one import button, installed-content counts and a return button when
  the core files are ready. Removed the file-guide toggle, Mission export,
  Campaign movies and Controls & settings sections. Movie counts are included
  under Installed content.
- Renamed Testing Cheats to Cheats, including the menu heading and replay note.
- Renamed the victory action to Force victory (end match) and removed the
  test-defeat button.
- Removed control preset buttons and the preset label; Selection, Camera,
  Command settings and the Gesture guide remain. Comfortable is still the
  default for new installs. Existing control choices and zoom preferences
  are preserved.

## Project rename (build 63)

- Renamed the Android launcher entry, project, theme, setup screen, diagnostics,
  clipboard label, application messages and release artifacts to StarDroid.
- Renamed mission, music, interface, story and cinematic bundle filenames,
  exported missions, replay exports and generated hero-chart files.
- Existing imported bundles are recognized under their old names. They are
  renamed in their existing directory without replacing newer imports; if a
  rename fails, the old file is still read. Format identifiers remain compatible.
- Bluetooth service labels, Wi-Fi Direct group names, logs and worker labels
  use StarDroid. New clients accept both old and new Wi-Fi invitation names.
  Update every multiplayer device to 1.0 because older clients only recognize
  the old Wi-Fi group name.
- The initial rename used version name 1.0 and Android version code 63. The installed application
  identity, signing certificate, preferences, profiles and save formats are
  retained. Install over the existing app without uninstalling.
- Current documentation and visible legacy-web text use StarDroid. Upstream
  engine names, credits, licenses, technical compatibility identifiers and
  historical release records are preserved. ToadWarrior's credit remains.

The native command-card library was rebuilt; simulation rules are unchanged. Validation covers
old and new bundle names, actual campaign export/import, multiplayer protocol and
encrypted socket checks, permissions, menu/placement rendering and signed APK
identity. Android hardware testing remains pending.

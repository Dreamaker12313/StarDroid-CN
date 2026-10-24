# 0.60 — placement confirmation controls

- **Build buttons follow placement** is enabled by default in Game Menu →
  Options → Touch Controls → Command Settings. It is saved with the device's
  touch preferences. Existing customized preferences are preserved.
- Build and Cancel move together beside the placement preview, accounting for
  zoom and the building finger offset. They move around edge controls and stay
  within the screen. The existing in-game button artwork is retained.
- Disabling the setting restores the previous fixed position. The separate
  **Confirm building placement** setting still controls confirmation behavior.
- Build confirms the stored placement target; tapping the button does not move
  that target. Cancel still exits placement. Confirmation buttons are hidden
  while a menu is open.
- The Command Settings rows have been spaced to fit the added option without
  overlapping labels or touch targets.

This release changes the Android interface only. Native libraries are identical
to 0.59 and multiplayer retains protocol build 60. Existing imports and saves
remain in place when updating the app without uninstalling.

Host checks cover preference migration/persistence, fixed and following modes,
1,728 edge/zoom/control arrangements, actual Build/Cancel callbacks, and rendered
settings and placement controls for all three races. The signed APK passes lint,
update-identity and package checks. Physical Android installation and touch
testing remain pending.

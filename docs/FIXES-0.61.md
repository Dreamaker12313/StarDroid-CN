# 0.61 — placement controls stay below

- Following Build and Cancel buttons stay below the visible placement preview.
  They no longer shift above or beside it to avoid HUD controls. At the bottom
  of the world view, they sit beneath its clipped preview over the HUD.
- The row renders last, with a dark backing to keep its labels readable over
  other controls. Horizontal screen edges still keep both buttons reachable.
- The entire row captures touches, including the gap. Covered buttons, command
  icons and the minimap cannot receive taps or holds through it. A gesture that
  begins on an exposed control is also consumed if it enters the covered area.
- A placement drag continues normally through the row; it cannot accidentally
  press Build or Cancel. A fresh touch is required. Ending placement restores
  access to the controls underneath.
- The existing follow-placement setting and fixed-position option are retained.
  Follow placement and Allow zoom out default to On; saved choices are preserved.

The focused host harness exercises the actual touch handler with Android event
shims, including redraws during a press, holds, gaps, covered releases, dragging,
cancellation and restored controls. It checks screen-edge/zoom positions and
renders the original HUD artwork for all three races. Physical Android touch
testing remains pending.

Install over the current app without uninstalling. This interface-only update
uses the same native libraries and multiplayer protocol as 0.59 and 0.60.

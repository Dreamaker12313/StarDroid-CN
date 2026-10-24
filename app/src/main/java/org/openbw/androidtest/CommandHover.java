package org.openbw.androidtest;

import java.util.List;

/** Live hit testing for mouse/stylus hover and touch-and-hold inspection. */
final class CommandHover {
  static final long HOLD_MS = 220;
  long holdMs = HOLD_MS;
  boolean enabled = true;
  NativeHud.Hit pressed;
  private boolean hovering, touching, inspecting;
  private float hoverX, hoverY, x, y, downX, downY;
  private long downAt;

  void hover(float x, float y, boolean leave) {
    hovering = !leave;
    hoverX = x;
    hoverY = y;
  }

  void begin(NativeHud.Hit hit, float x, float y, long time) {
    cancel();
    pressed = hit;
    touching = true;
    this.x = downX = x;
    this.y = downY = y;
    downAt = time;
  }

  void move(float x, float y, long time, float slop) {
    if (!touching) return;
    inspecting |= enabled && time - downAt >= holdMs;
    this.x = x;
    this.y = y;
    if (!inspecting && Math.hypot(x - downX, y - downY) > slop) {
      inspecting = enabled;
      pressed = null;
    }
  }

  NativeHud.Hit tooltip(List<NativeHud.Hit> hits, long time) {
    if (!enabled) return null;
    if (hovering) return hit(hits, hoverX, hoverY);
    if (!touching) return null;
    inspecting |= enabled && time - downAt >= holdMs;
    return inspecting ? hit(hits, x, y) : null;
  }

  NativeHud.Hit release(List<NativeHud.Hit> hits, float x, float y, long time) {
    NativeHud.Hit current = hit(hits, x, y);
    boolean activate = touching && !inspecting && (!enabled || time - downAt < holdMs)
        && sameAction(pressed, current);
    cancel();
    return activate ? current : null;
  }

  void cancel() {
    pressed = null;
    hovering = touching = inspecting = false;
  }

  private static NativeHud.Hit hit(List<NativeHud.Hit> hits, float x, float y) {
    for (NativeHud.Hit hit : hits) if (hit.rect.contains(x, y)) return hit;
    // Fill the tiny gutters between command icons for inspection only.
    NativeHud.Hit nearest=null;float best=3.5f*3.5f;
    for(NativeHud.Hit h:hits){if(h.fields==null)continue;float dx=Math.max(h.rect.left-x,Math.max(0,x-h.rect.right)),dy=Math.max(h.rect.top-y,Math.max(0,y-h.rect.bottom)),d=dx*dx+dy*dy;if(d<best){best=d;nearest=h;}}
    if(nearest!=null)return nearest;
    return null;
  }

  private static boolean sameAction(NativeHud.Hit a, NativeHud.Hit b) {
    if (a == null || b == null) return false;
    if (a.cancel != b.cancel || a.selectUnit != b.selectUnit || a.more != b.more) return false;
    if (a.fields == null || b.fields == null)
      return a.fields == b.fields && java.util.Objects.equals(a.help, b.help);
    for (int index : new int[] {0, 1, 3, 11, 12}) {
      String av = index < a.fields.length ? a.fields[index] : "";
      String bv = index < b.fields.length ? b.fields[index] : "";
      if (!java.util.Objects.equals(av, bv)) return false;
    }
    return true;
  }
}

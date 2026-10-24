package org.openbw.androidtest;

import android.graphics.RectF;

/** Keeps confirmation controls below the visible placement preview, over the HUD if needed. */
final class PlacementButtons {
  static final float BUTTON = 104, GAP = 6, HEIGHT = 28, WIDTH = BUTTON * 2 + GAP;

  static RectF position(float width, float x, float y, float zoom) {
    float left = Math.max(8, Math.min(width - WIDTH - 8, x - WIDTH / 2));
    // Allow the largest normal footprint plus tile snapping. The world preview
    // is clipped at WORLD_BOTTOM, so its visible lower edge never extends below it.
    float top = Math.min(NativeHud.WORLD_BOTTOM, y + 64 * zoom) + 8;
    return new RectF(left, top, left + WIDTH, top + HEIGHT);
  }
}

package org.openbw.androidtest;

/** Largest opening-text size that fits inside the original 640x480 safe area. */
final class StoryLayout {
  final float scale, top, height;
  final int width, lineHeight;

  private StoryLayout(NativeArt.Font font, String text, boolean lower, float size) {
    scale = size;
    width = Math.max(1, (int) (576 / size));
    lineHeight = Math.max(22, font.height);
    height = font.lines(text, width).size() * lineHeight * size;
    top = lower ? 448 - height : 52;
  }

  private boolean fits(NativeArt.Font font, String text, boolean lower) {
    if (height > (lower ? 416 : 396)) return false;
    for (String line : font.lines(text, width))
      if (font.measure(line) * scale > 576) return false;
    return true;
  }

  static StoryLayout fit(NativeArt.Font font, String text, boolean lower) {
    StoryLayout full = new StoryLayout(font, text, lower, 1.5f);
    if (full.fits(font, text, lower)) return full;
    float lo = .01f, hi = 1.5f;
    // Wrapping is recalculated for each candidate, including explicit line breaks.
    for (int i = 0; i < 20; i++) {
      float mid = (lo + hi) / 2;
      if (new StoryLayout(font, text, lower, mid).fits(font, text, lower)) lo = mid;
      else hi = mid;
    }
    return new StoryLayout(font, text, lower, lo);
  }
}

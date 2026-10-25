package org.openbw.androidtest;

import android.graphics.*;
import java.nio.file.*;
import java.util.*;
import javax.imageio.ImageIO;

/** Host-only regression checks; uses the production renderer with an AWT shim. */
final class FontFallbackTest {
  private static int checks;
  private static void check(boolean value, String reason) {
    checks++;
    if (!value) throw new AssertionError(reason);
  }

  static void run(Path out, NativeArt.PCX tint, int[] palette) throws Exception {
    for (int slot : new int[]{0, 1, 2, 4})
      for (String prefix : new String[]{"font/", "files/font/"})
        for (String size : new String[]{"8", "10", "12", "14", "16", "16x", "32", "50"})
          NativeBridge.overrides.put(slot + "/" + prefix + "font" + size + ".fnt", null);
    NativeArt art = new NativeArt();
    Bitmap sample = Bitmap.createBitmap(640, 320, Bitmap.Config.ARGB_8888);
    Canvas canvas = new Canvas(sample);
    Paint bg = new Paint(); bg.setColor(0xff081329); canvas.drawRect(0, 0, 640, 320, bg);
    int y = 16;
    for (String size : new String[]{"8", "10", "14", "16", "16x"}) {
      NativeArt.Font font = art.font(size, tint, palette, 1);
      check(font.fallback, "Expected no-original-font fixture");
      check(font.measure("iii") < font.measure("WWW"), "Lost proportional letter widths");
      check(font.measure("\u0003Test\u0001") == font.measure("Test"), "Color codes occupy width");
      check(font.advance('\t') == 4 * font.advance(' '), "Tab width differs from layout");
      for (int c = 32; c < 256; c++) {
        if (c == 127 || c >= 128 && c <= 159) continue;
        Bitmap glyph = font.glyph(c, 2);
        check(glyph == font.glyph(c, 2), "Glyph not cached");
        check(glyph.getHeight() == font.height, "Glyph outside line height");
        check(glyph.getWidth() <= font.advance(c) + 1, "Ink overruns next letter");
      }
      for (String line : font.lines("A very long mission name WWWiiii and another word", 94))
        check(font.measure(line) <= 94, "Wrapped text outside box");
      Bitmap h = font.glyph('H', 2);
      Set<Integer> shades = new HashSet<Integer>(); int top = h.getHeight(), bottom = -1;
      for (int py = 0; py < h.getHeight(); py++) for (int x = 0; x < h.getWidth(); x++) {
        int color = h.getPixel(x, py);
        if (color >>> 24 > 0) { shades.add(color & 0xffffff); top = Math.min(top, py); bottom = py; }
        check((color & 0xffffff) != 0xfc00fc, "Transparent palette key became magenta text");
      }
      check(bottom >= top && bottom - top + 1 >= font.height / 2, "Fallback text too small/empty");
      if (font.height >= 14) check(shades.size() >= 3, "Menu text lost palette bevel/shadow");
      check(!samePixels(font.glyph('H', 2), font.glyph('H', 4)), "Hover color does not change");
      check(font.withColor(0xffcc8844).glyph('H', 2).getHeight() == font.height, "Fixed color changed metrics");
      check(font.withShadedColor(0xff30e050).glyph('H', 2).getHeight() == font.height, "Story tint changed metrics");
      font.draw(canvas, size + "  Terran  Episode I  Load Saved  Play Custom", 16, y, 610, 0, 2, 0);
      font.draw(canvas, "Selected  Disabled  Égj Áy", 16, y + font.height + 3, 610, 0, 4, 0);
      y += font.height * 2 + 18;
    }
    check(art.font("16x", tint, palette, 1).measure("Load Saved")
        > art.font("16", tint, palette, 1).measure("Load Saved"), "Wide button font has no distinct width");
    check(art.diagnostics().contains("STYLED SYSTEM FALLBACK"), "Styled fallback absent from diagnostics");
    check(art.diagnostics().contains("any supported size"), "Report hides original-size search");
    ImageIO.write(sample.image, "png", out.resolve("font-fallback.png").toFile());
    for (String name : new String[]{"glumain", "glucmpgn", "gluexpcmpgn", "glulogin"}) {
      NativeGlue glue = new NativeGlue(new NativeArt(), name, name.equals("glumain") ? "palmm" : "palnl", false);
      for (NativeArt.Widget w : glue.layout.widgets) {
        if (w.type == 5 || w.text.isEmpty()) continue;
        String label = w.text.substring((w.flags & 0x200) != 0 ? 1 : 0);
        NativeArt.Font f = (w.flags & 0x4000) != 0 ? glue.button
            : (w.flags & 0x800) != 0 || w.type == 14 ? glue.large : (w.flags & 0x400) != 0 ? glue.small : glue.tiny;
        int width = Math.max(1, (w.rw > 0 ? w.rw : w.w) - w.tx);
        for (String line : f.lines(label, width))
          check(f.measure(line) <= width, name + ": label exceeds horizontal bounds: " + label);
        if (w.type == 14 || w.id >= 5 && w.id <= 11 && name.contains("cmpgn")) {
          int height = Math.max(1, (w.rh > 0 ? w.rh : w.h) - w.ty);
          check(f.lines(label, width).size() * f.height <= height,
              name + ": label exceeds vertical bounds: " + label);
        }
      }
      glue.close();
    }
    NativeBridge.overrides.clear();
    System.out.println("PASS " + checks + " font checks: original-size reuse, no-font fallback, cached glyphs, colors, accents, proportional wrapping and real dialog label bounds. AWT stand-in for Android sans font.");
  }

  private static boolean samePixels(Bitmap a, Bitmap b) {
    if (a.getWidth() != b.getWidth() || a.getHeight() != b.getHeight()) return false;
    for (int y = 0; y < a.getHeight(); y++) for (int x = 0; x < a.getWidth(); x++)
      if (a.getPixel(x, y) != b.getPixel(x, y)) return false;
    return true;
  }
}

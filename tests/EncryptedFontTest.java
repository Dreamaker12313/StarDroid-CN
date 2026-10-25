package org.openbw.androidtest;

import android.graphics.*;
import java.nio.file.*;
import java.util.*;
import javax.imageio.ImageIO;

/** Runs only against caller-owned archives. No font or installation metadata is bundled. */
final class EncryptedFontTest {
  static int checks;
  static void check(boolean ok, String message) { checks++; if (!ok) throw new AssertionError(message); }
  static void reject(byte[] font, byte[] metadata) {
    try { ClassicFontCipher.decodeFont(font, metadata); throw new AssertionError("Invalid envelope accepted"); }
    catch (IllegalArgumentException expected) { checks++; }
  }

  public static void main(String[] args) throws Exception {
    NativeBridge.root = Paths.get(args[0]);
    Path out = Paths.get(args[1]);
    byte[] metadata = Files.readAllBytes(NativeBridge.root.resolve("0/font/font.gid"));
    byte[] savedMetadata = metadata.clone();
    NativeArt art = new NativeArt();
    NativeArt.PCX tint = art.pcx("glue/palcs/tfont.pcx", false, -1);
    NativeArt.PCX background = art.pcx("glue/palcs/backgnd.pcx", false, -1);
    for (String size : new String[]{"8", "10", "12", "14", "16", "16x", "32", "50"}) {
      byte[] encrypted = Files.readAllBytes(NativeBridge.root.resolve("0/font/font" + size + ".fnt"));
      byte[] snapshot = encrypted.clone();
      byte[] original = ClassicFontCipher.decodeFont(encrypted, metadata);
      check(ClassicFontCipher.isPlain(original), "Decoded font has no FONT header");
      check(Arrays.equals(snapshot, encrypted) && Arrays.equals(savedMetadata, metadata), "Decoder modified source data");
      if (args.length > 2)
        check(Arrays.equals(original, Files.readAllBytes(Paths.get(args[2]).resolve("font" + size + ".fnt"))),
            "Independent decoder mismatch: font" + size);
      NativeArt.Font font = art.font(size, tint, background.palette, 1);
      check(!font.fallback && font.substitute == null, "Exact original font was not selected: " + size);
      check(Arrays.equals(original, font.data), "Renderer font differs from decoded original");
      int visible = 0;
      for (int c = Math.max(33, font.low); c <= font.high; c++) {
        Bitmap glyph = font.glyph(c, 2);
        if (glyph == null) continue;
        check(glyph.getHeight() == font.height, "Glyph outside original line height");
        for (int y = 0; y < glyph.getHeight(); y++) for (int x = 0; x < glyph.getWidth(); x++)
          if (glyph.getPixel(x, y) >>> 24 != 0) visible++;
      }
      check(visible > 100, "Decoded glyphs are empty");
      reject(Arrays.copyOf(encrypted, encrypted.length - 1), metadata);
      byte[] corrupt = encrypted.clone(); corrupt[corrupt.length - 8] ^= 1; reject(corrupt, metadata);
      corrupt = encrypted.clone(); corrupt[corrupt.length - 3] = (byte) 255; reject(corrupt, metadata);
      reject(encrypted, null);
    }
    check(art.diagnostics().contains("installed font decrypted; checksum verified"), "Font source not identifiable internally");
    check(!art.diagnostics().contains("font.gid"), "Installation metadata exposed in asset diagnostics");
    reject(new byte[1024 * 1024 + 72], metadata);
    for (String bin : new String[]{"glumain", "glucmpgn", "gluexpcmpgn", "glulogin"}) {
      String pal = bin.equals("glumain") ? "palmm" : bin.equals("glulogin") ? "palnl" : "palcs";
      NativeGlue glue = new NativeGlue(art, bin, pal, false);
      check(glue.recovery.isEmpty() && glue.paletteName.equals(pal), "Menu still uses recovery: " + bin);
      for (NativeArt.Font font : new NativeArt.Font[]{glue.tiny, glue.small, glue.dialogue, glue.large, glue.button})
        check(!font.fallback && font.substitute == null, "Menu still uses substitute font");
      Bitmap view = Bitmap.createBitmap(640, 480, Bitmap.Config.ARGB_8888);
      Canvas canvas = new Canvas(view); glue.draw(canvas, 1000);
      int[] ids = bin.equals("glumain") ? new int[]{3, 5, 2, 9, 4, 8}
          : bin.equals("glulogin") ? new int[]{4, 5} : new int[]{6, 7, 8, 9, 5, 11, 10};
      for (int id : ids) glue.label(canvas, id, null, true);
      ImageIO.write(view.image, "png", out.resolve(bin + "-original-fonts.png").toFile());
      glue.close();
    }
    byte[] broken = metadata.clone(); broken[0] ^= 32;
    NativeBridge.overrides.put("0/font/font.gid", broken);
    check(new NativeArt().font("16", tint, background.palette, 1).fallback, "Invalid key metadata should keep text readable");
    NativeBridge.overrides.put("4/files/font/font16.fnt", art.fonts.get("16"));
    check(!new NativeArt().font("16", tint, background.palette, 1).fallback, "Invalid encrypted source hid valid imported original");
    NativeBridge.overrides.clear();
    check(!new NativeArt().font("16", tint, background.palette, 1).fallback, "Reopened menu did not recover automatically");
    Arrays.fill(metadata, (byte) 0); Arrays.fill(savedMetadata, (byte) 0); Arrays.fill(broken, (byte) 0);
    System.out.println("PASS " + checks + " encrypted-font checks: all eight original fonts, independent reference comparison when supplied, exact menu fonts, malformed metadata/trailers, fallback recovery and source preservation.");
  }
}

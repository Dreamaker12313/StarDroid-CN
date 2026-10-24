package org.openbw.androidtest;

import android.graphics.*;
import java.nio.charset.Charset;
import java.util.*;

/** Original PCX, GRP, FONT, BIN and Smacker presentation, drawn by Android Canvas. */
final class NativeArt {
  static final Charset CP = Charset.forName("windows-1252");

  static int u16(byte[] b, int p) {
    return (b[p] & 255) | (b[p + 1] & 255) << 8;
  }

  static int u32(byte[] b, int p) {
    return u16(b, p) | u16(b, p + 2) << 16;
  }

  static String str(byte[] b, int p) {
    if (p < 1 || p >= b.length) return "";
    int e = p;
    while (e < b.length && b[e] != 0) e++;
    return new String(b, p, e - p, CP);
  }

  static String clean(String s) {
    return s.replaceAll("[\\x00-\\x09\\x0b-\\x1f]", "");
  }

  static String normal(String s) {
    return s.replace('\\', '/').toLowerCase(Locale.ROOT);
  }

  static String[] tbl(byte[] b) {
    if (b == null || b.length < 2) return new String[0];
    int count = u16(b, 0);
    if (2 + 2 * count > b.length) throw new IllegalArgumentException("Invalid string table");
    String[] out = new String[count];
    for (int i = 0; i < count; i++) out[i] = str(b, u16(b, 2 + i * 2));
    return out;
  }

  static final Paint PIXELS = new Paint();

  static final class PCX {
    Bitmap image;
    byte[] pixels;
    int[] palette = new int[256];
    int width, height, stride;

    PCX(byte[] b, boolean transparent, int glass) {
      if (b == null || b.length < 897 || b[0] != 10 || b[2] != 1 || b[3] != 8 || b[65] != 1)
        throw new IllegalArgumentException("Missing or invalid PCX");
      width = u16(b, 8) - u16(b, 4) + 1;
      height = u16(b, 10) - u16(b, 6) + 1;
      stride = u16(b, 66);
      if (width < 1
          || height < 1
          || width > 2048
          || height > 2048
          || stride < width
          || stride > 4096) throw new IllegalArgumentException("Invalid PCX dimensions");
      pixels = new byte[stride * height];
      for (int i = 0; i < 256; i++) {
        int p = b.length - 768 + i * 3;
        palette[i] = Color.rgb(b[p] & 255, b[p + 1] & 255, b[p + 2] & 255);
      }
      int p = 128, o = 0;
      while (o < pixels.length) {
        if (p >= b.length - 769) throw new IllegalArgumentException("Truncated PCX");
        int v = b[p++] & 255, n = (v & 192) == 192 ? v & 63 : 1;
        if ((v & 192) == 192) {
          if (p >= b.length - 769) throw new IllegalArgumentException("Truncated PCX run");
          v = b[p++] & 255;
        }
        if (n == 0 || o + n > pixels.length) throw new IllegalArgumentException("Invalid PCX run");
        Arrays.fill(pixels, o, o + n, (byte) v);
        o += n;
      }
      int[] out = new int[width * height];
      for (int y = 0; y < height; y++)
        for (int x = 0; x < width; x++) {
          int i = pixels[y * stride + x] & 255;
          out[y * width + x] =
              transparent && i == 0
                  ? 0
                  : i == glass ? (palette[i] & 0xffffff) | 0x99000000 : palette[i];
        }
      image = Bitmap.createBitmap(out, width, height, Bitmap.Config.ARGB_8888);
    }
  }

  static Bitmap grp(byte[] b, int id, int[] palette, boolean raw, boolean centered) {
    if (b == null || b.length < 6 || id < 0 || id >= u16(b, 0)) return null;
    int at = 6 + id * 8;
    if (at + 8 > b.length) return null;
    int w = b[at + 2] & 255,
        h = b[at + 3] & 255,
        base = u32(b, at + 4),
        cw = centered ? u16(b, 2) : w,
        ch = centered ? u16(b, 4) : h;
    if (w == 0
        || h == 0
        || cw > 1024
        || ch > 768
        || w > cw
        || h > ch
        || base < 0
        || base >= b.length) return null;
    int[] out = new int[cw * ch];
    int ox = (cw - w) / 2, oy = (ch - h) / 2;
    if (raw) {
      if (base + (long) w * h > b.length) return null;
      for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
          int i = b[base + y * w + x] & 255;
          out[(y + oy) * cw + x + ox] = i == 0 ? 0 : palette[i];
        }
    } else {
      if (base + h * 2 > b.length) return null;
      for (int y = 0; y < h; y++) {
        int p = base + u16(b, base + y * 2), x = 0;
        while (x < w) {
          if (p >= b.length) return null;
          int v = b[p++] & 255, n = (v & 128) != 0 ? v & 127 : (v & 64) != 0 ? v & 63 : v;
          if (n == 0 || x + n > w) return null;
          if ((v & 128) != 0) {
            x += n;
            continue;
          }
          int repeat = -1;
          if ((v & 64) != 0) {
            if (p >= b.length) return null;
            repeat = b[p++] & 255;
          }
          for (int k = 0; k < n; k++, x++) {
            if (repeat < 0 && p >= b.length) return null;
            int i = repeat < 0 ? b[p++] & 255 : repeat;
            out[(y + oy) * cw + x + ox] = palette[i];
          }
        }
      }
    }
    return Bitmap.createBitmap(out, cw, ch, Bitmap.Config.ARGB_8888);
  }

  static final class Font {
    final byte[] data;
    final PCX tint;
    final int[] palette;
    final boolean game, fallback;
    final int low, high, height, spacing;
    final Map<Integer, Bitmap> glyphs = new HashMap<Integer, Bitmap>();
    int fixedColor, shadedColor;

    Font withShadedColor(int color) {
      Font copy = new Font(fallback ? null : data, tint, palette, spacing, height);
      copy.shadedColor = color;
      return copy;
    }

    Font withColor(int color) {
      Font copy = new Font(fallback ? null : data, tint, palette, spacing, height);
      copy.fixedColor = color;
      return copy;
    }

    Font(byte[] bytes, PCX tint, int[] palette, int spacing, int size) {
      fallback = bytes == null;
      if (fallback) {
        bytes = new byte[12];
        System.arraycopy("FONT".getBytes(CP), 0, bytes, 0, 4);
        bytes[6] = (byte) (size * .65);
        bytes[7] = (byte) size;
      }
      if (bytes == null || bytes.length < 8 || !new String(bytes, 0, 4, CP).equals("FONT"))
        throw new IllegalArgumentException("Original font is missing");
      data = bytes;
      low = data[4] & 255;
      high = data[5] & 255;
      height = data[7] & 255;
      if (high < low || height > 64 || 8 + 4 * (high - low + 1) > data.length)
        throw new IllegalArgumentException("Invalid FONT");
      this.tint = tint;
      this.palette = palette;
      this.spacing = spacing;
      game = tint.stride >= 64 && tint.pixels.length >= 192;
    }

    int[] ramp(int c) {
      if (!game) return new int[] {0, c >= 2 && c <= 6 ? c - 2 : 0};
      switch (c) {
        case 3:
          return new int[] {0, 1};
        case 4:
          return new int[] {0, 2};
        case 5:
          return new int[] {0, 3};
        case 6:
          return new int[] {0, 4};
        case 7:
          return new int[] {0, 5};
        case 8:
          return new int[] {1, 0};
        case 11:
          return new int[] {0, 6};
        case 14:
          return new int[] {1, 1};
        case 15:
          return new int[] {1, 2};
        case 16:
          return new int[] {1, 3};
        case 17:
          return new int[] {1, 4};
        case 20:
          return new int[] {0, 7};
        case 21:
          return new int[] {1, 5};
        case 22:
          return new int[] {1, 6};
        case 23:
          return new int[] {1, 7};
        case 24:
          return new int[] {2, 0};
        case 25:
          return new int[] {2, 1};
        case 27:
          return new int[] {2, 2};
        case 28:
          return new int[] {2, 3};
        case 29:
          return new int[] {2, 4};
        case 30:
          return new int[] {2, 5};
        case 31:
          return new int[] {2, 7};
        default:
          return new int[] {0, 0};
      }
    }

    Bitmap glyph(int code, int color) {
      int key = code + color * 256;
      if (glyphs.containsKey(key)) return glyphs.get(key);
      if (fallback) {
        int w = Math.max(1, (int) Math.ceil(height * .65));
        Bitmap bitmap = Bitmap.createBitmap(w, height, Bitmap.Config.ARGB_8888);
        Paint ink = new Paint(Paint.ANTI_ALIAS_FLAG);
        ink.setTextSize(height);
        ink.setTypeface(Typeface.MONOSPACE);
        int[] ramp = ramp(color);
        int tintIndex = ramp[0] * tint.stride + ramp[1] * 8 + 1;
        int originalColor = tintIndex < tint.pixels.length ? palette[tint.pixels[tintIndex] & 255] : 0xffcbd3e8;
        ink.setColor(shadedColor != 0 ? shadedColor : fixedColor != 0 ? fixedColor : originalColor);
        new Canvas(bitmap).drawText(Character.toString((char) code), 0, height - 2, ink);
        glyphs.put(key, bitmap);
        return bitmap;
      }
      if (code < low || code > high) return null;
      int p = u32(data, 8 + (code - low) * 4);
      if (p < 1 || p + 4 > data.length) return null;
      int w = data[p++] & 255, h = data[p++] & 255, ox = data[p++] & 255, oy = data[p++] & 255;
      if (w > 64 || h > 64 || ox + w > 96 || oy + h > height || w == 0) return null;
      int cw = Math.max(1, w + ox + 1), n = 0;
      int[] out = new int[cw * height], r = ramp(color);
      while (n < w * h && p < data.length) {
        int b = data[p++] & 255;
        n += b >> 3;
        if (n >= w * h) break;
        int col = b & 7;
        if (col != 0) {
          int index = tint.pixels[r[0] * tint.stride + r[1] * 8 + col] & 255, rgb = palette[index];
          boolean transparent = index == 0 || (Color.red(rgb) >= 248 && Color.green(rgb) == 0 && Color.blue(rgb) >= 248);
          if (shadedColor != 0 && !transparent) {
            int shade = Math.max(Color.red(rgb), Math.max(Color.green(rgb), Color.blue(rgb)));
            rgb = Color.rgb(Color.red(shadedColor) * shade / 255,
                Color.green(shadedColor) * shade / 255, Color.blue(shadedColor) * shade / 255);
          }
          if (!transparent)
            out[(n / w + oy) * cw + n % w + ox] =
                fixedColor != 0 && (rgb & 0xffffff) != 0 ? fixedColor : rgb;
        }
        n++;
      }
      Bitmap image = Bitmap.createBitmap(out, cw, height, Bitmap.Config.ARGB_8888);
      glyphs.put(key, image);
      return image;
    }

    int advance(int c) {
      if (c == 32) return (data[6] & 255) / 2;
      if (c == 9) return (data[6] & 255) * 2;
      if (c < 32) return 0;
      Bitmap b = glyph(c, 2);
      return b == null ? 0 : b.getWidth() - 1 + spacing;
    }

    int measure(String s) {
      int w = 0;
      for (int i = 0; i < s.length(); i++) w += advance(s.charAt(i));
      return w;
    }

    List<String> lines(String s, int width) {
      ArrayList<String> lines = new ArrayList<String>();
      StringBuilder line = new StringBuilder();
      int x = 0;
      for (String token : s.replace("\r", "").split("(?<=\\n)|(?=\\n)|(?<= )")) {
        if (token.equals("\n")) {
          lines.add(line.toString());
          line.setLength(0);
          x = 0;
          continue;
        }
        int w = measure(token);
        if (width > 0 && x > 0 && x + w > width) {
          lines.add(line.toString().replaceAll(" +$", ""));
          line.setLength(0);
          x = 0;
        }
        // A long name or untranslated token still has to stay within its box.
        if(width>0&&w>width){for(int i=0;i<token.length();i++){char ch=token.charAt(i);int a=advance(ch);if(x>0&&x+a>width){lines.add(line.toString());line.setLength(0);x=0;}line.append(ch);x+=a;}}
        else {line.append(token);x+=w;}
      }
      lines.add(line.toString().replaceAll(" +$", ""));
      return lines;
    }

    float draw(
        Canvas c,
        String s,
        float left,
        float top,
        int width,
        int align,
        int color,
        int lineHeight) {
      int current = color;
      boolean hidden = false;
      for (String line : lines(s, width)) {
        int a = line.indexOf('\u0013') >= 0 ? 1 : line.indexOf('\u0012') >= 0 ? 2 : align;
        float x =
            left + (a == 1 ? (width - measure(line)) / 2f : a == 2 ? width - measure(line) : 0);
        for (int i = 0; i < line.length(); i++) {
          int code = line.charAt(i);
          if (code < 32) {
            if (code == 1) {
              current = color;
              hidden = false;
            } else if (code == 9) x += advance(code);
            else if (code == 12) hidden = true;
            else if (code != 18 && code != 19) {
              current = code;
              hidden = false;
            }
            continue;
          }
          Bitmap b = glyph(code, current);
          if (b != null && !hidden) c.drawBitmap(b, x, top, PIXELS);
          x += advance(code);
        }
        top += lineHeight > 0 ? Math.max(lineHeight,height+1) : height;
      }
      return top;
    }
  }

  static final class Widget {
    int id, type, x, y, w, h, flags, smk, tx, ty, rx, ry, rx2, ry2, rw, rh;
    String text;

    RectF rect() {
      return new RectF(x, y, x + w, y + h);
    }

    RectF hit() {
      return (flags & 16) != 0 && rx2 > rx && ry2 > ry
          ? new RectF(x + rx, y + ry, x + rx2 + 1, y + ry2 + 1)
          : rect();
    }
  }

  static final class Anim {
    String name;
    int flags, x, y;
  }

  static final class Dialog {
    final byte[] b;
    final List<Widget> widgets = new ArrayList<Widget>();

    Dialog(byte[] b) {
      if (b == null || b.length < 86) throw new IllegalArgumentException("Missing original dialog");
      this.b = b;
      Set<Integer> seen = new HashSet<Integer>();
      int p = u32(b, 66);
      while (p > 0) {
        if (p + 86 > b.length || !seen.add(p) || seen.size() > 512)
          throw new IllegalArgumentException("Invalid dialog chain");
        Widget w = new Widget();
        w.x = u16(b, p + 4);
        w.y = u16(b, p + 6);
        w.w = u16(b, p + 12);
        w.h = u16(b, p + 14);
        w.text = str(b, u32(b, p + 20));
        w.flags = u32(b, p + 24);
        w.id = u16(b, p + 32);
        w.type = u32(b, p + 34);
        w.smk = u32(b, p + 66);
        w.tx = u16(b, p + 70);
        w.ty = u16(b, p + 72);
        w.rx = u16(b, p + 54);
        w.ry = u16(b, p + 56);
        w.rx2 = u16(b, p + 58);
        w.ry2 = u16(b, p + 60);
        w.rw = u16(b, p + 74);
        w.rh = u16(b, p + 76);
        widgets.add(w);
        p = u32(b, p);
      }
    }

    Widget get(int id) {
      for (Widget w : widgets) if (w.id == id) return w;
      return null;
    }

    List<Anim> animations(Widget w) {
      ArrayList<Anim> list = new ArrayList<Anim>();
      Set<Integer> seen = new HashSet<Integer>();
      int p = w.smk;
      while (p > 0) {
        if (p + 30 > b.length || !seen.add(p)) break;
        Anim a = new Anim();
        a.name = normal(str(b, u32(b, p + 10)));
        a.flags = u16(b, p + 4);
        a.x = (short) u16(b, p + 18);
        a.y = (short) u16(b, p + 20);
        list.add(a);
        p = u32(b, p);
      }
      Collections.reverse(list);
      return list;
    }
  }

  static final class Movie implements AutoCloseable {
    final int id, frames, interval;
    final Bitmap bitmap;
    int frame = -1;

    Movie(byte[] data) {
      this(data, false);
    }

    Movie(byte[] data, boolean audio) {
      this(NativeBridge.movieOpen(data, audio));
    }

    Movie(int slot, String path) {this(NativeBridge.movieOpenAsset(slot, path, true));}

    private Movie(int[] m) {
      id = m[0];
      frames = m[3];
      interval = Math.max(1, m[4]);
      bitmap = Bitmap.createBitmap(m[1], m[2], Bitmap.Config.ARGB_8888);
    }

    void draw(
        Canvas c,
        float x,
        float y,
        float width,
        float height,
        double time,
        boolean loop,
        Paint paint) {
      int f = (int) (Math.max(0, time) / interval);
      f = loop ? f % frames : Math.min(f, frames - 1);
      if (f != frame) {
        NativeBridge.movieFrame(id, time, loop, bitmap);
        frame = f;
      }
      c.drawBitmap(bitmap, null, new RectF(x, y, x + width, y + height), paint);
    }

    public void close() {
      NativeBridge.movieClose(id);
    }
  }

  final Map<String, byte[]> bytes = new HashMap<String, byte[]>();
  final Map<String, PCX> images = new HashMap<String, PCX>();
  final Map<String, byte[]> fonts = new HashMap<String, byte[]>();

  byte[] read(String name) {
    String n = normal(name);
    if (bytes.containsKey(n)) return bytes.get(n);
    byte[] b = NativeBridge.asset(-1, n);
    if (b != null && b.length < 1024 * 1024) bytes.put(n, b);
    return b;
  }

  PCX pcx(String name, boolean alpha, int glass) {
    String k = name + ":" + alpha + ":" + glass;
    if (images.containsKey(k)) return images.get(k);
    PCX p = new PCX(read(name), alpha, glass);
    images.put(k, p);
    return p;
  }

  Font font(String size, PCX tint, int[] pal, int spacing) {
    int height = Integer.parseInt(size.replace("x", ""));
    byte[] b = fonts.get(size);
    if (b != null) return new Font(b, tint, pal, spacing, height);
    for (String prefix : new String[] {"files/font/", "font/"}) {
      try {
        b = read(prefix + "font" + size + ".fnt");
        if (b == null || b.length < 8 || !new String(b, 0, 4, CP).equals("FONT")) continue;
        Font font = new Font(b, tint, pal, spacing, height);
        fonts.put(size, b);
        return font;
      } catch (RuntimeException unavailableFont) {
        // Installed archives may contain unreadable font payloads. Try the
        // next original source, then use the readable UI fallback.
      }
    }
    return new Font(null, tint, pal, spacing, height);
  }

  void clearImages() {
    images.clear();
    bytes.clear();
  }
}

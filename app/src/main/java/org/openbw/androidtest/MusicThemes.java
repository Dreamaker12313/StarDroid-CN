package org.openbw.androidtest;

/** Finds an original race theme appended to a Brood War WAV, without guessing timings. */
final class MusicThemes {
  private MusicThemes() {}

  static int appendedThemeMs(byte[] combined, byte[] original) {
    Pcm a = Pcm.read(combined), b = Pcm.read(original);
    if (a == null || b == null || a.rate != b.rate || a.channels != b.channels
        || a.bits != b.bits || b.frames < 30L * b.rate) return 0;
    int offset = a.frames - b.frames;
    if (offset < 30L * a.rate) return 0;
    // Duration alone is insufficient: variants may contain unrelated music.
    // Compare three separated passages, tolerating MPQ's lossy sound compression.
    int window = 12 * b.rate;
    for (int start : new int[] {3 * b.rate, (b.frames - window) / 2,
        b.frames - window - 3 * b.rate}) {
      if (!matches(a, offset + start, b, start)) return 0;
    }
    return (int) ((1000L * offset + a.rate - 1) / a.rate);
  }

  private static boolean matches(Pcm a, int offsetA, Pcm b, int offsetB) {
    final int count = 120, width = b.rate / 10;
    double sa = 0, sb = 0, aa = 0, bb = 0, ab = 0;
    for (int i = 0; i < count; i++) {
      double x = a.energy(offsetA + i * width, width), y = b.energy(offsetB + i * width, width);
      sa += x; sb += y; aa += x * x; bb += y * y; ab += x * y;
    }
    double va = aa - sa * sa / count, vb = bb - sb * sb / count;
    return va > 1 && vb > 1 && sa > sb * .8 && sa < sb * 1.2
        && (ab - sa * sb / count) / Math.sqrt(va * vb) > .995;
  }

  private static final class Pcm {
    byte[] data;
    int start, frames, channels, bits, rate, stride;

    static Pcm read(byte[] data) {
      if (data == null || data.length < 44 || u32(data, 0) != 0x46464952L
          || u32(data, 8) != 0x45564157L || u32(data, 4) + 8 > data.length) return null;
      Pcm p = new Pcm(); p.data = data;
      int format = 0, bytes = 0;
      for (int i = 12; i <= data.length - 8;) {
        long length = u32(data, i + 4);
        if (length > data.length - i - 8) return null;
        int n = (int) length;
        if (u32(data, i) == 0x20746d66L && n >= 16) {
          format = u16(data, i + 8); p.channels = u16(data, i + 10);
          long rate = u32(data, i + 12);
          if (rate < 4000 || rate > 192000) return null;
          p.rate = (int) rate; p.stride = u16(data, i + 20); p.bits = u16(data, i + 22);
        } else if (u32(data, i) == 0x61746164L) { p.start = i + 8; bytes = n; }
        long next = (long) i + 8 + n + (n & 1);
        if (next > data.length) break;
        i = (int) next;
      }
      if (format != 1 || p.channels < 1 || p.channels > 2 || (p.bits != 8 && p.bits != 16)
          || p.stride != p.channels * p.bits / 8 || p.rate == 0 || bytes == 0
          || bytes % p.stride != 0) return null;
      p.frames = bytes / p.stride;
      return p;
    }

    double energy(int frame, int count) {
      double sum = 0;
      for (int i = start + frame * stride, end = i + count * stride; i < end; i += bits / 8) {
        int value = bits == 8 ? ((data[i] & 255) - 128) * 256 : (short) u16(data, i);
        sum += (double) value * value;
      }
      return Math.sqrt(sum / (count * channels));
    }
  }

  private static int u16(byte[] b, int i) { return (b[i] & 255) | (b[i + 1] & 255) << 8; }
  private static long u32(byte[] b, int i) { return u16(b, i) | (long) u16(b, i + 2) << 16; }
}

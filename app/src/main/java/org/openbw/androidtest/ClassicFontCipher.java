package org.openbw.androidtest;

import java.util.Arrays;

/** Reads the classic installer's encrypted FONT envelope. Installation metadata
 * and derived keys stay in memory; callers must never include them in reports. */
final class ClassicFontCipher {
  private static final int LIMIT = 1024 * 1024;
  private static final int[] INITIAL = {
      0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0
  };

  static boolean isPlain(byte[] data) {
    return data != null && data.length >= 8 && data[0] == 'F' && data[1] == 'O'
        && data[2] == 'N' && data[3] == 'T';
  }

  static boolean isWrapped(byte[] data) {
    if (data == null || data.length < 72 || data.length > LIMIT || (data.length - 8) % 64 != 0)
      return false;
    int tail = data[data.length - 3] & 255;
    return data[data.length - 4] == 0 && tail <= 64 && data.length - 72 + tail > 0;
  }

  static byte[] decodeFont(byte[] data, byte[] installedMetadata) {
    if (isPlain(data)) return data;
    if (!isWrapped(data)) throw new IllegalArgumentException("Unsupported font data; file exists but is not a readable FONT");
    if (!isWrapped(installedMetadata) || installedMetadata.length > 4096)
      throw new IllegalArgumentException("Encrypted font: installation metadata unavailable");
    byte[] fixed = metadataPassword(), identity = null, password = null;
    try {
      identity = unwrap(installedMetadata, fixed, false);
      int end = 0;
      while (end < identity.length && identity[end] != 0) {
        int c = identity[end] & 255;
        if (c < 32 || c > 126 || end >= 63)
          throw new IllegalArgumentException("Encrypted font: invalid installation metadata");
        end++;
      }
      if (end == 0 || end == identity.length)
        throw new IllegalArgumentException("Encrypted font: invalid installation metadata");
      password = Arrays.copyOf(identity, end);
      return unwrap(data, password, true);
    } finally {
      Arrays.fill(fixed, (byte) 0);
      if (identity != null) Arrays.fill(identity, (byte) 0);
      if (password != null) Arrays.fill(password, (byte) 0);
    }
  }

  private static byte[] metadataPassword() {
    byte[] result = new byte[19];
    int state = 0x150b, count = 0;
    while (count < result.length) {
      state = state * 214013 + 2531011;
      byte next = (byte) (state >>> 16);
      if (next != 0) result[count++] = next;
    }
    return result;
  }

  private static byte[] unwrap(byte[] encoded, byte[] password, boolean requireFont) {
    byte[] seed = new byte[112], repeated = new byte[64], clear = new byte[encoded.length - 8];
    int[] keys = null, inverses = null, state = null, digest = null;
    try {
      for (int i = 0; i < repeated.length; i++) repeated[i] = password[i % password.length];
      digest = INITIAL.clone(); compress(digest, repeated, 0);
      int random = 0x4fa7;
      for (int i = 0; i < seed.length; i++) {
        random = random * 214013 + 2531011;
        seed[i] = (byte) ((random >>> 16) ^ (digest[i % 20 / 4] >>> (i % 4 * 8)));
      }
      keys = expand(seed);
      inverses = new int[52];
      for (int i = 0; i < 52; i += 6) {
        inverses[i] = inverse(keys[i]);
        inverses[i + 3] = inverse(keys[i + 3]);
      }
      state = INITIAL.clone(); compress(state, seed, 48);
      for (int offset = 0; offset < clear.length; offset += 64) {
        if (offset % 512 == 0) {
          for (int block = offset; block < offset + 64; block += 8)
            decryptBlock(encoded, block, clear, block, keys, inverses);
        } else System.arraycopy(encoded, offset, clear, offset, 64);
        for (int i = 0; i < 64; i++) {
          int at = (63 - i) % 20;
          clear[offset + i] -= (byte) (state[at / 4] >>> (at % 4 * 8));
        }
        if (requireFont && offset == 0 && !isPlain(clear))
          throw new IllegalArgumentException("Encrypted font: cannot decode with installed metadata");
        if (offset % 1024 == 0) compress(state, clear, offset);
      }
      if (word(encoded, clear.length) != state[0])
        throw new IllegalArgumentException("Encrypted font: checksum mismatch");
      int length = clear.length - 64 + (encoded[encoded.length - 3] & 255);
      return Arrays.copyOf(clear, length);
    } finally {
      Arrays.fill(seed, (byte) 0); Arrays.fill(repeated, (byte) 0); Arrays.fill(clear, (byte) 0);
      if (keys != null) Arrays.fill(keys, 0);
      if (inverses != null) Arrays.fill(inverses, 0);
      if (state != null) Arrays.fill(state, 0);
      if (digest != null) Arrays.fill(digest, 0);
    }
  }

  private static int word(byte[] data, int offset) {
    return (data[offset] & 255) | (data[offset + 1] & 255) << 8
        | (data[offset + 2] & 255) << 16 | (data[offset + 3] & 255) << 24;
  }

  // This legacy digest deliberately uses arithmetic shifts and SHA-0's
  // message schedule. Replacing it with standard SHA-1 would break decoding.
  private static int rotate(int n, int bits) { return n << bits | n >> (32 - bits); }

  private static void compress(int[] state, byte[] input, int offset) {
    int[] schedule = new int[80];
    for (int i = 0; i < 16; i++) schedule[i] = word(input, offset + i * 4);
    for (int i = 16; i < 80; i++)
      schedule[i] = schedule[i - 3] ^ schedule[i - 8] ^ schedule[i - 14] ^ schedule[i - 16];
    int a = state[0], b = state[1], c = state[2], d = state[3], e = state[4];
    for (int i = 0; i < 80; i++) {
      int mix, constant;
      if (i < 20) { mix = (b & c) | (~b & d); constant = 0x5a827999; }
      else if (i < 40) { mix = b ^ c ^ d; constant = 0x6ed9eba1; }
      else if (i < 60) { mix = (b & c) | (b & d) | (c & d); constant = 0x8f1bbcdc; }
      else { mix = b ^ c ^ d; constant = 0xca62c1d6; }
      int next = rotate(a, 5) + mix + e + constant + schedule[i];
      e = d; d = c; c = rotate(b, 30); b = a; a = next;
    }
    state[0] += a; state[1] += b; state[2] += c; state[3] += d; state[4] += e;
    Arrays.fill(schedule, 0);
  }

  private static int[] expand(byte[] seed) {
    int[] keys = new int[52];
    for (int i = 0; i < 8; i++) keys[i] = (seed[i * 2] & 255) | (seed[i * 2 + 1] & 255) << 8;
    for (int i = 8; i < 52; i++) {
      int lane = i % 8;
      int left = lane < 6 ? i - 7 : lane == 6 ? i - 7 : i - 15;
      int right = lane < 6 ? i - 6 : lane == 6 ? i - 14 : i - 14;
      keys[i] = (keys[left] << 9 | keys[right] >>> 7) & 65535;
    }
    return keys;
  }

  private static int multiply(int a, int b) {
    return (int) (((a == 0 ? 65536L : a) * (b == 0 ? 65536L : b)) % 65537) & 65535;
  }

  private static int inverse(int value) {
    long result = 1, base = value == 0 ? 65536 : value;
    for (int exponent = 65535; exponent != 0; exponent >>>= 1) {
      if ((exponent & 1) != 0) result = result * base % 65537;
      base = base * base % 65537;
    }
    return (int) result & 65535;
  }

  // Undo the output transform, then undo the IDEA rounds in reverse order.
  private static void decryptBlock(byte[] input, int offset, byte[] out, int target,
                                   int[] keys, int[] inverses) {
    int a = multiply(word(input, offset) & 65535, inverses[48]);
    int b = ((word(input, offset + 4) & 65535) - keys[50]) & 65535;
    int c = ((word(input, offset) >>> 16) - keys[49]) & 65535;
    int d = multiply(word(input, offset + 4) >>> 16, inverses[51]);
    for (int at = 42; at >= 0; at -= 6) {
      int first = multiply(a ^ b, keys[at + 4]);
      int second = multiply(((c ^ d) + first) & 65535, keys[at + 5]);
      int sum = (first + second) & 65535;
      int nextB = ((c ^ sum) - keys[at + 1]) & 65535;
      int nextC = ((b ^ second) - keys[at + 2]) & 65535;
      a = multiply(a ^ second, inverses[at]);
      d = multiply(d ^ sum, inverses[at + 3]);
      b = nextB; c = nextC;
    }
    out[target] = (byte) a; out[target + 1] = (byte) (a >>> 8);
    out[target + 2] = (byte) b; out[target + 3] = (byte) (b >>> 8);
    out[target + 4] = (byte) c; out[target + 5] = (byte) (c >>> 8);
    out[target + 6] = (byte) d; out[target + 7] = (byte) (d >>> 8);
  }
}

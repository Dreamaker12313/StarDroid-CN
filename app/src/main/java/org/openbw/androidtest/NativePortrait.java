package org.openbw.androidtest;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Bitmap;
import java.util.Random;

/** Original idle weights, talking variants and communication-monitor shading. */
final class NativePortrait implements AutoCloseable {
  private final NativeArt art;
  private final byte[] data;
  private final String[] names;
  private final Random random = new Random();
  private final Paint paint = new Paint();
  private NativeArt.Movie movie;
  private int type = -1, variant = -1;
  private boolean talking;
  private double elapsed, lastTime = -1;
  private int selection = -1;
  private double staticStart = -1;
  private boolean newSelection;
  private final Bitmap staticBitmap = Bitmap.createBitmap(60, 56, Bitmap.Config.ARGB_8888);
  private final int[] staticPixels = new int[60 * 56];

  void selection(int identity) {
    if (identity == selection) return;
    selection = identity;
    newSelection = identity != -1;
    staticStart = -1;
  }

  NativePortrait(NativeArt art, byte[] data, String[] names) {
    this.art = art;
    this.data = data;
    this.names = names;
  }

  void target(int type, boolean talking) {
    if (type == this.type && talking == this.talking) return;
    this.type = type;
    this.talking = talking;
    variant = -1;
    elapsed = 0;
    lastTime = -1;
    next();
  }

  static int weightedVariant(byte[] data, int count, int id, double roll) {
    int total = 0;
    for (int i = 0; i < 4; i++) total += data[(8 + i) * count + id] & 255;
    double remaining = roll * total;
    for (int i = 0; i < 4; i++) {
      remaining -= data[(8 + i) * count + id] & 255;
      if (remaining < 0) return i;
    }
    return 0;
  }

  private byte[] bytes(int id, int choice, boolean talk) {
    int count = data.length / 12;
    int index = NativeArt.u32(data, (talk ? count * 4 : 0) + id * 4) - 1;
    if (index < 0 || index >= names.length) return null;
    for (int i = choice; i >= 0; i--) {
      byte[] b = art.read("portrait/" + names[index] + i + ".smk");
      if (b != null) return b;
    }
    return talk ? bytes(id, choice, false) : null;
  }

  private void next() {
    if (movie != null) movie.close();
    movie = null;
    if (type < 0 || data == null) return;
    int count = data.length / 12, id = NativeBridge.value(11, type);
    if (id < 0 || id >= count) return;
    int choice = 0;
    if (variant >= 0) {
      if (talking) {
        choice = random.nextInt(2);
        if (choice >= variant) choice++;
      } else choice = weightedVariant(data, count, id, random.nextDouble());
    }
    byte[] b = bytes(id, choice, talking);
    if (b == null) return;
    try {
      movie = new NativeArt.Movie(b);
      variant = choice;
      elapsed = 0;
    } catch (RuntimeException e) {
      android.util.Log.w("StarDroid", "Portrait decode", e);
    }
  }

  void draw(Canvas c, float x, float y, float width, float height, double now,
      boolean paused, boolean communicationMonitor) {
    if (lastTime >= 0 && !paused) elapsed += Math.max(0, Math.min(100, now - lastTime));
    lastTime = now;
    if (movie != null && elapsed >= movie.frames * (double) movie.interval) next();
    // Black in a portrait is opaque; index-zero transparency belongs to menu overlays.
    paint.setColor(Color.BLACK);
    paint.setAlpha(255);
    c.drawRect(x, y, x + width, y + height, paint);
    if (movie == null) return;
    movie.draw(c, x, y, width, height, elapsed, false, NativeArt.PIXELS);
    if (newSelection) {staticStart = now; newSelection = false;}
    // The monitor's brief tuning noise is per selected unit, not per unit type.
    if (!communicationMonitor && staticStart >= 0 && now - staticStart < 180) {
      int seed = selection ^ (int)(now / 32) * 1103515245;
      int alpha = (int)(220 * (1 - (now - staticStart) / 180));
      for (int i = 0; i < staticPixels.length; i++) {
        seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5;
        int value = (seed & 3) == 0 ? 255 : (seed & 15) * 8;
        staticPixels[i] = (alpha << 24) | (value << 16) | (value << 8) | value;
      }
      staticBitmap.setPixels(staticPixels, 0, 60, 0, 0, 60, 56);
      c.drawBitmap(staticBitmap, null, new android.graphics.RectF(x, y, x + width, y + height), NativeArt.PIXELS);
    }
    if (communicationMonitor) {
      if (!talking) {
        paint.setAlpha(97);
        c.drawRect(x, y, x + width, y + height, paint);
      }
      paint.setAlpha(143);
      for (float line = 1; line < height; line += 2)
        c.drawRect(x, y + line, x + width, y + line + 1, paint);
    }
  }

  public void close() {
    if (movie != null) movie.close();
    movie = null;
  }
}

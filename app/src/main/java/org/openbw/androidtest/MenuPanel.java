package org.openbw.androidtest;

import java.util.ArrayDeque;

/** Remove only the edge-connected backdrop baked into a sliding button panel. */
final class MenuPanel {
  static int[] foreground(int[] panel, int width, int height, int[] background,
      int backgroundWidth, int backgroundHeight, int left, int top) {
    int[] result = panel.clone();
    boolean[] visited = new boolean[result.length];
    ArrayDeque<Integer> pending = new ArrayDeque<Integer>();
    for (int x = 0; x < width; x++) {pending.add(x); pending.add((height - 1) * width + x);}
    for (int y = 1; y < height - 1; y++) {pending.add(y * width); pending.add(y * width + width - 1);}
    while (!pending.isEmpty()) {
      int i = pending.removeFirst();
      if (visited[i]) continue;
      visited[i] = true;
      int x = i % width, y = i / width, bx = left + x, by = top + y;
      boolean clear = (panel[i] >>> 24) == 0;
      // Translucent panel pixels can still contain exactly the same baked
      // backdrop. Comparing alpha prevented those edge fragments being removed.
      boolean matches = bx >= 0 && by >= 0 && bx < backgroundWidth && by < backgroundHeight
          && (panel[i] & 0xffffff) == (background[by * backgroundWidth + bx] & 0xffffff);
      if (!clear && !matches) continue;
      result[i] = 0;
      if (x > 0) pending.add(i - 1);
      if (x + 1 < width) pending.add(i + 1);
      if (y > 0) pending.add(i - width);
      if (y + 1 < height) pending.add(i + width);
    }
    return result;
  }
}

package org.openbw.androidtest;

public final class CameraPanTest {
  static int checks;
  static void check(boolean ok, String why) { checks++; if (!ok) throw new AssertionError(why); }
  static int[] travel(int fps, double x, double y, double zoom, double speed) {
    CameraPan pan = new CameraPan(); int sx = 0, sy = 0;
    for (int i = 0; i < fps * 2; i++) {
      pan.edge(1000. / fps, x, y, 640, 376, zoom, speed);
      check((x != 0 || pan.dx <= 0) && (x != 640 || pan.dx >= 0), "Horizontal direction reversed");
      check((y != 0 || pan.dy <= 0) && (y != 376 || pan.dy >= 0), "Vertical direction reversed");
      sx += pan.dx; sy += pan.dy;
    }
    return new int[]{sx, sy};
  }
  public static void main(String[] args) {
    for (double distance : new double[]{28, 36, 47}) {
      int[] left = travel(60, distance, 180, 1, 1);
      int[] right = travel(60, 640 - distance, 180, 1, 1);
      int[] up = travel(60, 320, distance, 1, 1);
      int[] down = travel(60, 320, 376 - distance, 1, 1);
      check(left[0] < 0 && right[0] > 0 && up[1] < 0, "Top/side scrolling did not start in the wider band");
      check(-left[0] == right[0] && left[0] == up[1], "New edge bands have unequal strength");
      check(down[1] == 0, "Bottom scrolling threshold changed");
    }
    check(travel(60, 48, 180, 1, 1)[0] == 0 && travel(60, 592, 180, 1, 1)[0] == 0
        && travel(60, 320, 48, 1, 1)[1] == 0, "Scrolling starts outside the 48-pixel band");
    for (double zoom : new double[]{.5, 1, 1.4, 3}) for (double speed : new double[]{.5, 1, 2.5}) {
      int[] reference = travel(60, 640, 180, zoom, speed);
      for (int fps : new int[]{30, 60, 90, 120, 144}) {
        int[] right = travel(fps, 640, 180, zoom, speed), left = travel(fps, 0, 180, zoom, speed);
        int[] down = travel(fps, 320, 376, zoom, speed), up = travel(fps, 320, 0, zoom, speed);
        check(Math.abs(right[0] - reference[0]) <= 1, "Scrolling speed depends on display rate");
        check(right[0] == -left[0] && down[1] == -up[1] && right[0] == down[1], "Directions have unequal speed");
        check(right[1] == 0 && left[1] == 0 && down[0] == 0 && up[0] == 0, "Unwanted perpendicular drift");
        for (int corner = 0; corner < 4; corner++) {
          int[] diagonal = travel(fps, (corner & 1) == 0 ? 0 : 640, (corner & 2) == 0 ? 0 : 376, zoom, speed);
          check(Math.abs(diagonal[0]) == Math.abs(diagonal[1]), "Diagonal axes differ");
          check(Math.abs(Math.hypot(diagonal[0], diagonal[1]) - right[0]) < 2, "Diagonals scroll faster");
        }
      }
    }
    CameraPan pan = new CameraPan(); int steady = 0, total = 0;
    for (int i = 0; i < 120; i++) {
      pan.edge(1000. / 120, -40, 180, 640, 376, 1, 1);
      check(pan.dx <= 0, "Leaving the left screen edge stops/reverses scrolling");
      if (i > 60) { check(pan.dx >= -5 && pan.dx <= -3, "High-refresh motion jumps or stalls"); steady++; }
      total += pan.dx;
    }
    check(total < -400 && steady > 50, "Held edge does not keep scrolling without touch MOVE events");
    pan.edge(1000. / 120, 700, 180, 640, 376, 1, 1);
    check(pan.dx >= 0, "Direction reversal keeps moving the old way");
    pan.edge(16, 320, 180, 640, 376, 1, 1);
    check(pan.dx == 0 && pan.dy == 0, "Moving away from edge coasts");
    pan.edge(16, 320, 470, 640, 354, 1, 1);
    pan.edge(16, 320, 470, 640, 354, 1, 1);
    check(pan.dy > 0, "Holding below command bar does not scroll down");
    pan.stopEdge(); check(pan.dx == 0 && pan.dy == 0, "Stop retained movement");
    pan.edge(5000, 640, 180, 640, 376, 1, 1);
    check(pan.dx <= 24, "Long frame creates a large catch-up jump");
    pan.reset(); pan.edge(Double.NaN, 640, 180, 640, 376, 1, 1);
    check(pan.dx == 0 && pan.dy == 0, "Invalid clock creates movement");
    for (double sign : new double[]{-1, 1}) {
      pan.reset(); int x = 0, y = 0;
      for (int i = 0; i < 1000; i++) { pan.drag(sign * .125, sign * .375); x += pan.dx; y += pan.dy; }
      check(x == sign * 125 && y == sign * 375, "Small drag movements lost or rounded asymmetrically");
      pan.reset(); pan.drag(0, 0); check(pan.dx == 0 && pan.dy == 0, "New gesture retained old fractional movement");
    }
    int[] baseline = travel(60, 640, 180, 1, 1);
    pan.reset(); int irregular = 0; double time = 0;
    double[] intervals = {8, 9, 12, 22, 33, 16};
    for (int i = 0; time < 2000; i++) {
      double dt = Math.min(intervals[i % intervals.length], 2000 - time); time += dt;
      pan.edge(dt, 640, 180, 640, 376, 1, 1); irregular += pan.dx;
    }
    check(Math.abs(irregular - baseline[0]) <= 1, "Uneven frame intervals alter scroll distance");
    System.out.println("PASS " + checks + " camera checks: all directions, 30–144 Hz, zoom/speed, subpixel pans, stop/reverse, stalls");
  }
}

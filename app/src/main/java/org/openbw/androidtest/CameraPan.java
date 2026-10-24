package org.openbw.androidtest;

/** Time-based edge scrolling and symmetric subpixel accumulation for touch pans. */
final class CameraPan {
  private static final double EARLY_EDGE = 48, BOTTOM_EDGE = 24, SPEED = 480, RAMP_SECONDS = .06;
  private double edgeX, edgeY, dragX, dragY, velocityX, velocityY;
  int dx, dy;

  void reset() { stopEdge(); dragX = dragY = 0; }

  void stopEdge() {
    edgeX = edgeY = velocityX = velocityY = 0;
    dx = dy = 0;
  }

  void drag(double x, double y) {
    dragX += x; dragY += y;
    dx = (int) dragX; dy = (int) dragY;
    dragX -= dx; dragY -= dy;
  }

  void edge(double milliseconds, double x, double y, double width, double bottom,
      double zoom, double speed) {
    dx = dy = 0;
    if (!Double.isFinite(milliseconds) || milliseconds <= 0 || zoom <= 0) return;
    // Do not turn a delayed frame or resume into a large camera jump.
    double seconds = Math.min(50, milliseconds) / 1000;
    double sx = direction(x, width, EARLY_EDGE, EARLY_EDGE);
    double sy = direction(y, bottom, EARLY_EDGE, BOTTOM_EDGE);
    double length = Math.hypot(sx, sy);
    if (length > 1) { sx /= length; sy /= length; }
    double targetX = sx * SPEED * speed / zoom, targetY = sy * SPEED * speed / zoom;
    // Leaving an edge or reversing direction must stop that axis immediately.
    if (targetX == 0 || velocityX * targetX < 0) edgeX = velocityX = 0;
    if (targetY == 0 || velocityY * targetY < 0) edgeY = velocityY = 0;
    double decay = Math.exp(-seconds / RAMP_SECONDS);
    edgeX += targetX * seconds + (velocityX - targetX) * RAMP_SECONDS * (1 - decay);
    edgeY += targetY * seconds + (velocityY - targetY) * RAMP_SECONDS * (1 - decay);
    velocityX = targetX + (velocityX - targetX) * decay;
    velocityY = targetY + (velocityY - targetY) * decay;
    dx = (int) edgeX; dy = (int) edgeY;
    edgeX -= dx; edgeY -= dy;
  }

  private static double direction(double position, double end, double near, double far) {
    if (position < near) return -Math.min(1, (near - position) / near);
    if (position > end - far) return Math.min(1, (position - end + far) / far);
    return 0;
  }
}

package org.openbw.androidtest;

/** Shared text and value conversion for the original-artwork controller sheets. */
final class GamepadSettings {
  static final String POINTER_GUIDE = "Left stick moves the pointer; right stick moves the camera. Hold Select / click and move the pointer to drag a selection. Touch controls remain available.";
  static final String MENU_GUIDE = "Press the assigned Game menu button to open or close a menu. Use Cancel / back to return to the previous screen. Hold Precision pointer for slower aiming.";

  static int sliderPercent(float fraction, int min, int max) {
    if (Float.isNaN(fraction)) fraction = 0;
    return min + Math.round(Math.max(0, Math.min(1, fraction)) * (max - min));
  }

  private GamepadSettings() {}
}

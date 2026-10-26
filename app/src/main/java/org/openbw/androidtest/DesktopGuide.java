package org.openbw.androidtest;

/** Help kept together on the mouse and keyboard settings sheet. */
final class DesktopGuide {
  static final String MOUSE_GUIDE =
      "Left click selects; drag a selection box.\n"
      + "Right click orders. Shift adds or queues.\n"
      + "Double-click or Ctrl-click selects the same type.\n"
      + "Screen edges or middle-drag move the camera.\n"
      + "Wheel zooms or scrolls lists.";

  static final String KEYBOARD_GUIDE =
      "Arrow keys move the camera.\n"
      + "Original uses command letters; Grid uses QWE / ASD / ZXC.\n"
      + "Ctrl+0-9 assigns; Shift+0-9 adds; 0-9 recalls.\n"
      + "Press a group number twice to center the camera.\n"
      + "Space: latest alert. Tab: terrain. Enter: chat.\n"
      + "Escape cancels or goes back. F10 opens the game menu.";

  private DesktopGuide() {}
}

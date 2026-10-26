package org.openbw.androidtest;

import android.view.InputDevice;
import android.view.KeyEvent;
import android.view.MotionEvent;
import java.util.Arrays;

/** Host policy tests; the runner also compiles the production helper against Android SDK 35. */
public final class DesktopControls11Test {
  private static int checks;
  private static void eq(Object actual, Object expected, String reason) {
    ++checks;
    if (!actual.equals(expected)) throw new AssertionError(reason + ": " + actual + " != " + expected);
  }
  private static KeyEvent event(int key, int source, InputDevice device) {
    return new KeyEvent(key, source, device);
  }
  private static void sourcePolicy() {
    int mouse = InputDevice.SOURCE_MOUSE, keyboard = InputDevice.SOURCE_KEYBOARD;
    InputDevice typing = new InputDevice(keyboard, InputDevice.KEYBOARD_TYPE_ALPHABETIC);
    InputDevice controller = new InputDevice(InputDevice.SOURCE_GAMEPAD | keyboard,
        InputDevice.KEYBOARD_TYPE_NON_ALPHABETIC);
    InputDevice combo = new InputDevice(mouse | keyboard, InputDevice.KEYBOARD_TYPE_ALPHABETIC);
    InputDevice pointing = new InputDevice(mouse, InputDevice.KEYBOARD_TYPE_NONE);
    eq(DesktopControls.mouseSource(mouse), true, "mouse source");
    for (int source : new int[]{InputDevice.SOURCE_STYLUS, InputDevice.SOURCE_TOUCHSCREEN,
        InputDevice.SOURCE_JOYSTICK, InputDevice.SOURCE_GAMEPAD, InputDevice.SOURCE_UNKNOWN})
      eq(DesktopControls.mouseSource(source), false, "other pointer is not a mouse");
    eq(DesktopControls.keyboard(event(KeyEvent.KEYCODE_A, keyboard, typing)), true, "physical keyboard");
    eq(DesktopControls.keyboard(event(KeyEvent.KEYCODE_A, InputDevice.SOURCE_UNKNOWN, typing)), true,
        "keyboard device fallback");
    eq(DesktopControls.keyboard(event(KeyEvent.KEYCODE_DPAD_UP, keyboard, typing)), true,
        "keyboard arrows reach desktop camera");
    eq(DesktopControls.keyboard(event(KeyEvent.KEYCODE_DPAD_UP, keyboard, controller)), false,
        "controller D-pad stays with gamepad controls even when source says keyboard");
    eq(DesktopControls.keyboard(event(KeyEvent.KEYCODE_BUTTON_A, keyboard, controller)), false,
        "controller buttons stay with gamepad controls");
    eq(DesktopControls.keyboard(event(KeyEvent.KEYCODE_A, InputDevice.SOURCE_GAMEPAD, controller)), false,
        "gamepad source is never a desktop key");
    eq(DesktopControls.keyboard(event(KeyEvent.KEYCODE_A, mouse, pointing)), false,
        "mouse buttons never become hotkeys");
    eq(DesktopControls.keyboard(event(KeyEvent.KEYCODE_A, InputDevice.SOURCE_UNKNOWN, null)), false,
        "unknown hardware is not a keyboard");
    eq(DesktopControls.keyboardSource(keyboard | InputDevice.SOURCE_GAMEPAD), false,
        "combined controller source is not a desktop keyboard event");
    eq(DesktopControls.mouseBack(event(KeyEvent.KEYCODE_BACK, mouse, pointing)), true,
        "mouse Back event is consumed without opening the menu");
    eq(DesktopControls.mouseBack(event(KeyEvent.KEYCODE_BACK, InputDevice.SOURCE_UNKNOWN, pointing)), true,
        "mouse device identifies source-less Back");
    eq(DesktopControls.mouseBack(event(KeyEvent.KEYCODE_BACK, keyboard, combo)), false,
        "a real Back key on a combined keyboard and mouse remains a keyboard key");
    eq(DesktopControls.mouseBack(event(KeyEvent.KEYCODE_ESCAPE, mouse, pointing)), false,
        "mouse Back handling is limited to Back");
    eq(DesktopControls.mouseBack(event(KeyEvent.KEYCODE_BACK, keyboard, typing)), false,
        "ordinary keyboard Back is unaffected");
    System.out.println("PASS source policy preserves touch, stylus, controller D-pad and keyboard Back");
  }

  private static void keyPolicy() {
    for (int i = 0; i < 26; ++i) {
      int key = KeyEvent.KEYCODE_A + i;
      for (int unicode : new int[]{'a' + i, 'A' + i, 0x430 + i, 0})
        eq(DesktopControls.symbol(key, unicode), (int)'a' + i,
            "physical hotkey ignores Caps Lock, Shift and Cyrillic output");
      eq(DesktopControls.scanCode(key), 4 + i, "letter SDL scan code");
    }
    for (int i = 0; i < 10; ++i) {
      eq(DesktopControls.symbol(KeyEvent.KEYCODE_0 + i, '!'), (int)'0' + i,
          "shifted number still identifies the same control group");
      eq(DesktopControls.symbol(KeyEvent.KEYCODE_NUMPAD_0 + i, 0), (int)'0' + i,
          "numeric keypad control group");
      eq(DesktopControls.scanCode(KeyEvent.KEYCODE_0 + i), i == 0 ? 39 : 29 + i,
          "number SDL scan code");
    }
    int[][] scans = {{KeyEvent.KEYCODE_SPACE, 44}, {KeyEvent.KEYCODE_TAB, 43},
        {KeyEvent.KEYCODE_ESCAPE, 41}, {KeyEvent.KEYCODE_CTRL_LEFT, 224},
        {KeyEvent.KEYCODE_CTRL_RIGHT, 228}, {KeyEvent.KEYCODE_SHIFT_LEFT, 225},
        {KeyEvent.KEYCODE_SHIFT_RIGHT, 229}};
    for (int[] pair : scans) eq(DesktopControls.scanCode(pair[0]), pair[1], "special SDL scan code");
    for (int key : new int[]{KeyEvent.KEYCODE_DPAD_UP, KeyEvent.KEYCODE_DPAD_DOWN,
        KeyEvent.KEYCODE_DPAD_LEFT, KeyEvent.KEYCODE_DPAD_RIGHT}) {
      eq(DesktopControls.cameraKey(key), true, "arrow is a held camera control");
      eq(DesktopControls.symbol(key, 'x'), 0, "camera arrow cannot dispatch a native command");
      eq(DesktopControls.scanCode(key), 0, "camera arrows do not leak native hotkeys");
    }
    DesktopControls state = new DesktopControls();
    eq(state.key(KeyEvent.KEYCODE_A, true, 0), true, "first press dispatches command");
    eq(state.key(KeyEvent.KEYCODE_A, true, 1), false, "OS repeat cannot repeat an order");
    eq(state.key(KeyEvent.KEYCODE_A, true, 0), false, "duplicate down cannot repeat an order");
    eq(state.key(KeyEvent.KEYCODE_A, false, 0), true, "first release dispatches");
    eq(state.key(KeyEvent.KEYCODE_A, false, 0), false, "duplicate release is ignored");
    state.key(KeyEvent.KEYCODE_CTRL_LEFT, true, 0);
    state.key(KeyEvent.KEYCODE_SHIFT_RIGHT, true, 0);
    state.key(KeyEvent.KEYCODE_DPAD_LEFT, true, 0);
    state.key(KeyEvent.KEYCODE_DPAD_UP, true, 0);
    eq(state.ctrl(), true, "Ctrl held"); eq(state.shift(), true, "Shift held");
    eq(state.cameraX(), -1, "left camera movement"); eq(state.cameraY(), -1, "diagonal camera movement");
    state.key(KeyEvent.KEYCODE_DPAD_RIGHT, true, 0);
    eq(state.cameraX(), 0, "opposing arrows cancel");
    state.key(KeyEvent.KEYCODE_DPAD_LEFT, false, 0);
    eq(state.cameraX(), 1, "releasing one arrow preserves the other");
    int[] released = state.releaseKeys();
    int[] expected = {KeyEvent.KEYCODE_CTRL_LEFT, KeyEvent.KEYCODE_SHIFT_RIGHT,
        KeyEvent.KEYCODE_DPAD_UP, KeyEvent.KEYCODE_DPAD_RIGHT};
    Arrays.sort(expected);
    eq(Arrays.equals(released, expected), true, "focus loss releases every held key exactly once");
    eq(state.releaseKeys().length, 0, "focus cleanup is idempotent");
    eq(state.ctrl(), false, "no stuck Ctrl after focus loss");
    eq(state.shift(), false, "no stuck Shift after focus loss");
    eq(state.cameraX(), 0, "no stuck horizontal camera after focus loss");
    eq(state.cameraY(), 0, "no stuck vertical camera after focus loss");
    eq(state.key(KeyEvent.KEYCODE_DPAD_UP, true, 3), false, "stale OS repeats cannot restart a released camera");
    eq(state.cameraY(), 0, "stale repeated arrow remains released");
    System.out.println("PASS physical hotkeys, repeat suppression, modifiers and focus cleanup");
  }

  private static void mousePolicy() {
    int left = MotionEvent.BUTTON_PRIMARY, right = MotionEvent.BUTTON_SECONDARY;
    int middle = MotionEvent.BUTTON_TERTIARY;
    for (int button : new int[]{left, right, middle}) {
      DesktopControls state = new DesktopControls();
      eq(state.updateButtons(MotionEvent.ACTION_DOWN, button, 0), button, "DOWN begins click");
      eq(state.updateButtons(MotionEvent.ACTION_BUTTON_PRESS, button, button), 0,
          "BUTTON_PRESS duplicate cannot double click");
      eq(state.updateButtons(MotionEvent.ACTION_BUTTON_RELEASE, 0, button), button,
          "BUTTON_RELEASE finishes click");
      eq(state.updateButtons(MotionEvent.ACTION_UP, 0, 0), 0, "UP duplicate cannot double release");
      eq(state.updateButtons(MotionEvent.ACTION_BUTTON_PRESS, button, button), button,
          "BUTTON_PRESS also works first");
      eq(state.updateButtons(MotionEvent.ACTION_DOWN, button, 0), 0,
          "DOWN duplicate cannot double click");
      eq(state.updateButtons(MotionEvent.ACTION_UP, 0, 0), button, "UP also works first");
      eq(state.updateButtons(MotionEvent.ACTION_BUTTON_RELEASE, 0, button), 0,
          "BUTTON_RELEASE duplicate cannot double release");
    }
    DesktopControls state = new DesktopControls();
    state.updateButtons(MotionEvent.ACTION_DOWN, left, 0);
    eq(state.updateButtons(MotionEvent.ACTION_BUTTON_PRESS, left | right, right), right,
        "chord presses only the additional button");
    eq(state.updateButtons(MotionEvent.ACTION_BUTTON_RELEASE, left | right, left), left,
        "action button release overrides a stale state for that button");
    eq(state.buttons, right, "release leaves the other chord button held");
    eq(state.updateButtons(MotionEvent.ACTION_HOVER_EXIT, 0, 0), 0,
        "hover exit is not a release (Android may emit it before a click)");
    eq(state.buttons, right, "hover exit preserves button state");
    eq(state.updateButtons(MotionEvent.ACTION_CANCEL, right, 0), right,
        "cancel releases buttons even if state was stale");
    eq(state.buttons, 0, "cancel leaves no stuck mouse button");
    eq(state.updateButtons(MotionEvent.ACTION_DOWN, 0, 0), left, "legacy primary down with empty state");
    eq(state.updateButtons(MotionEvent.ACTION_MOVE, left, 0), 0, "drag does not repeat mouse-down");
    eq(state.releaseButtons(), left, "focus loss releases held pointer");
    eq(state.releaseButtons(), 0, "focus pointer cleanup is idempotent");
    eq(state.updateButtons(MotionEvent.ACTION_SCROLL, 0, 0), 0, "wheel never synthesizes clicks");
    eq(state.updateButtons(MotionEvent.ACTION_BUTTON_PRESS, MotionEvent.BUTTON_BACK,
        MotionEvent.BUTTON_BACK), 0, "back mouse button is not a game click");
    eq(state.updateButtons(MotionEvent.ACTION_BUTTON_PRESS, MotionEvent.BUTTON_FORWARD,
        MotionEvent.BUTTON_FORWARD), 0, "forward mouse button is not a game click");
    eq(state.updateButtons(MotionEvent.ACTION_BUTTON_PRESS, 0, middle), middle,
        "explicit pressed button repairs missing buttonState");
    eq(state.updateButtons(MotionEvent.ACTION_DOWN, 0, 0), 0,
        "legacy duplicate DOWN cannot replace a middle click with left");
    eq(state.buttons, middle, "middle remains middle");
    eq(state.updateButtons(MotionEvent.ACTION_HOVER_MOVE, 0, 0), middle,
        "authoritative hover state clears a missed release");
    System.out.println("PASS mouse transition deduplication, left/right/middle, chords and focus cleanup");
  }

  public static void main(String[] args) {
    sourcePolicy(); keyPolicy(); mousePolicy();
    System.out.println("PASS " + checks + " desktop input policy assertions");
  }
}

package org.openbw.androidtest;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;

/** Controller preferences shared by the app-options and in-game controls menus. */
final class GamepadSettings {
  private static String t(String value) { return PortText.text(value); }

  static void show(Activity activity, SharedPreferences preferences, Runnable dismissed) {
    GamepadControls controls = new GamepadControls();
    controls.load(preferences);
    ScrollView scroll = new ScrollView(activity);
    LinearLayout panel = new LinearLayout(activity);
    panel.setOrientation(LinearLayout.VERTICAL);
    int padding = Math.round(20 * activity.getResources().getDisplayMetrics().density);
    panel.setPadding(padding, padding / 2, padding, padding);
    scroll.addView(panel);
    TextView help = new TextView(activity);
    help.setText(t("Left stick moves the pointer; right stick moves the camera. Hold Select / click and move the pointer to drag a selection. Touch controls remain available."));
    panel.addView(help);
    Runnable save = () -> controls.save(preferences);
    toggle(activity, panel, "Enable gamepad", controls.enabled, value -> { controls.enabled = value; save.run(); });
    toggle(activity, panel, "Swap pointer and camera sticks", controls.swapSticks, value -> { controls.swapSticks = value; save.run(); });
    slider(activity, panel, "Pointer speed", Math.round(controls.pointerSpeed * 100), 25, 300,
        value -> { controls.pointerSpeed = value / 100f; save.run(); });
    slider(activity, panel, "Camera speed", Math.round(controls.cameraSpeed * 100), 25, 300,
        value -> { controls.cameraSpeed = value / 100f; save.run(); });
    slider(activity, panel, "Stick dead zone", Math.round(controls.deadZone * 100), 5, 50,
        value -> { controls.deadZone = value / 100f; save.run(); });
    TextView heading = new TextView(activity);
    heading.setText(t("Button assignments")); heading.setTextSize(18); heading.setPadding(0, padding, 0, 0);
    panel.addView(heading);
    for (int i = 0; i < GamepadControls.BUTTONS.length; i++) {
      final int index = i;
      Button button = new Button(activity);
      button.setAllCaps(false);
      Runnable label = () -> button.setText(t(GamepadControls.BUTTON_LABELS[index]) + ": "
          + t(GamepadControls.ACTION_LABELS[controls.bindings[index]]));
      label.run(); panel.addView(button);
      button.setOnClickListener(view -> {
        String[] actions = new String[GamepadControls.ACTION_LABELS.length];
        for (int n = 0; n < actions.length; n++) actions[n] = t(GamepadControls.ACTION_LABELS[n]);
        new AlertDialog.Builder(activity).setTitle(t(GamepadControls.BUTTON_LABELS[index]))
            .setSingleChoiceItems(actions, controls.bindings[index], (dialog, which) -> {
              controls.bindings[index] = which; save.run(); label.run(); dialog.dismiss();
            }).setNegativeButton(t("Cancel"), null).show();
      });
    }
    AlertDialog dialog = new AlertDialog.Builder(activity).setTitle(t("Gamepad controls"))
        .setView(scroll).setPositiveButton(t("Close"), null)
        .setNeutralButton(t("Reset to defaults"), null).create();
    dialog.setOnDismissListener(ignored -> dismissed.run());
    dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(view -> {
      controls.reset(); save.run();
      // Reopen with fresh slider and binding values, keeping the host paused.
      dialog.setOnDismissListener(null); dialog.dismiss();
      show(activity, preferences, dismissed);
    }));
    dialog.show();
  }

  private interface BooleanChanged { void changed(boolean value); }
  private interface IntChanged { void changed(int value); }
  private static void toggle(Activity activity, LinearLayout panel, String label, boolean checked, BooleanChanged changed) {
    Switch control = new Switch(activity);
    control.setText(t(label)); control.setChecked(checked);
    control.setPadding(0, 12, 0, 12); panel.addView(control);
    control.setOnCheckedChangeListener((view, value) -> changed.changed(value));
  }
  private static void slider(Activity activity, LinearLayout panel, String label, int value, int min, int max, IntChanged changed) {
    TextView title = new TextView(activity);
    title.setText(t(label) + ": " + value + "%"); panel.addView(title);
    SeekBar bar = new SeekBar(activity); bar.setMax(max - min); bar.setProgress(value - min);
    bar.setContentDescription(t(label)); panel.addView(bar);
    bar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
      public void onProgressChanged(SeekBar view, int progress, boolean fromUser) {
        title.setText(t(label) + ": " + (progress + min) + "%");
        if (fromUser) changed.changed(progress + min);
      }
      public void onStartTrackingTouch(SeekBar view) {}
      public void onStopTrackingTouch(SeekBar view) {}
    });
  }
  private GamepadSettings() {}
}

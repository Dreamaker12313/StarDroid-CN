package org.openbw.androidtest;

import android.content.SharedPreferences;
import org.json.JSONObject;

/** Device preferences, independent of the mission and save-slot state. */
final class ControlSettings {
  String preset;
  int dragMode, holdMs, radius, doubleTapMs, tooltipMs, miniHoldMs, placementOffset, selectionButton;
  float panSpeed, pinchSpeed;
  boolean doubleTap, holdSelect, attackTap, pinchZoom, reversePan, minimapOrders,
      tooltips, confirmBuild, placementButtonsFollow, placementScroll, groundOrders, controlGroups, commandModeButton, originalLarvae, singleLarvaMorph;

  ControlSettings() { preset("Comfortable"); }

  void preset(String name) {
    preset = name;
    dragMode = name.equals("Drag to select") ? 1 : 0;
    holdMs = name.equals("Precise") ? 260 : 180;
    radius = name.equals("Precise") ? 8 : 28;
    doubleTapMs = 300; tooltipMs = 220; miniHoldMs = 450; placementOffset = 48;
    panSpeed = pinchSpeed = 1;
    doubleTap = holdSelect = attackTap = pinchZoom = tooltips = confirmBuild = placementButtonsFollow = placementScroll = true;
    minimapOrders = false; reversePan = false; groundOrders = true; selectionButton = 1; controlGroups = false; commandModeButton = true;
    originalLarvae = true; singleLarvaMorph = false;
  }

  void load(SharedPreferences prefs) {
    try {
      JSONObject j = new JSONObject(prefs.getString("touch-controls", "{}"));
      preset = j.optString("preset", preset);
      selectionButton = clamp(j.optInt("selectionButton", selectionButton), 0, 2);
      // Migrate the old preset default; preserve a deliberately customized side.
      if (j.optInt("version", 1) < 2 && !preset.equals("Custom") && selectionButton == 2) selectionButton = 1;
      groundOrders = j.optBoolean("groundOrders", true);
      controlGroups = j.optBoolean("controlGroups", false);
      commandModeButton = j.optBoolean("commandModeButton", true);
      originalLarvae = j.optBoolean("originalLarvae", true);
      singleLarvaMorph = j.optBoolean("singleLarvaMorph", false);
      dragMode = clamp(j.optInt("dragMode", dragMode), 0, 1);
      holdMs = clamp(j.optInt("holdMs", holdMs), 100, 600);
      radius = clamp(j.optInt("radius", radius), 0, 40);
      doubleTapMs = clamp(j.optInt("doubleTapMs", doubleTapMs), 180, 500);
      tooltipMs = clamp(j.optInt("tooltipMs", tooltipMs), 150, 800);
      miniHoldMs = clamp(j.optInt("miniHoldMs", miniHoldMs), 250, 800);
      placementOffset = clamp(j.optInt("placementOffset", placementOffset), 0, 96);
      panSpeed = finite(j.optDouble("panSpeed", panSpeed));
      pinchSpeed = finite(j.optDouble("pinchSpeed", pinchSpeed));
      doubleTap = j.optBoolean("doubleTap", doubleTap);
      holdSelect = j.optBoolean("holdSelect", holdSelect);
      attackTap = j.optBoolean("attackTap", attackTap);
      pinchZoom = j.optBoolean("pinchZoom", pinchZoom);
      reversePan = j.optBoolean("reversePan", reversePan);
      minimapOrders = j.optBoolean("minimapOrders", minimapOrders);
      tooltips = j.optBoolean("tooltips", tooltips);
      confirmBuild = j.optBoolean("confirmBuild", confirmBuild);
      placementButtonsFollow = j.optBoolean("placementButtonsFollow", true);
      placementScroll = j.optBoolean("placementScroll", true);
    } catch (Exception ignored) { preset("Comfortable"); }
  }

  void save(SharedPreferences prefs) {
    try {
      JSONObject j = new JSONObject();
      j.put("version", 2).put("commandModeButton", commandModeButton).put("controlGroups", controlGroups).put("preset", preset).put("selectionButton", selectionButton).put("groundOrders", groundOrders).put("dragMode", dragMode).put("holdMs", holdMs)
          .put("radius", radius).put("doubleTapMs", doubleTapMs).put("tooltipMs", tooltipMs)
          .put("miniHoldMs", miniHoldMs).put("placementOffset", placementOffset)
          .put("panSpeed", panSpeed).put("pinchSpeed", pinchSpeed)
          .put("doubleTap", doubleTap).put("holdSelect", holdSelect).put("attackTap", attackTap)
          .put("pinchZoom", pinchZoom).put("reversePan", reversePan)
          .put("minimapOrders", minimapOrders).put("tooltips", tooltips).put("confirmBuild", confirmBuild)
          .put("placementButtonsFollow", placementButtonsFollow).put("placementScroll", placementScroll)
          .put("originalLarvae", originalLarvae).put("singleLarvaMorph", singleLarvaMorph);
      prefs.edit().putString("touch-controls", j.toString()).apply();
    } catch (Exception e) { throw new IllegalStateException(e); }
  }

  String dragGesture(long elapsed) {
    return dragMode == 1 || elapsed >= holdMs ? "box" : "pan";
  }
  float panFactor() { return panSpeed * (reversePan ? -1 : 1); }
  static int clamp(int n, int lo, int hi) { return Math.max(lo, Math.min(hi, n)); }
  private static float finite(double n) {
    return Double.isNaN(n) || Double.isInfinite(n) ? 1 : (float) Math.max(.5, Math.min(2.5, n));
  }
}

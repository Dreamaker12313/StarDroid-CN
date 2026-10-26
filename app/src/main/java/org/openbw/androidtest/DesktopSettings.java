package org.openbw.androidtest;

import android.content.SharedPreferences;
import org.json.JSONObject;

/** Mouse and keyboard preferences, independent of touch and gamepad controls. */
final class DesktopSettings {
  boolean gridHotkeys, edgeScroll=true, wheelZoom=true, middlePan=true, arrowPan=true;
  float cameraSpeed=1;

  void load(SharedPreferences prefs) {
    gridHotkeys=false;edgeScroll=wheelZoom=middlePan=arrowPan=true;cameraSpeed=1;
    try {
      JSONObject data=new JSONObject(prefs.getString("desktop-controls", "{}"));
      gridHotkeys=data.optBoolean("gridHotkeys",false);
      edgeScroll=data.optBoolean("edgeScroll",true);
      wheelZoom=data.optBoolean("wheelZoom",true);
      middlePan=data.optBoolean("middlePan",true);
      arrowPan=data.optBoolean("arrowPan",true);
      cameraSpeed=speed(data.optDouble("cameraSpeed",1));
    } catch (Exception ignored) {
      gridHotkeys=false;edgeScroll=wheelZoom=middlePan=arrowPan=true;cameraSpeed=1;
    }
  }

  void save(SharedPreferences prefs) {
    cameraSpeed=speed(cameraSpeed);
    try {
      JSONObject data=new JSONObject().put("version",1).put("gridHotkeys",gridHotkeys)
          .put("edgeScroll",edgeScroll).put("wheelZoom",wheelZoom)
          .put("middlePan",middlePan).put("arrowPan",arrowPan).put("cameraSpeed",cameraSpeed);
      prefs.edit().putString("desktop-controls",data.toString()).apply();
    } catch (Exception error) { throw new IllegalStateException(error); }
  }

  static float speed(double value) {
    return Double.isNaN(value)||Double.isInfinite(value)?1:(float)Math.max(.25,Math.min(2.5,value));
  }

  static int gridSlot(int symbol) { return "qweasdzxc".indexOf(Character.toLowerCase((char)symbol)); }
}

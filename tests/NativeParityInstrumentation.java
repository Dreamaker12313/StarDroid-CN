package org.openbw.androidtest;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.os.*;
import android.view.MotionEvent;
import java.io.*;
import java.util.*;
import org.json.*;

/** Matched browser-reference scenes and real Android touch regression cases. */
public final class NativeParityInstrumentation extends NativeInstrumentation {
  boolean touchOnly;
  @Override public void onCreate(Bundle args) {
    touchOnly = args != null && "touch".equals(args.getString("section"));
    super.onCreate(args);
  }
  void load(int code) throws Exception {
    task(() -> {
      JSONArray missions = (JSONArray) field(game, "missions");
      for (int i = 0; i < missions.length(); i++) if (missions.getJSONObject(i).getInt("code") == code) {
        call(game, "loadMission", new Class<?>[] {JSONObject.class}, missions.getJSONObject(i));
        call(game, "showBriefing", new Class<?>[0]);
        return;
      }
      throw new Exception("Missing catalog mission " + code);
    });
    Thread.sleep(900);
  }

  int[] camera() {
    java.util.regex.Matcher m = java.util.regex.Pattern.compile("camera=(\\d+),(\\d+)").matcher(NativeBridge.text(13));
    if (!m.find()) throw new RuntimeException("No camera diagnostic");
    return new int[] {Integer.parseInt(m.group(1)), Integer.parseInt(m.group(2))};
  }

  void centerWorker() throws Exception {
    int id = unit("SCV", 1);
    for (String row : NativeBridge.text(10).split("\n")) {
      String[] u = row.split("\t");
      if (u.length > 4 && Integer.parseInt(u[0]) == id) {
        NativeBridge.command(3, -65536, -65536, 0, 0);
        NativeBridge.command(3, Math.max(0, Integer.parseInt(u[3]) - 240), Math.max(0, Integer.parseInt(u[4]) - 140), 0, 0);
        return;
      }
    }
  }

  void back() throws Exception {game.back(); task(() -> {}); Thread.sleep(300);}

  void openMenu() throws Exception {
    int[] width = {640}; task(() -> width[0] = (Integer) field(game, "logicalWidth"));
    tap(width[0] - 197, 397);
  }

  void pointers(int action, float x1, float y1, float x2, float y2, long t) throws Exception {
    int width = (Integer) field(game, "logicalWidth"), pw = (Integer) field(game, "physicalWidth"), ph = (Integer) field(game, "physicalHeight");
    float scale = Math.min(pw / (float) width, ph / 480f);
    MotionEvent.PointerProperties[] props = new MotionEvent.PointerProperties[2];
    MotionEvent.PointerCoords[] coords = new MotionEvent.PointerCoords[2];
    for (int i = 0; i < 2; i++) {
      props[i] = new MotionEvent.PointerProperties(); props[i].id = i; props[i].toolType = MotionEvent.TOOL_TYPE_FINGER;
      coords[i] = new MotionEvent.PointerCoords(); coords[i].x = (pw - width * scale) / 2 + (i == 0 ? x1 : x2) * scale;
      coords[i].y = (ph - 480 * scale) / 2 + (i == 0 ? y1 : y2) * scale; coords[i].pressure = 1; coords[i].size = 1;
    }
    MotionEvent e = MotionEvent.obtain(t, t + 50, action, 2, props, coords, 0, 0, 1, 1, 0, 0, 0, 0);
    runOnMainSync(() -> game.dispatchTouchEvent(e)); e.recycle(); task(() -> {});
  }

  @Override public void onStart() {
    Bundle result = new Bundle();
    try {
      output = new File(getTargetContext().getFilesDir(), "native-parity"); output.mkdirs();
      for (File old : output.listFiles()) old.delete();
      report.put("version", getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest", 0).versionName);
      report.put("android", Build.VERSION.RELEASE); report.put("abi", Build.SUPPORTED_ABIS[0]);
      recordPackageHashes();
      MainActivity activity = (MainActivity) startActivitySync(new Intent(getTargetContext(), MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
      game = (NativeSurface) field(activity, "game");
      task(() -> {
        check(game != null, "Native surface missing"); set(game, "wide", false); set(game, "zoom", 1f); set(game, "speed", 42.);
        set(game, "muted", false); set(game, "music", .65f); set(game, "orderLines", false);
      });
      if (!touchOnly) {
      screenshot("title"); glueTap(3); screenshot("chooser");
      RectF[] choice = {null};
      task(() -> {
        NativeArt art = (NativeArt) field(game, "art");
        NativeArt.PCX bg = art.pcx("glue/palmm/retail_ex.pcx", false, -1);
        choice[0] = new NativeArt.Dialog(art.read("rez/glugamemode.bin")).get(6).hit();
        choice[0].offset((640 - bg.width) / 2f, (480 - bg.height) / 2f);
      });
      tap(choice[0].centerX(), choice[0].centerY());
      task(() -> check(field(game, "page").equals("registry"), "Chooser skipped Registry"));
      screenshot("registry");
      task(() -> {
        ArrayList<String> names = (ArrayList<String>) field(game, "profiles");
        if (!names.contains("Tester")) names.add("Tester"); set(game, "selectedProfile", "Tester"); call(game, "saveProfiles", new Class<?>[0]);
      });
      glueTap(4); Thread.sleep(1200); screenshot("campaign");
      task(() -> {
        NativeGlue glue = (NativeGlue) field(game, "glue");
        double old = glue.elapsed; glue.elapsed = 140;
        for (int i = 6; i <= 8; i++) check(glue.shift(glue.layout.get(i)) == 0, "Campaign figure slides");
        check(glue.shift(glue.layout.get(5)) == glue.shift(glue.layout.get(1)), "Campaign text detached from panel");
        glue.elapsed = old;
        report.put("stationaryFiguresAndAttachedLabels", true);
      });
      glueTap(8); task(() -> check(field(game, "modal").equals("missions"), "Campaign click did not open mission history"));
      screenshot("missions"); tap(230, 185);
      task(() -> check(field(game, "page").equals("campaign"), "Mission selection started without OK"));
      back(); glueTap(10); Thread.sleep(1000); screenshot("custom");
      task(() -> check(field(game, "page").equals("custom"), "Custom Game did not open"));
      task(() -> {
        File bad = new File(getTargetContext().getCacheDir(), "parity-invalid.scx");
        try (FileOutputStream out = new FileOutputStream(bad)) {out.write(new byte[80]);}
        game.mapsSelected(java.util.Collections.singletonList(new NativeMaps.Staged(bad,bad.getName())), "");
      }); task(() -> {});
      task(() -> {check(field(game, "page").equals("custom") && field(game, "modal").equals("map-error"), "Bad map closed setup"); set(game, "modal", "");});
      task(() -> {
        File map = new File(getTargetContext().getCacheDir(), "parity-weave.scx");
        try (InputStream in = getTargetContext().getAssets().open("native/weave.scx"); FileOutputStream out = new FileOutputStream(map)) {
          byte[] b = new byte[65536]; int n; while ((n = in.read(b)) >= 0) out.write(b, 0, n);
        }
        game.mapsSelected(java.util.Collections.singletonList(new NativeMaps.Staged(map,map.getName())), "");
      }); task(() -> {});
      task(() -> {
        check(field(game, "page").equals("custom") && !(Boolean) field(game, "activeGame"), "Map import launched immediately");
        check(((Integer) field(game, "customWidth")) == 64, "Map dimensions missing");
        report.put("mapValidationAndExplicitStart", true);
      });
      glueTap(12); settle();
      task(() -> {
        check(field(game, "page").equals("game") && (Boolean) field(game, "activeGame"), "Custom map OK did not start game");
        report.put("customMapStart", true);
      });
      task(() -> call(game, "showCustom", new Class<?>[0]));
      glueTap(21); // Close the default computer slot.
      task(() -> check((Integer) field(game, "customBotSlot") == -1, "Computer slot did not close"));
      glueTap(12); settle();
      task(() -> {
        int own = 0, enemies = 0;
        for (String row : NativeBridge.text(10).split("\n")) {
          String[] unit = row.split("\t");
          if (unit.length < 3) continue;
          int owner = Integer.parseInt(unit[2]);
          if (owner == 0) own++;
          else if (owner < 8) enemies++;
        }
        check(own > 0 && enemies == 0, "Practice mode spawned an opponent");
        report.put("practiceWithoutComputer", true);
        call(game, "showCustom", new Class<?>[0]);
      });
      glueTap(22); // Move the one supported computer to a different start.
      task(() -> check((Integer) field(game, "customBotSlot") == 2, "Computer slot did not change"));
      glueTap(12); settle();
      task(() -> {
        check(unit("Hatchery", 2) >= 0, "Computer did not use the selected slot");
        render(600);
        report.put("customComputerUnits", NativeBridge.text(10));
        report.put("customComputerSlot", 2);
      });
      load(202); screenshot("protoss-briefing");
      task(() -> {
        NativeCampaign campaign = (NativeCampaign) field(game, "campaign");
        int checked = 0;
        for (int i = 0; i < campaign.actions.size(); i++) if (campaign.actions.get(i).type == 8) {
          campaign.transmission = false; campaign.remaining = 0; campaign.index = i; campaign.tick(0);
          check(campaign.remaining >= campaign.spokenLength, "Briefing truncates original WAV");
          checked++;
        }
        check(checked > 0, "No Protoss speech checked");
        report.put("untruncatedBriefingRecordings", checked);
        campaign.replay(); campaign.tick(0);
      });
      task(() -> {
        NativeCampaign campaign = (NativeCampaign) field(game, "campaign");
        for (int i = 0; i < 100 && !campaign.transmission; i++) campaign.tick(1000);
        check(campaign.transmission && campaign.talking >= 0, "Briefing voice did not start");
      });
      screenshot("protoss-speaking");
      load(102); screenshot("briefing"); glueTap(13); Thread.sleep(1200);
      task(() -> {check(field(game, "page").equals("game"), "Briefing Start failed"); select("Hatchery");}); screenshot("hatchery");
      task(() -> select("Larva")); screenshot("larva");
      openMenu(); screenshot("menu"); menuTap("gamemenu", 3); screenshot("options");
      menuTap("options", 2); screenshot("sound");
      tap(230, 101); task(() -> check((Boolean) field(game, "muted"), "Mute toggle missing")); tap(230, 101);
      task(() -> check(field(game, "currentMusicPath").equals("music/zerg1.wav"), "Automatic race music missing"));
      back(); menuTap("options", 1); screenshot("speed"); tap(240, 264);
      task(() -> {check((Double) field(game, "speed") == 2.625, "16x speed is missing"); report.put("speed16x", true);});
      back(); menuTap("options", 3); screenshot("video"); tap(250, 89);
      task(() -> {check(NativeBridge.value(18, 0) == 1, "Order lines do not reach engine"); report.put("orderLines", true);});
      back(); tap(300, 218); screenshot("testing"); tap(300, 197);
      task(() -> check((Double) field(game, "speed") == 42, "Reset speed failed"));
      back(); back(); back();
      }
      load(1); task(() -> call(game, "startMission", new Class<?>[0])); Thread.sleep(600);
      settle();
      task(() -> {NativeBridge.command(11, 0, 0, 0, 0); NativeBridge.command(9, 0, 0, 0, 0); select("SCV", 1); NativeBridge.command(3, 400, 400, 0, 0);});
      task(() -> {
        int count = 0;
        for (String row : NativeBridge.text(10).split("\n")) {
          String[] fields = row.split("\t");
          if (fields.length > 2 && fields[2].equals("1") && (fields[1].equals("SCV") || fields[1].contains("Raynor"))) {
            NativeBridge.command(14, Integer.parseInt(fields[0]), count++ == 0 ? 0 : 1, 0, 0);
            if (count == 6) break;
          }
        }
        render(0); check(NativeBridge.text(3).trim().split("\n").length > 1, "No group for wire tile check");
      });
      screenshot("terran-group");
      task(() -> {
        NativeHud hud = (NativeHud) field(game, "hud");
        check(hud.wireTiles[0] != hud.wireTiles[1], "Group wires share the same mutable bitmap");
      });
      long wireTouch = SystemClock.uptimeMillis(); touch(0, 180, 408, wireTouch, wireTouch);
      task(() -> {
        NativeHud.Hit hit = (NativeHud.Hit) field(game, "pressedHit");
        report.put("wireTouch", new JSONObject().put("gesture", field(game, "gesture"))
            .put("hit", hit == null ? -1 : hit.selectUnit).put("before", NativeBridge.text(3)));
        save();
      });
      touch(1, 180, 408, wireTouch, wireTouch + 80);
      task(() -> {
        report.put("wireTouchAfter", NativeBridge.text(3)); save();
        check(NativeBridge.text(3).trim().split("\n").length == 1, "Wire tile tap did not select one unit");
        select("SCV", 1); report.put("groupWireTileSelection", true);
      });
      int[][] before = {null}; String[] selected = {null};
      task(() -> {before[0] = camera(); selected[0] = NativeBridge.text(3);});
      long t = SystemClock.uptimeMillis(); touch(0, 220, 140, t, t); touch(2, 270, 140, t, t + 80);
      task(() -> check(field(game, "gesture").equals("pan"), "Quick drag is not pan")); touch(1, 270, 140, t, t + 120);
      task(() -> {check(!Arrays.equals(before[0], camera()), "Pan did not move camera"); check(NativeBridge.text(3).equals(selected[0]), "Pan changed selection"); before[0] = camera();});
      t = SystemClock.uptimeMillis(); touch(0, 20, 20, t, t); touch(2, 610, 280, t, t + 450);
      task(() -> check(field(game, "gesture").equals("box"), "Hold-drag is not selection")); touch(1, 610, 280, t, t + 550);
      task(() -> {check(Arrays.equals(before[0], camera()), "Box selection panned"); select("SCV", 1);});
      commandTap("Move"); task(() -> {
        before[0] = camera();
        report.put("beforeTarget", new JSONObject().put("cursor", NativeBridge.value(0, 0))
            .put("touchAction", NativeBridge.value(17, (250 << 16) | 150)).put("card", NativeBridge.text(0)));
        save(); check(NativeBridge.value(0, 0) == 1, "Move command did not set target cursor");
      });
      t = SystemClock.uptimeMillis(); touch(0, 250, 150, t, t); touch(2, 290, 170, t, t + 70);
      task(() -> check(field(game, "gesture").equals("aim"), "Target drag turned into pan")); touch(1, 290, 170, t, t + 120);
      task(() -> {check(Arrays.equals(before[0], camera()), "Targeting changed camera"); render(2); check(NativeBridge.value(0, 0) == 0, "Target order was not sent");});
      t = SystemClock.uptimeMillis(); touch(0, 220, 140, t, t); pointers(MotionEvent.ACTION_POINTER_DOWN | 256, 220, 140, 420, 140, t);
      pointers(2, 170, 160, 450, 160, t + 60);
      task(() -> check((Float) field(game, "zoom") > 1.2, "Pinch did not zoom"));
      touch(3, 200, 140, t, t + 200);
      task(() -> {check(field(game, "gesture").equals(""), "Cancel left pinch active"); set(game, "zoom", 1f); call(game, "resizeWorld", new Class<?>[0]); report.put("panBoxAimPinchAndCancel", true);});
      task(() -> {select("SCV", 1); centerWorker();}); commandTap("Build"); back();
      task(() -> check(field(game, "modal").equals(""), "Back from build submenu opened menu"));
      task(() -> {set(game, "instant", true); NativeBridge.command(10, 1, 0, 0, 0);});
      commandTap("Build"); commandTap("Supply Depot");
      int[] site = {-1, -1};
      task(() -> {
        check(NativeBridge.value(0, 0) == 2, "Supply Depot did not enter placement mode");
        outer: for (int y = 40; y < 300; y += 8) for (int x = 40; x < 600; x += 8)
          if (NativeBridge.value(16, (x << 16) | y) != 0) {site[0] = x; site[1] = y; break outer;}
        check(site[0] >= 0, "No valid build site");
      });
      float scale = Math.min((Integer) field(game, "physicalWidth") / 640f, (Integer) field(game, "physicalHeight") / 480f);
      tap(site[0], site[1] + 48 / scale);
      task(() -> {check((Boolean) field(game, "placement"), "Finger release placed building"); check((Integer) field(game, "placeY") == site[1], "Preview is not 48 screen pixels above finger");}); screenshot("placement");
      tap(374, 282); task(() -> {check(!(Boolean) field(game, "placement"), "Placement Cancel failed"); check(NativeBridge.value(0, 0) == 0, "Cancel left build cursor"); report.put("placementPreviewAndCancel", true);});
      task(() -> select("SCV", 1)); commandTap("Build"); commandTap("Supply Depot");
      task(() -> {
        site[0] = -1;
        outer: for (int y = 70; y < 220; y += 8) for (int x = 70; x < 560; x += 8)
          if (NativeBridge.value(16, (x << 16) | y) != 0) {site[0] = x; site[1] = y; break outer;}
        check(site[0] >= 0, "No valid confirmation site");
      });
      tap(site[0], site[1] + 48 / scale); settle(); tap(265, 282);
      task(() -> {render(2); check(NativeBridge.value(0, 0) == 0, "Build confirmation did not send order"); report.put("placementConfirmed", true);});
      openMenu(); menuTap("gamemenu", 3); tap(300, 218); tap(300, 234); Thread.sleep(500); screenshot("victory");
      back(); screenshot("results"); task(() -> {check(field(game, "page").equals("results"), "Back from victory did not open scores"); report.put("passed", true);});
      save(); result.putString("report", report.toString()); finish(Activity.RESULT_OK, result);
    } catch (Throwable e) {
      try {report.put("failure", android.util.Log.getStackTraceString(e)); save();} catch (Exception ignored) {}
      result.putString("failure", android.util.Log.getStackTraceString(e)); finish(Activity.RESULT_CANCELED, result);
    }
  }
}

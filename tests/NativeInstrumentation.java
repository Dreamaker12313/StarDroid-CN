package org.openbw.androidtest;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.os.*;
import android.view.MotionEvent;
import java.io.*;
import java.lang.reflect.*;
import java.util.concurrent.*;
import org.json.*;

/** Android integration checks. Built into a separate test APK, never the app. */
public class NativeInstrumentation extends Instrumentation {
  NativeSurface game;
  File output;
  JSONObject report = new JSONObject();

  interface Task {
    void run() throws Exception;
  }

  String sha256(String path) throws Exception {
    java.security.MessageDigest digest = java.security.MessageDigest.getInstance("SHA-256");
    try (InputStream in = new FileInputStream(path)) {
      byte[] buffer = new byte[65536]; int size;
      while ((size = in.read(buffer)) >= 0) digest.update(buffer, 0, size);
    }
    StringBuilder result = new StringBuilder();
    for (byte b : digest.digest()) result.append(String.format("%02x", b & 255));
    return result.toString();
  }

  void recordPackageHashes() throws Exception {
    report.put("apkSha256", sha256(getTargetContext().getApplicationInfo().sourceDir));
    report.put("testApkSha256", sha256(getContext().getApplicationInfo().sourceDir));
  }

  static Object field(Object o, String name) throws Exception {
    Field f = o.getClass().getDeclaredField(name);
    f.setAccessible(true);
    return f.get(o);
  }

  static void set(Object o, String name, Object value) throws Exception {
    Field f = o.getClass().getDeclaredField(name);
    f.setAccessible(true);
    f.set(o, value);
  }

  static Object call(Object o, String name, Class<?>[] types, Object... args) throws Exception {
    Method m = o.getClass().getDeclaredMethod(name, types);
    m.setAccessible(true);
    return m.invoke(o, args);
  }

  void task(Task action) throws Exception {
    CountDownLatch latch = new CountDownLatch(1);
    Throwable[] error = {null};
    game.enqueue(
        () -> {
          try {
            action.run();
          } catch (Throwable e) {
            error[0] = e;
          } finally {
            latch.countDown();
          }
        });
    if (!latch.await(120, TimeUnit.SECONDS)) throw new Exception("Native task timed out");
    if (error[0] != null) throw new Exception("Native task", error[0]);
  }

  void render(int steps) {
    try {
      NativeBridge.frame(
          (Bitmap) field(game, "world"), steps, (Double) field(game, "clock"));
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  int unit(String name, int owner) throws Exception {
    for (String row : NativeBridge.text(10).split("\n")) {
      String[] a = row.split("\t");
      if (a.length > 2 && a[1].equals(name) && (owner < 0 || Integer.parseInt(a[2]) == owner))
        return Integer.parseInt(a[0]);
    }
    throw new Exception("Missing unit " + name);
  }

  void select(String name) throws Exception { select(name, name.contains("Chrysalis") ? -1 : 3); }

  void select(String name, int owner) throws Exception {
    render(0); // Drain any earlier pointer event before diagnostic selection.
    NativeBridge.command(14, unit(name, owner), 0, 0, 0);
    render(0);
  }

  void touch(int action, float x, float y, long start, long time) throws Exception {
    int width = (Integer) field(game, "logicalWidth");
    int pw = (Integer) field(game, "physicalWidth"), ph = (Integer) field(game, "physicalHeight");
    float scale = Math.min(pw / (float) width, ph / 480f);
    MotionEvent event = MotionEvent.obtain(start, time, action,
        (pw - width * scale) / 2 + x * scale, (ph - 480 * scale) / 2 + y * scale, 0);
    runOnMainSync(() -> game.dispatchTouchEvent(event));
    event.recycle();
    task(() -> {});
  }

  void tap(float x, float y) throws Exception {
    long now = SystemClock.uptimeMillis();
    touch(MotionEvent.ACTION_DOWN, x, y, now, now);
    touch(MotionEvent.ACTION_UP, x, y, now, now + 80);
    Thread.sleep(300);
  }

  void commandTap(String label) throws Exception {
    settle(); // The command card is rebuilt when the selected unit is drawn.
    RectF[] target = {null};
    task(() -> {
      NativeHud hud = (NativeHud) field(game, "hud");
      for (NativeHud.Hit hit : hud.hits)
        if (hit.fields != null && hit.fields[1].startsWith(label)) target[0] = new RectF(hit.rect);
      check(target[0] != null, "Command touch target missing: " + label);
    });
    tap(target[0].centerX(), target[0].centerY());
  }

  void glueTap(int id) throws Exception {
    settle();
    RectF[] rect = {null};
    task(() -> rect[0] = ((NativeGlue) field(game, "glue")).layout.get(id).hit());
    tap(rect[0].centerX(), rect[0].centerY());
  }

  void menuTap(String layout, int id) throws Exception {
    settle();
    RectF[] rect = {null};
    task(() -> {
      NativeArt art = (NativeArt) field(game, "art");
      rect[0] = new NativeArt.Dialog(art.read("rez/" + layout + ".bin")).get(id).rect();
      rect[0].offset(((Integer) field(game, "logicalWidth") - 264) / 2f - 4, 32);
    });
    tap(rect[0].centerX(), rect[0].centerY());
  }

  void key(String name) throws Exception {
    for (String row : NativeBridge.text(0).split("\n")) {
      String[] a = row.split("\t");
      if (a.length > 2 && a[1].startsWith(name)) {
        NativeBridge.command(2, a[0].charAt(0), 0, 0, 0);
        render(0);
        render(1);
        return;
      }
    }
    throw new Exception("Missing command " + name);
  }

  void check(boolean condition, String text) throws Exception {
    if (!condition) throw new Exception(text);
  }

  void screenshot(String name) throws Exception {
    settle();
    Thread.sleep(250);
    Bitmap b = getUiAutomation().takeScreenshot();
    if (b == null) throw new Exception("Screenshot unavailable");
    try (FileOutputStream out = new FileOutputStream(new File(output, name + ".png"))) {
      b.compress(Bitmap.CompressFormat.PNG, 100, out);
    }
    b.recycle();
    task(
        () -> {
          report.put(
              name,
              new JSONObject()
                  .put("page", field(game, "page"))
                  .put("modal", field(game, "modal"))
                  .put("failure", field(game, "failure")));
        });
    save();
  }

  void settle() throws Exception {
    long[] first = {0}; task(() -> first[0] = (Long) field(game, "renderedFrames"));
    long deadline = SystemClock.uptimeMillis() + 90000;
    do {
      boolean[] ready = {false};
      task(() -> {
        NativeGlue glue = (NativeGlue) field(game, "glue");
        ready[0] = (Boolean) field(game, "foreground")
            && (Long) field(game, "renderedFrames") >= first[0] + 2
            && field(game, "pendingScreen") == null
            && (glue == null || !glue.slide || glue.elapsed >= NativeGlue.ENTER_MS);
      });
      if (ready[0]) return;
      Thread.sleep(100);
    } while (SystemClock.uptimeMillis() < deadline);
    throw new Exception("Screen did not finish rendering/transitioning (check emulator System UI)");
  }

  void save() throws Exception {
    try (FileOutputStream f = new FileOutputStream(new File(output, "report.json"))) {
      f.write(report.toString(2).getBytes("UTF-8"));
    }
  }

  @Override
  public void onCreate(Bundle args) {
    super.onCreate(args);
    getTargetContext().getSharedPreferences("native-settings",0).edit().putBoolean("show-tips",false).apply();
    start();
  }

  @Override
  public void onStart() {
    Bundle result = new Bundle();
    try {
      output = new File(getTargetContext().getFilesDir(), "native-validation");
      output.mkdirs();
      for (File old : output.listFiles()) old.delete();
      report.put("version", getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest", 0).versionName);
      report.put("android", Build.VERSION.RELEASE);
      report.put("abi", Build.SUPPORTED_ABIS[0]);
      recordPackageHashes();
      Intent launch =
          new Intent(getTargetContext(), MainActivity.class)
              .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
      MainActivity a = (MainActivity) startActivitySync(launch);
      game = (NativeSurface) field(a, "game");
      check(game != null, "Imported core files unavailable");
      task(() -> check(field(game, "art") != null, "Native art did not initialize"));
      screenshot("title");
      glueTap(3);
      task(() -> check(field(game, "modal").equals("choose"), "Single Player tap failed"));
      screenshot("chooser");
      task(
          () -> {
            set(game, "expansion", true);
            call(game, "showCampaign", new Class<?>[0]);
          });
      screenshot("broodwar");
      task(
          () -> {
            JSONArray missions = (JSONArray) field(game, "missions");
            for (int i = 0; i < missions.length(); i++)
              if (missions.getJSONObject(i).getInt("code") == 102) {
                call(
                    game,
                    "loadMission",
                    new Class<?>[] {JSONObject.class},
                    missions.getJSONObject(i));
                break;
              }
            check(
                (Boolean) field(game, "activeGame"),
                "Mission did not initialize: " + field(game, "failure"));
            call(game, "showBriefing", new Class<?>[0]);
          });
      screenshot("briefing");
      RectF[] briefBox = {null};
      task(() -> {
        NativeGlue glue = (NativeGlue) field(game, "glue");
        check(!glue.dialogue.fallback && glue.dialogue.height > glue.small.height,
            "Original briefing font missing: height=" + glue.dialogue.height);
        report.put("briefingFontHeight", glue.dialogue.height);
        briefBox[0] = glue.layout.get(65526).rect();
      });
      long drag = SystemClock.uptimeMillis();
      touch(MotionEvent.ACTION_DOWN, briefBox[0].centerX(), briefBox[0].bottom - 10, drag, drag);
      touch(MotionEvent.ACTION_MOVE, briefBox[0].centerX(), briefBox[0].top + 10, drag, drag + 200);
      touch(MotionEvent.ACTION_UP, briefBox[0].centerX(), briefBox[0].top + 10, drag, drag + 240);
      task(() -> {
        check((Float) field(game, "briefManual") >= 0, "Briefing drag did not scroll");
        report.put("briefingDrag", true);
      });
      task(
          () -> {
            call(game, "startMission", new Class<?>[0]);
            NativeBridge.command(17, 9000, 9000, 0, 0);
            render(24);
            select("Hatchery");
            check(NativeBridge.text(0).contains("Lair"), "Missing Lair command");
          });
      screenshot("hatchery");
      task(
          () -> {
            select("Larva");
            check(NativeBridge.text(0).contains("Mutalisk\t0"), "Locked Mutalisk missing");
          });
      screenshot("larva");
      commandTap("Mutalisk");
      task(() -> {
        check(NativeBridge.value(1, 0) == 35, "Disabled unit command executed");
        check(((String) field(game, "hint")).contains("Spire"), "Locked Mutalisk command has no Spire requirement");
        report.put("disabledCommandTouch", true);
      });
      commandTap("Drone");
      task(
          () -> {
            render(5);
            select("Egg");
            check(NativeBridge.value(4, 0) == 41, "Egg target missing");
          });
      screenshot("egg");
      task(
          () -> {
            set(game, "modal", "menu");
          });
      screenshot("egg-paused");
      menuTap("gamemenu", 3);
      task(() -> check(field(game, "modal").equals("options"), "Options tap failed"));
      screenshot("options");
      task(() -> {
        set(game, "modal", "");
        NativeBridge.command(6, 0, 0, 0, 0);
        NativeBridge.command(7, 0, 0, 0, 0);
        render(5);
        select("Young Chrysalis");
        check(NativeBridge.text(4).isEmpty(), "Chrysalis still has armor details");
      });
      screenshot("chrysalis");
      task(() -> select("Hatchery"));
      screenshot("hatchery-before-morph");
      commandTap("Lair");
      task(() -> {
        NativeBridge.command(10, 1, 0, 0, 0);
        render(180);
        select("Lair");
        report.put("lairMorphTouch", true);
        NativeBridge.command(10, 0, 0, 0, 0);
      });
      screenshot("lair");
      task(() -> {
        NativeAudio audio = (NativeAudio) field(game, "audio");
        android.media.AudioTrack track = (android.media.AudioTrack) field(audio, "track");
        check(track != null && track.getPlayState() == android.media.AudioTrack.PLAYSTATE_PLAYING,
            "AudioTrack not playing");
        report.put("audioTrackPlaying", true);
        call(game, "sfx", new Class<?>[] {String.class}, "youwin");
        check(NativeBridge.playing(59), "Victory cue not scheduled");
        short[] samples = new short[16384]; NativeBridge.mix(samples, 48000);
        int nonzero = 0; for (short sample : samples) if (sample != 0) nonzero++;
        check(nonzero > 100, "Native audio mixer silent");
        report.put("mixedNonzeroSamples", nonzero);
      });
      task(
          () -> {
            set(game, "modal", "");
            NativeBridge.command(13, 1, 0, 0, 0);
          });
      screenshot("victory");
      task(() -> call(game, "showResults", new Class<?>[0]));
      screenshot("results");
      task(() -> call(game, "startSkirmish", new Class<?>[] {int.class, File.class}, 1, null));
      for (int i = 0; i < 4; i++) task(() -> render(600));
      task(
          () -> {
            check(NativeBridge.value(8, 0) >= 2400, "Bot game did not advance");
            report.put("botUnits", NativeBridge.text(10));
          });
      screenshot("skirmish");
      task(() -> {
        select("Command Center", 0);
        NativeBridge.command(17, 9000, 9000, 0, 0);
        key("SCV"); key("SCV"); key("SCV");
      });
      screenshot("terran-queue");
      task(
          () -> {
            call(game, "showTitle", new Class<?>[0]);
            call(game, "startSkirmish", new Class<?>[] {int.class, File.class}, 2, null);
            render(60);
            select("Nexus", 0);
            NativeBridge.command(15, unit("Nexus", 0), 100, 100, 0);
            render(0);
            check(NativeHud.healthColor("100/750") == 6, "Damaged health is not red");
            check(NativeBridge.text(4).split("\n")[0].split("\t")[1].equals("100"), "Shield readout incorrect");
          });
      screenshot("protoss-health-shields");
      task(() -> {
        set(game, "wide", true);
        call(game, "resizeWorld", new Class<?>[0]);
      });
      screenshot("widescreen");
      task(() -> {
        NativeHud hud = (NativeHud) field(game, "hud");
        NativePortrait portrait = hud.portrait;
        portrait.target(7, false);
        byte[] weights = hud.portraitData;
        int count = weights.length / 12, id = NativeBridge.value(11, 7);
        int[] bins = new int[4];
        for (int i = 0; i < 100; i++) bins[NativePortrait.weightedVariant(weights, count, id, (i + .5) / 100)]++;
        for (int i = 0; i < 4; i++) check(bins[i] == (weights[(8+i)*count+id] & 255), "Portrait idle weights differ");
        portrait.target(7, true);
        Bitmap b = Bitmap.createBitmap(60, 56, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(b);
        int previous = (Integer) field(portrait, "variant");
        for (int i = 0; i < 4; i++) {
          set(portrait, "elapsed", 100000.0);
          portrait.draw(c, 0, 0, 60, 56, 0, false, false);
          int choice = (Integer) field(portrait, "variant");
          check(choice != previous && choice >= 0 && choice <= 2, "Talking portrait repeats a variant");
          previous = choice;
        }
        check((b.getPixel(0, 0) >>> 24) == 255, "Portrait background is transparent");
        b.recycle();
        report.put("portraitVariantsAndOpacity", true);
      });
      game.suspend();
      task(() -> check(!(Boolean) field(game, "foreground"), "Suspend failed"));
      game.resume();
      task(() -> check((Boolean) field(game, "foreground"), "Resume failed"));
      task(
          () -> {
            call(game, "showTitle", new Class<?>[0]);
            call(game, "playIntroduction", new Class<?>[0]);
            check(
                field(game, "page").equals("movie"),
                "Cinematic did not start: " + field(game, "failure"));
            set(game, "cinematicStart", (Double) field(game, "clock") - 12000);
          });
      screenshot("cinematic");
      report.put("passed", true);
      save();
      result.putString("result", report.toString());
      finish(Activity.RESULT_OK, result);
    } catch (Throwable error) {
      try {
        report.put("passed", false);
        report.put("error", android.util.Log.getStackTraceString(error));
        save();
      } catch (Exception ignored) {
      }
      result.putString("error", android.util.Log.getStackTraceString(error));
      finish(Activity.RESULT_CANCELED, result);
    }
  }
}

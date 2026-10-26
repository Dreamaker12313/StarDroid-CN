package org.openbw.androidtest;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.RectF;
import android.media.AudioManager;
import android.os.*;
import android.view.MotionEvent;
import java.io.*;
import org.json.*;

/** Focused Android regression checks for 0.27 UI and audio changes. */
public final class NativePolishInstrumentation extends NativeInstrumentation {
  void invoke(String name) throws Exception { call(game, name, new Class<?>[0]); }
  void sound(String name) throws Exception { call(game, "sfx", new Class<?>[] {String.class}, name); }
  void music(String phase) throws Exception { call(game, "music", new Class<?>[] {String.class}, phase); }
  void passed(String name) throws Exception { report.put(name, true); save(); }
  int samples() {
    short[] pcm = new short[16384]; NativeBridge.mix(pcm, 48000);
    int count = 0; for (short s : pcm) if (s != 0) count++; return count;
  }

  @Override public void onStart() {
    Bundle result = new Bundle();
    try {
      output = new File(getTargetContext().getFilesDir(), "native-polish"); output.mkdirs();
      for (File old : output.listFiles()) old.delete();
      report.put("version", getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest", 0).versionName);
      report.put("android", Build.VERSION.RELEASE); report.put("abi", Build.SUPPORTED_ABIS[0]);
      recordPackageHashes();
      MainActivity activity = (MainActivity) startActivitySync(new Intent(getTargetContext(), MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
      game = (NativeSurface) field(activity, "game");
      check(game != null, "Native surface missing");
      task(() -> {
        set(game, "wide", false); set(game, "zoom", 1f); set(game, "muted", false);
        set(game, "effects", 1f); set(game, "music", .65f);
        invoke("syncAudio");
      });
      screenshot("title");
      task(() -> {
        NativeAudio audio = (NativeAudio) field(game, "audio");
        check(audio.canPlay(), "Initial audio focus not granted");
        NativeBridge.sound(null, 63, false); sound("youwin");
        sound("button"); sound("swishin"); sound("scorefill");
        check(NativeBridge.playing(59), "Click or transition cut off victory cue");
        check(NativeBridge.playing(58), "Transition cue missing");
        check(NativeBridge.playing(57), "Score fill cue missing");
        check(NativeBridge.playing(61), "Button cue missing");
        int audible = samples(); check(audible > 100, "Sound mixer silent");
        report.put("mixedNonzeroSamples", audible); passed("independentSoundChannels");
        audio.focus(AudioManager.AUDIOFOCUS_LOSS_TRANSIENT); invoke("syncAudio");
        check(!audio.canPlay() && samples() == 0, "Transient focus loss did not pause audio");
        check(NativeBridge.playing(59), "Pause discarded cue");
        audio.focus(AudioManager.AUDIOFOCUS_GAIN); invoke("syncAudio");
        check(audio.canPlay() && samples() > 100, "Focus gain did not restore audio");
        passed("focusLossAndResume");
        set(game, "muted", true); invoke("saveSettings");
        check(samples() == 0, "Mute did not silence mixer");
        set(game, "muted", false); invoke("saveSettings");
        passed("muteImmediate");
      });
      game.suspend();
      task(() -> {
        invoke("saveSettings");
        check(samples() == 0, "Settings update resumed background audio");
        passed("backgroundAudioStaysPaused");
      });
      game.resume(); settle();
      task(() -> {
        check(((NativeAudio) field(game, "audio")).canPlay(), "Foreground failed to reacquire audio");
        set(game, "missionRace", 0); music("briefing");
        check(field(game, "currentMusicPath").equals("music/zrdyroom.wav") && NativeBridge.playing(63), "Briefing music missing");
        music("victory"); check(field(game, "currentMusicPath").equals("music/zvict.wav"), "Victory music missing");
        music("game"); check(field(game, "currentMusicPath").equals("music/zerg1.wav"), "Automatic race music ignored");
        passed("phaseAwareMusic"); invoke("showTitle");
      });
      glueTap(3); settle();
      // The intro button lies outside the chooser. A dialog must block it.
      RectF[] hidden = {null};
      task(() -> hidden[0] = ((NativeGlue) field(game, "glue")).layout.get(8).hit());
      tap(hidden[0].centerX(), hidden[0].centerY());
      task(() -> {check(field(game, "page").equals("main") && field(game, "modal").equals("choose"), "Dialog activated underlying button"); passed("modalBlocksUnderlyingButtons"); set(game, "modal", ""); invoke("showCampaign");});
      settle();
      task(() -> {
        NativeGlue g = (NativeGlue) field(game, "glue"); double elapsed = g.elapsed;
        NativeArt.Widget w = g.layout.get(1); g.elapsed = 0; float start = Math.abs(g.shift(w));
        g.elapsed = NativeGlue.ENTER_MS / 2.; float half = Math.abs(g.shift(w));
        g.elapsed = NativeGlue.ENTER_MS; check(g.shift(w) == 0, "Menu not settled at duration");
        check(start > 0 && half < start * .2, "Menu does not decelerate quickly");
        g.elapsed = elapsed; passed("quickEaseOutMenuMotion");
        set(game, "expansion", false); call(game, "missionList", new Class<?>[] {int.class}, 1);
      });
      settle();
      RectF[] viewport = {null}; int[] selected = {0};
      task(() -> {viewport[0] = new RectF((RectF) field(game, "missionViewport")); selected[0] = (Integer) field(game, "chosenMission");});
      long now = SystemClock.uptimeMillis(); float x = viewport[0].centerX(), y = viewport[0].centerY();
      touch(MotionEvent.ACTION_DOWN, x, y, now, now);
      touch(MotionEvent.ACTION_MOVE, x, y - 17.5f, now, now + 60);
      task(() -> check(Math.abs((Float) field(game, "missionOffset") - 17.5f) < .2, "List jumps by rows instead of following touch"));
      touch(MotionEvent.ACTION_UP, x, y - 17.5f, now, now + 70);
      task(() -> {
        // Integrate a fixed interval on the same render worker to check decay independently of emulator speed.
        set(game, "listVelocity", .5f); set(game, "missionOffset", 20f);
        call(game, "advanceLists", new Class<?>[] {double.class}, 95.);
        float offset = (Float) field(game, "missionOffset"), velocity = (Float) field(game, "listVelocity");
        check(offset > 55 && offset < 60 && velocity > .28 && velocity < .31, "List inertia incorrect");
        call(game, "advanceLists", new Class<?>[] {double.class}, 950.);
        check(Math.abs((Float) field(game, "listVelocity")) < .012, "List takes too long to stop");
        check((Integer) field(game, "chosenMission") == selected[0], "Scroll selected a mission");
        passed("pixelScrollWithSmoothInertia");
      });
      screenshot("missions-scrolled");
      task(() -> {
        set(game, "modal", "");
        JSONArray missions = (JSONArray) field(game, "missions");
        for (int i = 0; i < missions.length(); i++) if (missions.getJSONObject(i).getInt("code") == 102) {
          call(game, "loadMission", new Class<?>[] {JSONObject.class}, missions.getJSONObject(i)); invoke("showBriefing"); return;
        }
        throw new Exception("Zerg mission 2 unavailable");
      });
      settle();
      task(() -> {
        NativeCampaign campaign = (NativeCampaign) field(game, "campaign");
        for (int i = 0; i < 100 && !NativeBridge.playing(62); i++) campaign.tick(1000);
        check(NativeBridge.playing(62), "Briefing voice did not start");
        set(game, "speechMusicGain", 1f); call(game, "tick", new Class<?>[] {double.class}, 200.);
        check((Float) field(game, "speechMusicGain") < .5f, "Music did not fade beneath speech");
        NativeBridge.sound(null, 62, false); set(game, "modal", "message");
        call(game, "tick", new Class<?>[] {double.class}, 1000.);
        check((Float) field(game, "speechMusicGain") > .98f, "Music did not recover after speech");
        set(game, "modal", ""); passed("briefingMusicDucking"); invoke("startMission");
      });
      settle();
      task(() -> {select("Larva"); set(game, "modal", "menu");});
      menuTap("gamemenu", 3); menuTap("options", 2); screenshot("sound");
      task(() -> check(field(game, "modal").equals("sound"), "Sound sheet did not open"));
      // Effects slider: 162 + 160 = 322; value 1/4 at x=362.
      tap(362, 146);
      task(() -> {check(Math.abs((Float) field(game, "effects") - .25f) < .025, "Sound slider did not update value"); passed("soundSliderTouch");});
      tap(400, 287); screenshot("sound-adjusted");
      task(() -> {set(game, "effects", 1f); set(game, "modal", ""); invoke("saveSettings"); NativeBridge.command(9, 0, 0, 0, 0); select("Hatchery");});
      settle();
      RectF[] command = {null};
      task(() -> {
        for (NativeHud.Hit h : ((NativeHud) field(game, "hud")).hits)
          if (h.fields != null && h.fields[1].startsWith("Lair")) command[0] = new RectF(h.rect);
        check(command[0] != null, "Lair command missing");
      });
      now = SystemClock.uptimeMillis(); x = command[0].centerX(); y = command[0].centerY();
      touch(MotionEvent.ACTION_DOWN, x, y, now, now);
      screenshot("command-pressed");
      touch(MotionEvent.ACTION_MOVE, x - 80, y, now, now + 80);
      touch(MotionEvent.ACTION_UP, x, y, now, now + 160);
      task(() -> {check(field(game, "pressedHit") == null && NativeBridge.text(0).contains("Lair"), "Drag-off executed a command"); passed("commandDragCancelsTap"); NativeBridge.command(13, 1, 0, 0, 0);});
      settle();
      task(() -> {check(field(game, "modal").equals("outcome"), "Victory modal missing"); check(!NativeBridge.playing(63), "Battle music continues over victory cue"); passed("victoryStopsBattleMusic");});
      screenshot("victory");
      game.back(); settle();
      task(() -> {check(field(game, "page").equals("results") && field(game, "currentMusicPath").equals("music/zvict.wav"), "Results music incorrect"); passed("resultsMusic"); invoke("showTitle"); invoke("saveSettings");});
      settle();
      runOnMainSync(activity::requestAppOptions);
      Thread.sleep(1800); waitForIdleSync();
      Bitmap options = getUiAutomation().takeScreenshot();
      check(options != null, "App options screenshot missing");
      try (FileOutputStream out = new FileOutputStream(new File(output, "app-options.png"))) {options.compress(Bitmap.CompressFormat.PNG, 100, out);}
      options.recycle();
      check((Boolean) field(activity, "optionsVisible"), "App options did not open");
      task(() -> {
        check(!(Boolean) field(game, "foreground") && !((NativeAudio) field(game, "audio")).canPlay(), "App options did not suspend game/audio");
        passed("appOptionsSuspendsGame");
      });
      report.put("passed", true); save(); result.putString("report", report.toString()); finish(Activity.RESULT_OK, result);
    } catch (Throwable e) {
      try {report.put("passed", false); report.put("failure", android.util.Log.getStackTraceString(e)); save();} catch (Exception ignored) {}
      result.putString("failure", android.util.Log.getStackTraceString(e)); finish(Activity.RESULT_CANCELED, result);
    }
  }
}

package org.openbw.androidtest;

import android.content.*;
import android.graphics.*;
import android.os.*;
import android.view.MotionEvent;
import java.io.*;
import java.util.*;
import org.json.*;

/** Actual Android feedback regression, separate from the shipping application. */
public final class NativeFeedbackInstrumentation extends NativeInstrumentation {
  void invoke(String name) throws Exception {call(game,name,new Class<?>[0]);}
  void pass(String name) throws Exception {report.put(name,true); save();}
  void load(int code, boolean start) throws Exception {
    task(() -> {
      JSONArray all = (JSONArray)field(game,"missions");
      for (int i=0;i<all.length();i++) if(all.getJSONObject(i).getInt("code")==code) {
        call(game,"loadMission",new Class<?>[]{JSONObject.class},all.getJSONObject(i));
        if(start) invoke("startMission");
        return;
      }
      throw new Exception("Missing mission "+code);
    }); settle();
  }
  NativeHud.Hit hit(String label) throws Exception {
    for (NativeHud.Hit h : ((NativeHud)field(game,"hud")).hits)
      if(h.fields!=null && h.fields[1].equals(label)) return h;
    throw new Exception("Missing HUD command "+label);
  }
  boolean has(String label) throws Exception {
    for(NativeHud.Hit h:((NativeHud)field(game,"hud")).hits)
      if(h.fields!=null && h.fields[1].equals(label)) return true;
    return false;
  }
  void slot(String label,int slot) throws Exception {
    RectF r=((NativeHud)field(game,"hud")).commandRect(slot,640);
    check(hit(label).rect.contains(r.centerX(),r.centerY()),label+" in wrong slot");
  }
  @Override public void onStart() {
    Bundle result = new Bundle();
    try {
      output = new File(getTargetContext().getFilesDir(),"native-feedback"); output.mkdirs();
      for(File old:output.listFiles()) old.delete();
      report.put("version",getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest",0).versionName);
      report.put("android",Build.VERSION.RELEASE); report.put("abi",Build.SUPPORTED_ABIS[0]); recordPackageHashes();
      MainActivity a=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
      game=(NativeSurface)field(a,"game"); check(game!=null,"Missing native view"); settle();
      task(() -> {
        set(game,"wide",false); set(game,"zoom",1f); set(game,"musicEnabled",true); set(game,"muted",false);
        invoke("syncAudio"); invoke("showTitle");
        short[] pcm=new short[96000]; NativeBridge.mix(pcm,48000);
        int before=NativeBridge.value(19,63); check(before>0,"Title music is silent");
        invoke("showCampaign"); int after=NativeBridge.value(19,63);
        check(after>=before,"Campaign button restarted title music");
        invoke("showTitle"); check(NativeBridge.value(19,63)>=after,"Back button restarted title music");
        pass("continuousMenuMusic"); set(game,"modal","choose");
      }); screenshot("chooser");
      task(() -> {
        set(game,"modal",""); set(game,"expansion",false); invoke("showCampaign");
        NativeGlue g=(NativeGlue)field(game,"glue"); g.elapsed=90;
        Bitmap frame=Bitmap.createBitmap(960,640,Bitmap.Config.ARGB_8888);
        call(game,"renderCanvas",new Class<?>[]{Canvas.class,double.class},new Canvas(frame),0.);
        for(int y=0;y<640;y+=16) check(frame.getPixel(5,y)==Color.BLACK && frame.getPixel(954,y)==Color.BLACK,"Menu spilled into letterbox");
        frame.recycle(); pass("menuClipsToLetterbox");
        call(game,"missionList",new Class<?>[]{int.class},1);
        ArrayList<JSONObject> rows=(ArrayList<JSONObject>)field(game,"visibleMissions");
        check(rows.get(0).optInt("code")==50,"Terran tutorial missing");
        check(rows.get(3).optString("cinematic").equals("smk/terran1.smk"),"Wasteland Patrol out of sequence");
        check(call(game,"historyLabel",new Class<?>[]{JSONObject.class},rows.get(0)).equals("Tutorial: Boot Camp"),"Tutorial label wrong");
        int[] predecessors={2,5,9,12,103,105,108,110,203,205,207,210,308,408,510};
        check(CinematicCatalog.ALL.length==predecessors.length,"Incomplete cinematic sequence");
        for(int code:predecessors)check(CinematicCatalog.after(code)!=null,"Missing intermission after "+code);
        pass("tutorialAndCinematicOrdering");
      }); screenshot("mission-list");
      load(102,false);
      task(() -> {check(field(game,"page").equals("story"),"Mission splash missing"); NativeBridge.sound(null,61,false);});
      tap(320,240);
      task(() -> {check(!NativeBridge.playing(61),"Splash tap made button sound"); pass("silentMissionSplash"); invoke("showBriefing");}); settle();
      task(() -> {
        NativeCampaign c=(NativeCampaign)field(game,"campaign");
        for(int i=0;i<100&&!c.transmission;i++)c.tick(1000);
        check(c.transmission,"Original briefing speech missing");
        NativeGlue g=(NativeGlue)field(game,"glue"); NativeArt.Widget box=g.layout.get(65526);
        List<String> lines=g.dialogue.lines(c.message,box.w);
        check(BriefingText.scroll(lines,0,c.spokenLength,box.h)==0,"Briefing starts already scrolled");
        check(BriefingText.scroll(lines,c.spokenLength,c.spokenLength,box.h)==Math.max(0,lines.size()*19-box.h),"Final caption not reached");
        set(game,"modal","message"); c.transmissionPosition=0;
        Bitmap frame=Bitmap.createBitmap(960,640,Bitmap.Config.ARGB_8888);
        call(game,"renderCanvas",new Class<?>[]{Canvas.class,double.class},new Canvas(frame),0.); frame.recycle();
        check((Float)field(game,"briefScroll")==0,"Briefing scroll advances before voice");
        pass("continuousSpeechClockCaptionScroll"); set(game,"modal",""); invoke("startMission");
        NativeBridge.command(9,0,0,0,0); select("Hatchery");
      }); settle();
      task(() -> {slot("Set Rally Point",1); check(has("Lair"),"Mission 2 Lair missing"); pass("hatcheryRallyAndLair");}); screenshot("hatchery");
      task(() -> select("Overlord")); settle();
      task(() -> {check(!has("Attack"),"Overlord has Attack"); pass("unarmedCommandCard");});
      task(() -> select("Drone")); settle(); commandTap("Move");
      task(() -> {check(!has("Cancel"),"Move displaced Burrow with Cancel"); pass("noPersistentTargetingCancel");});
      game.back(); task(() -> {}); settle(); commandTap("Build"); settle();
      task(() -> {slot("Hydralisk Den",6); pass("droneHydraliskDenSlot");}); screenshot("drone-build");
      commandTap("Cancel"); task(() -> check(!has("Hydralisk Den"),"Cancel did not leave build menu"));
      commandTap("Build"); commandTap("Hatchery"); commandTap("Cancel");
      task(() -> {check(NativeBridge.value(0,0)!=2,"Cancel did not leave building placement"); pass("touchBuildCancel"); select("Larva");}); settle();
      commandTap("Drone"); task(() -> {render(3); select("Egg");}); settle();
      task(() -> {check(NativeBridge.value(2,0)==41,"Egg target icon incorrect");pass("eggTargetIcon");}); screenshot("egg-production");
      commandTap("Cancel"); task(() -> {render(4); check(NativeBridge.value(1,0)!=36,"Egg Cancel did not restore larva");pass("touchEggCancel");});
      task(() -> {set(game,"modal","objectives");}); screenshot("objectives");
      task(() -> {set(game,"modal","tips");set(game,"startupTips",false);}); screenshot("tips");
      int[] oldTip={0};task(() -> oldTip[0]=(Integer)field(game,"tipIndex"));tap(440,262);
      task(() -> {check((Integer)field(game,"tipIndex")!=oldTip[0],"Tips navigation broken");pass("tipsNavigation");set(game,"modal","");});
      task(() -> {select("Drone");}); settle();
      task(() -> {
        NativeCampaign campaign=(NativeCampaign)field(game,"campaign"); campaign.talking=-1;
        NativePortrait p=((NativeHud)field(game,"hud")).portrait;
        int first=(Integer)field(p,"selection");
        int next=-1;for(String row:NativeBridge.text(10).split("\n")){String[] u=row.split("\t");if(u.length>2&&u[1].equals("Drone")&&Integer.parseInt(u[2])==3&&Integer.parseInt(u[0])!=first){next=Integer.parseInt(u[0]);break;}}
        check(next>=0,"Second Drone fixture absent");NativeBridge.command(14,next,0,0,0);render(0);
        Bitmap canvas=Bitmap.createBitmap(960,640,Bitmap.Config.ARGB_8888);
        call(game,"renderCanvas",new Class<?>[]{Canvas.class,double.class},new Canvas(canvas),0.); canvas.recycle();
        check((Integer)field(p,"selection")==next && ((Double)field(p,"staticStart")).doubleValue()== ((Double)field(game,"clock")).doubleValue(),"Same-type portrait transition missing");pass("portraitSelectionIdentity");
        set(game,"modal","menu");
      }); screenshot("menu");
      load(101,true); task(() -> select("Creep Colony")); settle();
      task(() -> {slot("Spore Colony",6);slot("Sunken Colony",7);check(!has("Set Rally Point"),"Colony has a producer's rally command");pass("creepColonySlots");}); screenshot("creep-colony");
      task(() -> select("Hatchery")); settle();
      task(() -> {slot("Set Rally Point",1);pass("restrictedMissionHatcheryRally");});
      long pressedAt=SystemClock.uptimeMillis();
      touch(MotionEvent.ACTION_DOWN,443,397,pressedAt,pressedAt); screenshot("menu-pressed");
      task(() -> {check(((NativeHud)field(game,"hud")).pressedButton!=null,"Menu pressed frame missing");pass("hudButtonPressedState");});
      touch(MotionEvent.ACTION_UP,443,397,pressedAt,pressedAt+100); task(() -> set(game,"modal",""));
      task(() -> {
        for(String row:NativeBridge.text(10).split("\n")){String[] u=row.split("\t");if(u.length>2&&u[1].startsWith("Mineral Field")){NativeBridge.command(14,Integer.parseInt(u[0]),0,0,0);render(0);return;}}
        throw new Exception("Mineral fixture missing");
      }); screenshot("minerals");
      task(() -> {select("Vespene Geyser",-1);}); screenshot("vespene-gas");
      task(() -> {set(game,"lastOutcome",1);invoke("showResults");}); screenshot("results");
      // Real intermission playback from the predecessor's result screen.
      load(2,true); task(() -> {set(game,"lastOutcome",1);invoke("nextMission");check(field(game,"page").equals("movie"),"Campaign skipped installed intermission");});
      screenshot("cinematic");
      task(() -> {
        ArrayList<?> buttons=(ArrayList<?>)field(game,"buttons");check(buttons.size()==1,"Cinematic has a visible Skip control");
        NativeBridge.sound(null,61,false); invoke("finishCinematic");
        check((Integer)field(game,"missionCode")==3,"Intermission did not continue to mission 3");
        pass("cinematicToNextMission"); check(field(game,"failure").equals(""),"Runtime error: "+field(game,"failure"));
      });
      report.put("passed",true);save();result.putString("result",report.toString());finish(-1,result);
    } catch(Throwable error) {
      try{report.put("passed",false);report.put("error",android.util.Log.getStackTraceString(error));save();}catch(Exception ignored){}
      result.putString("error",android.util.Log.getStackTraceString(error));finish(0,result);
    }
  }
}

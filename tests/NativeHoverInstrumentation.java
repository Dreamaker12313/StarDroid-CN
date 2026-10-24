package org.openbw.androidtest;

import android.content.*;
import android.graphics.*;
import android.os.*;
import java.io.*;
import java.util.*;

/** Asset-independent Android interaction checks, using the shipped UI classes. */
public final class NativeHoverInstrumentation extends NativeInstrumentation {
  void pass(String name) throws Exception {report.put(name,true);save();}
  NativeHud.Hit hit(String name, float left, int minerals, int gas, int supply) {
    NativeHud.Hit h=new NativeHud.Hit();h.rect=new RectF(left,380,left+36,416);
    h.fields=new String[15];Arrays.fill(h.fields,"");
    h.fields[0]=name.substring(0,1);h.fields[1]=name;h.fields[2]="1";h.fields[3]="38";
    h.fields[4]=""+minerals;h.fields[5]=""+gas;h.fields[6]="1";
    h.fields[11]="-1";h.fields[12]="-1";h.fields[14]=""+supply;return h;
  }
  void clickChoice(int index) throws Exception {
    Bitmap bitmap=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);
    call(game,"drawModal",new Class<?>[]{Canvas.class},new Canvas(bitmap));
    List<?> buttons=(List<?>)field(game,"buttons");check(buttons.size()==3,"Chooser needs Original, Expansion, Cancel");
    ((Runnable)field(buttons.get(index),"action")).run();bitmap.recycle();
  }
  @Override public void onStart() {
    Bundle result=new Bundle();
    try {
      output=new File(getTargetContext().getExternalFilesDir(null),"native-hover");output.mkdirs();
      recordPackageHashes();report.put("version",getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest",0).versionName);report.put("android",Build.VERSION.RELEASE);
      report.put("abi",Build.SUPPORTED_ABIS[0]);report.put("originalGameAssets",false);
      List<NativeHud.Hit> hits=new ArrayList<>();
      NativeHud.Hit a=hit("Hydralisk",500,75,25,2), b=hit("Drone",545,50,0,2);hits.add(a);hits.add(b);
      a.fields[8]="Ground unit. Attacks ground and air targets.";
      String info=CommandHint.describe(a.fields,"");
      check(info.contains("75 minerals · 25 Vespene Gas · 1 supply")&&info.contains(a.fields[8]),"Unit cost/supply/description missing");
      b.fields[14]="1";check(CommandHint.describe(b.fields,"").contains("0.5 supply"),"Half supply lost");
      b.fields[14]="2";b.fields[6]="0";
      check(CommandHint.describe(b.fields,"").endsWith("Not enough minerals"),"Resource shortage absent");
      b.fields[6]="1";pass("unitPricesSupplyAndDescriptions");
      CommandHover pointer=new CommandHover();pointer.hover(510,390,false);
      check(pointer.tooltip(hits,0)==a,"Mouse/stylus hover not immediate");
      NativeHud.Hit updated=hit("Hydralisk",500,100,50,2);hits.set(0,updated);
      check(pointer.tooltip(hits,1)==updated,"Hover retains obsolete command/cost after redraw");
      pointer.hover(510,390,true);check(pointer.tooltip(hits,2)==null,"Hover exit keeps tooltip");
      pass("hoverUsesCurrentCardAndExits");
      pointer.begin(updated,510,390,1000);check(pointer.tooltip(hits,1219)==null,"Hold triggers too early");
      check(pointer.tooltip(hits,1220)==updated,"Short hold does not inspect");
      check(pointer.release(hits,510,390,1221)==null,"Inspection release issued an order");
      // A delayed renderer must not turn a long press into an order.
      pointer.begin(updated,510,390,2000);
      check(pointer.release(hits,510,390,2220)==null,"Long press activates before next render");
      pointer.begin(updated,510,390,3000);
      check(pointer.release(hits,510,390,3100)==updated,"Quick tap no longer activates");
      pass("holdNeverActivatesButQuickTapDoes");
      pointer.begin(updated,510,390,4000);pointer.move(555,390,4300,10);
      check(pointer.tooltip(hits,4300)==b,"Hold and slide cannot inspect another button");
      pointer.move(450,350,4350,10);check(pointer.tooltip(hits,4350)==null,"Outside HUD still shows hovered button");
      pointer.move(555,390,4400,10);check(pointer.tooltip(hits,4400)==b,"Inspection cannot reenter HUD");
      check(pointer.release(hits,555,390,4450)==null,"Slide inspection issues an order");
      pass("holdSlideInspectionAcrossButtons");
      pointer.begin(updated,510,390,5000);pointer.move(555,390,5100,10);
      check(pointer.release(hits,555,390,5150)==null,"Early drag activates adjacent command");
      pointer.begin(updated,510,390,6000);hits.set(0,hit("Stop",500,0,0,0));
      check(pointer.release(hits,510,390,6100)==null,"Selection change activates a different command");
      pointer.begin(b,555,390,7000);pointer.cancel();
      check(pointer.tooltip(hits,7500)==null&&pointer.release(hits,555,390,7600)==null,"Canceled gesture survives");
      pass("dragSelectionChangeAndCancelSafety");
      MainActivity activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
      waitForIdleSync();
      runOnMainSync(() -> {game=new NativeSurface(activity);game.shutdown();});
      Thread worker=(Thread)field(game,"worker");worker.join(15000);check(!worker.isAlive(),"Test surface worker still running");
      set(game,"art",new NativeArt());set(game,"page","main");set(game,"logicalWidth",640);
      ((Set<?>)field(game,"availableMovies")).clear();
      SharedPreferences prefs=activity.getSharedPreferences("native-settings",0);
      boolean saved=prefs.getBoolean("expansion",false);
      try {
        prefs.edit().putBoolean("expansion",true).commit();set(game,"expansion",true);
        call(game,"playIntroduction",new Class<?>[]{});
        check(field(game,"modal").equals("intro-choose"),"Intro skips the game chooser");
        clickChoice(0);
        check(field(game,"hint").toString().contains("StarCraft.mpq")&&!field(game,"hint").toString().contains("BroodWar.mpq"),"Original choice points to wrong archive");
        check((Boolean)field(game,"expansion")&&prefs.getBoolean("expansion",false),"Intro changes campaign selection");
        prefs.edit().putBoolean("expansion",false).commit();set(game,"expansion",false);
        call(game,"playIntroduction",new Class<?>[]{});clickChoice(1);
        check(field(game,"hint").toString().contains("BroodWar.mpq"),"Expansion choice points to wrong archive");
        check(!(Boolean)field(game,"expansion")&&!prefs.getBoolean("expansion",true),"Expansion intro changes campaign selection");
        call(game,"playIntroduction",new Class<?>[]{});clickChoice(2);
        check(field(game,"modal").equals(""),"Intro cancel does not return to menu");
      } finally {prefs.edit().putBoolean("expansion",saved).commit();}
      pass("introChooserOriginalExpansionCancelAndCampaignPreference");
      report.put("cinematicPlaybackTested",false);report.put("originalChooserArtworkTested",false);
      report.put("passed",true);save();result.putString("stream","PASS native hover and intro chooser\n");finish(-1,result);
    } catch(Throwable e) {
      try {report.put("passed",false);report.put("error",android.util.Log.getStackTraceString(e));save();}catch(Exception ignored){}
      result.putString("stream",android.util.Log.getStackTraceString(e));finish(0,result);
    }
  }
}

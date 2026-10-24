package org.openbw.androidtest;

import android.content.*;
import android.graphics.*;
import android.os.*;
import android.view.MotionEvent;
import java.io.*;
import java.util.*;
import org.json.*;

/** Production menu, preferences, gesture dispatch, error feedback and splash text. */
public final class NativeControlsInstrumentation extends NativeInstrumentation {
  private Bundle args;
  @Override public void onCreate(Bundle b) { args=b;super.onCreate(b); }
  void pass(String key) throws Exception { report.put(key,true);save(); }
  void direct(int action,float x,float y,long start,long time) throws Exception {
    MotionEvent e=MotionEvent.obtain(start,time,action,x,y,0);
    try {call(game,"touch",new Class<?>[]{MotionEvent.class},e);}finally{e.recycle();}
  }
  void canvas(String modal,String name) throws Exception {
    set(game,"modal",modal);((List<?>)field(game,"buttons")).clear();
    Bitmap b=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);
    call(game,"renderCanvas",new Class<?>[]{Canvas.class,double.class},new Canvas(b),0d);
    if(name!=null)try(FileOutputStream out=new FileOutputStream(new File(output,name+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,out);}
    b.recycle();
  }
  void menuChoice(int n) throws Exception {
    List<?> buttons=(List<?>)field(game,"buttons");
    // renderCanvas also registers HUD controls. Use drawClassicMenu by itself.
    buttons.clear();Bitmap b=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);
    call(game,"drawClassicMenu",new Class<?>[]{Canvas.class},new Canvas(b));b.recycle();
    ((Runnable)field(buttons.get(n),"action")).run();
  }
  @Override public void onStart() {
    Bundle result=new Bundle();SharedPreferences prefs=null;String old=null;
    try {
      output=new File(getTargetContext().getExternalFilesDir(null),"native-controls40");output.mkdirs();
      recordPackageHashes();report.put("version",getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest",0).versionName);
      MainActivity activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
      waitForIdleSync();runOnMainSync(()->{game=new NativeSurface(activity);game.shutdown();});
      ((Thread)field(game,"worker")).join(15000);
      check(!((Thread)field(game,"worker")).isAlive(),"Test engine worker did not stop");
      prefs=activity.getSharedPreferences("native-settings",0);old=prefs.getString("touch-controls",null);
      String dir=args.getString("dataDir");String[] core={"StarDat.mpq","BrooDat.mpq","patch_rt.mpq"};
      for(int i=0;i<3;i++)NativeBridge.open(i,new File(dir,core[i]).getPath());
      File map=new File(output,"weave.scx");try(InputStream in=activity.getAssets().open("native/weave.scx");FileOutputStream out=new FileOutputStream(map)){out.write(NativeData.read(in,4000000));}
      NativeBridge.open(3,map.getPath());NativeBridge.command(20,-1,0,0,0);NativeBridge.init(640,480,0,1);
      NativeBridge.frame(null,24,1008);
      NativeArt art=new NativeArt();JSONObject commands=new JSONObject(new String(NativeData.read(activity.getAssets().open("native/commands.json"),262144),"UTF-8"));
      NativeHud hud=new NativeHud(art,1,commands);
      report.put("originalFontAvailable",!hud.large.fallback);
      report.put("fontSource",hud.large.fallback?"Readable fallback; supplied core font payload is not a FONT file":"Original FONT asset");
      set(game,"art",art);set(game,"hud",hud);set(game,"commandMaps",commands);set(game,"page","game");
      set(game,"logicalWidth",640);set(game,"physicalWidth",640);set(game,"physicalHeight",480);
      set(game,"activeGame",true);set(game,"world",Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888));
      ControlSettings c=(ControlSettings)field(game,"controls");c.preset("Comfortable");call(game,"applyControls",new Class<?>[]{});
      canvas("controls","touch-controls");menuChoice(0);check(field(game,"modal").equals("control-select"),"Selection settings did not open");
      check(c.radius==28&&c.holdMs==180,"Comfortable defaults changed");
      canvas("control-select","selection-settings");menuChoice(1);check(c.holdMs==230&&c.preset.equals("Custom"),"Hold setting does not change");
      canvas("control-camera","camera-settings");menuChoice(0);check(c.panSpeed==1.25f,"Pan setting does not change");
      canvas("control-orders","command-settings");menuChoice(1);check(!c.attackTap,"Move-tap setting does not change");
      ControlSettings loaded=new ControlSettings();loaded.load(prefs);
      check(loaded.holdMs==230&&loaded.panSpeed==1.25f&&!loaded.attackTap&&loaded.preset.equals("Custom"),"Custom preferences were not saved");
      pass("menusCustomizationAndPersistence");
      c.preset("Comfortable");call(game,"applyControls",new Class<?>[]{});set(game,"modal","");
      ((List<?>)field(game,"buttons")).clear();hud.hits.clear();hud.minimap.setEmpty();
      direct(0,300,200,1000,1000);direct(2,350,200,1000,1080);check(field(game,"gesture").equals("pan"),"Quick drag is not pan");direct(3,350,200,1000,1090);
      direct(0,300,200,2000,2000);direct(2,350,200,2000,2200);check(field(game,"gesture").equals("box"),"Short hold does not box-select");direct(3,350,200,2000,2210);
      c.preset("Drag to select");call(game,"applyControls",new Class<?>[]{});
      direct(0,300,200,3000,3000);direct(2,350,200,3000,3080);check(field(game,"gesture").equals("box"),"Immediate drag-select preset ignored");direct(3,350,200,3000,3090);
      c.holdMs=500;c.dragMode=0;
      direct(0,300,200,4000,4000);direct(2,350,200,4000,4300);check(field(game,"gesture").equals("pan"),"Custom hold threshold ignored");direct(3,350,200,4000,4310);
      pass("actualPanAndSelectionGestureDispatch");
      c.preset("Comfortable");call(game,"applyControls",new Class<?>[]{});
      check(!c.groundOrders&&c.selectionButton==1&&!c.controlGroups,"New defaults are not disabled ground orders / left cursor / hidden groups");
      canvas("control-orders",null);menuChoice(0);check(c.groundOrders,"Ground-order opt-in does not change setting");menuChoice(0);check(!c.groundOrders,"Ground-order disable does not persist");
      canvas("control-select",null);menuChoice(6);check(c.selectionButton==2,"Selection button cannot be placed right");menuChoice(6);check(c.selectionButton==0,"Selection button cannot be disabled");menuChoice(6);check(c.selectionButton==1,"Selection button cannot be placed left");
      set(game,"modal","");((List<?>)field(game,"buttons")).clear();
      Bitmap selection=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);
      call(game,"drawSelectionButton",new Class<?>[]{Canvas.class},new Canvas(selection));
      List<?> cursorButtons=(List<?>)field(game,"buttons");check(cursorButtons.size()==1,"Missing one-shot cursor button");
      RectF cursor=(RectF)field(cursorButtons.get(0),"rect");check(cursor.left==8,"Cursor is not on left");
      ((Runnable)field(cursorButtons.get(0),"action")).run();check((Boolean)field(game,"oneShotSelect"),"Cursor did not arm selection");
      cursorButtons.clear();hud.hits.clear();hud.minimap.setEmpty();
      direct(0,300,200,6000,6000);direct(2,350,220,6000,6030);check(field(game,"gesture").equals("box"),"Armed selection still requires long press");direct(1,350,220,6000,6070);
      check(!(Boolean)field(game,"oneShotSelect"),"One-shot selection remained armed");
      c.selectionButton=2;call(game,"applyControls",new Class<?>[]{});cursorButtons.clear();call(game,"drawSelectionButton",new Class<?>[]{Canvas.class},new Canvas(selection));
      check(((RectF)field(cursorButtons.get(0),"rect")).right==632,"Cursor is not on right");selection.recycle();
      ControlSettings reloaded=new ControlSettings();reloaded.load(prefs);check(!reloaded.groundOrders&&reloaded.selectionButton==2,"New controls are not persistent");
      pass("oneShotCursorBothSidesAndGroundTapDefault");
      c.commandModeButton=true;c.attackTap=true;c.selectionButton=1;call(game,"applyControls",new Class<?>[]{});
      Bitmap modes=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);
      for(int side:new int[]{1,2}){
        c.selectionButton=side;cursorButtons.clear();
        call(game,"drawCommandModeButton",new Class<?>[]{Canvas.class},new Canvas(modes));
        check(cursorButtons.size()==1,"Attack/move toggle missing");
        RectF r=(RectF)field(cursorButtons.get(0),"rect");
        check(r.bottom<=202&&(side==1?r.left==8:r.right==632),"Mode toggle position or spacing incorrect");
        boolean before=c.attackTap;((Runnable)field(cursorButtons.get(0),"action")).run();
        check(c.attackTap!=before&&!c.groundOrders,"Mode toggle changed ground-order opt-in");
        reloaded.load(prefs);check(reloaded.attackTap==c.attackTap,"Tap mode not persistent");
      }
      check(!hud.icon(228,0).sameAs(hud.icon(230,0)),"Attack and move icons are the same");
      c.commandModeButton=false;cursorButtons.clear();call(game,"drawCommandModeButton",new Class<?>[]{Canvas.class},new Canvas(modes));check(cursorButtons.isEmpty(),"Mode toggle cannot be hidden");
      c.commandModeButton=true;c.selectionButton=1;modes.recycle();
      pass("attackMoveToggleOriginalIconsBothSidesAndPreferences");
      canvas("video",null);menuChoice(5);check((Integer)field(game,"resourcePercent")==125,"Resource size 125% unavailable");
      menuChoice(5);check((Integer)field(game,"resourcePercent")==150&&prefs.getInt("resource-percent",0)==150,"Resource size 150% not saved");
      c.controlGroups=true;canvas("","larger-resources-and-top-groups");
      set(game,"resourcePercent",100);c.controlGroups=false;
      pass("largerResourceIconsAndTextSetting");

      canvas("control-select",null);menuChoice(7);check(c.controlGroups,"Control groups cannot be enabled");
      reloaded.load(prefs);check(reloaded.controlGroups,"Control group preference not saved");
      canvas("control-help","gesture-guide");
      set(game,"modal","");select("SCV",0);
      List<?> groupButtons=(List<?>)field(game,"buttons");groupButtons.clear();
      Bitmap groupImage=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);
      call(game,"drawControlGroups",new Class<?>[]{Canvas.class},new Canvas(groupImage));
      check(groupButtons.size()==10,"Expected ten group buttons");
      RectF groupRect=(RectF)field(groupButtons.get(0),"rect");
      check(groupRect.top==2&&groupRect.right<=36,"Control group bar is not at the top");
      direct(0,groupRect.centerX(),groupRect.centerY(),10000,10000);direct(1,groupRect.centerX(),groupRect.centerY(),10000,10500);
      check(NativeBridge.value(21,1)==1,"Holding group does not assign selection");
      select("Command Center",0);direct(0,groupRect.centerX(),groupRect.centerY(),11000,11000);direct(1,groupRect.centerX(),groupRect.centerY(),11000,11060);
      check(NativeBridge.value(1,0)==7,"Tapping group did not recall SCV");
      select("Command Center",0);direct(0,groupRect.centerX(),groupRect.centerY(),12000,12000);direct(3,groupRect.centerX(),groupRect.centerY(),12000,12600);
      check(NativeBridge.value(21,1)==1,"Cancelled hold reassigned group");
      c.controlGroups=false;groupButtons.clear();call(game,"drawControlGroups",new Class<?>[]{Canvas.class},new Canvas(groupImage));
      check(groupButtons.isEmpty(),"Disabled groups remain touchable");groupImage.recycle();
      pass("optionalGroupButtonsHoldAssignTapRecallCancelAndPersistence");
      canvas("misc","miscellaneous-settings");menuChoice(0);check(!(Boolean)field(game,"nearbyDefenders")&&NativeBridge.value(20,0)==0,"Defender toggle does not reach engine");
      menuChoice(0);check((Boolean)field(game,"nearbyDefenders")&&NativeBridge.value(20,0)==1,"Defenders cannot be re-enabled");menuChoice(1);check(field(game,"modal").equals("testing"),"Testing cheats are not in Miscellaneous");
      pass("miscellaneousDefenderToggleAndCheats");set(game,"modal","");

      CommandHover hover=new CommandHover();NativeHud.Hit h=new NativeHud.Hit();h.rect=new RectF(10,10,40,40);h.help="Test";
      List<NativeHud.Hit> hits=Arrays.asList(h);hover.holdMs=600;hover.begin(h,20,20,1000);
      check(hover.tooltip(hits,1599)==null&&hover.tooltip(hits,1600)==h,"Custom description delay ignored");
      check(hover.release(hits,20,20,1700)==null,"Description long press activates command");
      hover.enabled=false;hover.begin(h,20,20,2000);check(hover.tooltip(hits,3000)==null&&hover.release(hits,20,20,3000)==h,"Disabling inspection prevents command activation");
      pass("customTooltipDelayAndDisable");
      // Full HUD touch -> JNI -> original advisor -> PCM, with no minerals.
      c.preset("Comfortable");call(game,"applyControls",new Class<?>[]{});NativeBridge.command(17,0,0,0,0);
      select("Command Center",0);canvas("",null);NativeHud.Hit train=null;
      for(NativeHud.Hit x:hud.hits)if(x.fields!=null&&x.fields[1].equals("SCV"))train=x;
      check(train!=null,"SCV command missing from HUD");
      direct(0,train.rect.centerX(),train.rect.centerY(),5000,5000);direct(1,train.rect.centerX(),train.rect.centerY(),5000,5070);
      NativeBridge.frame(null,0,2000);check(NativeBridge.text(8).contains("Not enough minerals"),"Touch does not report insufficient minerals");
      short[] pcm=new short[48000];NativeBridge.mix(pcm,24000);int nonzero=0;for(short n:pcm)if(n!=0)++nonzero;
      check(nonzero>100,"Resource failure produces silent PCM");pass("unaffordableUnitTouchMessageAndAudio");
      // Use production splash drawing and whichever font the supplied assets support.
      Class<?> type=Class.forName("org.openbw.androidtest.NativeSurface$StoryPage");
      java.lang.reflect.Constructor<?> constructor=type.getDeclaredConstructor();constructor.setAccessible(true);Object story=constructor.newInstance();
      NativeArt.Font font=hud.large.withShadedColor(0xff30e050);set(story,"font",font);set(story,"text","Eye of the Storm\nHigh orbit over Aiur");
      set(story,"background",Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888));
      List list=(List)field(game,"story");list.clear();list.add(story);set(game,"storyTime",1000d);set(game,"storyIndex",0);
      Bitmap splash=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);call(game,"drawStory",new Class<?>[]{Canvas.class},new Canvas(splash));
      int green=0,minY=480,maxY=0;Set<Integer> tones=new HashSet<>();
      for(int y=0;y<480;y++)for(int x=0;x<640;x++){int rgb=splash.getPixel(x,y);if(Color.green(rgb)>Color.red(rgb)*2&&Color.green(rgb)>Color.blue(rgb)*2){green++;minY=Math.min(y,minY);maxY=Math.max(y,maxY);tones.add(rgb);}}
      check(green>100&&maxY-minY>=40&&tones.size()>1,"Splash font is not larger, shaded green");
      try(FileOutputStream out=new FileOutputStream(new File(output,"mission-splash.png"))){splash.compress(Bitmap.CompressFormat.PNG,100,out);}splash.recycle();
      pass("largerGreenShadedMissionFont");
      check(commands.getJSONObject("orderIcons").getInt("Load")==309&&commands.getJSONObject("orderIcons").getInt("Unload")==312,"Cargo icons differ from original orders.dat");
      check(hud.icon(309,0)!=null&&hud.icon(312,0)!=null,"Original cargo icons unavailable");pass("originalLoadUnloadIcons");
      check(CommandSlots.override(51,"Consume",0)==5&&CommandSlots.override(51,"Cloak",0)==6&&CommandSlots.override(51,"Decloak",0)==6&&CommandSlots.override(51,"Ensnare",0)==7&&CommandSlots.override(51,"Psionic Storm",0)==8,"Kerrigan slots do not match reference");
      pass("kerriganReferenceSlots");
      int layouts=0;
      for(boolean lower:new boolean[]{false,true})for(int rows:new int[]{1,8,13,20,32,48})for(int width:new int[]{3,12,24}){
        StringBuilder text=new StringBuilder();for(int row=0;row<rows;row++){for(int word=0;word<width;word++)text.append("text ");text.append('\n');}
        StoryLayout fit=StoryLayout.fit(font,text.toString(),lower);
        check(fit.top>=31.99f&&fit.top+fit.height<=448.01f,"Opening text exceeds vertical safe area");
        for(String line:font.lines(text.toString(),fit.width))check(font.measure(line)*fit.scale<=576.01f,"Opening text exceeds horizontal safe area");
        layouts++;
      }
      check(StoryLayout.fit(font,"A short opening",false).scale==1.5f,"Short splash unnecessarily shrunk");
      report.put("splashStressLayouts",layouts).put("originalMissionOpeningTextsAvailable",false);pass("splashFitsWithoutClipping");
      set(game,"zoom",1f);set(game,"wide",false);call(game,"resizeWorld",new Class<?>[]{});
      NativeBridge.command(11,0,0,0,0);
      NativeBridge.command(3,0,65536,0,0);
      NativeBridge.frame((Bitmap)field(game,"world"),0,10000);
      c.controlGroups=true;set(game,"resourcePercent",150);
      canvas("","map-bottom-center-edge");
      pass("realWorldRenderedAtBottomWithLargerHud");

      hud.close();NativeBridge.close();report.put("passed",true);save();result.putString("result","PASS controls and feedback");
    } catch(Throwable e){try{report.put("passed",false).put("error",android.util.Log.getStackTraceString(e));save();}catch(Exception ignored){}result.putString("error",e.toString());}
    finally {if(prefs!=null){SharedPreferences.Editor e=prefs.edit();if(old==null)e.remove("touch-controls");else e.putString("touch-controls",old);e.commit();}}
    finish(report.optBoolean("passed")?0:1,result);
  }
}

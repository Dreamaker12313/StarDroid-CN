package org.openbw.androidtest;

import android.content.*;
import android.graphics.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;
import java.util.zip.*;

/** Android checks that can run without copyrighted game archives. */
public final class NativeRevisionInstrumentation extends NativeInstrumentation {
  void pass(String name) throws Exception {report.put(name,true);save();}
  String hint(String label, boolean enabled, int minerals, int gas, int energy, String required) {
    String[] fields=new String[14];Arrays.fill(fields,"");
    fields[1]=label;fields[2]=enabled?"1":"0";fields[4]=""+minerals;fields[5]=""+gas;fields[13]=""+energy;
    return CommandHint.describe(fields,required);
  }
  String allText(View view) {
    StringBuilder b=new StringBuilder();
    if(view instanceof TextView)b.append(((TextView)view).getText()).append('\n');
    if(view instanceof ViewGroup){ViewGroup group=(ViewGroup)view;for(int i=0;i<group.getChildCount();i++)b.append(allText(group.getChildAt(i)));}
    return b.toString();
  }
  @Override public void onStart() {
    Bundle result=new Bundle();
    try {
      output=new File(getTargetContext().getExternalFilesDir(null),"native-revision");output.mkdirs();
      recordPackageHashes();report.put("version",getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest",0).versionName);report.put("android",Build.VERSION.RELEASE);
      report.put("abi",Build.SUPPORTED_ABIS[0]);report.put("originalGameAssets",false);
      MainActivity activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
      waitForIdleSync();
      String[] text={""};
      runOnMainSync(() -> text[0]=allText(activity.getWindow().getDecorView()));
      for(String label:new String[]{"App Options","StarDroid · "+getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest",0).versionName,"Installed content","StarCraft.mpq","BroodWar.mpq","Install.exe","13 movies","4 movies"})
        check(text[0].contains(label),"Missing app/import guidance: "+label);
      pass("movieImportGuidanceAndCounts");
      check(hint("Cancel",true,0,0,0,"").equals("Cancel"),"Free cancel shows a price");
      check(hint("Move",true,0,0,0,"").equals("Move"),"Move shows a price");
      check(hint("Drone",true,50,0,0,"").equals("Drone\n50 minerals"),"Zero gas displayed");
      check(hint("Hydralisk",true,75,25,0,"").equals("Hydralisk\n75 minerals · 25 Vespene Gas"),"Mixed price missing spacing/name");
      check(hint("Storm",false,0,0,75,"").equals("Storm\n75 energy\nNot enough energy"),"Energy blocker unclear");
      check(hint("Mutalisk",false,100,100,0,"Spire").equals("Mutalisk\n100 minerals · 100 Vespene Gas\nRequires Spire"),"Requirement hint lost");
      String[] upgrade=new String[14];Arrays.fill(upgrade,"");upgrade[1]="Terran Infantry Weapons";upgrade[2]="1";
      upgrade[4]="100";upgrade[5]="100";upgrade[8]="Increases damage dealt by Terran infantry.";
      check(CommandHint.describe(upgrade,"").contains("\nIncreases damage dealt by Terran infantry."),"Upgrade description omitted");
      pass("readableCommandHints");
      List<String> lines=Arrays.asList("Equal text","Equal text","Equal text","Equal text","Equal text","Equal text","Equal text","Equal text");
      check(BriefingText.scroll(lines,0,8000,57)==0,"Caption scroll begins before speech");
      check(BriefingText.scroll(lines,2000,8000,57)==0,"First viewport not held for reading");
      float a=BriefingText.scroll(lines,2300,8000,57), b=BriefingText.scroll(lines,2400,8000,57), c=BriefingText.scroll(lines,2500,8000,57);
      check(a>0&&b>a&&c>b&&Math.abs((b-a)-(c-b))<.001f,"Caption motion has per-line jumps or pauses");
      check(BriefingText.scroll(lines,8000,8000,57)==95,"Last line not reached");
      check(BriefingText.scroll(lines,8000,8000,200)==0,"Short text scrolls unnecessarily");
      pass("continuousSpeechTimedScroll");
      for(int type:new int[]{1,16,100}) {
        check(CommandSlots.override(type,"Lockdown",6)==7,"Lockdown displaced");
        check(CommandSlots.override(type,"Cloak",6)==6&&CommandSlots.override(type,"Decloak",6)==6,"Ghost cloak overlaps Lockdown");
      }
      for(int type:new int[]{99,104}) {
        check(CommandSlots.override(type,"Lockdown",6)==7,"Duran Lockdown must be bottom centre");
        check(CommandSlots.override(type,"Cloak",6)==6&&CommandSlots.override(type,"Decloak",6)==6,"Duran cloak must be bottom left");
      }
      check(CommandSlots.override(51,"Cloak",6)==6&&CommandSlots.override(51,"Psionic Storm",6)==8
          &&CommandSlots.override(51,"Ensnare",6)==7&&CommandSlots.override(51,"Consume",6)==5,"Infested Kerrigan spell positions wrong");
      for(int type:new int[]{46,52})check(CommandSlots.override(type,"Burrow",6)==5,"Defiler burrow overlaps spells");
      pass("heroAbilitySlots");
      NativeCampaign campaign=new NativeCampaign(new byte[0],0);
      campaign.message="Briefing text";campaign.messages.add("Old dialogue");campaign.messageEnds.add(10000d);
      campaign.portraits[0]=51;campaign.talking=0;campaign.remaining=5000;campaign.transmission=true;
      campaign.enterMission();
      check(campaign.message.isEmpty()&&campaign.messages.isEmpty()&&campaign.messageEnds.isEmpty()
          &&campaign.talking==-1&&campaign.portraits[0]==-1&&!campaign.transmission&&campaign.remaining==0,"Briefing survives mission start while polling is paused");
      pass("briefingClearedBeforeMissionPause");
      int[] bg=new int[49], panel=new int[25];Arrays.fill(bg,0xff334455);Arrays.fill(panel,0xff334455);
      for(int i:new int[]{6,7,8,11,13,16,17,18})panel[i]=Color.RED;
      int[] cut=MenuPanel.foreground(panel,5,5,bg,7,7,1,1);
      check(cut[0]==0&&cut[24]==0,"Baked background still travels with panel");
      check(cut[6]==Color.RED&&cut[12]==0xff334455,"Panel frame/interior damaged");
      check(panel[0]==0xff334455,"Source artwork mutated");pass("slidingPanelBackgroundMask");
      for(int i=0;i<panel.length;i++)if(panel[i]==0xff334455)panel[i]=0x00334455;
      cut=MenuPanel.foreground(panel,5,5,bg,7,7,1,1);
      check(cut[0]==0&&cut[24]==0&&cut[6]==Color.RED,"PCX alpha difference leaks baked background");pass("panelMaskIgnoresPaletteAlpha");
      check(NativeGlue.ENTER_MS>620&&NativeGlue.ENTER_MS<=700&&NativeGlue.EXIT_MS>340&&NativeGlue.EXIT_MS<=385,"Menu slowdown outside requested small adjustment");
      pass("slightlySlowerMenuTiming");
      // Missing/corrupt optional imports are reported as absent, never as complete.
      File fixture=new File(output,"movie-fixture");fixture.mkdirs();
      try(ZipOutputStream zip=new ZipOutputStream(new FileOutputStream(new File(fixture,StoryData.MOVIES)))) {
        zip.putNextEntry(new ZipEntry("manifest.json"));zip.write(("{\"format\":\"openbw-cinematic-bundle-v1\",\"entries\":[{\"name\":\"SMK\\\\TERRAN1.SMK\",\"block\":1},{\"name\":\"smk\\\\zerg1.smk\",\"block\":2}]}").getBytes("UTF-8"));zip.closeEntry();
        zip.putNextEntry(new ZipEntry("blocks/1.bin"));zip.write(1);zip.closeEntry();
      }
      Set<String> installed=StoryData.installedMovies(fixture);
      check(installed.size()==1&&installed.contains("smk/terran1.smk"),"Movie inventory includes missing payload or mishandles names");pass("movieInventoryChecksPayloads");
      // Exercise JNI loading and the native mixer without requiring imported assets.
      short[] pcm=new short[2048];NativeBridge.mix(pcm,1024);pass("nativeLibraryAndMixerLoad");
      waitForIdleSync();
      // UiAutomation's accessibility connection may need a moment to attach.
      boolean foreground=false;String foregroundPackage="none";
      for(int attempt=0;attempt<50&&!foreground;attempt++){
        android.view.accessibility.AccessibilityNodeInfo window=getUiAutomation().getRootInActiveWindow();
        if(window!=null){foregroundPackage=String.valueOf(window.getPackageName());
          foreground=getTargetContext().getPackageName().equals(foregroundPackage);window.recycle();}
        if(!foreground)SystemClock.sleep(100);
      }
      check(foreground,"App is not the foreground accessibility window: "+foregroundPackage);
      pass("appIsForegroundWithoutSystemDialog");
      Bitmap screen=getUiAutomation().takeScreenshot();
      check(screen!=null,"Android screenshot unavailable");
      try(FileOutputStream out=new FileOutputStream(new File(output,"app-options.png"))){screen.compress(Bitmap.CompressFormat.PNG,100,out);}screen.recycle();
      runOnMainSync(() -> {ViewGroup root=(ViewGroup)activity.getWindow().getDecorView().findViewById(android.R.id.content);
        ArrayDeque<View> queue=new ArrayDeque<View>();queue.add(root);
        while(!queue.isEmpty()){View v=queue.remove();if(v instanceof ScrollView){((ScrollView)v).fullScroll(View.FOCUS_DOWN);break;}
          if(v instanceof ViewGroup){ViewGroup group=(ViewGroup)v;for(int i=0;i<group.getChildCount();i++)queue.add(group.getChildAt(i));}}
      });waitForIdleSync();SystemClock.sleep(400);
      screen=getUiAutomation().takeScreenshot();
      try(FileOutputStream out=new FileOutputStream(new File(output,"movie-guide.png"))){screen.compress(Bitmap.CompressFormat.PNG,100,out);}screen.recycle();
      report.put("passed",true);save();result.putString("result",report.toString());finish(-1,result);
    } catch(Throwable error) {
      try{report.put("passed",false);report.put("error",android.util.Log.getStackTraceString(error));save();}catch(Exception ignored){}
      result.putString("error",android.util.Log.getStackTraceString(error));finish(0,result);
    }
  }
}

package org.openbw.androidtest;

import android.app.*;
import android.content.*;
import android.os.*;
import java.io.*;
import org.json.*;

/** Actual Android command-card/placement checks complementing the all-race C++ matrix. */
public final class NativeGameplayInstrumentation extends NativeInstrumentation {
  boolean inspect;
  boolean nydusOnly;
  int owner=0;
  @Override public void onCreate(Bundle args) {
    inspect=args!=null&&"inspect".equals(args.getString("section"));
    nydusOnly=args!=null&&"nydus".equals(args.getString("section"));super.onCreate(args);
  }
  String[] row(String name) throws Exception {
    for(String line:NativeBridge.text(10).split("\n")) {String[] r=line.split("\t");if(r.length>4&&r[1].equals(name)&&Integer.parseInt(r[2])==owner)return r;}
    throw new Exception("Missing "+name);
  }
  void center(String name) throws Exception {
    String[] r=row(name);NativeBridge.command(3,-65536,-65536,0,0);NativeBridge.command(3,Math.max(0,Integer.parseInt(r[3])-240),Math.max(0,Integer.parseInt(r[4])-140),0,0);render(0);
  }
  String[] cmd(String name) throws Exception {
    for(String line:NativeBridge.text(0).split("\n")){String[] r=line.split("\t");if(r.length>2&&r[1].equals(name))return r;}throw new Exception("Missing command "+name);
  }
  @Override void commandTap(String name) throws Exception {
    task(()->{render(0);check(cmd(name)[2].equals("1"),"Command disabled: "+name);});super.commandTap(name);
  }
  void frames(int n) throws Exception {for(int i=0;i<n;i+=120){final int count=Math.min(120,n-i);task(()->render(count));}}
  void enabledInstant(boolean enabled) throws Exception {task(()->{set(game,"instant",enabled);NativeBridge.command(10,enabled?1:0,0,0,0);});}
  void preview(int x,int y) throws Exception {
    float scale=Math.min((Integer)field(game,"physicalWidth")/640f,(Integer)field(game,"physicalHeight")/480f);tap(x,y+48/scale);settle();
  }
  void placeValid() throws Exception {
    int[] site={-1,-1};task(()->{outer:for(int y=60;y<220;y+=8)for(int x=60;x<580;x+=8)if(NativeBridge.value(16,(x<<16)|y)!=0){site[0]=x;site[1]=y;break outer;}check(site[0]>=0,"No valid placement");
      int type=NativeBridge.value(1,0);if(type==7||type==41||type==64){
        String worker=type==7?"SCV":type==41?"Drone":"Probe";String[] unit=row(worker);
        java.util.regex.Matcher m=java.util.regex.Pattern.compile("camera=(\\d+),(\\d+)").matcher(NativeBridge.text(13));check(m.find(),"No camera for worker fixture");
        int wx=Integer.parseInt(m.group(1))+site[0],wy=Integer.parseInt(m.group(2))+site[1];
        NativeBridge.command(18,Integer.parseInt(unit[0]),wx,wy-(type==41?7:0),0);render(0);
      }
    });
    preview(site[0],site[1]);tap(265,282);frames(1200);
  }
  void build(String name,boolean advanced) throws Exception {
    task(()->{String worker=(Integer)field(game,"missionRace")==1?"SCV":"Drone";select(worker,owner);center(worker);
      if(worker.equals("Drone"))for(String base:new String[]{"Hive","Lair","Hatchery"})try{center(base);break;}catch(Exception ignored){}
    });commandTap(advanced?"Advanced":"Build");commandTap(name);placeValid();task(()->row(name));
  }
  void blocked(String name,String scene) throws Exception {
    int[] xy={0,0};task(()->{center(name);String[] r=row(name);java.util.regex.Matcher m=java.util.regex.Pattern.compile("camera=(\\d+),(\\d+)").matcher(NativeBridge.text(13));check(m.find(),"Missing camera");xy[0]=Integer.parseInt(r[3])-Integer.parseInt(m.group(1));xy[1]=Integer.parseInt(r[4])-Integer.parseInt(m.group(2));check(NativeBridge.value(16,(xy[0]<<16)|xy[1])==0,"Occupied site is enabled");});
    preview(xy[0],xy[1]);screenshot(scene);tap(265,282);task(()->check((Boolean)field(game,"placement"),"Disabled Build accepted blocked site"));tap(374,282);
  }
  void zergMission() throws Exception {
    task(()->{JSONArray ms=(JSONArray)field(game,"missions");for(int i=0;i<ms.length();++i)if(ms.getJSONObject(i).getInt("code")==110){call(game,"loadMission",new Class<?>[]{JSONObject.class},ms.getJSONObject(i));call(game,"startMission",new Class<?>[0]);break;}NativeBridge.command(17,50000,50000,0,0);NativeBridge.command(11,0,0,0,0);render(0);report.put("zerg10Units",NativeBridge.text(10));String[] drone=null;for(String line:NativeBridge.text(10).split("\n")){String[] r=line.split("\t");if(r.length>2&&r[1].equals("Drone")){drone=r;break;}}check(drone!=null,"No Drone in Zerg 10");owner=Integer.parseInt(drone[2]);report.put("zergOwner",owner);});
  }
  @Override public void onStart() {
    Bundle result=new Bundle();try {
      output=new File(getTargetContext().getFilesDir(),nydusOnly?"native-gameplay-nydus":"native-gameplay");output.mkdirs();for(File f:output.listFiles())f.delete();
      report.put("version",getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest",0).versionName);report.put("android",Build.VERSION.RELEASE);report.put("abi",Build.SUPPORTED_ABIS[0]);
      recordPackageHashes();
      report.put("section",nydusOnly?"nydus":inspect?"inspect":"all");
      MainActivity a=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));game=(NativeSurface)field(a,"game");
      task(()->{check(game!=null,"Missing imported data");set(game,"wide",false);set(game,"zoom",1f);set(game,"speed",42.);set(game,"customBotSlot",-1);});
      if(inspect){zergMission();screenshot("zerg10");}
      else {
        if(!nydusOnly){
        task(()->{call(game,"startSkirmish",new Class<?>[]{int.class,File.class},1,null);NativeBridge.command(17,50000,50000,0,0);NativeBridge.command(11,0,0,0,0);});enabledInstant(true);
        build("Barracks",false);task(()->select("Barracks",0));enabledInstant(false);commandTap("Marine");task(()->check(cmd("Lift Off")[2].equals("0"),"Busy Lift Off is enabled"));screenshot("busy-barracks");
        task(()->{NativeBridge.command(7,0,0,0,0);render(8);});enabledInstant(true);commandTap("Lift Off");frames(180);commandTap("Land");blocked("Command Center","blocked-landing");
        build("Factory",true);task(()->select("Factory",0));commandTap("Machine Shop");blocked("Command Center","blocked-addon");
        task(()->{select("Factory",0);center("Factory");});commandTap("Machine Shop");placeValid();task(()->row("Machine Shop"));screenshot("completed-addon");report.put("terranPlacementAndBusyControls",true);
        }
        zergMission();enabledInstant(true);task(()->save());
        // Zerg 10 begins with a Hatchery/Lair path; build any missing prerequisites normally.
        boolean[] have={false};task(()->{try{row("Hive");have[0]=true;}catch(Exception ignored){}});
        if(!have[0]) {
          task(()->{try{row("Spawning Pool");have[0]=true;}catch(Exception ignored){}});if(!have[0])build("Spawning Pool",false);
          have[0]=false;
          task(()->{try{row("Lair");have[0]=true;}catch(Exception ignored){}});
          if(!have[0]){task(()->select("Hatchery",owner));commandTap("Lair");frames(240);task(()->row("Lair"));}
          have[0]=false;task(()->{try{row("Queen's Nest");have[0]=true;}catch(Exception ignored){}});if(!have[0])build("Queen's Nest",true);
          task(()->select("Lair",owner));commandTap("Hive");frames(240);task(()->row("Hive"));
        }
        build("Nydus Canal",true);task(()->{select("Nydus Canal",owner);center("Nydus Canal");});commandTap("Build Nydus Exit");screenshot("nydus-exit-preview");placeValid();
        task(()->{int count=0;for(String line:NativeBridge.text(10).split("\n")){String[] r=line.split("\t");if(r.length>2&&r[1].equals("Nydus Canal")&&Integer.parseInt(r[2])==owner)++count;}check(count>=2,"Nydus exit not created");report.put("nydusExitTouch",true);});screenshot("nydus-linked");
      }
      report.put("passed",true);save();result.putString("report",report.toString());finish(Activity.RESULT_OK,result);
    }catch(Throwable e){try{report.put("passed",false);report.put("error",android.util.Log.getStackTraceString(e));save();}catch(Exception ignored){}result.putString("error",android.util.Log.getStackTraceString(e));finish(Activity.RESULT_CANCELED,result);}
  }
}

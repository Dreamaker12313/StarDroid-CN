package org.openbw.androidtest;
import android.content.*;
import android.graphics.*;
import android.os.*;
import android.util.AtomicFile;
import java.io.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** File persistence and shipped save-menu checks; original game archives not required. */
public final class NativeSaveInstrumentation extends NativeInstrumentation {
  private Bundle runArgs;
  @Override public void onCreate(Bundle args){runArgs=args;super.onCreate(args);}
  void pass(String name) throws Exception {report.put(name,true);save();}
  @Override public void onStart() {
    Bundle result=new Bundle();
    try {
      output=new File(getTargetContext().getExternalFilesDir(null),"native-saves");output.mkdirs();
      recordPackageHashes();report.put("version",getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest",0).versionName);report.put("android",Build.VERSION.RELEASE);report.put("originalGameAssets",false);
      File root=new File(getTargetContext().getCacheDir(),"save-validation");root.mkdirs();
      File map=new File(root,"mission.mpq");byte[] mapBytes=new byte[8192];new Random(47).nextBytes(mapBytes);
      try(FileOutputStream out=new FileOutputStream(map)){out.write(mapBytes);}
      byte[] state=new byte[40000];new Random(42).nextBytes(state);
      JSONObject info=new JSONObject().put("name","Save check").put("missionCode",0).put("race",0).put("frame",427);
      NativeSaves store=new NativeSaves(root);store.write(0,info,state,map);
      // A fresh store instance opens the bytes from disk, with no shared session state.
      try(NativeSaves.Loaded loaded=new NativeSaves(root).read(0,root)) {
        check(Arrays.equals(state,loaded.state),"Snapshot bytes changed");check(loaded.info.getInt("frame")==427,"Saved details changed");
        try(InputStream in=new FileInputStream(loaded.map)){check(Arrays.equals(mapBytes,NativeData.read(in,8192)),"Map/voice bundle changed");}
      }
      pass("diskSnapshotMapAndMetadataRoundTrip");
      boolean failed=false;try{store.write(0,info,state,new File(root,"missing-map"));}catch(Exception e){failed=true;}
      check(failed&&store.info(0).getInt("frame")==427,"Failed save overwrote existing slot");
      AtomicFile atomic=new AtomicFile(new File(root,"saves/slot-1.obwsave"));
      FileOutputStream partial=atomic.startWrite();partial.write(new byte[]{1,2,3});partial.close();
      try(NativeSaves.Loaded loaded=store.read(0,root)){check(Arrays.equals(state,loaded.state),"Interrupted write did not recover previous save");}
      pass("failedAndInterruptedOverwriteRetainsPreviousSave");
      File damaged=new File(root,"saves/slot-2.obwsave");
      try(ZipFile zip=new ZipFile(new File(root,"saves/slot-1.obwsave"));ZipOutputStream out=new ZipOutputStream(new FileOutputStream(damaged))) {
        Enumeration<? extends ZipEntry> entries=zip.entries();while(entries.hasMoreElements()) {
          ZipEntry e=entries.nextElement();byte[] b=NativeData.read(zip.getInputStream(e),NativeSaves.STATE_LIMIT);
          if(e.getName().equals("state.bin"))b[10]^=7;out.putNextEntry(new ZipEntry(e.getName()));out.write(b);out.closeEntry();
        }
      }
      failed=false;try(NativeSaves.Loaded ignored=store.read(1,root)){}catch(Exception e){failed=true;}
      check(failed,"Tampered snapshot accepted");pass("tamperedSaveRejected");
      // Actual import -> sparse MPQ -> save -> load -> native decrypt/decompress.
      String exported=runArgs.getString("missionExport");
      if(exported!=null) {
        JSONArray missions=new JSONArray(new String(NativeData.read(getTargetContext().getAssets().open("native/missions.json"),131072),"UTF-8"));
        JSONArray checked=new JSONArray();
        try(ZipFile outer=new ZipFile(exported)) {
          Enumeration<? extends ZipEntry> all=outer.entries();
          while(all.hasMoreElements()) {
            ZipEntry e=all.nextElement();if(!e.getName().startsWith("missions/")||!e.getName().endsWith(".zip"))continue;
            File bundle=new File(root,"input.zip");
            try(InputStream in=outer.getInputStream(e);FileOutputStream out=new FileOutputStream(bundle)) {
              byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);
            }
            JSONObject manifest;
            try(ZipFile zip=new ZipFile(bundle)){manifest=new JSONObject(new String(NativeData.read(zip.getInputStream(zip.getEntry("manifest.json")),131072),"UTF-8"));}
            String id=manifest.getString("mission");JSONObject mission=null;
            for(int i=0;i<missions.length();i++)if(missions.getJSONObject(i).getString("id").equals(id))mission=missions.getJSONObject(i);
            check(mission!=null,"Export missing from campaign catalog: "+id);
            new File(root,"import.stamp").delete();
            File prepared=NativeData.prepare(bundle,root,"import");
            String name=mission.getString("prefix")+"staredit/scenario.chk";
            NativeBridge.open(3,prepared.getPath());byte[] expected=NativeBridge.asset(3,name);
            check(expected.length>1000,"Native reader did not extract original map: "+id);
            JSONObject details=new JSONObject().put("name",mission.getString("title")).put("missionCode",mission.getInt("code"))
                .put("race",mission.getInt("race")).put("frame",427).put("mission",mission);
            store.write(2,details,state,prepared);
            check(store.info(2).getInt("missionCode")==mission.getInt("code"),"Campaign save rejected after writing: "+id);
            try(NativeSaves.Loaded loaded=store.read(2,root)) {
              check(loaded.map.length()==prepared.length(),"Archive logical size changed");
              NativeBridge.open(3,loaded.map.getPath());
              check(Arrays.equals(expected,NativeBridge.asset(3,name)),"Original mission did not survive save/load: "+id);
              check(Arrays.equals(state,loaded.state),"Campaign snapshot bytes changed");
              if(id.equals("expzerg05")) {
                bundle.delete();prepared.delete();store.write(3,details,state,loaded.map);
                try(NativeSaves.Loaded again=store.read(3,root)) {
                  NativeBridge.open(3,again.map.getPath());check(Arrays.equals(expected,NativeBridge.asset(3,name)),"Reloaded mission cannot be saved again");
                }
              }
            }
            long saved=new File(root,"saves/slot-3.obwsave").length();
            check(saved<4*1024*1024,"Sparse map save writes archive padding: "+id);
            checked.put(new JSONObject().put("id",id).put("mapBytes",expected.length).put("archiveBytes",manifest.getLong("archiveSize")).put("saveBytes",saved));
          }
        }
        check(checked.length()==64,"All 64 original mission archives must be tested");
        report.put("originalMissionArchives",checked);pass("all64ImportedMissionSaveLoadAndNativeMapRead");
        pass("loadedTrueColorsCanBeSavedAgainWithoutOriginalBundle");
      }
      check(store.info(0).getInt("format")==1,"Legacy save format missing");
      JSONObject invalid=new JSONObject(info.toString()).put("missionCode",999);
      failed=false;try{store.write(0,invalid,state,map);}catch(Exception e){failed=true;}
      check(failed&&store.info(0).getInt("frame")==427,"Invalid campaign metadata replaced a good save");
      pass("legacySaveCompatibilityAndInvalidMetadataAtomicity");
      for(int type:new int[]{99,104})check(CommandSlots.override(type,"Cloak",6)==6&&CommandSlots.override(type,"Decloak",6)==6&&CommandSlots.override(type,"Lockdown",6)==7,"Duran ability slots wrong");
      pass("bothDuranAbilitySlots");
      // Test persistence across a separate instrumentation process invocation too.
      if("true".equals(runArgs.getString("verifyOnly"))) {
        try(NativeSaves.Loaded loaded=new NativeSaves(new File(getTargetContext().getFilesDir(),"save-validation")).read(5,root)) {
          check(Arrays.equals(state,loaded.state),"Save did not survive process restart");
        }
        pass("survivesProcessRestart");
      } else new NativeSaves(new File(getTargetContext().getFilesDir(),"save-validation")).write(5,info,state,map);
      NativeBridge.endGame();failed=false;try{NativeBridge.saveState();}catch(Exception e){failed=true;}
      check(failed,"No-game JNI save must report an error");pass("newSaveJniEntryPointsLoad");
      MainActivity activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
      waitForIdleSync();runOnMainSync(()->{game=new NativeSurface(activity);game.shutdown();});
      Thread worker=(Thread)field(game,"worker");worker.join(15000);check(!worker.isAlive(),"Test surface worker is still active");
      set(game,"art",new NativeArt());set(game,"page","campaign");set(game,"logicalWidth",640);
      call(game,"openSaves",new Class<?>[]{boolean.class},false);
      check(field(game,"modal").equals("load"),"Main menu load browser absent");
      JSONObject[] slots=(JSONObject[])field(game,"savedSlots");slots[0]=info;
      Bitmap b=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);
      call(game,"drawModal",new Class<?>[]{Canvas.class},new Canvas(b));
      List<?> buttons=(List<?>)field(game,"buttons");check(buttons.size()==7,"Expected six slots and Cancel");
      set(game,"page","game");set(game,"activeGame",true);
      ((Runnable)field(buttons.get(0),"action")).run();check(field(game,"modal").equals("save-confirm"),"Load discarded active game without confirmation");
      call(game,"modalBack",new Class<?>[]{});check(field(game,"modal").equals("load"),"Cancel confirmation lost browser");
      call(game,"modalBack",new Class<?>[]{});check(field(game,"modal").equals("menu"),"Back failed to return to paused game");
      call(game,"openSaves",new Class<?>[]{boolean.class},true);slots[0]=info;
      call(game,"drawModal",new Class<?>[]{Canvas.class},new Canvas(b));buttons=(List<?>)field(game,"buttons");
      ((Runnable)field(buttons.get(0),"action")).run();check(field(game,"modal").equals("save-confirm"),"Save overwrote slot without confirmation");b.recycle();
      pass("sixSlotsAndCancelAndOverwriteLoadConfirmations");
      report.put("passed",true);save();result.putString("result","PASS native saves");
    } catch(Throwable e){try{report.put("passed",false);report.put("error",e.toString());save();}catch(Exception ignored){}result.putString("error",e.toString());}
    finish(report.optBoolean("passed")?0:1,result);
  }
}

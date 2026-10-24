package org.openbw.androidtest;

import android.os.*;
import android.graphics.*;
import java.io.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Real core data, actual world snapshots and production JNI/file save path. */
public final class NativeCampaignInstrumentation extends NativeInstrumentation {
  private Bundle args;
  @Override public void onCreate(Bundle b){args=b;super.onCreate(b);}
  private byte[] read(File p) throws Exception {try(InputStream in=new FileInputStream(p)){return NativeData.read(in,NativeSaves.STATE_LIMIT);}}
  private void write(File p,byte[] b) throws Exception {try(FileOutputStream out=new FileOutputStream(p)){out.write(b);}}
  private void openCore(String dir) {
    NativeBridge.open(0,new File(dir,"StarDat.mpq").getPath());
    NativeBridge.open(1,new File(dir,"BrooDat.mpq").getPath());
    NativeBridge.open(2,new File(dir,"patch_rt.mpq").getPath());
  }
  @Override void screenshot(String name) throws Exception {
    Bitmap b=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);
    NativeBridge.frame(b,0,NativeBridge.value(8,0)*42.);
    try(FileOutputStream out=new FileOutputStream(new File(output,name+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,out);}
    b.recycle();
  }
  @Override public void onStart() {
    Bundle result=new Bundle();
    try {
      output=new File(getTargetContext().getExternalFilesDir(null),"native-campaign-world");output.mkdirs();
      recordPackageHashes();report.put("version",getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest",0).versionName).put("originalCoreAssets",true).put("fullPlaythrough",false);
      openCore(args.getString("dataDir"));
      File root=new File(getTargetContext().getFilesDir(),"campaign-world-validation");root.mkdirs();
      NativeSaves store=new NativeSaves(root);
      if("true".equals(args.getString("verifyOnly"))) {
        try(NativeSaves.Loaded loaded=store.read(0,root)) {
          NativeBridge.open(3,loaded.map.getPath());NativeBridge.init(640,480,505,0);NativeBridge.restoreState(loaded.state);
          check(Arrays.equals(loaded.state,NativeBridge.saveState()),"Process restart changes saved world");
          NativeBridge.frame(null,240,(NativeBridge.value(8,0)+240)*42.);
          check(Arrays.equals(read(new File(root,"expected.bin")),NativeBridge.saveState()),"Process restart changes continued world");
        }
        report.put("survivesProcessRestart",true);
      } else {
        JSONArray catalog=new JSONArray(new String(NativeData.read(getTargetContext().getAssets().open("native/missions.json"),131072),"UTF-8"));
        JSONArray checked=new JSONArray();
        for(String id:new String[]{"zerg04","expzerg05"}) {
          JSONObject mission=null;for(int i=0;i<catalog.length();i++)if(catalog.getJSONObject(i).getString("id").equals(id))mission=catalog.getJSONObject(i);
          check(mission!=null,"Missing test mission");File bundle=new File(root,id+".zip");boolean found=false;
          try(ZipFile outer=new ZipFile(args.getString("missionExport"))) {
            Enumeration<? extends ZipEntry> entries=outer.entries();
            while(entries.hasMoreElements()) {
              ZipEntry entry=entries.nextElement();if(!entry.getName().endsWith(".zip"))continue;
              byte[] bytes=NativeData.read(outer.getInputStream(entry),16*1024*1024);
              try(ZipInputStream zip=new ZipInputStream(new ByteArrayInputStream(bytes))) {
                ZipEntry e;while((e=zip.getNextEntry())!=null)if(e.getName().equals("manifest.json")) {
                  JSONObject manifest=new JSONObject(new String(NativeData.read(zip,131072),"UTF-8"));
                  if(id.equals(manifest.optString("mission"))){write(bundle,bytes);found=true;}break;
                }
              }
              if(found)break;
            }
          }
          check(found,"Mission bundle not found: "+id);
          File map=NativeData.prepare(bundle,root,id);NativeBridge.open(3,map.getPath());
          NativeBridge.init(640,480,mission.getInt("code"),mission.getInt("race"));
          NativeBridge.frame(null,4800,4800*42.);check(NativeBridge.value(7,0)==0,"Opening unexpectedly ends: "+id);
          check(NativeBridge.text(11).isEmpty(),"Original AI script error: "+id);screenshot(id);
          byte[] state=NativeBridge.saveState();
          JSONObject info=new JSONObject().put("name",mission.getString("title")).put("missionCode",mission.getInt("code"))
              .put("race",mission.getInt("race")).put("frame",NativeBridge.value(8,0)).put("mission",mission);
          store.write(0,info,state,map);
          NativeBridge.frame(null,240,(NativeBridge.value(8,0)+240)*42.);byte[] expected=NativeBridge.saveState();
          NativeBridge.endGame();
          try(NativeSaves.Loaded loaded=store.read(0,root)) {
            NativeBridge.open(3,loaded.map.getPath());NativeBridge.init(640,480,mission.getInt("code"),mission.getInt("race"));
            NativeBridge.restoreState(loaded.state);check(Arrays.equals(state,NativeBridge.saveState()),"Restored world differs: "+id);
            NativeBridge.frame(null,240,(NativeBridge.value(8,0)+240)*42.);
            check(Arrays.equals(expected,NativeBridge.saveState()),"Continued world differs: "+id);
            store.write(1,info,loaded.state,loaded.map); // Saving again from the loaded map.
          }
          long bytes=new File(root,"saves/slot-1.obwsave").length();check(bytes>0&&bytes<8*1024*1024,"Real save contains sparse archive padding");
          checked.put(new JSONObject().put("mission",id).put("snapshotBytes",state.length).put("saveBytes",bytes).put("exactContinuation",true));
          if(id.equals("expzerg05"))write(new File(root,"expected.bin"),expected);
          NativeBridge.endGame();report.put("missions",checked);save();
        }
      }
      NativeBridge.close();report.put("passed",true);save();result.putString("result","PASS real campaign save/load");
    } catch(Throwable e){try{report.put("passed",false).put("error",e.toString());save();}catch(Exception ignored){}result.putString("error",e.toString());}
    finish(report.optBoolean("passed")?0:1,result);
  }
}

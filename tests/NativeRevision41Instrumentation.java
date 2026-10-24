package org.openbw.androidtest;

import android.app.Instrumentation;
import android.graphics.*;
import android.os.Bundle;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import org.json.*;

/** Real APK/MPQ rendering and interaction checks for the 0.41 command and cargo HUD. */
public final class NativeRevision41Instrumentation extends Instrumentation {
  Bundle args; File output, input, map; NativeArt art; JSONObject commands;
  JSONObject report = new JSONObject(); JSONArray checks = new JSONArray();
  @Override public void onCreate(Bundle arguments) { args=arguments; start(); }
  void check(boolean value,String message) { if(!value)throw new AssertionError(message); }
  void pass(String name) { checks.put(name); }
  String hash(File f) throws Exception {
    MessageDigest d=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)d.update(b,0,n);}
    StringBuilder s=new StringBuilder();for(byte b:d.digest())s.append(String.format(Locale.ROOT,"%02x",b&255));return s.toString();
  }
  void fixture(String name,int race) throws Exception {
    NativeBridge.endGame(); NativeBridge.open(3,map.getPath()); NativeBridge.command(20,-1,0,0,0); NativeBridge.init(640,480,0,race);
    NativeBridge.restoreState(Files.readAllBytes(new File(input,name+".bin").toPath()));
  }
  NativeHud draw(String name,int race,int width) throws Exception {
    NativeBridge.resize(width,480,1);NativeBridge.command(21,104,0,0,0);
    Bitmap world=Bitmap.createBitmap(width,480,Bitmap.Config.ARGB_8888);NativeBridge.frame(world,0,0);
    NativeHud hud=new NativeHud(art,race,commands);Bitmap screen=Bitmap.createBitmap(width,480,Bitmap.Config.ARGB_8888);
    Canvas c=new Canvas(screen);c.drawBitmap(world,0,0,null);hud.draw(c,world,width,1,0);
    try(OutputStream out=new FileOutputStream(new File(output,name+".png"))){screen.compress(Bitmap.CompressFormat.PNG,100,out);}
    world.recycle();screen.recycle();return hud;
  }
  @Override public void onStart() {
    Bundle result=new Bundle();
    try {
      input=new File(args.getString("dataDir"));output=new File(getTargetContext().getExternalFilesDir(null),"native-revision41");output.mkdirs();
      String[] core={"StarDat.mpq","BrooDat.mpq","patch_rt.mpq"};for(int i=0;i<3;i++)NativeBridge.open(i,new File(input,core[i]).getPath());
      map=new File(output,"weave.scx");try(InputStream in=getTargetContext().getAssets().open("native/weave.scx")){Files.copy(in,map.toPath(),StandardCopyOption.REPLACE_EXISTING);}
      art=new NativeArt();commands=new JSONObject(new String(NativeData.read(getTargetContext().getAssets().open("native/commands.json"),262144),"UTF-8"));
      report.put("version",getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest",0).versionName);
      report.put("apkSha256",hash(new File(getTargetContext().getApplicationInfo().sourceDir)));
      JSONObject libs=new JSONObject();for(String name:new String[]{"libopenbw.so","libsmacker.so"})libs.put(name,hash(new File(getTargetContext().getApplicationInfo().nativeLibraryDir,name)));report.put("nativeLibraries",libs);
      fixture("ghost-unresearched",2);
      try(NativeHud hud=draw("ghost-unresearched",2,640)){
        boolean lock=false,cloak=false;for(NativeHud.Hit h:hud.hits)if(h.fields!=null){if(h.fields[1].equals("Lockdown"))lock=h.fields[2].equals("0");if(h.fields[1].equals("Cloak"))cloak=h.fields[2].equals("0");}
        check(lock&&cloak,"Unresearched Ghost abilities not grey");
      }
      fixture("ghost-no-energy",2);
      try(NativeHud hud=draw("ghost-no-energy",2,640)){
        boolean lock=false;for(NativeHud.Hit h:hud.hits)if(h.fields!=null&&h.fields[1].equals("Lockdown")){lock=h.fields[2].equals("1");NativeBridge.command(2,h.fields[0].charAt(0),0,0,0);}
        check(lock,"Low-energy researched ability greyed out");check(NativeBridge.text(8).contains("energy"),"Energy error missing");
        for(int width:new int[]{640,960}){
          Bitmap b=Bitmap.createBitmap(width,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);c.drawColor(0xff263a2c);
          String[] messages={hud.string(849,"Minerals"),hud.string(850,"Gas"),hud.string(863,"Energy"),hud.string(843,"Overlords"),hud.string(844,"Supply Depots"),hud.string(845,"Pylons")};
          for(int i=0;i<messages.length;i++){
            c.drawColor(0xff263a2c);hud.commandError(c,messages[i],width);
            check(b.getPixel(width/2,NativeHud.WORLD_BOTTOM-6)==0xff263a2c,"Error panel/background still present");
            int pixels=0;for(int y=320;y<NativeHud.WORLD_BOTTOM;y++)for(int x=60;x<width-60;x++)if(b.getPixel(x,y)!=0xff263a2c)pixels++;
            check(pixels>20,"Error text invisible");
            try(OutputStream out=new FileOutputStream(new File(output,"warning-"+i+"-"+width+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,out);}
          }b.recycle();
        }
      }pass("researchTintEnergyAndSixUnboxedWarningsAtTwoWidths");
      for(String name:new String[]{"archon-merging","dark-archon-merging"}){
        fixture(name,2);check(NativeBridge.value(3,0)==5,"Merge progress not exposed");
        try(NativeHud hud=draw(name,2,640)){check(hud.hits.stream().noneMatch(h->h.fields!=null||h.cancel>=0),"Merge presents normal/cancel commands");}
        int before=Integer.parseInt(NativeBridge.text(2).split("\\t")[0]);NativeBridge.frame(null,60,2520);
        check(Integer.parseInt(NativeBridge.text(2).split("\\t")[0])>before,"Merge bar not advancing");
      }pass("bothArchonMergeProgressPanels");
      fixture("cargo",1);
      try(NativeHud hud=draw("cargo",1,640)){
        ArrayList<NativeHud.Hit> cargo=new ArrayList<NativeHud.Hit>();for(NativeHud.Hit h:hud.hits)if(h.unload>=0)cargo.add(h);
        check(cargo.size()==4,"Missing passenger wireframes");
        check(cargo.get(0).rect.width()==69&&cargo.get(0).rect.height()==71,"Tank not four spaces");
        check(cargo.get(1).rect.width()==33&&cargo.get(1).rect.height()==71,"Vulture not two spaces");
        check(cargo.get(2).rect.width()==33&&cargo.get(2).rect.height()==34,"Marine not one space");
        for(int i=0;i<cargo.size();i++)for(int j=i+1;j<cargo.size();j++)check(!RectF.intersects(cargo.get(i).rect,cargo.get(j).rect),"Cargo wireframes overlap");
        NativeBridge.command(24,cargo.get(2).unload,0,0,0);NativeBridge.frame(null,120,5040);
        check(NativeBridge.text(14).trim().split("\\n").length==3,"Cargo tap did not unload selected passenger");
      }
      fixture("cargo",1);try(NativeHud hud=draw("cargo-wide",1,960)){}pass("originalWireframesDataSizedBordersAndPassengerUnload");
      File pack=new File(input,"OpenBW-Skirmish-Maps.zip");
      List<NativeMaps.Staged> maps=NativeMaps.stage(new FileInputStream(pack),pack.getName(),getTargetContext().getCacheDir());check(maps.size()==8,"Map pack count wrong");
      File collection=new File(output,"map-store");collection.mkdirs();
      for(NativeMaps.Staged item:maps){NativeBridge.open(3,item.file.getPath());check(NativeBridge.asset(3,"staredit/scenario.chk")!=null,"Imported map has no scenario");NativeMaps.install(item,collection);NativeMaps.install(item,collection);item.file.delete();}
      check(NativeMaps.list(collection).size()==9,"Maps not persistent/deduplicated");pass("eightOriginalMapsZipImportPersistentCollectionAndDeduplication");
      report.put("checks",checks);report.put("passed",true);result.putString("result","PASS");
    }catch(Throwable e){try{report.put("passed",false);report.put("error",e.toString());report.put("checks",checks);}catch(Exception ignored){}result.putString("result","FAIL "+e);}
    finally{
      try{NativeBridge.close();if(output!=null)Files.write(new File(output,"report.json").toPath(),report.toString(2).getBytes("UTF-8"));}catch(Exception ignored){}
      finish(report.optBoolean("passed")?-1:0,result);
    }
  }
}

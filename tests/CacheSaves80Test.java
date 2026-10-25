package org.openbw.androidtest;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;
public final class CacheSaves80Test {
  static int checks;
  static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
  static byte[] bytes(File f)throws Exception{return Files.readAllBytes(f.toPath());}
  static void put64(byte[] b,int p,long value){for(int i=0;i<8;i++)b[p+i]=(byte)(value>>>(8*i));}
  static byte[] snapshot() {
    byte[] b=new byte[96];put64(b,0,0x3156415357424fL);put64(b,8,4);
    long hash=0xcbf29ce484222325L;for(int i=0;i<b.length-8;i++){hash^=b[i]&255L;hash*=0x100000001b3L;}put64(b,b.length-8,hash);return b;
  }
  static byte[] changeEntry(byte[] source,String name,byte[] value)throws Exception {
    ByteArrayOutputStream out=new ByteArrayOutputStream();
    try(ZipInputStream in=new ZipInputStream(new ByteArrayInputStream(source));ZipOutputStream zip=new ZipOutputStream(out)) {
      ZipEntry e;while((e=in.getNextEntry())!=null){zip.putNextEntry(new ZipEntry(e.getName()));zip.write(e.getName().equals(name)?value:NativeData.read(new FilterInputStream(in){public void close(){}},NativeSaves.MAP_LIMIT));zip.closeEntry();}
    }
    return out.toByteArray();
  }
  static void rejected(NativeSaves store,File slot,File cache,byte[] input,String name,String message)throws Exception {
    byte[] before=bytes(slot);boolean failed=false;
    try{store.importSave(new ByteArrayInputStream(input),name,cache,0);}catch(Exception e){failed=true;if(message!=null)check(e.getMessage().contains(message),"Wrong rejection: "+e);}
    check(failed,"Accepted invalid save "+name);check(Arrays.equals(before,bytes(slot)),"Rejected import changed existing save");
    File[] left=cache.listFiles((d,n)->n.startsWith("save-import-")||n.startsWith("saved-map-"));check(left!=null&&left.length==0,"Import leaked temporary files");
  }
  public static void main(String[] args)throws Exception {
    File base=new File(args[0]),cache=new File(base,"cache");cache.mkdirs();
    File bundle=new File(base,"fixture.zip"),dest=new File(cache,"fixture.mpq"),stamp=new File(cache,"fixture.stamp");
    try(RandomAccessFile out=new RandomAccessFile(dest,"rw")){out.setLength(506995955);}
    Files.write(stamp.toPath(),(bundle.getName()+":"+bundle.length()+":"+bundle.lastModified()+":native1").getBytes("UTF-8"));
    File compact=NativeData.prepare(bundle,cache,"fixture");check(compact.length()<1024*1024,"Old sparse cache was not compacted");
    byte[] exact=bytes(compact);long modified=compact.lastModified();
    check(NativeData.prepare(bundle,cache,"fixture").lastModified()==modified,"Valid compact cache was rewritten");
    File bad=new File(base,"invalid.zip");boolean failed=false;try{NativeData.prepare(bad,cache,"fixture");}catch(Exception e){failed=true;}
    check(failed&&Arrays.equals(exact,bytes(dest)),"Invalid replacement destroyed working cache");check(!new File(cache,"fixture.tmp").exists(),"Failed preparation leaked temporary file");
    File missing=new File(base,"missing.zip");check(NativeData.prepare(missing,cache,"absent")==null,"Missing bundle should not create cache");
    // Recreate the output used by the independent native decoder comparison.
    NativeData.prepare(bundle,cache,"fixture");

    File data=new File(base,"installed");data.mkdirs();NativeSaves store=new NativeSaves(data);
    File map=new File(base,"original.mpq");
    // The compact cache is the same map format saved by normal gameplay.
    JSONObject info=new JSONObject().put("missionCode",0).put("race",1).put("frame",10).put("name","Test match").put("opponentRace",1);
    byte[] state=snapshot();store.write(0,info,state,compact);
    ByteArrayOutputStream export=new ByteArrayOutputStream();store.exportSave(0,export);byte[] portable=export.toByteArray();
    check(portable.length>100,"Export empty");
    store.importSave(new ByteArrayInputStream(portable),"PC backup.obwsave",cache,1);
    try(NativeSaves.Loaded loaded=store.read(1,cache)){check(Arrays.equals(state,loaded.state),"Imported state changed");check(Arrays.equals(exact,bytes(loaded.map)),"Imported map changed");}
    check(store.info(1).getString("name").equals("Test match"),"Imported details changed");
    File slot=new File(data,"saves/slot-1.obwsave");
    for(String name:new String[]{"original.sng","original.snx","original.sav"})rejected(store,slot,cache,"StarCraft saved game".getBytes("UTF-8"),name,"Original StarCraft PC saves");
    rejected(store,slot,cache,"StarCraft saved game".getBytes("UTF-8"),"renamed.obwsave",null);
    rejected(store,slot,cache,new byte[]{1,2,3},"broken.obwsave",null);
    byte[] broken=state.clone();broken[40]^=1;rejected(store,slot,cache,changeEntry(portable,"state.bin",broken),"broken.obwsave","damaged");
    rejected(store,slot,cache,changeEntry(portable,"map.mpq",new byte[64]),"broken.obwsave","damaged");
    JSONObject badInfo=new JSONObject(store.info(0).toString()).put("multiplayer",true);
    rejected(store,slot,cache,changeEntry(portable,"manifest.json",badInfo.toString().getBytes("UTF-8")),"multi.obwsave","single-player");
    badInfo=new JSONObject(store.info(0).toString()).put("stateSha256",NativeSaves.digest(broken));
    rejected(store,slot,cache,changeEntry(changeEntry(portable,"state.bin",broken),"manifest.json",badInfo.toString().getBytes("UTF-8")),"checksum.obwsave","damaged");
    byte[] fakeMap=new byte[64];badInfo=new JSONObject(store.info(0).toString()).put("mapBytes",fakeMap.length).put("mapSha256",NativeSaves.digest(fakeMap));
    rejected(store,slot,cache,changeEntry(changeEntry(portable,"map.mpq",fakeMap),"manifest.json",badInfo.toString().getBytes("UTF-8")),"fake-map.obwsave","archive");
    // Valid ZIP hashes cannot make a different engine's state compatible.
    badInfo=new JSONObject(store.info(0).toString());byte[] alien=state.clone();alien[0]='X';
    badInfo.put("stateSha256",NativeSaves.digest(alien));byte[] alienZip=changeEntry(changeEntry(portable,"state.bin",alien),"manifest.json",badInfo.toString().getBytes("UTF-8"));
    rejected(store,slot,cache,alienZip,"alien.obwsave","Unsupported StarDroid");
    byte[] future=state.clone();put64(future,8,99);badInfo=new JSONObject(store.info(0).toString()).put("stateSha256",NativeSaves.digest(future));
    rejected(store,slot,cache,changeEntry(changeEntry(portable,"state.bin",future),"manifest.json",badInfo.toString().getBytes("UTF-8")),"future.obwsave","Unsupported StarDroid");
    // Large logical legacy map snapshots continue to restore via format2.
    store.write(2,info,state,map);check(store.info(2).getInt("format")==2,"Legacy sparse map not retained");
    ByteArrayOutputStream sparseExport=new ByteArrayOutputStream();store.exportSave(2,sparseExport);
    store.importSave(new ByteArrayInputStream(sparseExport.toByteArray()),"old.obwsave",cache,3);
    try(NativeSaves.Loaded loaded=store.read(3,cache)){check(loaded.map.length()==map.length(),"Legacy sparse map length changed");check(Arrays.equals(state,loaded.state),"Legacy snapshot changed");}
    check(cache.listFiles((d,n)->n.startsWith("saved-map-")).length==0,"Loaded map close leaked file");
    // Only recognized work files are removed; durable user content is outside cache.
    File engine=new File(cache,"native-mpq");engine.mkdirs();
    for(String name:new String[]{"map-import-orphan.scx","mission-export-orphan.zip","save-import-orphan.obwsave"})Files.write(new File(cache,name).toPath(),new byte[]{1});
    for(String name:new String[]{"saved-map-orphan.mpq","content0.tmp","mission.tmp","cinematic.mpq","cinematic.stamp","cinematic.tmp"})Files.write(new File(engine,name).toPath(),new byte[]{1});
    File keep=new File(cache,"unrelated.bin"),active=new File(engine,"content0.mpq");Files.write(keep.toPath(),new byte[]{1});Files.write(active.toPath(),new byte[]{1});
    NativeCache.beginSession(cache);
    check(keep.isFile()&&active.isFile()&&slot.isFile(),"Cleanup removed persistent content");
    check(!new File(cache,"save-import-orphan.obwsave").exists()&&!new File(engine,"saved-map-orphan.mpq").exists(),"Cleanup left stale work files");
    check(!new File(engine,"cinematic.mpq").exists()&&!new File(engine,"cinematic.stamp").exists()&&!new File(engine,"cinematic.tmp").exists(),"Abandoned movie staging survived startup");
    File newer=new File(cache,"map-import-new.scx");Files.write(newer.toPath(),new byte[]{1});NativeCache.beginSession(cache);check(newer.isFile(),"Repeated startup removed live import");
    System.out.println("PASS "+checks+" cache migration/rollback and portable save import/export checks");
  }
}

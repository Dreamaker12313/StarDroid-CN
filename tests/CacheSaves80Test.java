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
  static void rejectedRead(NativeSaves store,File slot,File cache,byte[] damaged)throws Exception {
    byte[] before=bytes(slot);boolean failed=false;
    try {
      Files.write(slot.toPath(),damaged);
      try(NativeSaves.Loaded ignored=store.read(0,cache)){}catch(Exception e){failed=true;}
      check(failed,"Accepted damaged saved game");
      File[] left=cache.listFiles((d,n)->n.startsWith("saved-map-"));check(left!=null&&left.length==0,"Failed load leaked temporary map");
    } finally {Files.write(slot.toPath(),before);}
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
    File slot=new File(data,"saves/slot-1.obwsave");
    byte[] saved=bytes(slot);
    try(NativeSaves.Loaded loaded=store.read(0,cache)){check(Arrays.equals(state,loaded.state),"Saved state changed");check(Arrays.equals(exact,bytes(loaded.map)),"Saved map changed");}
    check(store.info(0).getString("name").equals("Test match"),"Saved details changed");
    byte[] broken=state.clone();broken[40]^=1;
    rejectedRead(store,slot,cache,changeEntry(saved,"state.bin",broken));
    rejectedRead(store,slot,cache,changeEntry(saved,"map.mpq",new byte[64]));
    rejectedRead(store,slot,cache,new byte[]{1,2,3});
    boolean badWrite=false;try{store.write(0,info,new byte[1],compact);}catch(Exception e){badWrite=true;}
    check(badWrite&&Arrays.equals(saved,bytes(slot)),"Invalid snapshot changed existing save");
    badWrite=false;try{store.write(0,info,state,new File(base,"missing-map.mpq"));}catch(Exception e){badWrite=true;}
    check(badWrite&&Arrays.equals(saved,bytes(slot)),"Missing map changed existing save");
    // Normal gameplay can still load older sparse map snapshots via format2.
    store.write(2,info,state,map);check(store.info(2).getInt("format")==2,"Legacy sparse map not retained");
    try(NativeSaves.Loaded loaded=store.read(2,cache)){check(loaded.map.length()==map.length(),"Legacy sparse map length changed");check(Arrays.equals(state,loaded.state),"Legacy snapshot changed");}
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
    System.out.println("PASS "+checks+" cache migration/rollback and normal in-game save/load checks");
  }
}

package org.openbw.androidtest;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;
public final class CinematicCache80Test {
 static int checks;
 static void check(boolean value,String why){checks++;if(!value)throw new AssertionError(why);}
 public static void main(String[] args)throws Exception {
  if(args.length==3) {
   File bundle=new File(args[0]),cache=new File(args[1]);cache.mkdirs();
   File movie=NativeData.prepareEntry(bundle,cache,"cinematic",args[2]);
   check(movie!=null&&movie.length()>32,"Missing requested movie");
   try(RandomAccessFile in=new RandomAccessFile(movie,"r")) {
    byte[] h=new byte[32];in.readFully(h);byte[] blocks=new byte[(int)NativeData.u32(h,28)*16];in.seek(NativeData.u32(h,20));in.readFully(blocks);
    blocks=NativeData.decodeTable(blocks,"(block table)");int selected=0;
    for(int i=0;i<blocks.length;i+=16)if((NativeData.u32(blocks,i+12)&0x80000000L)!=0)selected++;
    check(selected==1,"Prepared more than the requested cinematic");
   }
   System.out.println("Prepared one movie: "+movie.length()+" bytes");return;
  }
  File base=new File(args[0]),cache=new File(base,"movie-lifecycle"),files=new File(base,"movie-installed");cache.mkdirs();files.mkdirs();
  File fixture=new File(base,"fixture.zip");
  Files.copy(fixture.toPath(),new File(files,StoryData.MOVIES).toPath(),StandardCopyOption.REPLACE_EXISTING);
  Files.copy(fixture.toPath(),new File(files,StoryData.EXP_MOVIES).toPath(),StandardCopyOption.REPLACE_EXISTING);
  byte[] source=Files.readAllBytes(new File(files,StoryData.MOVIES).toPath());
  for(int i=5;i<7;i++)for(String suffix:new String[]{".mpq",".stamp",".tmp"})Files.write(new File(cache,"content"+i+suffix).toPath(),new byte[]{1});
  MovieLifecycle80 host=new MovieLifecycle80(files,cache);host.loadArchives();
  for(int i=5;i<7;i++)for(String suffix:new String[]{".mpq",".stamp",".tmp"})check(!new File(cache,"content"+i+suffix).exists(),"Old movie cache retained");
  check(NativeBridge.paths[9].isEmpty()&&NativeBridge.paths[10].isEmpty(),"Movie archive opened eagerly");
  check(host.availableMovies.contains("test/entry0.bin"),"Movie catalogue omitted");
  check(host.playCinematic("test/entry0.bin",false,()->{},true)&&host.page.equals("movie"),"Requested cinematic did not open");
  check(NativeBridge.lastMovieSlot==9,"Wrong original movie source");
  check(NativeBridge.paths[9].isEmpty()&&!new File(cache,"cinematic.mpq").exists(),"Live movie kept backing archive/cache");
  check(!new File(cache,"cinematic.stamp").exists()&&!new File(cache,"cinematic.tmp").exists(),"Transient movie metadata leaked");
  check(host.playCinematic("test/entry1.bin",true,()->{},true)&&NativeBridge.lastMovieSlot==10,"Brood War source failed");
  NativeBridge.failMovie=true;host.failed=false;host.playCinematic("test/entry0.bin",false,()->{},true);
  check(host.failed&&NativeBridge.paths[9].isEmpty()&&!new File(cache,"cinematic.mpq").exists(),"Failed movie leaked archive/cache");
  NativeBridge.failMovie=false;host.failed=false;host.availableMovies.add("smk/absent.smk");host.playCinematic("smk/absent.smk",false,()->{},true);
  check(host.failed&&!new File(cache,"cinematic.mpq").exists(),"Missing entry promoted empty archive");
  check(Arrays.equals(source,Files.readAllBytes(new File(files,StoryData.MOVIES).toPath())),"Cinematic playback altered imported bundle");
  check(!host.playCinematic("not-installed.smk",false,()->{},true),"Missing movie ignored catalogue guard");
  File standalone=NativeData.prepareEntry(fixture,cache,"case","TEST/ENTRY0.BIN");byte[] before=Files.readAllBytes(standalone.toPath());
  boolean rejected=false;try{NativeData.prepareEntry(fixture,cache,"case","not-there.bin");}catch(IOException expected){rejected=true;}
  check(rejected&&Arrays.equals(before,Files.readAllBytes(standalone.toPath())),"Missing entry replaced valid prepared file");
  NativeData.discard(cache,"case");check(!standalone.exists(),"Discard did not remove temporary archive");
  System.out.println("PASS "+checks+" production cinematic lifecycle and one-entry-cache checks");
 }
}

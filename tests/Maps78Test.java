package org.openbw.androidtest;
import java.io.*;import java.nio.file.*;import java.util.*;import java.util.zip.*;
public final class Maps78Test {
 static int checks;
 static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static byte[] scenario(int id) throws Exception {
  ByteArrayOutputStream out=new ByteArrayOutputStream();
  out.write(new byte[]{68,73,77,32,4,0,0,0,64,0,64,0});
  out.write(new byte[]{85,78,73,84,36,0,0,0});byte[] unit=new byte[36];unit[8]=(byte)214;out.write(unit);
  out.write(new byte[]{73,68,32,32,4,0,0,0,(byte)id,(byte)(id>>8),(byte)(id>>16),0});return out.toByteArray();
 }
 static File zip(File dir,int count,boolean invalid)throws Exception {
  File file=new File(dir,"pack.zip");try(ZipOutputStream z=new ZipOutputStream(new FileOutputStream(file))) {
   z.putNextEntry(new ZipEntry("readme.txt"));z.write("not a map".getBytes());z.closeEntry();
   for(int i=0;i<count;i++){z.putNextEntry(new ZipEntry("../../nested/Map "+i+".SCX"));z.write(invalid&&i==count-1?new byte[3]:scenario(i));z.closeEntry();}
  }return file;
 }
 public static void main(String[] a)throws Exception {
  Path temp=Files.createTempDirectory("maps78-");File cache=Files.createDirectory(temp.resolve("cache")).toFile(),files=Files.createDirectory(temp.resolve("files")).toFile();
  try {
   check(NativeMaps.MAX_COUNT>=2501&&NativeMaps.MAX_BATCH>Integer.MAX_VALUE,"Limits still too small");
   File zip=zip(temp.toFile(),2501,false);List<NativeMaps.Staged> maps=NativeMaps.stage(new FileInputStream(zip),"pack.zip",cache);
   check(maps.size()==2501,"2501 map ZIP rejected");for(NativeMaps.Staged map:maps)check(map.file.getParentFile().equals(cache)&&!map.name.contains("/"),"ZIP path escaped");
   int[] progress={0,0};NativeMaps.Validator validator=f->NativeMapCheck.validate(Files.readAllBytes(f.toPath()));
   NativeMaps.Imported result=NativeMaps.importMaps(maps,files,validator,(done,total)->{check(done>progress[0]&&total==2501,"Bad progress");progress[0]=done;progress[1]++;});
   check(result.accepted==2501&&result.rejected==0&&result.collection.size()==2502,"Large collection incomplete");
   check(progress[0]==2501&&progress[1]<110,"Progress floods UI or never finishes");check(cache.list().length==0,"Staging files left behind");
   for(int i=2;i<result.collection.size();i++)check(NativeMaps.label(result.collection.get(i-1)).compareToIgnoreCase(NativeMaps.label(result.collection.get(i)))<=0,"Collection not sorted");
   List<NativeMaps.Staged> again=NativeMaps.stage(new FileInputStream(zip),"pack.zip",cache);result=NativeMaps.importMaps(again,files,validator,(d,t)->{});
   check(result.collection.size()==2502&&cache.list().length==0,"Reimport duplicated files");
   zip=zip(temp.toFile(),3,true);maps=NativeMaps.stage(new FileInputStream(zip),"pack.zip",cache);result=NativeMaps.importMaps(maps,files,validator,(d,t)->{});
   check(result.accepted==2&&result.rejected==1&&cache.list().length==0,"Malformed map batch handling failed");
   zip=zip(temp.toFile(),NativeMaps.MAX_COUNT+1,false);try{NativeMaps.stage(new FileInputStream(zip),"pack.zip",cache);throw new AssertionError("Count unbounded");}catch(IOException expected){}
   check(cache.list().length==0,"Over-limit ZIP leaked staged maps");
   InputStream large=new InputStream(){long left=NativeMaps.MAX_MAP+1L;public int read(){return left-->0?0:-1;}public int read(byte[] b,int o,int n){if(left<=0)return -1;int v=(int)Math.min(left,n);Arrays.fill(b,o,o+v,(byte)0);left-=v;return v;}};
   try{NativeMaps.stage(large,"large.scx",cache);throw new AssertionError("Individual map limit removed");}catch(IOException expected){}
   check(cache.list().length==0,"Oversized map leaked temporary file");
   byte[] bad=scenario(1);bad[4]=(byte)255;bad[5]=bad[6]=bad[7]=(byte)255;
   try{NativeMapCheck.validate(bad);throw new AssertionError("Unsigned CHK size accepted");}catch(IOException expected){}
   System.out.println("PASS "+checks+" checks: 2501 distinct maps, bounded streaming, sorted collection, reimport deduplication, progress, partial rejection, ZIP traversal, 10000-map/64-MiB limits and cleanup");
  }finally{try(java.util.stream.Stream<Path> paths=Files.walk(temp)){paths.sorted(Comparator.reverseOrder()).forEach(p->{try{Files.delete(p);}catch(IOException e){throw new UncheckedIOException(e);}});}}
 }
}

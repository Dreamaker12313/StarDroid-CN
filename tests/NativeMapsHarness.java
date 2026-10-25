package org.openbw.androidtest;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
/** Exercises the exact Java importer without Android or proprietary game archives. */
public final class NativeMapsHarness {
 static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
 static byte[] zip(int count,boolean map) throws Exception {
  ByteArrayOutputStream b=new ByteArrayOutputStream();
  try(ZipOutputStream z=new ZipOutputStream(b)){for(int i=0;i<count;i++){z.putNextEntry(new ZipEntry("../../maps/"+i+(map?".scx":".txt")));z.write(new byte[8]);z.closeEntry();}}
  return b.toByteArray();
 }
 public static void main(String[] args) throws Exception {
  Path temp=Files.createTempDirectory("openbw-map-check-");File cache=Files.createDirectory(temp.resolve("cache")).toFile();File files=Files.createDirectory(temp.resolve("files")).toFile();
  try {
   List<NativeMaps.Staged> maps=NativeMaps.stage(new FileInputStream(args[0]),"maps.zip",cache);
   check(maps.size()==8,"Expected eight maps");
   for(NativeMaps.Staged m:maps){File first=NativeMaps.install(m,files);check(first.equals(NativeMaps.install(m,files)),"Duplicate path differs");check(!NativeMaps.label(first).endsWith(".scx"),"Extension leaked");}
   check(NativeMaps.list(files).size()==9,"Collection is not persistent/deduplicated");
   List<NativeMaps.Staged> single=NativeMaps.stage(new FileInputStream(maps.get(0).file),maps.get(0).name,cache);NativeMaps.install(single.get(0),files);
   check(NativeMaps.list(files).size()==9,"Single-file import is not deduplicated");
   List<NativeMaps.Staged> traversal=NativeMaps.stage(new ByteArrayInputStream(zip(1,true)),"pack.zip",cache);
   check(traversal.get(0).name.equals("0.scx")&&traversal.get(0).file.getParentFile().equals(cache),"ZIP path escaped staging");
   int before=cache.list().length;
   try{NativeMaps.stage(new ByteArrayInputStream(zip(NativeMaps.MAX_COUNT+1,true)),"large.zip",cache);throw new AssertionError("Map count unbounded");}catch(IOException expected){}
   check(cache.list().length==before,"Failed import left temporary files");
   try{NativeMaps.stage(new ByteArrayInputStream(zip(1,false)),"empty.zip",cache);throw new AssertionError("Non-map ZIP accepted");}catch(IOException expected){}
   System.out.println("PASS eight-map ZIP and individual imports, persistent collection, deduplication, path isolation, count bounds and failed-import cleanup");
  }finally{try(java.util.stream.Stream<Path> paths=Files.walk(temp)){paths.sorted(Comparator.reverseOrder()).forEach(p->{try{Files.delete(p);}catch(IOException e){throw new UncheckedIOException(e);}});}}
 }
}

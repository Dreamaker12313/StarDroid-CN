package org.openbw.androidtest;

import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Four verified scenarios in private app cache, at most 32 MiB. */
final class NearbyMapCache implements NearbyMatch.MapCache {
  private final File directory;
  NearbyMapCache(File directory){this.directory=directory;}
  private File file(String digest) throws IOException {
    if(digest==null || !digest.matches("[0-9a-f]{64}"))throw new IOException("Invalid map cache key");
    return new File(directory,digest+".chk");
  }
  public byte[] read(String digest,int size) throws Exception {
    File f=file(digest);
    if(size<8 || size>NearbyProtocol.MAX_MAP || !f.isFile())return null;
    if(f.length()!=size){f.delete();return null;}
    byte[] data;
    try(InputStream in=new FileInputStream(f)){data=NativeData.read(in,NearbyProtocol.MAX_MAP);}
    if(data.length!=size || !NearbyProtocol.digest(data).equals(digest)){f.delete();return null;}
    f.setLastModified(System.currentTimeMillis());return data;
  }
  public void write(String digest,byte[] data) throws Exception {
    File target=file(digest);
    if(data==null || data.length<8 || data.length>NearbyProtocol.MAX_MAP || !NearbyProtocol.digest(data).equals(digest))throw new IOException("Unverified map cache data");
    if(!directory.isDirectory() && !directory.mkdirs())throw new IOException("Map cache unavailable");
    File temporary=File.createTempFile("nearby-",".tmp",directory);
    try {
      try(OutputStream out=new FileOutputStream(temporary)){out.write(data);}
      try{Files.move(temporary.toPath(),target.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
      catch(AtomicMoveNotSupportedException e){Files.move(temporary.toPath(),target.toPath(),StandardCopyOption.REPLACE_EXISTING);}
      target.setLastModified(System.currentTimeMillis());
    } finally {temporary.delete();}
    File[] entries=directory.listFiles((dir,name)->name.matches("[0-9a-f]{64}\\.chk"));
    if(entries==null)return;
    Arrays.sort(entries,(a,b)->a.equals(b)?0:a.equals(target)?-1:b.equals(target)?1:Long.compare(b.lastModified(),a.lastModified()));
    long bytes=0;int count=0;
    for(File f:entries){bytes+=f.length();if(++count>4 || bytes>32L*1024*1024)f.delete();}
  }
}

package org.openbw.androidtest;

import android.util.AtomicFile;
import java.io.*;
import java.security.*;
import java.util.zip.*;
import org.json.*;

/** Six durable, atomic snapshots. A save owns its map, including mission voices. */
final class NativeSaves {
  static final int SLOTS=6, STATE_LIMIT=64*1024*1024, MAP_LIMIT=256*1024*1024;
  private final File directory;
  NativeSaves(File files) {directory=new File(files,"saves");}
  private AtomicFile slot(int n) throws IOException {
    if(n<0||n>=SLOTS)throw new IOException("Invalid save slot");
    if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("Cannot create saves folder");
    return new AtomicFile(new File(directory,"slot-"+(n+1)+".obwsave"));
  }
  private File recover(int n) throws IOException {
    AtomicFile f=slot(n);try(InputStream in=f.openRead()){}return f.getBaseFile();
  }
  JSONObject info(int n) throws Exception {
    try(ZipFile zip=new ZipFile(recover(n))) {return metadata(zip);}
  }
  private static JSONObject metadata(ZipFile zip) throws Exception {
    JSONObject m=new JSONObject(new String(read(zip,"manifest.json",131072),"UTF-8"));
    validate(m);return m;
  }
  private static void validate(JSONObject m) throws Exception {
    if(m.getInt("format")!=1&&m.getInt("format")!=2)throw new IOException("Unsupported saved game version");
    int code=m.getInt("missionCode"),race=m.getInt("race");
    if((code!=0&&!CampaignCatalog.supported(code))||race<0||race>2||m.getInt("frame")<0)throw new IOException("Invalid save details");
    if(code>0 && (m.getJSONObject("mission").getInt("code")!=code||m.getJSONObject("mission").getInt("race")!=race))throw new IOException("Mission details do not match");
    if(code>0 && !CampaignCatalog.id(code).equals(m.getJSONObject("mission").getString("id")))throw new IOException("Mission identity does not match");
  }
  static String digest(byte[] bytes) throws Exception {return hex(MessageDigest.getInstance("SHA-256").digest(bytes));}
  private static String hex(byte[] bytes) {StringBuilder s=new StringBuilder();for(byte b:bytes)s.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return s.toString();}
  private static MessageDigest sha() throws Exception {return MessageDigest.getInstance("SHA-256");}
  private static void entry(ZipOutputStream z,String name,byte[] bytes) throws IOException {z.putNextEntry(new ZipEntry(name));z.write(bytes);z.closeEntry();}
  void write(int n,JSONObject details,byte[] state,File map) throws Exception {
    if(state==null||state.length<40||state.length>STATE_LIMIT)throw new IOException("Invalid game snapshot");
    if(map==null||!map.isFile())throw new IOException("Mission map is unavailable. Reload the mission and try again.");
    if(map.length()<32)throw new IOException("Mission map is incomplete");
    // Imported missions are sparse copies of the original CD archive, often
    // 500+ MB in apparent size with less than 1 MB of occupied map data.
    NativeMapArchive.Plan sparse=map.length()>MAP_LIMIT?NativeMapArchive.inspect(map,MAP_LIMIT):null;
    JSONObject m=new JSONObject(details.toString());m.put("format",sparse==null?1:2);m.put("created",System.currentTimeMillis());m.put("stateSha256",digest(state));
    validate(m);
    AtomicFile file=slot(n);FileOutputStream stream=null;
    try {
      stream=file.startWrite();ZipOutputStream zip=new ZipOutputStream(stream);zip.setLevel(1);
      try {
        entry(zip,"state.bin",state);zip.putNextEntry(new ZipEntry(sparse==null?"map.mpq":"map.sparse"));
        MessageDigest mapHash=sha();long size=0;
        if(sparse!=null) {
          NativeMapArchive.write(map,sparse,new DigestOutputStream(zip,mapHash));size=sparse.bytes;m.put("mapLogicalBytes",sparse.length);
        } else try(InputStream in=new FileInputStream(map)) {byte[] b=new byte[65536];int count;while((count=in.read(b))!=-1){size+=count;if(size>MAP_LIMIT)throw new IOException("Map exceeds save limit");mapHash.update(b,0,count);zip.write(b,0,count);}}
        zip.closeEntry();m.put("mapSha256",hex(mapHash.digest()));m.put("mapBytes",size);
        entry(zip,"manifest.json",m.toString().getBytes("UTF-8"));zip.finish();zip.flush();stream.getFD().sync();file.finishWrite(stream);stream=null;
      } finally {try{zip.close();}catch(IOException ignored){}}
    } catch(Exception e) {if(stream!=null)file.failWrite(stream);throw e;}
  }
  static final class Loaded implements AutoCloseable {
    final JSONObject info;final byte[] state;final File map;
    Loaded(JSONObject i,byte[] s,File m){info=i;state=s;map=m;}
    public void close(){map.delete();}
  }
  Loaded read(int n,File cache) throws Exception {
    File map=null;
    try(ZipFile zip=new ZipFile(recover(n))) {
      JSONObject m=metadata(zip);byte[] state=read(zip,"state.bin",STATE_LIMIT);
      if(!digest(state).equals(m.getString("stateSha256")))throw new IOException("Saved game is damaged");
      boolean sparse=m.getInt("format")==2;
      ZipEntry entry=zip.getEntry(sparse?"map.sparse":"map.mpq");if(entry==null||entry.getSize()<32||entry.getSize()>MAP_LIMIT)throw new IOException("Saved map is damaged");
      map=File.createTempFile("saved-map-",".mpq",cache);MessageDigest h=sha();long size=0;
      if(sparse) {
        try(InputStream in=new DigestInputStream(zip.getInputStream(entry),h)) {
          long length=NativeMapArchive.restore(in,entry.getSize(),MAP_LIMIT,map);
          if(length!=m.getLong("mapLogicalBytes"))throw new IOException("Saved map is damaged");
          size=entry.getSize();
        }
      } else try(InputStream in=zip.getInputStream(entry);FileOutputStream out=new FileOutputStream(map)) {
        byte[] b=new byte[65536];int count;while((count=in.read(b))!=-1) {size+=count;if(size>MAP_LIMIT)throw new IOException("Saved map is too large");h.update(b,0,count);out.write(b,0,count);}out.getFD().sync();
      }
      if(size!=m.getLong("mapBytes")||!hex(h.digest()).equals(m.getString("mapSha256")))throw new IOException("Saved map is damaged");
      return new Loaded(m,state,map);
    } catch(Exception e) {if(map!=null)map.delete();throw e;}
  }
  private static byte[] read(ZipFile zip,String name,int limit) throws IOException {
    ZipEntry e=zip.getEntry(name);if(e==null||e.getSize()<0||e.getSize()>limit)throw new IOException("Missing or invalid "+name);
    try(InputStream in=zip.getInputStream(e)){return NativeData.read(in,limit);}
  }
}

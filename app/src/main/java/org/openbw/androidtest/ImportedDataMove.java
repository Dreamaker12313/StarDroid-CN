package org.openbw.androidtest;

import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Verified import-only transfer. Selection changes only after a complete destination exists. */
final class ImportedDataMove {
  interface Commit { void select() throws IOException; }
  interface Check { void check() throws IOException; }
  interface Progress { void update(int done,int total); }
  static final long RESERVE=64L*1024*1024;
  static boolean imported(String name) {
    if(name.equals("mpq")||name.equals("melee-maps"))return true;
    String current=name.replaceFirst("^OpenBW-","StarDroid-");
    if(current.matches("StarDroid-(?:(?:Music|Story|Cinematics)(?:-BroodWar)?|Interface)\\.zip"))return true;
    for(Object[] item:CampaignCatalog.ALL){String id=(String)item[1];if(current.equals("StarDroid-"+Character.toUpperCase(id.charAt(0))+id.substring(1)+".zip"))return true;}
    return false;
  }
  static List<File> files(File root) throws IOException {
    ArrayList<File> result=new ArrayList<File>();File[] entries=root.listFiles();
    if(entries==null)throw new IOException("Game data storage is unavailable.");
    for(File f:entries)if(imported(f.getName()))collect(root.getCanonicalFile(),f,result);
    Collections.sort(result,(a,b)->a.getPath().compareTo(b.getPath()));return result;
  }
  private static void collect(File root,File f,List<File> result)throws IOException {
    if(Files.isSymbolicLink(f.toPath())||!f.getCanonicalPath().startsWith(root.getPath()+File.separator))throw new IOException("Invalid game data path.");
    if(f.isDirectory()){File[] children=f.listFiles();if(children==null)throw new IOException("Cannot read game data.");for(File child:children)collect(root,child,result);}
    else if(f.isFile())result.add(f);else throw new IOException("Cannot read game data.");
  }
  static byte[] hash(File f)throws IOException {
    try{MessageDigest md=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)md.update(b,0,n);}return md.digest();}
    catch(NoSuchAlgorithmException e){throw new IOException(e);}
  }
  private static File target(File destination,String relative)throws IOException {
    File f=new File(destination,relative);File parent=f.getParentFile();
    if(!parent.isDirectory()&&!parent.mkdirs())throw new IOException("Cannot create game data folder.");
    if(Files.isSymbolicLink(f.toPath())||!f.getCanonicalPath().startsWith(destination.getCanonicalPath()+File.separator))throw new IOException("Invalid game data destination.");return f;
  }
  static void move(File source,File destination,long freeBytes,Check available,Commit commit,Progress progress)throws IOException {
    source=source.getCanonicalFile();destination=destination.getCanonicalFile();
    if(source.equals(destination)){commit.select();return;}
    if(source.toPath().startsWith(destination.toPath())||destination.toPath().startsWith(source.toPath()))throw new IOException("Invalid game data destination.");
    if(!destination.isDirectory()&&!destination.mkdirs())throw new IOException("Cannot create game data folder.");
    available.check();List<File> files=files(source);long needed=0;
    Set<String> sourceNames=new HashSet<String>();
    for(File f:files)sourceNames.add(source.toPath().relativize(f.toPath()).toString());
    for(File existing:files(destination))if(!sourceNames.contains(destination.toPath().relativize(existing.toPath()).toString()))
      throw new IOException("The destination contains different game files. Nothing was moved.");
    ArrayList<String> names=new ArrayList<String>();ArrayList<byte[]> hashes=new ArrayList<byte[]>();
    for(File f:files){String name=source.toPath().relativize(f.toPath()).toString();File to=target(destination,name);byte[] hash=hash(f);names.add(name);hashes.add(hash);
      if(to.exists()){if(!to.isFile()||to.length()!=f.length()||!Arrays.equals(hash,hash(to)))throw new IOException("The destination contains different game files. Nothing was moved.");}
      else {if(Long.MAX_VALUE-needed<f.length())throw new IOException("Game data is too large.");needed+=f.length();}}
    if(freeBytes<RESERVE||needed>freeBytes-RESERVE)throw new IOException("Not enough free space to move game data.");
    File stage=new File(destination,".data-move");
    if(stage.exists())removeStage(stage);if(!stage.mkdir())throw new IOException("Cannot prepare game data move.");
    try {
      for(int i=0;i<files.size();i++){
        available.check();File from=files.get(i),to=target(destination,names.get(i));
        if(!to.exists()){
          File temporary=new File(stage,"copy");
          try(InputStream in=new FileInputStream(from);FileOutputStream out=new FileOutputStream(temporary)){
            byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1){available.check();out.write(b,0,n);}out.getFD().sync();}
          if(temporary.length()!=from.length()||!Arrays.equals(hashes.get(i),hash(temporary)))throw new IOException("Game data verification failed. Original files were kept.");
          available.check();Files.move(temporary.toPath(),to.toPath());
        }
        progress.update(i+1,files.size());
      }
      // Recheck the full set immediately before committing the selected location.
      for(int i=0;i<files.size();i++){
        available.check();if(!Arrays.equals(hashes.get(i),hash(files.get(i)))||!Arrays.equals(hashes.get(i),hash(target(destination,names.get(i)))))throw new IOException("Game data changed while moving. Original files were kept.");}
      available.check();commit.select();
      // Once selected, remove only originals whose verified destination still exists.
      // Interruption leaves harmless duplicate files; a retry accepts equal copies.
      for(int i=0;i<files.size();i++)try{
        available.check();File from=files.get(i),to=target(destination,names.get(i));
        if(Arrays.equals(hashes.get(i),hash(from))&&Arrays.equals(hashes.get(i),hash(to)))Files.delete(from.toPath());
      }catch(IOException unavailableNow){break;}
    }finally{try{if(stage.exists())removeStage(stage);}catch(IOException unavailableNow){/* Originals remain intact until the commit. */}}
  }
  private static void removeStage(File f)throws IOException {
    if(Files.isSymbolicLink(f.toPath()))throw new IOException("Invalid move staging folder.");
    if(f.isDirectory()){File[] list=f.listFiles();if(list==null)throw new IOException("Cannot clear move staging folder.");for(File c:list)removeStage(c);}
    if(!f.delete()&&f.exists())throw new IOException("Cannot clear move staging folder.");
  }
}

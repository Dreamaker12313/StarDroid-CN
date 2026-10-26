package org.openbw.androidtest;

import android.content.Context;
import android.os.Environment;
import java.io.File;
import java.io.FileDescriptor;
import java.io.IOException;
import android.system.Os;
import android.system.OsConstants;
import android.system.ErrnoException;
import java.util.*;

/** Removable app-specific storage requires no broad storage permission. */
final class GameDataStorage {
  static final String PREFS="game-data-storage",KEY="root";
  static File root(Context context) {
    String path=context.getSharedPreferences(PREFS,0).getString(KEY,"");
    return path.isEmpty()?context.getFilesDir():new File(path);
  }
  static List<File> cards(Context context) {
    ArrayList<File> result=new ArrayList<File>();
    for(File dir:context.getExternalFilesDirs(null))if(dir!=null)try {
      if(dir.isDirectory()&&dir.canWrite()&&Environment.isExternalStorageRemovable(dir)&&Environment.MEDIA_MOUNTED.equals(Environment.getExternalStorageState(dir)))
        result.add(new File(dir,"game-data").getCanonicalFile());
    }catch(Exception ignored){}
    return result;
  }
  static boolean available(Context context) {return available(context,root(context));}
  static boolean available(Context context,File root) {
    try {return root.getCanonicalFile().equals(context.getFilesDir().getCanonicalFile())||cards(context).contains(root.getCanonicalFile());}
    catch(Exception ignored){return false;}
  }
  // File contents are synced by the copier; persist renamed directory entries
  // before selecting the new volume and removing any original bytes.
  static void syncImportedDirectories(File root) throws IOException {
    File[] entries=root.listFiles();
    if(entries==null)throw new IOException("Game data storage is unavailable.");
    for(File entry:entries)if(ImportedDataMove.imported(entry.getName())&&entry.isDirectory())syncDirectoryTree(entry);
    syncDirectory(root);
    if(root.getParentFile()!=null)syncDirectory(root.getParentFile());
  }
  private static void syncDirectoryTree(File root) throws IOException {
    File[] entries=root.listFiles();
    if(entries==null)throw new IOException("Game data storage is unavailable.");
    for(File entry:entries){
      if(java.nio.file.Files.isSymbolicLink(entry.toPath()))throw new IOException("Invalid game data destination.");
      if(entry.isDirectory())syncDirectoryTree(entry);
    }
    syncDirectory(root);
  }
  private static void syncDirectory(File dir) throws IOException {
    if(!dir.isDirectory())throw new IOException("Cannot finish game data move.");
    FileDescriptor fd=null;
    try {fd=Os.open(dir.getPath(),OsConstants.O_RDONLY,0);Os.fsync(fd);}
    catch(ErrnoException e){throw new IOException("Cannot finish game data move.",e);}
    finally {if(fd!=null)try{Os.close(fd);}catch(ErrnoException ignored){}}
  }
  static boolean internal(Context context) {return root(context).equals(context.getFilesDir());}
}

package org.openbw.androidtest;

import java.io.File;
import java.nio.file.Files;

/** Reclaim abandoned work files only, before the first import/game in this process. */
final class NativeCache {
  private static boolean started;
  static synchronized void beginSession(File cache) {
    if (started) return;
    started = true;
    clean(cache, false);
    clean(new File(cache, "native-mpq"), true);
  }
  private static void clean(File directory, boolean engine) {
    if (Files.isSymbolicLink(directory.toPath())) return;
    File[] files = directory.listFiles();
    if (files == null) return;
    for (File file : files) {
      String name = file.getName();
      boolean temporary = name.matches("(?:map-import-|mission-export-|mission-map-|save-import-|saved-map-).+")
          || engine && (name.matches("(?:content[0-6]|mission)\\.tmp")
              || name.matches("cinematic\\.(?:mpq|stamp|tmp)"));
      if (temporary && file.isFile() && !Files.isSymbolicLink(file.toPath())) file.delete();
    }
  }
}

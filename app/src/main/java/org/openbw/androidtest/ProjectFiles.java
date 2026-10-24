package org.openbw.androidtest;

import java.io.File;

/** Keeps imported content available when upgrading to the StarDroid name. */
final class ProjectFiles {
  private static final String CURRENT = "StarDroid-", LEGACY = "OpenBW-";

  static String currentName(String name) {
    return name.startsWith(LEGACY) ? CURRENT + name.substring(LEGACY.length()) : name;
  }

  static File existing(File directory, String name) {
    File current = new File(directory, name);
    if (current.isFile() || !name.startsWith(CURRENT)) return current;
    File legacy = new File(directory, LEGACY + name.substring(CURRENT.length()));
    if (!legacy.isFile()) return current;
    // Same-directory rename; never overwrite a newer import. If a device cannot
    // rename the old file, keep reading it instead of requiring another import.
    if (!current.exists() && legacy.renameTo(current)) return current;
    return legacy;
  }
}

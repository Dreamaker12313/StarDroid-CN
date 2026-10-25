package org.openbw.androidtest;

import java.io.File;
import java.io.FileInputStream;
import java.security.MessageDigest;
import java.util.Locale;

/** Stream file fingerprints on the I/O worker; never include game payloads. */
final class DiagnosticFiles {
  static String describe(File file) {
    if (!file.isFile()) return file.getName() + ": MISSING\n";
    long length = file.length(), modified = file.lastModified();
    try (FileInputStream input = new FileInputStream(file)) {
      MessageDigest digest = MessageDigest.getInstance("SHA-256");
      byte[] buffer = new byte[65536];
      int count;
      while ((count = input.read(buffer)) != -1) digest.update(buffer, 0, count);
      if (file.length() != length || file.lastModified() != modified)
        return file.getName() + ": changed during report; regenerate after importing\n";
      StringBuilder hex = new StringBuilder();
      for (byte b : digest.digest()) hex.append(String.format(Locale.ROOT, "%02x", b & 255));
      return file.getName() + ": " + length + " bytes; SHA-256=" + hex + "\n";
    } catch (Exception error) {
      return file.getName() + ": " + length + " bytes; fingerprint unavailable: "
          + error.getClass().getSimpleName() + "\n";
    }
  }
}

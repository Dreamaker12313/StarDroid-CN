package org.openbw.androidtest;

import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Owned replay files. Compressed replay contents are validated by the native reader. */
final class NativeReplays {
  static final int LIMIT = 32 * 1024 * 1024;
  interface Validator { void check(byte[] bytes) throws Exception; }
  private static final Set<File> cleanedFolders = new HashSet<File>();
  private final File directory;

  NativeReplays(File files) {
    try { directory = new File(files.getCanonicalFile(), "replays"); }
    catch (IOException e) { throw new IllegalArgumentException("Replay folder is unavailable", e); }
  }

  private boolean folder(boolean create) throws IOException {
    if (Files.isSymbolicLink(directory.toPath())) throw new IOException("Invalid replay folder");
    if (!directory.exists()) {
      if (!create) return false;
      if (!directory.mkdirs() && !directory.isDirectory()) throw new IOException("Cannot create replay folder");
    }
    if (!directory.isDirectory() || !directory.getCanonicalFile().equals(directory))
      throw new IOException("Invalid replay folder");
    // One pass per folder/process, before the first writer creates a temporary
    // file. All entry points hold the class lock, including other store instances.
    if (cleanedFolders.add(directory)) {
      File[] leftovers = directory.listFiles();
      if (leftovers != null) for (File leftover : leftovers) {
        if (leftover.getName().matches("replay-[0-9]+\\.pending") && !Files.isSymbolicLink(leftover.toPath())
            && leftover.isFile() && directory.equals(leftover.getCanonicalFile().getParentFile()))
          leftover.delete();
      }
    }
    return true;
  }

  private File owned(File file) throws IOException {
    if (file == null || !folder(false) || Files.isSymbolicLink(file.toPath()))
      throw new IOException("Replay is unavailable");
    File canonical = file.getCanonicalFile();
    if (!directory.equals(canonical.getParentFile()) || !canonical.getName().toLowerCase(Locale.ROOT).endsWith(".rep"))
      throw new IOException("Replay is outside the replay folder");
    return canonical;
  }

  List<File> list() throws IOException {
    synchronized (NativeReplays.class) {
      ArrayList<File> replays = new ArrayList<File>();
      if (!folder(false)) return replays;
      File[] entries = directory.listFiles();
      if (entries == null) throw new IOException("Cannot read replay folder");
      for (File file : entries) {
        if (!file.getName().toLowerCase(Locale.ROOT).endsWith(".rep") || Files.isSymbolicLink(file.toPath())) continue;
        File candidate = owned(file);
        if (candidate.isFile() && candidate.length() >= 16 && candidate.length() <= LIMIT) replays.add(candidate);
      }
      Collections.sort(replays, (a,b) -> {
        int recent = Long.compare(b.lastModified(), a.lastModified());
        return recent != 0 ? recent : a.getName().compareToIgnoreCase(b.getName());
      });
      return replays;
    }
  }

  private static void size(int length) throws IOException {
    if (length < 16 || length > LIMIT) throw new IOException("Replay must be between 16 bytes and 32 MiB");
  }

  private static String hash(byte[] bytes) throws IOException {
    try {
      StringBuilder value = new StringBuilder();
      for (byte b : MessageDigest.getInstance("SHA-256").digest(bytes))
        value.append(String.format(Locale.ROOT, "%02x", b & 255));
      return value.toString();
    } catch (NoSuchAlgorithmException e) { throw new IOException("Cannot identify replay", e); }
  }

  private static String safeName(String name) {
    if (name == null) name = "Replay";
    name = name.replace('\\', '/');
    name = name.substring(name.lastIndexOf('/') + 1).replaceFirst("(?i)\\.rep$", "");
    StringBuilder safe = new StringBuilder();
    int count = 0;
    for (int i = 0; i < name.length() && count < 32;) {
      int point = name.codePointAt(i); i += Character.charCount(point);
      if (Character.isLetterOrDigit(point) || point == '-' || point == '_' || point == ' ') {
        safe.appendCodePoint(point); count++;
      }
    }
    String result = safe.toString().trim();
    return result.isEmpty() ? "Replay" : result;
  }

  File save(byte[] bytes, String name) throws IOException {
    if (bytes == null) throw new IOException("Replay is unavailable");
    size(bytes.length);
    synchronized (NativeReplays.class) {
      folder(true);
      String digest = hash(bytes), suffix = "--" + digest + ".rep";
      // Reimporting the same replay under another name does not waste storage.
      for (File existing : list()) if (existing.getName().endsWith(suffix)) {
        if (!Arrays.equals(bytes, read(existing))) throw new IOException("Stored replay is damaged");
        return existing;
      }
      File target = new File(directory, safeName(name) + suffix);
      if (target.exists() || Files.isSymbolicLink(target.toPath())) throw new IOException("Replay destination already exists");
      File pending = File.createTempFile("replay-", ".pending", directory);
      try {
        try (FileOutputStream out = new FileOutputStream(pending)) { out.write(bytes); out.getFD().sync(); }
        try { Files.move(pending.toPath(), target.toPath(), StandardCopyOption.ATOMIC_MOVE); }
        catch (AtomicMoveNotSupportedException e) { Files.move(pending.toPath(), target.toPath()); }
        return target;
      } finally { pending.delete(); }
    }
  }

  /** Storage-only overload; callers must validate compressed contents before playback. */
  File importReplay(InputStream input, String name) throws IOException {
    return save(readBounded(input), name);
  }

  File importReplay(InputStream input, String name, Validator validator) throws Exception {
    if (validator == null) throw new IllegalArgumentException("Replay validator is required");
    byte[] bytes = readBounded(input);
    validator.check(bytes);
    return save(bytes, name);
  }

  private static byte[] readBounded(InputStream input) throws IOException {
    if (input == null) throw new IOException("Replay is unavailable");
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    byte[] buffer = new byte[65536]; int n;
    while ((n = input.read(buffer)) != -1) {
      if (n == 0) {
        int one = input.read(); if (one == -1) break;
        if (out.size() == LIMIT) throw new IOException("Replay exceeds 32 MiB");
        out.write(one); continue;
      }
      if (n > LIMIT - out.size()) throw new IOException("Replay exceeds 32 MiB");
      out.write(buffer, 0, n);
    }
    size(out.size());
    return out.toByteArray();
  }

  byte[] read(File file) throws IOException {
    synchronized (NativeReplays.class) {
      File source = owned(file);
      if (!source.isFile() || source.length() < 16 || source.length() > LIMIT)
        throw new IOException("Replay is unavailable or too large");
      try (InputStream in = new FileInputStream(source)) { return readBounded(in); }
    }
  }

  void delete(File file) throws IOException {
    synchronized (NativeReplays.class) {
      File target = owned(file);
      if (!target.isFile() || !target.delete()) throw new IOException("Cannot delete replay");
    }
  }

  static String label(File file) {
    if (file == null) return "Replay";
    return file.getName().replaceFirst("--[0-9a-f]{64}(?i:\\.rep)$", "").replaceFirst("(?i)\\.rep$", "");
  }
}

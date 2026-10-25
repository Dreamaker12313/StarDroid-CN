package org.openbw.androidtest;

import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.zip.*;

/** Persistent melee map collection; imports remain bounded and never use ZIP paths. */
final class NativeMaps {
  static final int MAX_MAP = 64 * 1024 * 1024, MAX_COUNT = 10000, MAX_ENTRIES = 50000;
  static final long MAX_BATCH = 8L * 1024 * 1024 * 1024, STORAGE_RESERVE = 64L * 1024 * 1024;
  private static final Map<String,String> labels = new java.util.concurrent.ConcurrentHashMap<String,String>();
  interface Progress { void update(int complete, int total); }
  interface Validator { void check(File map) throws Exception; }
  static final class Imported {
    int accepted, rejected; File first; String failure = ""; List<File> collection;
  }
  static Imported importMaps(List<Staged> maps, File files, Validator validator, Progress progress) {
    Imported result = new Imported();
    try {
      for (Staged map : maps) {
        try {
          validator.check(map.file);
          File installed = install(map, files, true);
          if (result.first == null) result.first = installed;
          result.accepted++;
        } catch (Exception e) { result.rejected++; result.failure = e.getMessage(); }
        finally { map.file.delete(); }
        int done = result.accepted + result.rejected;
        if (done % 25 == 0 || done == maps.size()) progress.update(done, maps.size());
      }
    } finally { for (Staged map : maps) map.file.delete(); }
    result.collection = list(files); return result;
  }
  static void storage(File cache) throws IOException {
    if (cache.getUsableSpace() < STORAGE_RESERVE) throw new IOException("Not enough storage to import maps.");
  }
  static boolean isMap(String name) {
    String n = name.toLowerCase(Locale.ROOT);
    return n.endsWith(".scm") || n.endsWith(".scx");
  }
  static final class Staged {
    final File file; final String name;
    Staged(File file, String name) { this.file = file; this.name = name; }
  }
  static List<Staged> stage(InputStream stream, String name, File cache) throws IOException {
    ArrayList<Staged> result = new ArrayList<Staged>();
    try (BufferedInputStream in = new BufferedInputStream(stream)) {
      storage(cache);
      in.mark(4); int a = in.read(), b = in.read(); in.reset();
      if (a == 'P' && b == 'K') {
        ZipInputStream zip = new ZipInputStream(in); ZipEntry entry; long total = 0; int entries = 0;
        while ((entry = zip.getNextEntry()) != null) {
          if (++entries > MAX_ENTRIES) throw new IOException("Too many entries in map pack.");
          // Bound even ignored files: ZIPs may contain unrelated huge payloads.
          boolean map = !entry.isDirectory() && isMap(entry.getName());
          if (map && result.size() >= MAX_COUNT) throw new IOException("Import up to 10000 maps at once.");
          File target = map ? File.createTempFile("map-import-", ".scx", cache) : null;
          if (map) result.add(new Staged(target, new File(entry.getName().replace('\\','/')).getName()));
          try (OutputStream out = map ? new FileOutputStream(target) : new ByteArrayOutputStream(0)) {
            byte[] buffer = new byte[65536]; int count; long size = 0;
            while ((count = zip.read(buffer)) != -1) {
              total += count; size += count;
              if (total > MAX_BATCH) throw new IOException("Map pack exceeds 8 GiB.");
              if (map && size > MAX_MAP) throw new IOException("Map exceeds 64 MB.");
              if (map && size % (1024*1024) < count) storage(cache);
              if (map) out.write(buffer, 0, count);
            }
          }
          zip.closeEntry();
        }
      } else {
        if (!isMap(name)) throw new IOException("Choose a .scm, .scx, or ZIP map pack.");
        File target = File.createTempFile("map-import-", ".scx", cache);
        result.add(new Staged(target, name));
        try (OutputStream out = new FileOutputStream(target)) {
          byte[] buffer = new byte[65536]; int count; long size = 0;
          while ((count = in.read(buffer)) != -1) {
            size += count; if (size > MAX_MAP) throw new IOException("Map exceeds 64 MB.");
            if (size % (1024*1024) < count) storage(cache);
            out.write(buffer, 0, count);
          }
        }
      }
      if (result.isEmpty()) throw new IOException("No .scm or .scx maps in this ZIP.");
      return result;
    } catch (IOException e) { for (Staged map : result) map.file.delete(); throw e; }
  }
  static File install(Staged staged, File files) throws Exception { return install(staged, files, false); }
  static File install(Staged staged, File files, boolean consume) throws Exception {
    MessageDigest sha = MessageDigest.getInstance("SHA-256");
    try (InputStream in = new FileInputStream(staged.file)) {
      byte[] buffer = new byte[65536]; int count;
      while ((count = in.read(buffer)) != -1) sha.update(buffer, 0, count);
    }
    StringBuilder hash = new StringBuilder(); for (byte v : sha.digest()) hash.append(String.format(Locale.ROOT, "%02x", v & 255));
    File dir = new File(files, "melee-maps"); if (!dir.isDirectory() && !dir.mkdirs()) throw new IOException("Cannot save maps.");
    // Hash names deduplicate imports, including differently named copies.
    File target = new File(dir, hash + ".scx");
    if (!target.isFile()) {
      // Cache and files normally share a volume: promote without a second full copy.
      if (!consume || !staged.file.renameTo(target)) {
        File pending = File.createTempFile("map-", ".pending", dir);
        try { Files.copy(staged.file.toPath(), pending.toPath(), StandardCopyOption.REPLACE_EXISTING);
          Files.move(pending.toPath(), target.toPath(), StandardCopyOption.REPLACE_EXISTING);
        } finally { pending.delete(); }
      }
    }
    String label = staged.name.replace('\\', '/'); label = label.substring(label.lastIndexOf('/') + 1);
    Files.write(new File(dir, hash + ".name").toPath(), label.getBytes("UTF-8"));
    labels.put(target.getAbsolutePath(), label.replaceFirst("(?i)\\.(scm|scx)$", ""));
    return target;
  }
  static String label(File map) {
    if (map == null) return "Weave";
    String hit = labels.get(map.getAbsolutePath()); if (hit != null) return hit;
    try { String value = new String(Files.readAllBytes(new File(map.getParentFile(), map.getName().replace(".scx", ".name")).toPath()), "UTF-8").replaceFirst("(?i)\\.(scm|scx)$", ""); labels.put(map.getAbsolutePath(), value); return value; }
    catch (Exception e) { return map.getName(); }
  }
  static List<File> list(File files) {
    ArrayList<File> maps = new ArrayList<File>();
    File[] saved = new File(files, "melee-maps").listFiles((d, n) -> n.endsWith(".scx"));
    if (saved != null) { maps.addAll(Arrays.asList(saved)); Collections.sort(maps, (a,b) -> label(a).compareToIgnoreCase(label(b))); }
    maps.add(0, null); return maps;
  }
}

package org.openbw.androidtest;

import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.zip.*;

/** Persistent melee map collection; imports remain bounded and never use ZIP paths. */
final class NativeMaps {
  static final int MAX_MAP = 64 * 1024 * 1024, MAX_BATCH = 256 * 1024 * 1024, MAX_COUNT = 128;
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
      in.mark(4); int a = in.read(), b = in.read(); in.reset();
      if (a == 'P' && b == 'K') {
        ZipInputStream zip = new ZipInputStream(in); ZipEntry entry; long total = 0;
        while ((entry = zip.getNextEntry()) != null) {
          // Bound even ignored files: ZIPs may contain unrelated huge payloads.
          boolean map = !entry.isDirectory() && isMap(entry.getName());
          if (map && result.size() >= MAX_COUNT) throw new IOException("Import up to 128 maps at once.");
          File target = map ? File.createTempFile("map-import-", ".scx", cache) : null;
          if (map) result.add(new Staged(target, new File(entry.getName().replace('\\','/')).getName()));
          try (OutputStream out = map ? new FileOutputStream(target) : new ByteArrayOutputStream(0)) {
            byte[] buffer = new byte[65536]; int count, size = 0;
            while ((count = zip.read(buffer)) != -1) {
              total += count; size += count;
              if (total > MAX_BATCH || (map && size > MAX_MAP)) throw new IOException("Map pack exceeds the import size limit.");
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
          byte[] buffer = new byte[65536]; int count, size = 0;
          while ((count = in.read(buffer)) != -1) {
            size += count; if (size > MAX_MAP) throw new IOException("Map exceeds 64 MB.");
            out.write(buffer, 0, count);
          }
        }
      }
      if (result.isEmpty()) throw new IOException("No .scm or .scx maps in this ZIP.");
      return result;
    } catch (IOException e) { for (Staged map : result) map.file.delete(); throw e; }
  }
  static File install(Staged staged, File files) throws Exception {
    MessageDigest sha = MessageDigest.getInstance("SHA-256");
    try (InputStream in = new FileInputStream(staged.file)) {
      byte[] buffer = new byte[65536]; int count;
      while ((count = in.read(buffer)) != -1) sha.update(buffer, 0, count);
    }
    StringBuilder hash = new StringBuilder(); for (byte v : sha.digest()) hash.append(String.format(Locale.ROOT, "%02x", v & 255));
    File dir = new File(files, "melee-maps"); if (!dir.isDirectory() && !dir.mkdirs()) throw new IOException("Cannot save maps.");
    // Hash names deduplicate imports, including differently named copies.
    File target = new File(dir, hash + ".scx");
    if (!target.isFile()) Files.copy(staged.file.toPath(), target.toPath());
    String label = staged.name.replace('\\', '/'); label = label.substring(label.lastIndexOf('/') + 1);
    Files.write(new File(dir, hash + ".name").toPath(), label.getBytes("UTF-8"));
    return target;
  }
  static String label(File map) {
    if (map == null) return "Weave";
    try { return new String(Files.readAllBytes(new File(map.getParentFile(), map.getName().replace(".scx", ".name")).toPath()), "UTF-8").replaceFirst("(?i)\\.(scm|scx)$", ""); }
    catch (Exception e) { return map.getName(); }
  }
  static List<File> list(File files) {
    ArrayList<File> maps = new ArrayList<File>();
    File[] saved = new File(files, "melee-maps").listFiles((d, n) -> n.endsWith(".scx"));
    if (saved != null) { maps.addAll(Arrays.asList(saved)); Collections.sort(maps, (a,b) -> label(a).compareToIgnoreCase(label(b))); }
    maps.add(0, null); return maps;
  }
}

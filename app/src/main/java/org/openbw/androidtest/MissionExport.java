package org.openbw.androidtest;

import java.io.*;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.zip.*;
import org.json.*;

/** Exports only catalogued campaign maps, without changing installed content. */
final class MissionExport {
  static final String NAME = "StarDroid-Missions.zip";

  static final class Result {
    final File file;
    final int count;
    Result(File file, int count) { this.file = file; this.count = count; }
  }

  static int installedCount(File directory) {
    int count = 0;
    for (Object[] mission : CampaignCatalog.ALL)
      if (ProjectFiles.existing(directory, CampaignData.filename((String) mission[1])).isFile()) count++;
    return count;
  }

  static Result create(File directory, File cache) throws IOException {
    if (installedCount(directory) == 0)
      throw new IOException("No mission maps are installed. Import your campaign files first.");
    File destination = File.createTempFile("mission-export-", ".zip", cache);
    boolean complete = false;
    try {
      JSONArray included = new JSONArray(), missing = new JSONArray();
      try (ZipOutputStream zip = new ZipOutputStream(new BufferedOutputStream(new FileOutputStream(destination)))) {
        for (Object[] mission : CampaignCatalog.ALL) {
          String id = (String) mission[1];
          File source = ProjectFiles.existing(directory, CampaignData.filename(id));
          if (!source.isFile()) { missing.put(id); continue; }
          File compact = File.createTempFile("mission-map-", ".zip", cache);
          try {
            if (!id.equals(CampaignData.validate(source))) throw new IOException("Mission name does not match its file");
            writeMap(source, compact, id);
            String entry = "missions/" + CampaignData.filename(id);
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            zip.putNextEntry(new ZipEntry(entry));
            try (InputStream in = new BufferedInputStream(new FileInputStream(compact))) {
              byte[] buffer = new byte[65536]; int n;
              while ((n = in.read(buffer)) != -1) { zip.write(buffer, 0, n); digest.update(buffer, 0, n); }
            }
            zip.closeEntry();
            StringBuilder hash = new StringBuilder();
            for (byte b : digest.digest()) hash.append(String.format(Locale.ROOT, "%02x", b & 255));
            included.put(new JSONObject().put("mission", id).put("title", mission[2])
                .put("file", entry).put("sha256", hash.toString()));
          } catch (Exception error) {
            throw new IOException("Could not export " + mission[2] + ": " + error.getMessage(), error);
          } finally { compact.delete(); }
        }
        put(zip, "manifest.json", new JSONObject().put("format", "openbw-mission-export-v1")
            .put("mapsOnly", true).put("missions", included).put("notInstalled", missing).toString(2));
        put(zip, "README.txt", "StarDroid mission maps\n\n"
            + included.length() + " installed campaign maps are included. Upload this ZIP to the project chat.\n"
            + "Contains original map data, unit placements, alliances, briefing text and triggers.\n"
            + "Voices, movies, core game archives, saves and personal settings are not included.\n\n"
            + "Each missions/*.zip is an openbw-mission-bundle-v1 containing only scenario.chk.\n"
            + "Original compressed/encrypted MPQ bytes, offsets and tables are preserved.\n"
            + "The source project's scripts/rebuild_mission_mpq.py can reconstruct each sparse MPQ.\n"
            + "Use the scenario path in its manifest with an MPQ reader to extract scenario.chk.\n"
            + "These map-only bundles are for inspection; keep the full installed bundles for play.\n");
      }
      complete = true;
      return new Result(destination, included.length());
    } catch (JSONException error) {
      throw new IOException("Could not write the mission list", error);
    } finally { if (!complete) destination.delete(); }
  }

  private static void writeMap(File source, File destination, String id) throws Exception {
    try (ZipFile input = new ZipFile(source);
        ZipOutputStream output = new ZipOutputStream(new BufferedOutputStream(new FileOutputStream(destination)))) {
      JSONObject original = new JSONObject(new String(NativeData.read(
          input.getInputStream(input.getEntry("manifest.json")), 131072), "UTF-8"));
      JSONArray entries = original.getJSONArray("entries");
      String name = CampaignCatalog.prefix(id) + "staredit\\scenario.chk";
      JSONObject scenario = null;
      for (int i = 0; i < entries.length(); i++) {
        JSONObject item = entries.getJSONObject(i);
        if (item.getString("name").equalsIgnoreCase(name)) {
          if (scenario != null) throw new IOException("Duplicate mission map");
          scenario = item;
        }
      }
      if (scenario == null) throw new IOException("Mission map is missing");
      JSONObject map = new JSONObject();
      for (String key : new String[] {"name", "block", "offset", "packedSize", "size", "flags", "hashSlots"})
        map.put(key, scenario.get(key));
      JSONObject manifest = new JSONObject().put("format", "openbw-mission-bundle-v1")
          .put("mission", id).put("entries", new JSONArray().put(map));
      for (String key : new String[] {"archiveSize", "sourceSize"})
        if (original.has(key)) manifest.put(key, original.getLong(key));
      put(output, "manifest.json", manifest.toString(2));
      copyEntry(input, output, "header.bin", 32);
      copyEntry(input, output, "hash-table.bin", 8L * 1024 * 1024);
      copyEntry(input, output, "block-table.bin", 8L * 1024 * 1024);
      copyEntry(input, output, "blocks/" + scenario.getInt("block") + ".bin", 64L * 1024 * 1024);
    }
    CampaignData.validate(destination);
  }

  private static void copyEntry(ZipFile source, ZipOutputStream destination, String name, long limit) throws IOException {
    ZipEntry entry = source.getEntry(name);
    if (entry == null || entry.getSize() < 1 || entry.getSize() > limit) throw new IOException("Invalid " + name);
    destination.putNextEntry(new ZipEntry(name));
    CRC32 crc = new CRC32(); long count = 0;
    try (InputStream input = source.getInputStream(entry)) {
      byte[] buffer = new byte[65536]; int n;
      while ((n = input.read(buffer)) != -1) {
        count += n;
        if (count > limit || count > entry.getSize()) throw new IOException("Oversized " + name);
        destination.write(buffer, 0, n); crc.update(buffer, 0, n);
      }
    }
    if (count != entry.getSize() || crc.getValue() != entry.getCrc()) throw new IOException("Damaged " + name);
    destination.closeEntry();
  }

  private static void put(ZipOutputStream output, String name, String value) throws IOException {
    output.putNextEntry(new ZipEntry(name)); output.write(value.getBytes("UTF-8")); output.closeEntry();
  }
}

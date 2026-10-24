package org.openbw.androidtest;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Bounded local access to the user's small export ZIP; never unpacks paths. */
final class CampaignData {
    private static final long MAX_BUNDLE = 160L * 1024 * 1024;
    static final String NAME = "StarDroid-Terran01.zip";
    static void copy(InputStream input, File destination) throws IOException {
        File temporary = new File(destination.getPath() + ".import");
        try {
            try (FileOutputStream out = new FileOutputStream(temporary)) {
                byte[] buffer = new byte[65536]; int n; long total = 0;
                while ((n = input.read(buffer)) != -1) {
                    total += n; if (total > MAX_BUNDLE) throw new IOException("Select a small mission export ZIP.");
                    out.write(buffer, 0, n);
                }
                out.getFD().sync();
            }
            String mission = validate(temporary);
            String destinationName = ProjectFiles.currentName(destination.getName());
            if (destinationName.matches("StarDroid-[A-Za-z0-9]+\\.zip") && !destinationName.equals(filename(mission))) throw new IOException("Wrong mission for this destination.");
            Files.move(temporary.toPath(), destination.toPath(), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } finally { temporary.delete(); }
    }
    static String validate(File file) throws IOException {
        try (ZipFile zip = new ZipFile(file)) {
            if (file.length() > MAX_BUNDLE || zip.size() > 264) throw new IOException("Mission ZIP is too large.");
            byte[] raw;
            try (InputStream in = openEntry(zip, "manifest.json", 131072)) {
                ByteArrayOutputStream out = new ByteArrayOutputStream(); byte[] b = new byte[4096]; int n;
                while ((n = in.read(b)) != -1) out.write(b, 0, n);
                raw = out.toByteArray();
            }
            JSONObject m = new JSONObject(new String(raw, "UTF-8"));
            if (!"openbw-mission-bundle-v1".equals(m.getString("format")) || !CampaignCatalog.supported(m.getString("mission"))) throw new IOException("This is not a supported mission export.");
            String mission = m.getString("mission");
            require(zip, "header.bin", 32); bounded(zip, "hash-table.bin", 8*1024*1024); bounded(zip, "block-table.bin", 8*1024*1024);
            JSONArray entries = m.getJSONArray("entries");
            if (entries.length() < 1 || entries.length() > 256) throw new IOException("Invalid mission entries.");
            boolean scenario = false; long total = 0; HashSet<Integer> blocks = new HashSet<Integer>();
            for (int i=0;i<entries.length();i++) {
                JSONObject e = entries.getJSONObject(i); int block = e.getInt("block");
                String name = e.getString("name").toLowerCase(Locale.ROOT);
                String prefix = CampaignCatalog.prefix(mission) + "staredit\\";
                if (!name.startsWith(prefix) || !name.substring(prefix.length()).matches("(?:scenario\\.chk|wav\\\\[a-z0-9 _'-]{1,80}\\.wav)")) throw new IOException("Unexpected mission filename.");
                if (name.endsWith("scenario.chk")) scenario = true;
                if (block < 0 || block > 524287 || !blocks.add(block)) throw new IOException("Invalid mission block.");
                long packed = e.getLong("packedSize");
                if (packed < 1 || packed > 64L*1024*1024) throw new IOException("Mission entry is too large.");
                total += packed; if (total > 128L*1024*1024) throw new IOException("Mission data is too large.");
                require(zip, "blocks/" + block + ".bin", packed);
            }
            if (!scenario) throw new IOException("The mission map is missing.");
            return mission;
        } catch (JSONException e) { throw new IOException("Invalid mission manifest: " + e.getMessage(), e); }
    }
    static String filename(String mission) { return "StarDroid-" + Character.toUpperCase(mission.charAt(0)) + mission.substring(1) + ".zip"; }
    static String install(InputStream input, File directory) throws IOException {
        File stage = new File(directory, "campaign-install.zip");
        try {
            copy(input, stage);
            String mission = validate(stage);
            File target = new File(directory, filename(mission));
            Files.move(stage.toPath(), target.toPath(), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            return mission;
        } finally { stage.delete(); }
    }
    private static void bounded(ZipFile zip, String name, long max) throws IOException {
        ZipEntry e = zip.getEntry(name); if (e == null || e.getSize() < 1 || e.getSize() > max) throw new IOException("Missing or invalid " + name);
    }
    private static void require(ZipFile zip, String name, long length) throws IOException {
        ZipEntry e = zip.getEntry(name); if (e == null || e.getSize() != length) throw new IOException("Missing or damaged " + name);
    }
    private static InputStream openEntry(ZipFile zip, String name, long limit) throws IOException {
        bounded(zip, name, limit);
        return new FilterInputStream(zip.getInputStream(zip.getEntry(name))) {
            private long seen;
            private void count(int n) throws IOException {
                if (n > 0) seen += n;
                if (seen > limit) throw new IOException("Mission entry exceeds its size limit.");
            }
            @Override public int read() throws IOException { int n = in.read(); count(n < 0 ? 0 : 1); return n; }
            @Override public int read(byte[] b, int off, int len) throws IOException { int n = in.read(b, off, len); count(n); return n; }
        };
    }
    static InputStream open(File file, String name) throws IOException {
        if (!(name.equals("manifest.json") || name.equals("header.bin") || name.equals("hash-table.bin") || name.equals("block-table.bin") || name.matches("blocks/[0-9]+\\.bin"))) throw new IOException("Unknown mission resource.");
        final ZipFile zip = new ZipFile(file);
        try {
            final InputStream stream = openEntry(zip, name, 64L*1024*1024);
            return new FilterInputStream(stream) { @Override public void close() throws IOException { try { super.close(); } finally { zip.close(); } } };
        } catch (IOException e) { zip.close(); throw e; }
    }
}

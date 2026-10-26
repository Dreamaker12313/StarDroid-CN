package org.openbw.androidtest;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Original fonts and optional menu artwork stay private on this device. */
final class InterfaceData {
    static final String NAME = "StarDroid-Interface.zip";
    static final String[] FONT_SIZES = {"8","10","12","14","16","16x","32","50"};
    static final String[] MENU_FONTS = {"8","10","14","16","16x"};
    static List<String> names() {
        ArrayList<String> names = new ArrayList<String>();
        for (String prefix : new String[]{"files\\font\\", "font\\"})
            for (String n : FONT_SIZES)
                names.add(prefix + "font" + n + ".fnt");
        for (String n : new String[]{"backgnd.pcx","tfont.pcx","teffect.pcx","dlg.grp","tile.grp"})
            names.add("glue\\palcs\\" + n);
        for (String n : new String[]{"plistmap2.pcx","pinfo.pcx","pslots.pcx"})
            names.add("glue\\create\\" + n);
        // The original load-list layout and its panel are on the campaign CD,
        // rather than in every installed StarDat/BrooDat version. Keep optional
        // so earlier bundles and core-only installs continue to work.
        names.add("rez\\gluload.bin");
        for (String n : new String[]{"plist.pcx","pinfo.pcx"}) names.add("glue\\load\\" + n);
        for (String n : new String[]{"pcancel.pcx","pok.pcx"}) names.add("glue\\palnl\\" + n);
        return names;
    }
    static void install(File temporary, File target) throws IOException {
        validate(temporary);
        if (target.isFile()) {
            Set<String> previous = new LinkedHashSet<String>();
            try { validate(target); previous.addAll(menuFiles(target)); } catch (IOException ignored) {}
            previous.removeAll(menuFiles(temporary));
            if (!previous.isEmpty()) throw new IOException("Your existing interface was kept because this replacement lacks previously imported menu files: "
                + String.join(", ", previous) + ".");
        }
        Files.move(temporary.toPath(), target.toPath(), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
    }
    static String importArchive(java.nio.channels.FileChannel input, File directory,
                                MissionBundle.Progress progress) throws IOException {
        File stage = new File(directory, "interface-import.tmp"), target = new File(directory, NAME);
        try {
            try (FileOutputStream out = new FileOutputStream(stage)) {
                MissionBundle.exportInterface(input, names(), out, progress);
            }
            install(stage, target);
            return "Available interface files imported.";
        } finally { stage.delete(); }
    }
    static String installedSummary(File file) {
        try {
            if (file.isFile()) {
                validate(file);
                if (hasCampaignPalette(file)) return "✓ Campaign artwork";
            }
        } catch (IOException ignored) {}
        return "○ Campaign artwork";
    }
    static String summary(File file) {
        if (!file.isFile()) return "Menu fonts and campaign artwork: interface bundle missing.";
        try {
            validate(file);
            Set<String> entries = entries(file);
            int fonts = 0;
            for (String size : MENU_FONTS) if (hasFont(entries, size)) fonts++;
            List<String> missing = missingMenuFiles(file);
            return "Menu font entries imported: " + fonts + " / " + MENU_FONTS.length
                + ". Campaign artwork: " + (hasCampaignPalette(file) ? "imported." : "incomplete.")
                + (missing.isEmpty() ? "" : " Missing: " + String.join(", ", missing) + ".")
                + (fonts < MENU_FONTS.length ? " Missing sizes automatically use another available original font, or a styled Android font if none can be read." : "")
                + " Decoding results are shown in the diagnostic report.";
        } catch (IOException error) { return "Interface bundle needs repair: " + error.getMessage(); }
    }
    static String details(File file) {
        StringBuilder result = new StringBuilder(summary(file)).append('\n');
        if (!file.isFile()) return result.toString();
        try (ZipFile zip = new ZipFile(file)) {
            JSONObject manifest = readManifest(zip);
            result.append("Original archive bytes: ").append(manifest.optLong("sourceSize", -1)).append('\n');
            Set<String> present = entries(file);
            for (String size : FONT_SIZES) if (!hasFont(present, size))
                result.append("Missing font").append(size).append(".fnt (both font locations checked)")
                    .append(Arrays.asList(MENU_FONTS).contains(size) ? " [menu font]\n" : " [not required by these menus]\n");
            JSONArray entries = manifest.getJSONArray("entries");
            for (int i = 0; i < Math.min(entries.length(), names().size()); i++) {
                JSONObject e = entries.getJSONObject(i);
                result.append(e.getString("name")).append(": packed=").append(e.getLong("packedSize"))
                    .append("; decoded=").append(e.getLong("size")).append('\n');
            }
        } catch (Exception error) { result.append("Manifest unreadable: ").append(error.getMessage()).append('\n'); }
        return result.toString();
    }
    static boolean hasCampaignPalette(File file) throws IOException {
        Set<String> names = entries(file);
        return names.contains("glue\\palcs\\backgnd.pcx") && names.contains("glue\\palcs\\tfont.pcx");
    }
    private static boolean hasFont(Set<String> entries, String size) {
        String name = "font\\font" + size + ".fnt";
        return entries.contains(name) || entries.contains("files\\" + name);
    }
    private static Set<String> entries(File file) throws IOException {
        try (ZipFile zip = new ZipFile(file)) {
            JSONObject manifest = readManifest(zip);
            JSONArray entries = manifest.getJSONArray("entries");
            Set<String> names = new LinkedHashSet<String>();
            for (int i=0; i<entries.length(); i++)
                names.add(entries.getJSONObject(i).getString("name").replace('/', '\\').toLowerCase(Locale.ROOT));
            return names;
        } catch (JSONException error) { throw new IOException("Invalid interface manifest.", error); }
    }
    private static Set<String> menuFiles(File file) throws IOException {
        Set<String> present = entries(file), result = new LinkedHashSet<String>();
        for (String size : MENU_FONTS) if (hasFont(present, size)) result.add("font" + size + ".fnt");
        for (String name : new String[]{"backgnd.pcx", "tfont.pcx"})
            if (present.contains("glue\\palcs\\" + name)) result.add("glue/palcs/" + name);
        return result;
    }
    static List<String> missingMenuFiles(File file) throws IOException {
        List<String> result = new ArrayList<String>();
        Set<String> present = menuFiles(file);
        for (String size : MENU_FONTS) if (!present.contains("font" + size + ".fnt")) result.add("font" + size + ".fnt");
        for (String name : new String[]{"backgnd.pcx", "tfont.pcx"})
            if (!present.contains("glue/palcs/" + name)) result.add("glue/palcs/" + name);
        return result;
    }
    private static JSONObject readManifest(ZipFile zip) throws IOException, JSONException {
        ZipEntry entry = zip.getEntry("manifest.json");
        if (entry == null || entry.getSize() < 1 || entry.getSize() > 131072)
            throw new IOException("Missing or oversized interface manifest.");
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (InputStream in = zip.getInputStream(entry)) {
            byte[] bytes = new byte[4096]; int count;
            while ((count=in.read(bytes)) != -1) {
                if (out.size()+count>131072) throw new IOException("Manifest too large.");
                out.write(bytes,0,count);
            }
        }
        return new JSONObject(new String(out.toByteArray(), "UTF-8"));
    }
    static void validate(File file) throws IOException {
        try (ZipFile zip = new ZipFile(file)) {
            if (file.length() > 20L*1024*1024 || zip.size() > names().size() + 5) throw new IOException("Interface import is too large.");
            JSONObject m = readManifest(zip);
            if (!"openbw-interface-bundle-v1".equals(m.getString("format"))) throw new IOException("Invalid interface format.");
            for (String n : new String[]{"header.bin","hash-table.bin","block-table.bin"}) {
                ZipEntry e = zip.getEntry(n);
                if (e == null || e.getSize() < 1 || e.getSize() > 8*1024*1024 || (n.equals("header.bin") && e.getSize()!=32)) throw new IOException("Missing MPQ metadata.");
            }
            JSONArray entries = m.getJSONArray("entries");
            if (entries.length() < 1 || entries.length() > names().size()) throw new IOException("Invalid interface entries.");
            Set<String> allowed = new HashSet<String>(names()); Set<Integer> blocks = new HashSet<Integer>(); long total = 0;
            for (int i=0;i<entries.length();i++) {
                JSONObject e = entries.getJSONObject(i);int block = e.getInt("block");
                String name = e.getString("name").replace('/', '\\').toLowerCase(Locale.ROOT);
                if (!allowed.contains(name) || block<0 || block>524287 || !blocks.add(block)) throw new IOException("Invalid interface entry.");
                long size = e.getLong("packedSize"), unpacked = e.getLong("size");
                ZipEntry packed = zip.getEntry("blocks/"+block+".bin");
                // A 640 x 480 8-bit PCX can exceed 256 KiB before MPQ compression.
                if (size<1 || size>1048576L || unpacked<1 || unpacked>1048576L || packed==null || packed.getSize()!=size)
                    throw new IOException("Damaged or oversized interface entry: " + name + " (packed=" + size + ", decoded=" + unpacked + "; limit=1048576 bytes).");
                total+=size;if(total>4L*1024*1024)throw new IOException("Interface import is too large.");
            }
            // Optional fonts must not invalidate other fonts or campaign artwork.
            // Missing entries are reported independently; corrupt ZIP metadata,
            // unexpected paths, missing payloads and size limits still fail above.
        } catch (JSONException e) { throw new IOException("Invalid interface manifest.", e); }
    }
}

package org.openbw.androidtest;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Music stays private on this device, separate from the campaign import. */
final class MusicData {
    static final String NAME = "StarDroid-Music.zip";
    static List<String> names() {
        ArrayList<String> names = new ArrayList<String>();
        for (String race : new String[]{"terran", "protoss", "zerg"})
            for (int n=1;n<=3;n++) names.add("music\\" + race + n + ".wav");
        for (String n : new String[]{"trdyroom","prdyroom","zrdyroom","tvict","pvict","zvict","tdefeat","pdefeat","zdefeat","title"})
            names.add("music\\" + n + ".wav");
        return names;
    }
    static void install(File temporary, File target) throws IOException {
        validate(temporary);
        Files.move(temporary.toPath(), target.toPath(), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
    }
    static void validate(File file) throws IOException {
        try (ZipFile zip = new ZipFile(file)) {
            if (file.length() > 160L*1024*1024 || zip.size() > 32) throw new IOException("Music import is too large.");
            ZipEntry me = zip.getEntry("manifest.json");
            if (me == null || me.getSize() < 1 || me.getSize() > 131072) throw new IOException("Missing music manifest.");
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            try (InputStream in = zip.getInputStream(me)) {
                byte[] b = new byte[4096]; int n;
                while ((n=in.read(b)) != -1) { if (out.size()+n>131072) throw new IOException("Manifest too large.");out.write(b,0,n); }
            }
            JSONObject m = new JSONObject(new String(out.toByteArray(), "UTF-8"));
            if (!"openbw-music-bundle-v1".equals(m.getString("format"))) throw new IOException("Invalid music format.");
            for (String n : new String[]{"header.bin","hash-table.bin","block-table.bin"}) {
                ZipEntry e = zip.getEntry(n);
                if (e == null || e.getSize() < 1 || e.getSize() > 8*1024*1024 || (n.equals("header.bin") && e.getSize()!=32)) throw new IOException("Missing MPQ metadata.");
            }
            JSONArray entries = m.getJSONArray("entries");
            if (entries.length() < 1 || entries.length() > 19) throw new IOException("Invalid music entries.");
            Set<String> allowed = new HashSet<String>(names()); Set<Integer> blocks = new HashSet<Integer>(); long total = 0;
            for (int i=0;i<entries.length();i++) {
                JSONObject e = entries.getJSONObject(i);int block = e.getInt("block");
                if (!allowed.contains(e.getString("name").toLowerCase(Locale.ROOT)) || block<0 || block>524287 || !blocks.add(block)) throw new IOException("Invalid music entry.");
                long size = e.getLong("packedSize"), unpacked = e.getLong("size");
                ZipEntry packed = zip.getEntry("blocks/"+block+".bin");
                if (size<1 || size>64L*1024*1024 || unpacked<1 || unpacked>64L*1024*1024 || packed==null || packed.getSize()!=size) throw new IOException("Damaged music entry.");
                total+=size;if(total>128L*1024*1024)throw new IOException("Music import is too large.");
            }
        } catch (JSONException e) { throw new IOException("Invalid music manifest.", e); }
    }
}

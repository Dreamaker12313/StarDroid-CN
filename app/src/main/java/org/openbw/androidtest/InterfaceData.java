package org.openbw.androidtest;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Original fonts and campaign palette stay private on this device. */
final class InterfaceData {
    static final String NAME = "StarDroid-Interface.zip";
    static List<String> names() {
        ArrayList<String> names = new ArrayList<String>();
        for (String prefix : new String[]{"files\\font\\"})
            for (String n : new String[]{"8","10","12","14","16","16x","32","50"})
                names.add(prefix + "font" + n + ".fnt");
        for (String n : new String[]{"backgnd.pcx","tfont.pcx","teffect.pcx","dlg.grp","tile.grp"})
            names.add("glue\\palcs\\" + n);
        for (String n : new String[]{"plistmap2.pcx","pinfo.pcx","pslots.pcx"})
            names.add("glue\\create\\" + n);
        return names;
    }
    static void install(File temporary, File target) throws IOException {
        validate(temporary);
        Files.move(temporary.toPath(), target.toPath(), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
    }
    static void validate(File file) throws IOException {
        try (ZipFile zip = new ZipFile(file)) {
            if (file.length() > 20L*1024*1024 || zip.size() > 32) throw new IOException("Interface import is too large.");
            ZipEntry me = zip.getEntry("manifest.json");
            if (me == null || me.getSize() < 1 || me.getSize() > 131072) throw new IOException("Missing interface manifest.");
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            try (InputStream in = zip.getInputStream(me)) {
                byte[] b = new byte[4096]; int n;
                while ((n=in.read(b)) != -1) { if (out.size()+n>131072) throw new IOException("Manifest too large.");out.write(b,0,n); }
            }
            JSONObject m = new JSONObject(new String(out.toByteArray(), "UTF-8"));
            if (!"openbw-interface-bundle-v1".equals(m.getString("format"))) throw new IOException("Invalid interface format.");
            for (String n : new String[]{"header.bin","hash-table.bin","block-table.bin"}) {
                ZipEntry e = zip.getEntry(n);
                if (e == null || e.getSize() < 1 || e.getSize() > 8*1024*1024 || (n.equals("header.bin") && e.getSize()!=32)) throw new IOException("Missing MPQ metadata.");
            }
            JSONArray entries = m.getJSONArray("entries");
            if (entries.length() < 1 || entries.length() > names().size()) throw new IOException("Invalid interface entries.");
            Set<String> allowed = new HashSet<String>(names()); Set<Integer> blocks = new HashSet<Integer>(); Set<String> fonts = new HashSet<String>(); long total = 0;
            for (int i=0;i<entries.length();i++) {
                JSONObject e = entries.getJSONObject(i);int block = e.getInt("block");
                if (!allowed.contains(e.getString("name").toLowerCase(Locale.ROOT)) || block<0 || block>524287 || !blocks.add(block)) throw new IOException("Invalid interface entry.");
                String name = e.getString("name").toLowerCase(Locale.ROOT);
                if (name.startsWith("files\\font\\") && name.endsWith(".fnt")) fonts.add(name);
                long size = e.getLong("packedSize"), unpacked = e.getLong("size");
                ZipEntry packed = zip.getEntry("blocks/"+block+".bin");
                if (size<1 || size>262144L || unpacked<1 || unpacked>262144L || packed==null || packed.getSize()!=size) throw new IOException("Damaged interface entry.");
                total+=size;if(total>4L*1024*1024)throw new IOException("Interface import is too large.");
            }
            if (fonts.size() != 8) throw new IOException("The original font set is incomplete. Choose the large StarCraft.mpq or original Install.exe.");
        } catch (JSONException e) { throw new IOException("Invalid interface manifest.", e); }
    }
}

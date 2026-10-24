package org.openbw.androidtest;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/** Read-only, bounded MPQ entry export. Payload bytes retain their original
 * compression/encryption; the companion script rebuilds a readable MPQ without
 * asking Android to decode any Blizzard audio format. No whole-archive copy. */
public final class MissionBundle {
    public interface Progress { void update(String message); }
    public static final String MISSION = "campaign\\terran\\terran01\\staredit\\scenario.chk";
    private static final int[] CRYPT = makeCrypt();
    private static final long LIMIT = 128L * 1024 * 1024;
    private MissionBundle() { }

    public static final class Result {
        public int files;
        public long packedBytes;
        public final List<String> missing = new ArrayList<String>();
    }
    private static final class Entry {
        String name;
        int block;
        long offset, packed, size, flags;
        final List<Integer> slots = new ArrayList<Integer>();
    }
    private static int[] makeCrypt() {
        int[] table = new int[1280]; long seed = 0x100001;
        for (int i = 0; i < 256; i++) for (int j = 0; j < 5; j++) {
            seed = (seed * 125 + 3) % 0x2AAAAB;
            int high = (int)(seed & 0xffff) << 16;
            seed = (seed * 125 + 3) % 0x2AAAAB;
            table[i + 256 * j] = high | (int)(seed & 0xffff);
        }
        return table;
    }
    private static int hash(String value, int type) {
        int a = 0x7fed7fed, b = 0xeeeeeeee;
        for (byte v : value.replace('/', '\\').toUpperCase(Locale.ROOT).getBytes(StandardCharsets.ISO_8859_1)) {
            int c = v & 255;
            a = CRYPT[(type << 8) + c] ^ (a + b);
            b = c + a + b + (b << 5) + 3;
        }
        return a;
    }
    private static byte[] decrypt(byte[] source, int key) {
        ByteBuffer input = ByteBuffer.wrap(source).order(ByteOrder.LITTLE_ENDIAN);
        ByteBuffer output = ByteBuffer.allocate(source.length).order(ByteOrder.LITTLE_ENDIAN);
        int seed = 0xeeeeeeee;
        while (input.remaining() >= 4) {
            seed += CRYPT[1024 + (key & 255)];
            int plain = input.getInt() ^ (key + seed);
            output.putInt(plain);
            key = ((~key << 21) + 0x11111111) | (key >>> 11);
            seed = plain + seed + (seed << 5) + 3;
        }
        return output.array();
    }
    private static byte[] read(FileChannel channel, long offset, int length, long fileSize) throws IOException {
        if (offset < 0 || length < 0 || offset > fileSize - length) throw new IOException("Archive contains an invalid file offset.");
        byte[] bytes = new byte[length]; ByteBuffer buffer = ByteBuffer.wrap(bytes);
        channel.position(offset);
        while (buffer.hasRemaining()) {
            if (channel.read(buffer) <= 0) throw new IOException("Cannot read the archive. Select the local file in Internal storage.");
        }
        return bytes;
    }
    private static long u32(byte[] a, int i) { return ByteBuffer.wrap(a, i, 4).order(ByteOrder.LITTLE_ENDIAN).getInt() & 0xffffffffL; }
    private static int u16(byte[] a, int i) { return (a[i] & 255) | ((a[i + 1] & 255) << 8); }
    private static int find(byte[] table, int count, String name) {
        long a = hash(name, 1) & 0xffffffffL, b = hash(name, 2) & 0xffffffffL;
        int start = hash(name, 0) & (count - 1), fallback = -1;
        for (int n = 0; n < count; n++) {
            int slot = (start + n) & (count - 1), p = slot * 16;
            long block = u32(table, p + 12);
            if (block == 0xffffffffL) break;
            if (block != 0xfffffffeL && u32(table, p) == a && u32(table, p + 4) == b) {
                if (u16(table, p + 8) == 0) return slot;
                if (fallback < 0) fallback = slot;
            }
        }
        return fallback;
    }
    private static void put(ZipOutputStream zip, String name, byte[] data) throws IOException {
        zip.putNextEntry(new ZipEntry(name)); zip.write(data); zip.closeEntry();
    }
    private static String quote(String value) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : value.toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c < 32) b.append(String.format(Locale.ROOT, "\\u%04x", (int)c));
            else b.append(c);
        }
        return b.append('"').toString();
    }

    public static Result export(FileChannel channel, List<String> names, String required,
                                OutputStream output, Progress progress) throws IOException {
        return exportEntries(channel, names, required, output, progress, "mission");
    }
    static boolean expansionArchive(FileChannel channel) throws IOException {
        long size=channel.size();
        for(long base=0;base<=Math.min(size-32,4L*1024*1024);base+=512) {
            byte[] h=read(channel,base,32,size);
            if(u32(h,0)!=0x1a51504dL || u32(h,4)!=32 || u16(h,12)!=0)continue;
            long count=u32(h,24);
            if(count<1||count>524288||(count&(count-1))!=0)continue;
            byte[] hashes=decrypt(read(channel,base+u32(h,16),(int)count*16,size),hash("(hash table)",3));
            if(find(hashes,(int)count,"campaign\\expprotoss\\protoss01\\staredit\\scenario.chk")>=0)return true;
            if(find(hashes,(int)count,MISSION)>=0)return false;
        }
        throw new IOException("Choose StarDat.mpq, BrooDat.mpq, Patch_rt.mpq, StarCraft.mpq or BroodWar.mpq from the classic installation.");
    }
    public static Result exportMusic(FileChannel channel, List<String> names,
                                     OutputStream output, Progress progress) throws IOException {
        return exportEntries(channel, names, null, output, progress, "music");
    }
    public static Result exportInterface(FileChannel channel, List<String> names,
                                         OutputStream output, Progress progress) throws IOException {
        return exportEntries(channel, names, null, output, progress, "interface");
    }
    public static Result exportStory(FileChannel channel, List<String> names,
                                     OutputStream output, Progress progress, boolean movies) throws IOException {
        return exportEntries(channel,names,null,output,progress,movies ? "cinematic" : "story");
    }
    private static Result exportEntries(FileChannel channel, List<String> names, String required,
                                 OutputStream output, Progress progress, String kind) throws IOException {
        boolean music = kind.equals("music"), ui = kind.equals("interface"), story = kind.equals("story") || kind.equals("cinematic");
        String mission = required != null && required.startsWith("campaign\\") ? CampaignCatalog.missionForPath(required) : "terran01";
        long fileSize = channel.size();
        if (fileSize < 32) throw new IOException("This is not a readable local MPQ file.");
        long base = -1; byte[] header = null;
        for (long offset = 0; offset <= Math.min(fileSize - 32, 4L * 1024 * 1024); offset += 512) {
            byte[] magic = read(channel, offset, 4, fileSize);
            if (magic[0] == 'M' && magic[1] == 'P' && magic[2] == 'Q' && magic[3] == 26) {
                base = offset; header = read(channel, offset, 32, fileSize); break;
            }
        }
        if (base < 0) throw new IOException("No classic MPQ archive found. Choose StarCraft.mpq.");
        if (u16(header, 12) != 0 || u32(header, 4) != 32) throw new IOException("Use the classic StarCraft MPQ, not Remastered data.");
        long hashCount = u32(header, 24), blockCount = u32(header, 28);
        if (hashCount < 1 || hashCount > 524288 || (hashCount & (hashCount - 1)) != 0 || blockCount < 1 || blockCount > 524288)
            throw new IOException("Invalid or unsupported MPQ file table.");
        progress.update(ui ? "Reading original interface…" : music ? "Reading the music index…" : "Reading the campaign index…");
        byte[] rawHashes = read(channel, base + u32(header, 16), (int)hashCount * 16, fileSize);
        byte[] rawBlocks = read(channel, base + u32(header, 20), (int)blockCount * 16, fileSize);
        byte[] hashes = decrypt(rawHashes, hash("(hash table)", 3));
        byte[] blocks = decrypt(rawBlocks, hash("(block table)", 3));
        if (required != null && find(hashes, (int)hashCount, required) < 0)
            throw new IOException("The selected mission was not found. Choose the matching StarCraft.mpq or BroodWar.mpq campaign archive.");
        Result result = new Result();
        Map<Integer,Entry> selected = new LinkedHashMap<Integer,Entry>();
        for (String name : names) {
            int slot = find(hashes, (int)hashCount, name);
            if (slot < 0) { result.missing.add(name); continue; }
            long bi = u32(hashes, slot * 16 + 12);
            if (bi >= blockCount) throw new IOException("Invalid campaign entry.");
            int block = (int)bi, at = block * 16;
            if (selected.containsKey(block)) { selected.get(block).slots.add(slot); continue; }
            Entry e = new Entry(); e.name = name; e.block = block; e.slots.add(slot);
            e.offset = u32(blocks, at); e.packed = u32(blocks, at + 4);
            e.size = u32(blocks, at + 8); e.flags = u32(blocks, at + 12);
            if (ui && (e.packed > 262144 || e.size > 262144)) throw new IOException("Invalid interface entry.");
            if ((e.flags & 0x80000000L) == 0 || e.packed > (kind.equals("cinematic") ? 128L : 64L) * 1024 * 1024 || base + e.offset > fileSize - e.packed)
                throw new IOException("Invalid or oversized campaign entry.");
            result.packedBytes += e.packed;
            if (result.packedBytes > (kind.equals("cinematic") ? 768L * 1024 * 1024 : LIMIT)) throw new IOException("Content import exceeds the size limit.");
            selected.put(block, e);
        }
        result.files = selected.size();
        if (ui && result.files == 0) throw new IOException("No original interface files found. Select the large StarCraft.mpq or the original Install.exe.");
        if (story && result.files == 0) throw new IOException("No original story/movie content found. Choose the large StarCraft.mpq.");
        if (result.files == 0) throw new IOException("No music tracks found. Select the large StarCraft.mpq or BroodWar.mpq, not StarDat.mpq.");
        StringBuilder manifest = new StringBuilder("{\n  \"format\":\"openbw-"+kind+"-bundle-v1\",\n  "+(!music&&!ui&&!story?"\"mission\":\""+mission+"\",\n  ":"")+"\"archiveSize\":");
        manifest.append(u32(header, 8)).append(",\n  \"sourceSize\":").append(fileSize);
        manifest.append(",\n  \"entries\":[\n");
        try (ZipOutputStream zip = new ZipOutputStream(output)) {
            put(zip, "header.bin", header); put(zip, "hash-table.bin", rawHashes); put(zip, "block-table.bin", rawBlocks);
            int index = 0; byte[] copy = new byte[65536];
            for (Entry e : selected.values()) {
                progress.update((ui ? "Importing original interface: " : music ? "Importing music: " : "Importing campaign: ") + (++index) + " / " + result.files);
                zip.putNextEntry(new ZipEntry("blocks/" + e.block + ".bin"));
                channel.position(base + e.offset); long remaining = e.packed;
                while (remaining > 0) {
                    int n = channel.read(ByteBuffer.wrap(copy, 0, (int)Math.min(copy.length, remaining)));
                    if (n <= 0) throw new IOException("Archive read stopped unexpectedly.");
                    zip.write(copy, 0, n); remaining -= n;
                }
                zip.closeEntry();
                if (index > 1) manifest.append(",\n");
                manifest.append("    {\"name\":").append(quote(e.name)).append(",\"block\":").append(e.block);
                manifest.append(",\"offset\":").append(e.offset).append(",\"packedSize\":").append(e.packed);
                manifest.append(",\"size\":").append(e.size).append(",\"flags\":").append(e.flags);
                manifest.append(",\"hashSlots\":").append(e.slots.toString()).append('}');
            }
            manifest.append("\n  ],\n  \"missing\":[");
            for (int i = 0; i < result.missing.size(); i++) {
                if (i > 0) manifest.append(','); manifest.append(quote(result.missing.get(i)));
            }
            manifest.append("]\n}\n");
            put(zip, "manifest.json", manifest.toString().getBytes(StandardCharsets.UTF_8));
            put(zip, "README.txt", (ui ? "Original interface fonts and campaign artwork for local StarDroid use. No game imagery or fonts are bundled with the application.\n" : music ? "Local music for StarDroid. Original compressed entries retained; only one track is decoded at a time.\n" : ("StarDroid local campaign bundle.\n"
                + "Only the selected mission entries and MPQ metadata are included.\n"
                + "Import this ZIP using the StarDroid home screen.\n"
                + "No upload of the full StarCraft archive is needed.\n"
                + "Developer: reconstruct with scripts/rebuild_mission_mpq.py from the app source.\n")).getBytes(StandardCharsets.UTF_8));
        }
        return result;
    }
}

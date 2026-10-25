package org.openbw.androidtest;

import java.io.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Compact, reproducible MPQ cache built from locally imported content. */
final class NativeData {
  private static final int[] CRYPT = crypt();

  private static int[] crypt() {
    int[] t = new int[1280];
    long s = 0x100001;
    for (int i = 0; i < 256; i++)
      for (int j = 0; j < 5; j++) {
        s = (s * 125 + 3) % 0x2aaaab;
        int hi = (int) s << 16;
        s = (s * 125 + 3) % 0x2aaaab;
        t[i + j * 256] = hi | (int) s & 65535;
      }
    return t;
  }

  private static int hash(String name) {return hash(name,3);}
  private static int hash(String name,int kind) {
    int a = 0x7fed7fed, b = 0xeeeeeeee;
    for (byte value : name.replace('/', '\\').toUpperCase(Locale.ROOT).getBytes(java.nio.charset.StandardCharsets.ISO_8859_1)) {
      int c = value & 255;
      a = CRYPT[256 * kind + c] ^ (a + b);
      b = c + a + b + (b << 5) + 3;
    }
    return a;
  }

  static long u32(byte[] b, int p) {
    return (b[p] & 255L)
        | (b[p + 1] & 255L) << 8
        | (b[p + 2] & 255L) << 16
        | (b[p + 3] & 255L) << 24;
  }

  private static void put(byte[] b, int p, int v) {
    for (int k = 0; k < 4; k++) b[p + k] = (byte) (v >>> (k * 8));
  }

  private static byte[] cipher(byte[] b, int key, boolean encode) {
    byte[] out = Arrays.copyOf(b, b.length);
    int seed = 0xeeeeeeee;
    for (int p = 0; p + 4 <= b.length; p += 4) {
      seed += CRYPT[1024 + (key & 255)];
      int word = (int) u32(b, p), value = word ^ (key + seed), plain = encode ? word : value;
      put(out, p, value);
      key = ((~key << 21) + 0x11111111) | (key >>> 11);
      seed = plain + seed + (seed << 5) + 3;
    }
    return out;
  }

  static byte[] decodeTable(byte[] bytes, String name) {
    return cipher(bytes, hash(name), false);
  }

  static byte[] read(InputStream in, int max) throws IOException {
    try (InputStream stream = in;
        ByteArrayOutputStream out = new ByteArrayOutputStream()) {
      byte[] b = new byte[65536];
      int n;
      while ((n = stream.read(b)) != -1) {
        if (out.size() > max - n) throw new IOException("Content exceeds size limit");
        out.write(b, 0, n);
      }
      return out.toByteArray();
    }
  }

  /** Minimal classic MPQ containing the verified scenario only; no paths from the peer. */
  static File nearbyMap(byte[] chk,File directory) throws Exception {
    if(chk==null || chk.length<8 || chk.length>NearbyProtocol.MAX_MAP)throw new IOException("Invalid nearby map");
    int position=0;boolean dimensions=false,terrain=false;
    while(position<chk.length) {
      if(chk.length-position<8)throw new IOException("Truncated nearby map");
      long length=u32(chk,position+4);if(length>chk.length-position-8)throw new IOException("Truncated nearby map");
      String tag=new String(chk,position,4,"US-ASCII");
      if(tag.equals("DIM ")){if(length!=4)throw new IOException("Invalid map dimensions");int w=(chk[position+8]&255)|((chk[position+9]&255)<<8),h=(chk[position+10]&255)|((chk[position+11]&255)<<8);if(w<1||w>256||h<1||h>256)throw new IOException("Unsupported map dimensions");dimensions=true;}
      if(tag.equals("MTXM"))terrain=true;position+=8+(int)length;
    }
    if(!dimensions||!terrain)throw new IOException("Nearby map has no terrain");
    directory.mkdirs();File dest=new File(directory,"nearby-map.mpq");
    int sectors=(chk.length+4095)/4096,tableBytes=4*(sectors+1);byte[] offsets=new byte[tableBytes];
    for(int i=0;i<=sectors;i++)put(offsets,i*4,tableBytes+Math.min(chk.length,i*4096));
    int ht=32+tableBytes+chk.length,bt=ht+64;byte[] header=new byte[32],hashes=new byte[64],block=new byte[16];
    put(header,0,0x1a51504d);put(header,4,32);put(header,8,bt+16);put(header,12,3<<16);put(header,16,ht);put(header,20,bt);put(header,24,4);put(header,28,1);
    Arrays.fill(hashes,(byte)255);String path="staredit\\scenario.chk";int index=(hash(path,0)&3)*16;
    put(hashes,index,hash(path,1));put(hashes,index+4,hash(path,2));put(hashes,index+8,0);put(hashes,index+12,0);
    put(block,0,32);put(block,4,tableBytes+chk.length);put(block,8,chk.length);put(block,12,0x80000200);
    try(FileOutputStream out=new FileOutputStream(dest)){out.write(header);out.write(offsets);out.write(chk);out.write(cipher(hashes,hash("(hash table)"),true));out.write(cipher(block,hash("(block table)"),true));}
    return dest;
  }

  /** Copy a bounded segment, rekeying whole cipher words without decoding audio/video. */
  private static void copySegment(DataInputStream in, RandomAccessFile out, long bytes,
      boolean rekey, int oldKey, int newKey, byte[] buffer) throws IOException {
    int oldSeed = 0xeeeeeeee, newSeed = 0xeeeeeeee;
    while (bytes > 0) {
      int n = (int)Math.min(bytes, buffer.length); in.readFully(buffer, 0, n);
      if (rekey) for (int p = 0; p + 4 <= n; p += 4) {
        oldSeed += CRYPT[1024 + (oldKey & 255)];
        int plain = (int)u32(buffer, p) ^ (oldKey + oldSeed);
        oldKey = ((~oldKey << 21) + 0x11111111) | (oldKey >>> 11);
        oldSeed = plain + oldSeed + (oldSeed << 5) + 3;
        newSeed += CRYPT[1024 + (newKey & 255)];
        put(buffer, p, plain ^ (newKey + newSeed));
        newKey = ((~newKey << 21) + 0x11111111) | (newKey >>> 11);
        newSeed = plain + newSeed + (newSeed << 5) + 3;
      }
      out.write(buffer, 0, n); bytes -= n;
    }
  }

  private static void compactBlock(InputStream stream, RandomAccessFile out, String name,
      long oldOffset, long newOffset, long packed, long size, long flags, int sectorSize,
      byte[] buffer) throws IOException {
    DataInputStream in = new DataInputStream(stream);
    if ((flags & 0x30000) != 0x30000 || oldOffset == newOffset) {
      copySegment(in, out, packed, false, 0, 0, buffer);
    } else {
      String normalized = name.replace('/', '\\');
      int key = hash(normalized.substring(normalized.lastIndexOf('\\') + 1));
      int oldKey = (key + (int)oldOffset) ^ (int)size;
      int newKey = (key + (int)newOffset) ^ (int)size;
      if ((flags & 0x01000000) != 0) {
        copySegment(in, out, packed, true, oldKey, newKey, buffer);
      } else if ((flags & 0x300) == 0) {
        if (packed != size && packed != ((size + 3) & ~3L))
          throw new IOException("Invalid encrypted raw block");
        long remaining = packed; int sector = 0;
        while (remaining > 0) {
          long n = Math.min(remaining, sectorSize);
          copySegment(in, out, n, true, oldKey + sector, newKey + sector, buffer);
          remaining -= n; sector++;
        }
      } else {
        int sectors = (int)((size + sectorSize - 1) / sectorSize);
        boolean checksums = (flags & 0x04000000) != 0;
        long tableSize = 4L * (sectors + 1L + (checksums ? 1 : 0));
        if (tableSize > packed || tableSize > 8 * 1024 * 1024)
          throw new IOException("Invalid encrypted sector table");
        byte[] table = new byte[(int)tableSize]; in.readFully(table);
        table = cipher(table, oldKey - 1, false);
        long first = u32(table, 0), previous = first;
        if (first < tableSize || first > packed)
          throw new IOException("Invalid encrypted sector offset");
        for (int i = 1; i <= sectors; i++) {
          long next = u32(table, i * 4);
          if (next <= previous || next > packed)
            throw new IOException("Invalid encrypted sector offset");
          previous = next;
        }
        if ((checksums ? u32(table, (sectors + 1) * 4) : previous) != packed)
          throw new IOException("Invalid encrypted sector end");
        out.write(cipher(table, newKey - 1, true));
        copySegment(in, out, first - tableSize, false, 0, 0, buffer);
        for (int i = 0; i < sectors; i++)
          copySegment(in, out, u32(table, (i + 1) * 4) - u32(table, i * 4),
              true, oldKey + i, newKey + i, buffer);
        // MPQ sector checksums are not encrypted (StormLib RecryptFileData).
        copySegment(in, out, packed - previous, false, 0, 0, buffer);
      }
    }
    if (in.read() != -1) throw new IOException("Oversized archive payload");
  }

  static File prepare(File bundle, File directory, String slot) throws Exception {
    return prepare(bundle, directory, slot, null);
  }

  /** One requested asset only; used for a cinematic during decoder initialization. */
  static File prepareEntry(File bundle, File directory, String slot, String name) throws Exception {
    if (name == null || name.isEmpty()) throw new IOException("Missing requested asset");
    return prepare(bundle, directory, slot, name.replace('/', '\\').toLowerCase(Locale.ROOT));
  }

  /** Call only after its native archive slot has been closed. Imported bundles are untouched. */
  static void discard(File directory, String slot) {
    for (String suffix : new String[]{".mpq", ".stamp", ".tmp"}) new File(directory, slot + suffix).delete();
  }

  private static File prepare(File bundle, File directory, String slot, String requested) throws Exception {
    directory.mkdirs();
    File dest = new File(directory, slot + ".mpq"), stamp = new File(directory, slot + ".stamp");
    if (!bundle.isFile()) {dest.delete(); stamp.delete(); return null;}
    String identity =
        bundle.getName() + ":" + bundle.length() + ":" + bundle.lastModified() + ":compact80"
            + (requested == null ? "" : ":" + requested);
    if (dest.isFile()
        && stamp.isFile()
        && identity.equals(new String(read(new FileInputStream(stamp), 1024), "UTF-8")))
      return dest;
    File temp = new File(directory, slot + ".tmp");
    try (ZipFile z = new ZipFile(bundle);
        RandomAccessFile out = new RandomAccessFile(temp, "rw")) {
      JSONObject manifest =
          new JSONObject(
              new String(
                  read(z.getInputStream(z.getEntry("manifest.json")), 1024 * 1024), "UTF-8"));
      byte[] header = read(z.getInputStream(z.getEntry("header.bin")), 32);
      if (header.length != 32 || u32(header, 0) != 0x1a51504dL || u32(header, 4) != 32
          || header[12] != 0 || header[13] != 0)
        throw new IOException("Invalid archive header");
      int shift = (header[14] & 255) | ((header[15] & 255) << 8);
      if (shift > 15) throw new IOException("Unsupported archive sector size");
      int sectorSize = 512 << shift;
      long size = u32(header, 8), ht = u32(header, 16), bt = u32(header, 20);
      int hn = (int) u32(header, 24), bn = (int) u32(header, 28);
      if (size < 32 || size > 0xffffffffL || hn < 1 || hn > 524288 || bn < 1 || bn > 524288)
        throw new IOException("Invalid archive bounds");
      byte[]
          hashes =
              cipher(
                  read(z.getInputStream(z.getEntry("hash-table.bin")), 8 * 1024 * 1024),
                  hash("(hash table)"),
                  false),
          blocks =
              cipher(
                  read(z.getInputStream(z.getEntry("block-table.bin")), 8 * 1024 * 1024),
                  hash("(block table)"),
                  false);
      if (hashes.length != hn * 16
          || blocks.length != bn * 16
          || ht + hashes.length > size
          || bt + blocks.length > size) throw new IOException("Invalid archive tables");
      JSONArray entries = manifest.getJSONArray("entries");
      Set<Integer> selected = new HashSet<Integer>(), slots = new HashSet<Integer>();
      out.setLength(0);
      out.write(header);
      long compactOffset = 32;
      byte[] buffer = new byte[65536];
      for (int i = 0; i < entries.length(); i++) {
        JSONObject item = entries.getJSONObject(i);
        if (requested != null && !requested.equals(item.getString("name").replace('/', '\\').toLowerCase(Locale.ROOT))) continue;
        int block = item.getInt("block");
        long offset = item.getLong("offset"), packed = item.getLong("packedSize");
        if (block < 0
            || block >= bn
            || offset < 32
            || packed < 1
            || packed > 128L * 1024 * 1024
            || offset + packed > size
            || u32(blocks, block * 16) != offset
            || u32(blocks, block * 16 + 4) != packed)
          throw new IOException("Invalid archive block");
        if (!selected.add(block)) throw new IOException("Duplicate archive block");
        JSONArray hs = item.getJSONArray("hashSlots");
        for (int j = 0; j < hs.length(); j++) {
          int h = hs.getInt(j);
          if (h < 0 || h >= hn || u32(hashes, h * 16 + 12) != block)
            throw new IOException("Invalid archive hash");
          slots.add(h);
        }
        ZipEntry e = z.getEntry("blocks/" + block + ".bin");
        if (e == null || e.getSize() != packed) throw new IOException("Missing archive payload");
        out.seek(compactOffset);
        long flags = u32(blocks, block * 16 + 12), decoded = u32(blocks, block * 16 + 8);
        if ((flags & 0x80000000L) == 0) throw new IOException("Missing archive block");
        CRC32 crc = new CRC32();
        try (InputStream in = new CheckedInputStream(z.getInputStream(e), crc)) {
          compactBlock(in, out, item.getString("name"), offset, compactOffset,
              packed, decoded, flags, sectorSize, buffer);
        }
        if (crc.getValue() != e.getCrc()) throw new IOException("Damaged archive payload");
        put(blocks, block * 16, (int)compactOffset);
        compactOffset += packed;
        if (compactOffset + hashes.length + blocks.length > 0xffffffffL)
          throw new IOException("Archive cache is too large");
      }
      if (requested != null && selected.isEmpty()) throw new IOException("Requested asset is unavailable: " + requested);
      for (int h = 0; h < hn; h++)
        if (!slots.contains(h) && u32(hashes, h * 16 + 12) != 0xffffffffL)
          put(hashes, h * 16 + 12, 0xfffffffe);
      for (int b = 0; b < bn; b++)
        if (!selected.contains(b)) Arrays.fill(blocks, b * 16, b * 16 + 16, (byte) 0);
      ht = compactOffset; bt = ht + hashes.length;
      size = bt + blocks.length;
      put(header, 8, (int)size); put(header, 16, (int)ht); put(header, 20, (int)bt);
      out.seek(0); out.write(header);
      out.seek(ht);
      out.write(cipher(hashes, hash("(hash table)"), true));
      out.seek(bt);
      out.write(cipher(blocks, hash("(block table)"), true));
      out.setLength(size); out.getFD().sync();
    } catch (Exception e) {
      temp.delete();
      throw e;
    }
    java.nio.file.Files.move(
        temp.toPath(),
        dest.toPath(),
        java.nio.file.StandardCopyOption.REPLACE_EXISTING,
        java.nio.file.StandardCopyOption.ATOMIC_MOVE);
    try (FileOutputStream out = new FileOutputStream(stamp)) {
      out.write(identity.getBytes("UTF-8"));
    }
    return dest;
  }
}

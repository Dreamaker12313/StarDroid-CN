package org.openbw.androidtest;

import java.io.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Rebuild sparse MPQs while preserving original encrypted block offsets. */
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
    for (char c : name.toUpperCase(Locale.ROOT).toCharArray()) {
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
    byte[] out = new byte[b.length];
    int seed = 0xeeeeeeee;
    for (int p = 0; p < b.length; p += 4) {
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

  static File prepare(File bundle, File directory, String slot) throws Exception {
    if (!bundle.isFile()) return null;
    directory.mkdirs();
    File dest = new File(directory, slot + ".mpq"), stamp = new File(directory, slot + ".stamp");
    String identity =
        bundle.getName() + ":" + bundle.length() + ":" + bundle.lastModified() + ":native1";
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
      if (header.length != 32 || header[0] != 'M' || header[1] != 'P' || header[2] != 'Q')
        throw new IOException("Invalid archive header");
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
      out.setLength(size);
      out.write(header);
      byte[] buffer = new byte[65536];
      for (int i = 0; i < entries.length(); i++) {
        JSONObject item = entries.getJSONObject(i);
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
        selected.add(block);
        JSONArray hs = item.getJSONArray("hashSlots");
        for (int j = 0; j < hs.length(); j++) {
          int h = hs.getInt(j);
          if (h < 0 || h >= hn || u32(hashes, h * 16 + 12) != block)
            throw new IOException("Invalid archive hash");
          slots.add(h);
        }
        ZipEntry e = z.getEntry("blocks/" + block + ".bin");
        if (e == null || e.getSize() != packed) throw new IOException("Missing archive payload");
        out.seek(offset);
        long count = 0;
        try (InputStream in = z.getInputStream(e)) {
          int n;
          while ((n = in.read(buffer)) != -1) {
            count += n;
            if (count > packed) throw new IOException("Oversized payload");
            out.write(buffer, 0, n);
          }
        }
        if (count != packed) throw new IOException("Truncated payload");
      }
      for (int h = 0; h < hn; h++)
        if (!slots.contains(h) && u32(hashes, h * 16 + 12) != 0xffffffffL)
          put(hashes, h * 16 + 12, 0xfffffffe);
      for (int b = 0; b < bn; b++)
        if (!selected.contains(b)) Arrays.fill(blocks, b * 16, b * 16 + 16, (byte) 0);
      out.seek(ht);
      out.write(cipher(hashes, hash("(hash table)"), true));
      out.seek(bt);
      out.write(cipher(blocks, hash("(block table)"), true));
      out.getFD().sync();
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

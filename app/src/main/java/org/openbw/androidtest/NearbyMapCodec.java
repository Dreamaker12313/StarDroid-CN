package org.openbw.androidtest;

import java.io.*;
import java.util.zip.*;

/** Compress only useful map data; both the wire and expanded data are bounded. */
final class NearbyMapCodec {
  static byte[] encode(byte[] raw) {
    Deflater deflater=new Deflater(Deflater.BEST_SPEED);
    try {
      deflater.setInput(raw);deflater.finish();
      ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] block=new byte[16384];
      while(!deflater.finished()) {
        int n=deflater.deflate(block);
        if(n<=0 || out.size()+n>=raw.length-256)return raw;
        out.write(block,0,n);
      }
      return out.size()<=raw.length*9L/10 ? out.toByteArray() : raw;
    } finally {deflater.end();}
  }
  static byte[] decode(byte[] wire,int size,boolean compressed) throws IOException {
    return decode(wire,size,compressed,NearbyProtocol.MAX_MAP);
  }
  static byte[] decode(byte[] wire,int size,boolean compressed,int limit) throws IOException {
    if(size<8 || size>limit || wire==null || wire.length<1 || wire.length>limit)throw new IOException("Invalid nearby map size");
    if(!compressed){if(wire.length!=size)throw new IOException("Map length differs");return wire;}
    Inflater inflater=new Inflater();byte[] raw=new byte[size];int offset=0;
    try {
      inflater.setInput(wire);
      while(offset<size && !inflater.finished()) {
        int n=inflater.inflate(raw,offset,size-offset);
        if(n==0)break;offset+=n;
      }
      if(offset!=size || !inflater.finished() || inflater.getRemaining()!=0)throw new IOException("Compressed map is truncated or exceeds its declared size");
      return raw;
    } catch(DataFormatException e){throw new IOException("Invalid compressed map",e);}
    finally {inflater.end();}
  }
}

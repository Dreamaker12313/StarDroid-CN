package org.openbw.androidtest;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
final class NativeMapCheck {
  static int u16(byte[] b, int p) { return (b[p]&255) | (b[p+1]&255)<<8; }
  static void validate(byte[] chk) throws IOException {
    if(chk==null)throw new IOException("No scenario in this map.");
    int width=0,height=0,starts=0;
    for(int p=0;p<chk.length;) {
      if(chk.length-p<8)throw new IOException("Truncated map.");
      String tag=new String(chk,p,4,StandardCharsets.US_ASCII);
      long size=(long)u16(chk,p+4) | (long)u16(chk,p+6)<<16;p+=8;
      if(size>chk.length-p)throw new IOException("Truncated map.");
      int n=(int)size;
      if(tag.equals("DIM ")) {
        if(n!=4)throw new IOException("Missing map dimensions.");width=u16(chk,p);height=u16(chk,p+2);
      } else if(tag.equals("UNIT")) {
        if(n%36!=0)throw new IOException("Truncated map units.");
        starts=0;for(int k=0;k<n;k+=36)if(u16(chk,p+k+8)==214)starts++;
      }
      p+=n;
    }
    if(width<1||height<1||width>256||height>256)throw new IOException("Unsupported map size.");
    if(starts<1||starts>8)throw new IOException("This map needs 1–8 start locations for Melee.");
  }
}

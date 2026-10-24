package org.openbw.androidtest;
import java.io.*;

/** Snapshot at a verified turn boundary, including already accepted inputs. */
final class MatchSnapshot {
  static final int LIMIT=64*1024*1024;
  final byte[] state,first,second;
  MatchSnapshot(byte[] s,byte[] a,byte[] b){state=s;first=a;second=b;}
  byte[] encode() throws IOException {
    if(state==null||state.length<40||state.length>LIMIT-32784||first.length>16384||second.length>16384)throw new IOException("Invalid multiplayer save");
    ByteArrayOutputStream bytes=new ByteArrayOutputStream();DataOutputStream out=new DataOutputStream(bytes);out.writeInt(0x4f42534d);
    for(byte[] b:new byte[][]{state,first,second}){out.writeInt(b.length);out.write(b);}return bytes.toByteArray();
  }
  static MatchSnapshot decode(byte[] data) throws IOException {
    if(data==null||data.length<56||data.length>LIMIT)throw new IOException("Invalid multiplayer save size");
    DataInputStream in=new DataInputStream(new ByteArrayInputStream(data));if(in.readInt()!=0x4f42534d)throw new IOException("Not a multiplayer save");
    byte[][] b=new byte[3][];for(int i=0;i<3;i++) {
      int n=in.readInt();if(n<(i==0?40:0)||n>(i==0?LIMIT-32784:16384)||n>in.available())throw new IOException("Truncated multiplayer save");
      b[i]=new byte[n];in.readFully(b[i]);
    }
    if(in.available()!=0)throw new IOException("Unexpected saved data");return new MatchSnapshot(b[0],b[1],b[2]);
  }
}

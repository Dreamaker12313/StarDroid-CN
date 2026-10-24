package org.openbw.androidtest;
import java.io.*;
import java.util.*;
/** Native world plus all accepted commands at a complete, verified eight-player turn. */
final class RoomSnapshot {
  static final int LIMIT=64*1024*1024;
  final byte[] state;final byte[][] commands;final int hostSlot;
  RoomSnapshot(byte[] s,byte[][] c,int host){state=s;commands=c;hostSlot=host;}
  byte[] encode()throws IOException {
    if(state==null||state.length<40||state.length>LIMIT-131120||commands.length!=8||hostSlot<0||hostSlot>7)throw new IOException("Invalid multiplayer save");
    ByteArrayOutputStream bytes=new ByteArrayOutputStream();DataOutputStream out=new DataOutputStream(bytes);
    out.writeInt(0x4f425338);out.writeInt(hostSlot);out.writeInt(state.length);out.write(state);
    for(byte[] c:commands){if(c==null||c.length>16384)throw new IOException("Invalid saved commands");out.writeInt(c.length);out.write(c);}return bytes.toByteArray();
  }
  static RoomSnapshot decode(byte[] b)throws IOException {
    if(b==null||b.length<56||b.length>LIMIT)throw new IOException("Invalid multiplayer save size");
    DataInputStream in=new DataInputStream(new ByteArrayInputStream(b));int magic=in.readInt();
    if(magic==0x4f42534d){MatchSnapshot old=MatchSnapshot.decode(b);byte[][] c=new byte[8][];Arrays.fill(c,RoomProtocol.EMPTY);c[0]=old.first;c[1]=old.second;return new RoomSnapshot(old.state,c,0);}
    if(magic!=0x4f425338)throw new IOException("Not a multiplayer save");int host=in.readInt(),size=in.readInt();
    if(host<0||host>7||size<40||size>LIMIT-131120||size>in.available())throw new IOException("Invalid saved world");
    byte[] state=new byte[size];in.readFully(state);byte[][] commands=new byte[8][];
    for(int i=0;i<8;i++){int n=in.readInt();if(n<0||n>16384||n>in.available())throw new IOException("Invalid saved input");commands[i]=new byte[n];in.readFully(commands[i]);}
    if(in.available()!=0)throw new IOException("Unexpected saved data");return new RoomSnapshot(state,commands,host);
  }
}

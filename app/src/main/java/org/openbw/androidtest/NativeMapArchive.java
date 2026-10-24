package org.openbw.androidtest;

import java.io.*;
import java.util.*;

/** Stores occupied MPQ ranges without moving encrypted FIX_KEY blocks. */
final class NativeMapArchive {
  private static final long MAGIC=0x4f42574d41503031L; // OBWMAP01, versioned independently of game state
  private static final int MAX_PREFIX=1024*1024, MAX_BLOCKS=524288;
  private static final long MAX_FILE=0xffffffffL+MAX_PREFIX;
  static final class Range {
    final long offset; long length;
    Range(long o,long n){offset=o;length=n;}
  }
  static final class Plan {
    final long length, bytes; final List<Range> ranges;
    Plan(long n,List<Range> r){length=n;ranges=r;long total=20+16L*r.size();for(Range x:r)total+=x.length;bytes=total;}
  }
  private static IOException damaged(){return new IOException("Mission archive has invalid bounds");}
  private static void range(List<Range> ranges,long offset,long length,long end)throws IOException {
    if(offset<0||length<1||offset>end||length>end-offset)throw damaged();
    ranges.add(new Range(offset,length));
  }
  static Plan inspect(File map,int limit)throws IOException {
    try(RandomAccessFile in=new RandomAccessFile(map,"r")) {
      long length=in.length();if(length<32||length>MAX_FILE)throw damaged();
      byte[] header=new byte[32];long base=0;
      // Standalone SCM/SCX archives may have a 512-byte-aligned launcher prefix.
      for(;;base+=512) {
        if(base>MAX_PREFIX||base+32>length)throw new IOException("Mission archive header is missing");
        in.seek(base);in.readFully(header);
        if(NativeData.u32(header,0)==0x1a51504dL)break;
      }
      if(NativeData.u32(header,4)!=32||header[12]!=0||header[13]!=0)
        throw new IOException("Unsupported mission archive version");
      long archive=NativeData.u32(header,8),hn=NativeData.u32(header,24),bn=NativeData.u32(header,28);
      if(archive<32||archive>length-base||hn<1||hn>MAX_BLOCKS||bn<1||bn>MAX_BLOCKS)throw damaged();
      long ht=NativeData.u32(header,16),bt=NativeData.u32(header,20);
      if(ht<32||bt<32||ht+16*hn>archive||bt+16*bn>archive)throw damaged();
      List<Range> ranges=new ArrayList<Range>();
      range(ranges,0,base+32,length);range(ranges,base+ht,16*hn,length);range(ranges,base+bt,16*bn,length);
      byte[] blocks=new byte[(int)bn*16];in.seek(base+bt);in.readFully(blocks);
      blocks=NativeData.decodeTable(blocks,"(block table)");
      for(int i=0;i<bn;i++) {
        long flags=NativeData.u32(blocks,i*16+12);if((flags&0x80000000L)==0)continue;
        long offset=NativeData.u32(blocks,i*16),packed=NativeData.u32(blocks,i*16+4);
        if(packed==0)continue;
        if(offset<32||offset>archive||packed>archive-offset)throw damaged();
        range(ranges,base+offset,packed,length);
      }
      // Preserve a possible trailer as well as a launcher prefix.
      if(base+archive<length)range(ranges,base+archive,length-base-archive,length);
      Collections.sort(ranges,(a,b)->Long.compare(a.offset,b.offset));
      List<Range> merged=new ArrayList<Range>();
      for(Range r:ranges) {
        Range previous=merged.isEmpty()?null:merged.get(merged.size()-1);
        if(previous!=null&&r.offset<=previous.offset+previous.length)
          previous.length=Math.max(previous.length,r.offset+r.length-previous.offset);
        else merged.add(r);
      }
      Plan plan=new Plan(length,merged);
      if(plan.bytes>limit)throw new IOException("Mission content exceeds the 256 MB save limit");
      return plan;
    }
  }
  static void write(File map,Plan plan,OutputStream stream)throws IOException {
    DataOutputStream out=new DataOutputStream(stream);
    out.writeLong(MAGIC);out.writeLong(plan.length);out.writeInt(plan.ranges.size());
    for(Range r:plan.ranges){out.writeLong(r.offset);out.writeLong(r.length);}
    try(RandomAccessFile in=new RandomAccessFile(map,"r")) {
      if(in.length()!=plan.length)throw new IOException("Mission archive changed while saving");
      byte[] b=new byte[65536];
      for(Range r:plan.ranges) {
        in.seek(r.offset);long left=r.length;
        while(left>0){int n=(int)Math.min(left,b.length);in.readFully(b,0,n);out.write(b,0,n);left-=n;}
      }
    }
    out.flush(); // The save writer owns the output stream.
  }
  static long restore(InputStream stream,long encodedBytes,int limit,File map)throws IOException {
    if(encodedBytes<36||encodedBytes>limit)throw damaged();
    DataInputStream in=new DataInputStream(stream);
    if(in.readLong()!=MAGIC)throw new IOException("Unsupported saved map version");
    long length=in.readLong();int count=in.readInt();
    if(length<32||length>MAX_FILE||count<1||count>MAX_BLOCKS+4||20+16L*count>encodedBytes)throw damaged();
    List<Range> ranges=new ArrayList<Range>();long previous=0,total=20+16L*count;
    for(int i=0;i<count;i++) {
      long offset=in.readLong(),n=in.readLong();
      if(offset<previous||n>encodedBytes-total)throw damaged();
      range(ranges,offset,n,length);previous=offset+n;total+=n;
    }
    if(total!=encodedBytes||ranges.get(0).offset!=0||ranges.get(0).length<32)throw damaged();
    try(RandomAccessFile out=new RandomAccessFile(map,"rw")) {
      out.setLength(0);out.setLength(length);byte[] b=new byte[65536];
      for(Range r:ranges) {
        out.seek(r.offset);long left=r.length;
        while(left>0){int n=(int)Math.min(left,b.length);in.readFully(b,0,n);out.write(b,0,n);left-=n;}
      }
      if(in.read()!=-1)throw damaged();out.getFD().sync();
    }
    return length;
  }
}

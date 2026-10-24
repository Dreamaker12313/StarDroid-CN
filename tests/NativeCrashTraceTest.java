package org.openbw.androidtest;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Random;

/** AOSP-wire fixtures are encoded independently of the production reader. */
public final class NativeCrashTraceTest {
  private static int checks;
  private static void check(boolean b, String message) {
    checks++;
    if (!b) throw new AssertionError(message);
  }
  private static byte[] join(byte[]... parts) {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    for (byte[] part : parts) out.write(part, 0, part.length);
    return out.toByteArray();
  }
  private static byte[] var(long value) {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    while ((value & ~127L) != 0) { out.write((int) value & 127 | 128); value >>>= 7; }
    out.write((int) value);
    return out.toByteArray();
  }
  private static byte[] num(int field, long value) { return join(var(field * 8), var(value)); }
  private static byte[] msg(int field, byte[] bytes) { return join(var(field * 8 + 2), var(bytes.length), bytes); }
  private static byte[] text(int field, String value) { return msg(field, value.getBytes(StandardCharsets.UTF_8)); }
  private static byte[] thread(int tid, String name, byte[]... frames) {
    byte[] value = join(num(1, tid), text(2, name));
    for (byte[] frame : frames) value = join(value, msg(4, frame));
    // Map value before key exercises arbitrary protobuf field ordering.
    return msg(16, join(msg(2, value), num(1, tid)));
  }
  private static byte[] frame(long address, String name) {
    return join(num(1, address), text(4, name), num(5, 24),
        text(6, "/data/app/private-token/lib/arm64/libopenbw.so"), text(8, "aabbccdd"));
  }
  public static byte[] sample() {
    return join(thread(71, "Other thread", frame(0x999, "not_the_crashing_thread")),
        thread(42, "StarDroid native renderer", frame(0x123456, "game_step"), frame(0xABCDEF, "NativeBridge_step")),
        num(6, 42), num(1, 1), text(4, "2025-01-01 12:00:00+0000"), num(20, 180),
        msg(10, join(num(1, 11), text(2, "SIGSEGV"), num(3, 1), text(4, "SEGV_MAPERR"), num(8, 1))),
        msg(15, text(1, "A test cause")),
        msg(18, text(1, "PRIVATE_LOGS_MUST_NOT_BE_COPIED")),
        msg(17, text(7, "PRIVATE_MEMORY_MUST_NOT_BE_COPIED")));
  }
  private static void rejected(byte[] data, String label) throws Exception {
    try { NativeCrashTrace.decode(data); throw new AssertionError("Accepted " + label); }
    catch (IOException expected) { checks++; }
  }
  public static void main(String[] args) throws Exception {
    String report = NativeCrashTrace.read(new ByteArrayInputStream(sample()));
    check(report.contains("StarDroid native renderer") && report.contains("tid 42"), "Faulting thread");
    check(!report.contains("Other thread") && !report.contains("not_the_crashing_thread"), "Exclude other threads");
    check(report.contains("SIGSEGV (11)") && report.contains("SEGV_MAPERR"), "Signal and code");
    check(report.contains("fault address: 0x0"), "Proto3 omitted zero address stays valid");
    check(report.contains("pc 0000000000123456") && report.contains("game_step+24"), "Symbolization inputs");
    check(report.contains("BuildId: aabbccdd"), "Build identity");
    check(!report.contains("private-token") && !report.contains("PRIVATE_"), "Exclude paths, memory and log contents");
    check(report.contains("A test cause") && report.contains("ARM64"), "Crash metadata");
    byte[] noAddress = join(thread(7,"Audio",frame(123,"mix")),num(6,7),msg(10,num(1,11)));
    check(NativeCrashTrace.decode(noAddress).contains("fault address unavailable"), "Missing address distinguished from null fault");
    byte[] unknown = join(sample(),var(1000*8+1),new byte[8],var(1001*8+5),new byte[4],msg(1002,new byte[100]));
    check(NativeCrashTrace.decode(unknown).contains("game_step"), "Skip future fixed and length fields");
    byte[] many = num(6,5), frames=join(num(1,5),text(2,"renderer"));
    for(int i=0;i<90;i++)frames=join(frames,msg(4,frame(i,"work")));
    many=join(many,msg(16,join(num(1,5),msg(2,frames))));
    String limited=NativeCrashTrace.decode(many);
    check(limited.contains("26 further frames omitted"),"Frame limit");
    check(limited.length()<=NativeCrashTrace.MAX_REPORT,"Bound clipboard output");
    rejected(new byte[0],"empty");rejected(new byte[]{0},"zero tag");
    rejected(new byte[]{34,100,1},"invalid string length");
    rejected(join(var(34),var(Long.MAX_VALUE)),"oversized length");
    rejected(new byte[]{(byte)128},"truncated integer");
    byte[] overflow=new byte[11];Arrays.fill(overflow,(byte)255);rejected(overflow,"overflowed integer");
    rejected(new byte[]{11},"invalid group wire type");
    rejected(join(num(6,99),thread(1,"Wrong",frame(1,"ignored"))),"missing faulting thread");
    rejected(join(num(6,1),thread(1,"Empty")),"empty stack");
    InputStream zeroOnce=new ByteArrayInputStream(sample()) {
      boolean once;
      public int read(byte[] b,int off,int len){if(!once){once=true;return 0;}return super.read(b,off,len);}
    };
    check(NativeCrashTrace.read(zeroOnce).contains("game_step"),"Zero-length read cannot loop forever");
    InputStream huge=new InputStream(){int left=NativeCrashTrace.MAX_BYTES+1;public int read(){return left-->0?1:-1;}
      public int read(byte[] b,int off,int len){if(left<=0)return -1;int n=Math.min(left,len);Arrays.fill(b,off,off+n,(byte)1);left-=n;return n;}};
    try{NativeCrashTrace.read(huge);throw new AssertionError("Read beyond input cap");}catch(IOException expected){checks++;}
    Random random=new Random(67);
    for(int i=0;i<1000;i++){
      byte[] bad=new byte[random.nextInt(256)+1];random.nextBytes(bad);
      try{check(NativeCrashTrace.decode(bad).length()<=NativeCrashTrace.MAX_REPORT,"Fuzz output bound");}
      catch(IOException expected){checks++;}
    }
    System.out.println("PASS "+checks+" native trace wire, metadata, privacy, bounds and malformed-input checks");
  }
}

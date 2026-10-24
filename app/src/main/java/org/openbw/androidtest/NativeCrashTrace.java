package org.openbw.androidtest;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Reads only crash metadata and the faulting thread, never memory dumps or logs.
 * Wire fields follow AOSP debuggerd/proto/tombstone.proto (Android 12+).
 */
final class NativeCrashTrace {
  static final int MAX_BYTES = 8 * 1024 * 1024;
  static final int MAX_REPORT = 24576;

  static String read(InputStream stream) throws IOException {
    ByteArrayOutputStream out = new ByteArrayOutputStream(32768);
    byte[] buffer = new byte[8192];
    int count;
    while ((count = stream.read(buffer)) != -1) {
      if (count == 0) {
        int one = stream.read();
        if (one == -1) break;
        if (out.size() == MAX_BYTES) throw new IOException("Native trace exceeds 8 MiB");
        out.write(one);
      } else {
        if (count > MAX_BYTES - out.size()) throw new IOException("Native trace exceeds 8 MiB");
        out.write(buffer, 0, count);
      }
    }
    return decode(out.toByteArray());
  }

  static String decode(byte[] bytes) throws IOException {
    if (bytes.length == 0 || bytes.length > MAX_BYTES) throw new IOException("Invalid native trace size");
    Cursor root = new Cursor(bytes, 0, bytes.length);
    long tid = 0, uptime = 0, arch = 0;
    String timestamp = "", signal = "", abort = "";
    List<String> causes = new ArrayList<>();
    List<Cursor> threads = new ArrayList<>();
    while (root.more()) {
      int tag = root.tag();
      switch (tag) {
        case 8: arch = root.number(); break;
        case 34: timestamp = root.string(128); break;
        case 48: tid = root.number(); break;
        case 82: signal = signal(root.message()); break;
        case 114: abort = root.string(1024); break;
        case 122:
          Cursor cause = root.message();
          if (causes.size() < 4) causes.add(cause(cause));
          break;
        case 130:
          Cursor entry = root.message();
          if (threads.size() >= 512) throw new IOException("Too many threads in native trace");
          threads.add(entry);
          break;
        case 160: uptime = root.number(); break;
        default: root.skip(tag);
      }
    }
    Cursor selected = null;
    for (Cursor entry : threads) {
      long key = 0;
      Cursor value = null;
      while (entry.more()) {
        int tag = entry.tag();
        if (tag == 8) key = entry.number();
        else if (tag == 18) value = entry.message();
        else entry.skip(tag);
      }
      if (key == tid && value != null) selected = value;
    }
    if (selected == null) throw new IOException("Native trace has no faulting-thread record");
    String name = "";
    List<String> frames = new ArrayList<>(), notes = new ArrayList<>();
    int omitted = 0;
    while (selected.more()) {
      int tag = selected.tag();
      if (tag == 18) name = selected.string(128);
      else if (tag == 34) {
        Cursor frame = selected.message();
        if (frames.size() < 64) frames.add(frame(frame, frames.size()));
        else omitted++;
      } else if (tag == 58) {
        String note = selected.string(512);
        if (notes.size() < 4) notes.add(note);
      } else selected.skip(tag);
    }
    if (frames.isEmpty()) throw new IOException("Android trace contains no native stack frames");
    String[] arches = {"ARM32", "ARM64", "x86", "x86-64", "RISCV64", "none"};
    StringBuilder b = new StringBuilder("Native crash stack (from Android):\n")
        .append("Trace time: ").append(timestamp).append("; architecture: ")
        .append(arch >= 0 && arch < arches.length ? arches[(int) arch] : Long.toString(arch))
        .append("; process uptime: ").append(uptime).append(" s\n")
        .append("Faulting thread: ").append(name).append(" (tid ").append(tid).append(")\n")
        .append(signal).append('\n');
    if (!abort.isEmpty()) b.append("Abort message: ").append(abort).append('\n');
    for (String cause : causes) if (!cause.isEmpty()) b.append("Android cause: ").append(cause).append('\n');
    for (String frame : frames) b.append(frame).append('\n');
    if (omitted != 0) b.append("[").append(omitted).append(" further frames omitted]\n");
    for (String note : notes) b.append("Unwind note: ").append(note).append('\n');
    return ExitReport.bounded(b.toString(), MAX_REPORT);
  }

  private static String signal(Cursor c) throws IOException {
    long number = 0, code = 0, address = 0;
    boolean hasAddress = false;
    String name = "", codeName = "";
    while (c.more()) {
      int tag = c.tag();
      switch (tag) {
        case 8: number = c.number(); break;
        case 18: name = c.string(64); break;
        case 24: code = c.number(); break;
        case 34: codeName = c.string(64); break;
        case 64: hasAddress = c.number() != 0; break;
        case 72: address = c.number(); break;
        default: c.skip(tag);
      }
    }
    return "Signal: " + name + " (" + (int) number + "); code: " + codeName + " (" + (int) code + ")"
        + (hasAddress ? "; fault address: 0x" + Long.toHexString(address) : "; fault address unavailable");
  }

  private static String cause(Cursor c) throws IOException {
    String text = "";
    while (c.more()) {
      int tag = c.tag();
      if (tag == 10) text = c.string(1024);
      else c.skip(tag);
    }
    return text;
  }

  private static String frame(Cursor c, int index) throws IOException {
    long relative = 0, offset = 0, mapOffset = 0;
    String function = "", file = "", build = "";
    while (c.more()) {
      int tag = c.tag();
      switch (tag) {
        case 8: relative = c.number(); break;
        case 34: function = c.string(384); break;
        case 40: offset = c.number(); break;
        case 50: file = c.string(512); break;
        case 56: mapOffset = c.number(); break;
        case 66: build = c.string(128); break;
        default: c.skip(tag);
      }
    }
    // Keep library identity and APK mapping offsets; omit installation paths.
    file = file.substring(file.lastIndexOf('/') + 1);
    return String.format(Locale.ROOT, "#%02d pc %016x  %s", index, relative, file)
        + (function.isEmpty() ? "" : " (" + function + "+" + Long.toUnsignedString(offset) + ")")
        + (mapOffset == 0 ? "" : " (map offset 0x" + Long.toHexString(mapOffset) + ")")
        + (build.isEmpty() ? "" : " (BuildId: " + build + ")");
  }

  private static final class Cursor {
    final byte[] bytes;
    final int end;
    int at;
    Cursor(byte[] bytes, int start, int end) { this.bytes = bytes; at = start; this.end = end; }
    boolean more() { return at < end; }
    long number() throws IOException {
      long value = 0;
      for (int shift = 0; shift < 64; shift += 7) {
        if (at >= end) throw new IOException("Truncated native trace integer");
        int b = bytes[at++] & 255;
        if (shift == 63 && b > 1) throw new IOException("Native trace integer overflow");
        value |= (long) (b & 127) << shift;
        if ((b & 128) == 0) return value;
      }
      throw new IOException("Invalid native trace integer");
    }
    int tag() throws IOException {
      long tag = number();
      if (tag < 8 || tag > 0xffffffffL) throw new IOException("Invalid native trace tag");
      return (int) tag;
    }
    Cursor message() throws IOException {
      long size = number();
      if (size < 0 || size > end - at) throw new IOException("Truncated native trace message");
      Cursor child = new Cursor(bytes, at, at + (int) size);
      at += (int) size;
      return child;
    }
    String string(int limit) throws IOException {
      Cursor c = message();
      String text = new String(bytes, c.at, Math.min(c.end - c.at, limit * 4), StandardCharsets.UTF_8);
      text = text.replace('\0', ' ').replace('\r', ' ').replace('\n', ' ');
      return ExitReport.bounded(text, limit);
    }
    void skip(int tag) throws IOException {
      int wire = tag & 7;
      if (wire == 0) { number(); return; }
      if (wire == 2) { message(); return; }
      int size = wire == 1 ? 8 : wire == 5 ? 4 : -1;
      if (size < 0 || size > end - at) throw new IOException("Invalid native trace field");
      at += size;
    }
  }
}

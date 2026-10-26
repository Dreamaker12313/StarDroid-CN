package org.openbw.androidtest;

import java.io.*;
import java.nio.file.*;
import java.util.*;

public final class ReplayStorage81Test {
  static int checks;
  interface Task { void run() throws Exception; }
  static void check(boolean test, String message) { checks++; if (!test) throw new AssertionError(message); }
  static void rejects(Task action, String message) throws Exception {
    try { action.run(); throw new AssertionError(message); }
    catch (IOException expected) { checks++; }
  }
  static byte[] payload(int variant) { byte[] bytes = new byte[64]; for (int i=0;i<bytes.length;i++) bytes[i]=(byte)(i+variant); return bytes; }

  public static void main(String[] args) throws Exception {
    Path root = Paths.get(args[0]); Files.createDirectories(root);
    NativeReplays store = new NativeReplays(root.toFile());
    check(store.list().isEmpty(), "Empty library is not empty");
    check(!root.resolve("replays").toFile().exists(), "Listing created an unnecessary folder");
    Files.createDirectory(root.resolve("replays"));
    Path stale=root.resolve("replays/replay-123.pending"), userPending=root.resolve("replays/replay-user.pending");
    Files.write(stale,payload(10));Files.write(userPending,payload(11));
    Path outsidePending=root.resolve("outside.pending"), linkedPending=root.resolve("replays/replay-234.pending");
    Files.write(outsidePending,payload(12));Files.createSymbolicLink(linkedPending,outsidePending);
    Path directoryPending=root.resolve("replays/replay-345.pending");Files.createDirectory(directoryPending);
    store.list();
    check(!Files.exists(stale), "Abandoned replay staging file was not cleaned");
    check(Files.exists(userPending), "Cleanup deleted an unrecognized staging name");
    check(Files.isSymbolicLink(linkedPending) && Files.exists(outsidePending), "Cleanup followed a symlink");
    check(Files.isDirectory(directoryPending), "Cleanup deleted a directory");
    Path live=root.resolve("replays/replay-456.pending");Files.write(live,payload(13));
    new NativeReplays(root.toFile()).list();
    check(Files.exists(live), "A second store cleaned an active-process staging file");
    for(Path p:new Path[]{userPending,linkedPending,directoryPending,live})Files.delete(p);
    byte[] one = payload(0), two = payload(1);
    File first = store.save(one, "../A Terran Game.rep");
    check(first.getParentFile().getCanonicalFile().equals(root.resolve("replays").toFile().getCanonicalFile()), "Name escaped library");
    check(NativeReplays.label(first).equals("A Terran Game"), "Display label exposes generated suffix");
    check(Arrays.equals(store.read(first), one), "Replay bytes changed");
    check(store.save(one, "Different filename.rep").equals(first), "Duplicate replay consumed storage");
    first.setLastModified(1000);
    File second = store.save(two, "C:\\temp\\Вторая игра.REP"); second.setLastModified(2000);
    check(NativeReplays.label(second).equals("Вторая игра"), "Localized label was lost");
    check(store.list().equals(Arrays.asList(second, first)), "Replay order should be newest first");
    File odd = store.save(payload(2), "\u0000\n...?.rep");
    check(NativeReplays.label(odd).equals("Replay"), "Invalid label needs useful fallback");
    File longName = store.save(payload(3), String.join("", Collections.nCopies(200,"漢"))+".rep");
    check(longName.getName().getBytes("UTF-8").length < 255, "Localized filename exceeds filesystem limit");
    File pending = root.resolve("replays/unfinished.pending").toFile(); Files.write(pending.toPath(), payload(4));
    File shortReplay = root.resolve("replays/truncated.rep").toFile(); Files.write(shortReplay.toPath(), new byte[2]);
    File unrelated = root.resolve("replays/keep.txt").toFile(); Files.write(unrelated.toPath(), one);
    check(store.list().size()==4, "Unfinished and unrelated files leaked into replay list");
    File outside = root.resolve("outside.rep").toFile(); Files.write(outside.toPath(), one);
    rejects(() -> store.read(outside), "Read escaped replay folder");
    rejects(() -> store.delete(outside), "Delete escaped replay folder");
    check(outside.isFile(), "Outside file was deleted");
    rejects(() -> store.delete(unrelated), "Deletion accepted non-replay file");
    check(unrelated.isFile(), "Unrelated file was deleted");
    Path symbolic = root.resolve("replays/linked.rep"); Files.createSymbolicLink(symbolic, outside.toPath());
    check(store.list().size()==4, "Symlink entered replay list");
    rejects(() -> store.read(symbolic.toFile()), "Read followed replay symlink");
    rejects(() -> store.delete(symbolic.toFile()), "Delete accepted replay symlink");
    rejects(() -> store.save(null,"missing"), "Null bytes were accepted");
    rejects(() -> store.save(new byte[15],"short"), "Truncated replay accepted");
    int count = store.list().size();
    rejects(() -> store.importReplay(new ByteArrayInputStream(payload(5)),"invalid.rep",bytes->{throw new IOException("Corrupt compressed replay");}), "Validator failure was ignored");
    check(store.list().size()==count, "Invalid import was persisted");
    boolean[] validated={false},closed={false};
    InputStream input = new ByteArrayInputStream(payload(6)) { public void close() { closed[0]=true; } };
    File imported=store.importReplay(input,"Imported.rep",bytes->{ validated[0]=Arrays.equals(bytes,payload(6)); });
    check(validated[0] && imported.isFile(), "Native validation was not run before import");
    check(!closed[0], "Store closed caller-owned stream");
    final long[] remaining={NativeReplays.LIMIT+1L};
    InputStream huge=new InputStream() {public int read(){return remaining[0]-->0?1:-1;}public int read(byte[] b,int o,int n){if(remaining[0]<=0)return -1;n=(int)Math.min(n,remaining[0]);Arrays.fill(b,o,o+n,(byte)1);remaining[0]-=n;return n;}};
    rejects(() -> store.importReplay(huge,"huge.rep"), "Oversized import accepted");
    check(store.list().size()==count+1, "Oversized import left a replay");
    InputStream zeroReads=new ByteArrayInputStream(payload(7)){boolean zero=true;public synchronized int read(byte[]b,int o,int n){if(zero){zero=false;return 0;}return super.read(b,o,n);}};
    File zero=store.importReplay(zeroReads,"Zero-read.rep");
    check(Arrays.equals(store.read(zero),payload(7)), "Zero-byte read loop lost input");
    store.delete(imported);
    check(!imported.exists() && !store.list().contains(imported), "DELETE did not remove chosen replay");
    check(first.isFile() && second.isFile(), "DELETE changed another replay");
    rejects(() -> store.delete(imported), "Deleting stale selection should fail clearly");
    check(Arrays.stream(root.resolve("replays").toFile().list()).filter(n->n.endsWith(".pending")).count()==1,"Write leaked temporary files");
    Path alternate=root.resolve("alternate");Files.createDirectories(alternate);Files.createSymbolicLink(alternate.resolve("replays"),root.resolve("replays"));
    NativeReplays linkedFolder=new NativeReplays(alternate.toFile());
    rejects(() -> linkedFolder.list(), "Linked replay folder accepted");
    rejects(() -> linkedFolder.save(payload(8),"escape"), "Write followed folder symlink");
    check(!Files.exists(root.resolve("replays/escape.rep")), "Invalid write created file");
    System.out.println("PASS "+checks+" replay storage checks: byte preservation, labels, order, deduplication, bounded imports, validation rollback, atomic writes, owned DELETE and symlink isolation");
  }
}

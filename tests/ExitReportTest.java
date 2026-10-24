package org.openbw.androidtest;

public final class ExitReportTest {
  private static int checks;
  private static void check(boolean value, String message) {
    checks++;
    if (!value) throw new AssertionError(message);
  }
  public static void main(String[] args) {
    check(ExitReport.reason(2, 9).contains("not confirmed"), "SIGKILL must not diagnose OOM");
    check(!ExitReport.reason(2, 9).equals(ExitReport.reason(3, 0)), "Signal and low-memory reasons differ");
    check(ExitReport.reason(5, 11).contains("Native C++"), "Native crash");
    check(ExitReport.reason(4, 0).contains("Java crash"), "Java crash");
    check(ExitReport.reason(6, 0).contains("ANR"), "ANR");
    check(ExitReport.reason(16, 0).contains("updated"), "Update not crash");
    check(ExitReport.reason(999, 0).contains("Unknown"), "Future reason stays unknown");
    check(ExitReport.bounded(null, 10).equals(""), "Null message");
    String large = new String(new char[40000]).replace('\0', 'x');
    for (int limit : new int[]{-1, 0, 1, 10, 15, 256, ExitReport.LIMIT})
      check(ExitReport.bounded(large, limit).length() <= Math.max(0, limit), "Size bound " + limit);
    Exception cause = new Exception("Missing graphics resource");
    Exception error = new Exception("Renderer failed", cause);
    String report = ExitReport.failure("Renderer stopped", "Page: game; foreground=true", error);
    check(report.contains("Missing graphics resource") && report.contains("Caused by:"), "Keep root cause");
    check(report.contains("Page: game"), "Keep session context");
    check(report.contains("ExitReportTest.main"), "Keep stack frame");
    Exception cyclic = new Exception("cycle");
    cyclic.initCause(error);
    cause.initCause(cyclic);
    String cycleReport = ExitReport.failure("cycle", "", error);
    check(cycleReport.indexOf("Renderer failed") == cycleReport.lastIndexOf("Renderer failed"), "Stop cause cycles");
    OutOfMemoryError allocation = new OutOfMemoryError(large);
    StackTraceElement[] frames = new StackTraceElement[300];
    java.util.Arrays.fill(frames, new StackTraceElement("Renderer", "draw", "Renderer.java", 123));
    allocation.setStackTrace(frames);
    String bounded = ExitReport.failure(large, large, allocation);
    check(bounded.length() <= ExitReport.LIMIT, "Bound complete report");
    check(bounded.contains("OutOfMemoryError"), "Preserve failure category");
    check(bounded.contains("remaining frames omitted"), "Bound huge stack");
    System.out.println("PASS " + checks + " exit classification, size, cause-chain, stack and OOM-report checks");
  }
}

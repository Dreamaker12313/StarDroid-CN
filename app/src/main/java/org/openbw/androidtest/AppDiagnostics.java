package org.openbw.androidtest;

import android.app.ActivityManager;
import android.app.ApplicationExitInfo;
import android.content.Context;
import android.os.Build;
import android.os.Debug;
import android.util.AtomicFile;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;

/** Local-only evidence for unexpected closes; nothing is uploaded automatically. */
final class AppDiagnostics {
  private static AtomicFile lastFailure;
  private static AtomicFile lastNativeTrace;
  private static volatile String savedFailure = "No saved Java/renderer failure.";
  private static volatile String savedNativeTrace = "No native stack captured yet.";
  private static volatile String exits = "Android exit history is loading; reopen Diagnostics shortly.";
  private static volatile String session = "Starting";
  private static volatile String trim = "No memory-pressure callback in this process.";
  private static volatile boolean foreground;
  private static boolean installed;

  static synchronized void install(Context context) {
    if (installed) return;
    installed = true;
    lastFailure = new AtomicFile(new File(context.getFilesDir(), "last-failure.txt"));
    lastNativeTrace = new AtomicFile(new File(context.getFilesDir(), "last-native-crash.txt"));
    try {
      File file = lastFailure.getBaseFile();
      if (file.isFile() && file.length() <= ExitReport.LIMIT * 4L)
        savedFailure = ExitReport.bounded(new String(lastFailure.readFully(), StandardCharsets.UTF_8), ExitReport.LIMIT);
    } catch (Exception ignored) { savedFailure = "Previous failure report could not be read."; }
    try {
      File file = lastNativeTrace.getBaseFile();
      if (file.isFile() && file.length() <= NativeCrashTrace.MAX_REPORT * 4L)
        savedNativeTrace = ExitReport.bounded(new String(lastNativeTrace.readFully(), StandardCharsets.UTF_8), NativeCrashTrace.MAX_REPORT);
    } catch (Exception ignored) { savedNativeTrace = "Previous native stack could not be read."; }
    final Thread.UncaughtExceptionHandler original = Thread.getDefaultUncaughtExceptionHandler();
    Thread.setDefaultUncaughtExceptionHandler((thread, error) -> {
      try { recordFailure("Unhandled Java failure on " + thread.getName(), error); }
      finally {
        // Preserve Android's normal crash reporting and termination behavior.
        if (original != null) original.uncaughtException(thread, error);
        else { android.os.Process.killProcess(android.os.Process.myPid()); System.exit(10); }
      }
    });
  }

  static void foreground(boolean value) { foreground = value; }
  static void session(String value) { session = ExitReport.bounded(value, 3500); }
  static void memoryPressure(int level) {
    trim = new Date() + ": onTrimMemory level " + level + "; foreground=" + foreground;
  }

  static synchronized void recordFailure(String heading, Throwable error) {
    FileOutputStream out = null;
    try {
      String context = "Recorded: " + new Date() + "\nStarDroid " + BuildConfig.VERSION_NAME
          + " (" + BuildConfig.VERSION_CODE + ")\nForeground: " + foreground
          + "\n" + memory() + "\n" + trim + "\n" + session;
      savedFailure = ExitReport.failure(heading, context, error);
      if (lastFailure != null) {
        out = lastFailure.startWrite();
        out.write(savedFailure.getBytes(StandardCharsets.UTF_8));
        lastFailure.finishWrite(out);
      }
    } catch (Throwable ignored) {
      // Reporting is best-effort, especially during an allocation failure.
      if (out != null && lastFailure != null) try { lastFailure.failWrite(out); } catch (Throwable alsoIgnored) {}
    }
  }

  static void loadPreviousExits(Context context) {
    if (Build.VERSION.SDK_INT < 30) {
      exits = "Android exit history requires Android 11+. Saved Java failures are still available.";
      return;
    }
    try { exits = Api30.previous(context); }
    catch (Exception error) { exits = "Android exit history unavailable: " + error.getClass().getSimpleName(); }
  }

  static String summary(Context context) {
    String system = "";
    try {
      ActivityManager manager = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
      ActivityManager.MemoryInfo info = new ActivityManager.MemoryInfo();
      if (manager != null) {
        manager.getMemoryInfo(info);
        system = "\nSystem RAM: " + info.availMem / 1048576 + " / " + info.totalMem / 1048576
            + " MiB available; lowMemory=" + info.lowMemory;
      }
    } catch (RuntimeException ignored) { system = "\nSystem memory information unavailable."; }
    return "\nMemory now (not memory at the previous close):\n" + memory() + system
        + "\n" + trim + "\n\nPrevious process exits reported by Android:\n" + exits
        + "\n\nLast captured native stack (check its timestamp):\n" + savedNativeTrace
        + "\n\nLast saved Java/renderer failure (check its timestamp):\n" + savedFailure + "\n";
  }

  private static synchronized void retainNativeTrace(String text) {
    savedNativeTrace = text;
    FileOutputStream out = null;
    try {
      if (lastNativeTrace != null) {
        out = lastNativeTrace.startWrite();
        out.write(text.getBytes(StandardCharsets.UTF_8));
        lastNativeTrace.finishWrite(out);
      }
    } catch (Exception ignored) {
      if (out != null && lastNativeTrace != null) try { lastNativeTrace.failWrite(out); } catch (Exception alsoIgnored) {}
    }
  }

  private static String memory() {
    Runtime runtime = Runtime.getRuntime();
    return "Java heap used/max: " + (runtime.totalMemory() - runtime.freeMemory()) / 1048576
        + "/" + runtime.maxMemory() / 1048576 + " MiB; native allocations: "
        + Debug.getNativeHeapAllocatedSize() / 1048576 + " MiB";
  }

  @android.annotation.TargetApi(30)
  private static final class Api30 {
    static String previous(Context context) {
      ActivityManager manager = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
      if (manager == null) return "Android activity service unavailable.";
      List<ApplicationExitInfo> history = manager.getHistoricalProcessExitReasons(context.getPackageName(), 0, 8);
      if (history.isEmpty()) return "No exits retained by Android. This does not rule out a previous crash.";
      StringBuilder b = new StringBuilder();
      boolean triedNative = false;
      for (ApplicationExitInfo info : history) {
        b.append(new Date(info.getTimestamp())).append(" — ")
            .append(ExitReport.reason(info.getReason(), info.getStatus())).append('\n')
            .append("  reason=").append(info.getReason()).append("; status=").append(info.getStatus())
            .append("; importance=").append(info.getImportance())
            .append(info.getImportance() == ActivityManager.RunningAppProcessInfo.IMPORTANCE_FOREGROUND ? " (foreground)" : "")
            .append("; last sampled PSS/RSS=").append(info.getPss()).append('/').append(info.getRss()).append(" KiB\n");
        String description = info.getDescription();
        if (description != null && !description.isEmpty())
          b.append("  ").append(ExitReport.bounded(description, 1200)).append('\n');
        if (!triedNative && info.getReason() == ApplicationExitInfo.REASON_CRASH_NATIVE) {
          triedNative = true;
          if (Build.VERSION.SDK_INT < 31) b.append("  Native stack retrieval requires Android 12+.\n");
          else try (InputStream trace = info.getTraceInputStream()) {
            if (trace == null) b.append("  Native stack no longer available from Android.\n");
            else {
              String text = "Exit recorded: " + new Date(info.getTimestamp()) + "\n" + NativeCrashTrace.read(trace);
              retainNativeTrace(ExitReport.bounded(text, NativeCrashTrace.MAX_REPORT));
              b.append("  Native stack captured below.\n");
            }
          } catch (Exception error) {
            b.append("  Native stack unavailable: ").append(error.getClass().getSimpleName())
                .append(": ").append(ExitReport.bounded(error.getMessage(), 160)).append('\n');
          }
        }
      }
      b.append("Android retains a limited history. An update or requested stop is not itself a crash.\n")
          .append("A signal-9 exit alone does not identify memory pressure or a vendor battery policy.\n");
      return b.toString();
    }
  }
}

package org.openbw.androidtest;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Bounded, plain-text reports. A SIGKILL alone must not be called an OOM. */
final class ExitReport {
  static final int LIMIT = 16384;

  static String reason(int reason, int status) {
    switch (reason) {
      case 1: return "App exited itself";
      case 2: return status == 9
          ? "Process killed (SIGKILL); memory pressure or another cause is not confirmed"
          : "Process terminated by signal " + status;
      case 3: return "Android low-memory kill";
      case 4: return "Unhandled Java crash";
      case 5: return "Native C++ crash";
      case 6: return "App not responding (ANR)";
      case 7: return "App initialization failure";
      case 8: return "Permission changed";
      case 9: return "Excessive resource use";
      case 10: return "User/system requested stop (may include an update on older Android)";
      case 11: return "User stopped";
      case 12: return "Required process stopped";
      case 13: return "Other system termination; see Android description";
      case 14: return "Freezer termination";
      case 15: return "App/package state changed";
      case 16: return "App updated";
      default: return "Unknown Android exit reason " + reason;
    }
  }

  static String bounded(String text, int limit) {
    if (text == null) return "";
    limit = Math.max(0, limit);
    String suffix = "\n[truncated]\n";
    if (text.length() <= limit) return text;
    if (limit < suffix.length()) return text.substring(0, limit);
    return text.substring(0, limit - suffix.length()) + suffix;
  }

  static String failure(String heading, String context, Throwable error) {
    StringBuilder b = new StringBuilder(bounded(heading, 256)).append('\n')
        .append(bounded(context, 4096)).append('\n');
    Set<Throwable> seen = Collections.newSetFromMap(new IdentityHashMap<Throwable, Boolean>());
    for (int cause = 0; error != null && cause < 5 && seen.add(error); cause++, error = error.getCause()) {
      if (cause != 0) b.append("Caused by: ");
      b.append(error.getClass().getName()).append(": ")
          .append(bounded(error.getMessage(), 1024)).append('\n');
      StackTraceElement[] frames = error.getStackTrace();
      for (int i = 0; i < Math.min(frames.length, 32); i++)
        b.append("  at ").append(bounded(frames[i].toString(), 256)).append('\n');
      if (frames.length > 32) b.append("  [remaining frames omitted]\n");
      if (b.length() >= LIMIT) break;
    }
    return bounded(b.toString(), LIMIT);
  }
}

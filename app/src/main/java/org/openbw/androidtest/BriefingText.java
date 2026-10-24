package org.openbw.androidtest;

import java.util.*;

/** Continuous scrolling follows speech, with the first viewport held until needed. */
final class BriefingText {
  static int activeLine(List<String> lines, double position, double spokenDuration) {
    if (lines.isEmpty()) return -1;
    if (spokenDuration <= 0) return lines.size() - 1;
    double total = 0;
    for (String line : lines) total += weight(line);
    double progress = Math.max(0, Math.min(1, position / spokenDuration)) * total;
    for (int i = 0; i < lines.size() - 1; i++) {
      progress -= weight(lines.get(i));
      if (progress < 0) return i;
    }
    return lines.size() - 1;
  }
  private static double weight(String line) {
    double result = 1;
    for (char c : NativeArt.clean(line).toCharArray())
      result += Character.isLetterOrDigit(c) ? 1 : ".!?;:".indexOf(c) >= 0 ? 5 : c == ',' ? 2 : .4;
    return result;
  }
  static float scrollFor(int line, int height) {
    return Math.max(0, (line + 1) * 19 - height);
  }

  static float scroll(List<String> lines, double position, double duration, int height) {
    float distance = Math.max(0, lines.size() * 19 - height);
    if (distance == 0 || duration <= 0 || position <= 0) return 0;
    double total = 0;
    for (String line : lines) total += weight(line);
    // One continuous crawl. Per-row easing produced a jump/pause for every line.
    int visible = Math.max(1, height / 19);
    double firstScreen = 0;
    for (int i = 0; i < Math.min(visible, lines.size()); i++) firstScreen += weight(lines.get(i));
    double start = Math.max(0, firstScreen / total * duration - 900);
    double end = Math.max(start + 1, duration - 500);
    return (float)(distance * Math.max(0, Math.min(1, (position - start) / (end - start))));
  }
}

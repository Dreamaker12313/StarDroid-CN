package org.openbw.androidtest;

/** Readable touch feedback shared by free actions, construction and abilities. */
final class CommandHint {
  static String describe(String[] fields, String requirement) {
    return describe(fields, requirement, originalHotkey(fields));
  }

  static String originalHotkey(String[] fields) {
    if (fields == null || fields.length == 0 || fields[0] == null || fields[0].length() != 1) return "";
    char key = fields[0].charAt(0);
    if (key == 27) return "Esc";
    return key >= 33 && key <= 126 ? Character.toString(Character.toUpperCase(key)) : "";
  }

  static String describe(String[] fields, String requirement, String hotkey) {
    if (fields == null || fields.length < 3) return "";
    String label = fields[1];
    if (hotkey != null && !hotkey.isEmpty()) label += " [\u0003" + hotkey + "\u0002]";
    StringBuilder cost = new StringBuilder();
    add(cost, number(fields, 4), "minerals");
    add(cost, number(fields, 5), "Vespene Gas");
    add(cost, number(fields, 13), "energy");
    int supply = number(fields, 14);
    if (supply > 0) {
      if (cost.length() > 0) cost.append(" · ");
      cost.append(supply / 2);
      if (supply % 2 != 0) cost.append(".5");
      cost.append(" supply");
    }
    StringBuilder text = new StringBuilder(label);
    if (cost.length() > 0) text.append('\n').append(cost);
    if (fields.length > 8 && fields[8] != null && !fields[8].isEmpty())
      text.append('\n').append(fields[8]);
    if (requirement != null && !requirement.isEmpty()) text.append("\nRequires ").append(requirement);
    return text.toString();
  }
  private static int number(String[] fields, int index) {
    try { return index < fields.length ? Math.max(0, Integer.parseInt(fields[index])) : 0; }
    catch (NumberFormatException ignored) { return 0; }
  }
  private static void add(StringBuilder text, int amount, String unit) {
    if (amount == 0) return;
    if (text.length() > 0) text.append(" · ");
    text.append(amount).append(' ').append(unit);
  }
}

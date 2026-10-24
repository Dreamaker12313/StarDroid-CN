package org.openbw.androidtest;

/** Unit-specific positions that cannot be represented by one label-to-slot map. */
final class CommandSlots {
  static int override(int type, String label, int normal) {
    if (type == 116) {
      if (label.equals("Terran Covert Ops") || label.equals("Covert Ops")) return 6;
      if (label.equals("Terran Physics Lab") || label.equals("Physics Lab")) return 7;
    }
    boolean cloak = label.equals("Cloak") || label.equals("Decloak");
    if (type == 1 || type == 16 || type == 99 || type == 100 || type == 104) {
      if (cloak) return 6;
      if (label.equals("Lockdown")) return 7;
    }

    if ((type == 46 || type == 52) && (label.equals("Burrow") || label.equals("Unburrow"))) return 5;
    if (type == 51) {
      if (cloak) return 6;
      if (label.equals("Psionic Storm")) return 8;
      if (label.equals("Ensnare")) return 7;
      if (label.equals("Consume")) return 5;
    }
    return normal;
  }
}

package org.openbw.androidtest;

/** Action names remain available even when original dialog artwork cannot load. */
final class MenuLabels {
  static String forWidget(String name, int id, NativeArt.Widget widget, String override) {
    String original = widget == null || widget.text == null ? "" : widget.text;
    // BIN button strings start with a keyboard dispatch byte when flag 0x200
    // is set. It is metadata, not part of the visible caption.
    if (widget != null && (widget.flags & 0x200) != 0 && !original.isEmpty())
      original = original.substring(1);
    return override == null ? forDialog(name, id, original) : applyMnemonic(original, override);
  }

  static String applyMnemonic(String original, String replacement) {
    return PortText.preserveHotkey(PortText.text(original), PortText.text(replacement));
  }

  static int mnemonic(String label) {
    String shown = PortText.text(label);
    if (shown == null) return 0;
    int at = shown.indexOf('\u0004');
    if (at < 0 || at + 1 >= shown.length()) return 0;
    int end = at + 1;
    while (end < shown.length() && shown.charAt(end) >= 32) end++;
    String key = shown.substring(at + 1, end);
    if (key.equalsIgnoreCase("Esc")) return 27;
    if (key.length() != 1) return 0;
    char ch = Character.toLowerCase(key.charAt(0));
    return ch >= 'a' && ch <= 'z' || ch >= '0' && ch <= '9' ? ch : 0;
  }

  static String forDialog(String name, int id, String original) {
    return applyMnemonic(original, caption(name, id, original));
  }

  private static String caption(String name, int id, String original) {
    if (name.equals("glumain")) return id == 8 ? "View Intro" : forButton("main", id);
    if (name.equals("glucmpgn") || name.equals("gluexpcmpgn")) {
      boolean expansion = name.equals("gluexpcmpgn");
      switch (id) {
        case 5: return "Load Saved";
        case 11: return "Load Replay";
        case 6: return "Protoss\nEpisode " + (expansion ? "IV" : "III");
        case 7: return "Terran\nEpisode " + (expansion ? "V" : "I");
        case 8: return "Zerg\nEpisode " + (expansion ? "VI" : "II");
        case 9: return "Cancel";
        case 10: return "Play Custom";
      }
    }
    if (name.equals("glulogin")) switch (id) {
      case 4: return "OK"; case 5: return "Cancel"; case 6: return "New ID";
      case 7: return "Delete ID"; case 9: return "Select Player";
    }
    if (name.equals("gamemenu")) switch (id) {
      case 1: return "Save Game"; case 2: return "Load Game"; case 3: return "Game Options";
      case 4: return "StarCraft Tips"; case 5: return "Mission Objectives"; case 6: return "End Mission";
      case 65533: return "Resume Game"; case 65535: return "Game Menu";
    }
    if (name.equals("options")) switch (id) {
      case 1: return "Game Speed"; case 2: return "Sound & Music"; case 3: return "Video Options";
      case 4: return "Controls"; case 65533: return "Previous"; case 65535: return "Game Options";
    }
    if (name.equals("abrtmenu")) switch (id) {
      case 1: return "Restart Mission"; case 2: return "Return to menu"; case 3: return "Exit";
      case 65533: return "Previous"; case 65535: return "End Mission";
    }
    return original;
  }

  static String forButton(String page, int id) {
    if (page.equals("main")) switch (id) {
      case 3: return "Single Player";
      case 5: return "App Options";
      case 2: return "Exit";
      case 9: return "Credits";
      case 4: return "Multiplayer";
      case 8: return "Play Introduction";
    }
    if (page.equals("campaign")) switch (id) {
      case 6: return "Protoss Campaign";
      case 7: return "Terran Campaign";
      case 8: return "Zerg Campaign";
      case 9: return "Back";
      case 5: return "Load Game";
      case 11: return "Play Replay";
      case 10: return "Custom Game";
    }
    return "Back";
  }
}

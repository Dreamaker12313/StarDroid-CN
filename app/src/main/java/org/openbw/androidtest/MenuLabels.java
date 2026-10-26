package org.openbw.androidtest;

/** Action names remain available even when original dialog artwork cannot load. */
final class MenuLabels {
  static String forDialog(String name, int id, String original) {
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

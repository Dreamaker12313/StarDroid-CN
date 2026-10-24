package org.openbw.androidtest;

import java.util.*;
import org.json.*;

/** Original campaign intermissions, keyed by the mission that precedes them. */
final class CinematicCatalog {
  static final class Entry {
    final int after;
    final String file, title;
    Entry(int after, String file, String title) {this.after = after; this.file = "smk/" + file + ".smk"; this.title = title;}
    boolean expansion() {return after >= 300;}
  }
  static final Entry[] ALL = {
    new Entry(2, "terran1", "Wasteland Patrol"),
    new Entry(5, "terran2", "The Downing of the Norad II"),
    new Entry(9, "terran3", "Open Rebellion"),
    new Entry(12, "terran4", "The Inauguration"),
    new Entry(103, "zerg1", "The Dream"),
    new Entry(105, "zerg2", "Battle on the Amerigo"),
    new Entry(108, "zerg3", "The Warp"),
    new Entry(110, "zerg4", "The Invasion of Aiur"),
    new Entry(203, "protoss1", "The Fall of Fenix"),
    new Entry(205, "protoss2", "The Ambush"),
    new Entry(207, "protoss3", "The Return to Aiur"),
    new Entry(210, "protoss4", "The Death of the Overmind"),
    new Entry(308, "xprotoss", "The Destruction of Shakuras"),
    new Entry(408, "xterran", "UED Victory Report"),
    new Entry(510, "xzerg", "The Ascension")
  };
  static Entry after(int code) {for (Entry e : ALL) if (e.after == code) return e; return null;}
  static List<String> names() {
    List<String> result = new ArrayList<String>();
    result.add("smk\\starintr.smk"); result.add("smk\\starxintr.smk");
    for (Entry e : ALL) result.add(e.file.replace('/', '\\'));
    return result;
  }
  static JSONObject row(Entry e) {
    JSONObject r = new JSONObject();
    try {r.put("cinematic", e.file); r.put("title", e.title); r.put("game", e.expansion() ? "broodwar" : "starcraft");}
    catch (JSONException impossible) {throw new IllegalStateException(impossible);}
    return r;
  }
}

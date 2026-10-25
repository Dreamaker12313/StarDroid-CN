package org.openbw.androidtest;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Translates presentation only. Command names, filenames and saved identifiers stay stable. */
final class PortText {
  static volatile String language = "en";
  private static volatile Map<String, String[]> entries = Collections.emptyMap();
  private static volatile List<String> keys = Collections.emptyList();
  private static final Map<String,String> cache = Collections.synchronizedMap(new LinkedHashMap<String,String>() {
    protected boolean removeEldestEntry(Map.Entry<String,String> e) { return size() > 2048; }
  });
  static void load(InputStream input) throws IOException {
    Map<String,String[]> result = new HashMap<>();
    try (BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8))) {
      String row;
      while ((row = reader.readLine()) != null) {
        if (row.isEmpty() || row.startsWith("#")) continue;
        String[] cells = row.split("\t", -1);
        if (cells.length != 5) throw new IOException("Invalid UI translation row");
        for (int i = 0; i < cells.length; i++) cells[i] = cells[i].replace("\\n", "\n");
        result.put(cells[0], cells);
      }
    }
    List<String> sorted = new ArrayList<>(result.keySet());
    Collections.sort(sorted, (a,b) -> Integer.compare(b.length(),a.length()));
    entries = Collections.unmodifiableMap(result); keys = Collections.unmodifiableList(sorted); cache.clear();
  }
  static void select(String code) {
    language = Arrays.asList("en","ru","de","es","fr").contains(code) ? code : "en";
    cache.clear();
  }
  static String[] availableLanguages(boolean russian) {
    return new String[]{"en","ru","de","es","fr"};
  }
  static String text(String value) {
    if (value == null || value.isEmpty() || language.equals("en")) return value;
    String hit = cache.get(value); if (hit != null) return hit;
    String translated = translate(value, 0); cache.put(value, translated); return translated;
  }
  private static String translate(String value, int depth) {
    if (depth > 5) return value;
    int column = language.equals("ru") ? 1 : language.equals("de") ? 2 : language.equals("es") ? 3 : 4;
    String plain = value.replaceAll("[\\x01-\\x08\\x0b-\\x1f]", "");
    String trimmed = plain.trim();
    String[] exact = entries.get(trimmed);
    if (exact != null) return plain.replace(trimmed, exact[column]);
    for (String marker : new String[]{"✓ ","○ ","> "})
      if (plain.startsWith(marker)) return marker + translate(plain.substring(marker.length()),depth+1);
    if (plain.contains(" · ")) {
      String[] parts=plain.split(" · ",-1);
      for(int i=0;i<parts.length;i++)parts[i]=translate(parts[i],depth+1);
      return String.join(" · ",parts);
    }
    if (plain.matches("[0-9 /]+ (maps|movies)")) {
      int at=plain.lastIndexOf(' ');return plain.substring(0,at+1)+entries.get(plain.substring(at+1))[column];
    }
    if (plain.contains("\n") || plain.contains("\t")) {
      StringBuilder out = new StringBuilder(); int start = 0;
      for (int i = 0; i < plain.length(); i++) if (plain.charAt(i) == '\n' || plain.charAt(i) == '\t') {
        out.append(translate(plain.substring(start,i),depth+1)).append(plain.charAt(i)); start = i+1;
      }
      return out.append(translate(plain.substring(start),depth+1)).toString();
    }
    for (String key : keys) {
      if (plain.startsWith(key + ": "))
        return entries.get(key)[column] + ": " + translate(plain.substring(key.length()+2),depth+1);
      if (plain.startsWith(key + " ") && plain.length() > key.length()+1
          && (Character.isDigit(plain.charAt(key.length()+1)) || key.endsWith("…")))
        return entries.get(key)[column] + " " + translate(plain.substring(key.length()+1),depth+1);
    }
    for (String prefix : new String[]{"Train ","Build ","Research ","Morph ","Upgrade ","Load Slot ","Slot ","Import ","Imported ","Missing   ","Ready   ","Game saved in Slot ","Multiplayer game saved in Slot ","Starting in ","Group ","Delete ","Connect to ","Hosting as ","Tap a destination slot to move ","Replace the game in Slot "}) {
      String[] word = entries.get(prefix.trim());
      if (word != null && plain.startsWith(prefix)) return word[column]+" "+translate(plain.substring(prefix.length()),depth+1);
    }
    return value;
  }
}

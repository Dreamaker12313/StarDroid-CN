package org.openbw.androidtest;

import android.graphics.*;
import java.util.*;

/** Race-specific original score artwork, BIN geometry and shaded UI fonts. */
final class NativeResults {
  final NativeArt.Dialog layout;
  final NativeArt.PCX background, main, inset, scorebox, tabArt;
  final NativeArt.Font tiny, small, medium, large, title;
  final boolean won;
  boolean canSave, exiting, counting, audioCounting;
  static final int COUNT_MS=2200;
  double countElapsed;
  final Bitmap[][] barParts=new Bitmap[12][6];
  String playerName = "Player";
  final String[] slotNames = new String[8];
  final List<String> factionNames = new ArrayList<String>();
  final List<int[]> rows = new ArrayList<int[]>();
  final int elapsed;
  int tab = 0, hot = -1;
  double progress = 0, animationElapsed = 0;
  final Paint paint = new Paint();

  NativeResults(NativeArt art, int race, boolean victory, String raw) {
    won = victory;
    String key = new String[] {"z", "t", "p"}[Math.max(0, Math.min(2, race))] + (won ? "v" : "d"),
        pal = "glue/pal" + key + "/", prefix = "glue/score" + key + "/";
    background = art.pcx(pal + "backgnd.pcx", false, -1);
    NativeArt.PCX tint = art.pcx(pal + "tfont.pcx", false, -1);
    int glass = art.pcx(pal + "teffect.pcx", false, -1).pixels[1] & 255;
    main = art.pcx(prefix + "pmain.pcx", true, glass);
    inset = art.pcx(prefix + "pinset.pcx", true, glass);
    scorebox = art.pcx(prefix + "scorebox.pcx", true, glass);
    tabArt = art.pcx(prefix + "untab.pcx", true, glass);
    byte[] bars=art.read(prefix+"iscore.grp");
    for(int color=0;color<12;color++)for(int part=0;part<6;part++)barParts[color][part]=NativeArt.grp(bars,6+color*6+part,background.palette,true,false);
    // Match the glue menus' inter-glyph spacing, including the fallback font.
    tiny = art.font("8", tint, background.palette, 1);
    small = art.font("10", tint, background.palette, 1);
    medium = art.font("14", tint, background.palette, 1);
    large = art.font("16", tint, background.palette, 1);
    title = art.font("16x", tint, background.palette, 1);
    layout = new NativeArt.Dialog(art.read("rez/gluscore.bin"));
    String[] lines = raw.split("\n");
    elapsed = Math.max(0, NativeHud.number(lines[0].split("\t"), 1, 0) / 24);
    for (int i = 1; i < lines.length && rows.size() < 8; i++) {
      String[] fields = lines[i].split("\t", -1);
      if (fields.length < 16) continue;
      int[] row = new int[19];
      for (int j = 0; j < row.length; j++) row[j] = NativeHud.number(fields, j, 0);
      rows.add(row);
      factionNames.add(fields.length > 19 ? NativeArt.clean(fields[19]).trim() : "");
    }
  }

  String rowName(int index) {
    int[] row=rows.get(index);if(row[0]!=0)return playerName;
    String faction=factionNames.get(index);if(!faction.isEmpty())return faction;
    int slot=row[16];String participant=slot>=0&&slot<slotNames.length?slotNames[slot]:null;
    return participant!=null&&!participant.trim().isEmpty()?participant:"Computer";
  }

  boolean ready() {return !exiting && animationElapsed >= NativeGlue.ENTER_MS;}

  int[] values(int[] r) {
    switch (tab) {
      case 1: return new int[] {r[3], r[8], r[9]};
      case 2: return new int[] {r[4], r[10], r[11]};
      case 3: return new int[] {r[5], r[6], r[14] + r[15]};
      default: return new int[] {r[12], r[13], r[5] + r[6]};
    }
  }

  static String fit(NativeArt.Font font, String text, int width) {
    text = NativeArt.clean(PortText.text(text)).replace('\n', ' ');
    if (font.measure(text) <= width) return text;
    while (!text.isEmpty() && font.measure(text + "...") > width) text = text.substring(0, text.length() - 1);
    return text + "...";
  }

  void line(Canvas c, String text, NativeArt.Font font, int color, int align,
      float x, float y, int width, int height) {
    c.save(); c.clipRect(x, y, x + width, y + height);
    font.draw(c, fit(font, text, width), x, y + Math.max(0, (height-font.height)/2), width, align, color, 0);
    c.restore();
  }

  NativeArt.Font nameFont(String text, int width) {
    for (NativeArt.Font font : new NativeArt.Font[] {large, medium, small})
      if (font.measure(text) <= width) return font;
    return tiny;
  }

  // Campaign factions and player IDs must remain complete. Use the largest
  // original bitmap font that fits, rather than hiding the end with an ellipsis.
  // Exceptionally long custom/localized names can still fit without crossing
  // the score columns; ordinary campaign names need no bitmap scaling.
  void nameLine(Canvas c, String text, NativeArt.Font font, int color,
      float x, float y, int width, int height) {
    text = NativeArt.clean(PortText.text(text)).replace('\n', ' ').trim();
    int measured = font.measure(text);
    float scale = Math.min(1f, width / (float)Math.max(1, measured));
    c.save(); c.clipRect(x, y, x + width, y + height);
    c.translate(x, y + Math.max(0, (height-font.height*scale)/2));
    c.scale(scale, scale);
    // Width zero keeps a name on one line; the outer transform owns its fit.
    font.draw(c, text, 0, 0, 0, 0, color, 0);
    c.restore();
  }

  void label(Canvas c, int id, String text, NativeArt.Font font, int color, int align) {
    NativeArt.Widget w = layout.get(id);
    if (w != null) line(c, text, font, color, align, w.x, w.y, w.w, w.h);
  }

  void image(Canvas c, NativeArt.PCX pcx, NativeArt.Widget w) {
    if (w != null) c.drawBitmap(pcx.image, null, w.rect(), NativeArt.PIXELS);
  }

  void panels(Canvas c) {
    c.drawBitmap(main.image, 0, 0, NativeArt.PIXELS);
    NativeArt.Widget active = layout.get(3 + tab);
    if (active != null) c.drawBitmap(tabArt.image, active.x, active.y, NativeArt.PIXELS);
    for (int i = 0; i < rows.size(); i++) {
      image(c, inset, layout.get(13 + i * 6));
      image(c, scorebox, layout.get(18 + i * 6));
    }
  }

  void bar(Canvas c,Bitmap[] parts,int first,float x,float y,int width) {
    Bitmap left=parts[first],middle=parts[first+1],right=parts[first+2];
    if(left==null||middle==null||right==null)return;
    float lw=left.getWidth(),rw=right.getWidth();
    c.drawBitmap(left,x,y,NativeArt.PIXELS);
    c.drawBitmap(middle,null,new RectF(x+lw,y,x+width-rw,y+middle.getHeight()),NativeArt.PIXELS);
    c.drawBitmap(right,x+width-rw,y,NativeArt.PIXELS);
  }
  void scoreBar(Canvas c,int color,float x,float y,int width,float fraction) {
    Bitmap[] parts=barParts[Math.max(0,Math.min(11,color))];
    bar(c,parts,3,x,y,width);
    if(fraction<=0)return;
    c.save();c.clipRect(x+1,y+2,x+1+(width-2)*Math.min(1,fraction),y+16);
    bar(c,parts,0,x+2,y+2,width-4);c.restore();
  }

  void draw(Canvas c, double dt) {
    animationElapsed += Math.max(0, dt);
    double p = Math.min(1, animationElapsed / (exiting ? NativeGlue.EXIT_MS : NativeGlue.ENTER_MS));
    float distance = 640 * (float)(exiting ? 1-Math.pow(1-p,3) : Math.pow(1-p,3));
    c.drawBitmap(background.image, 0, 0, NativeArt.PIXELS);
    c.save(); c.translate(-distance, 0);
    if(counting && !audioCounting && !exiting){countElapsed+=Math.max(0,dt);progress=Math.min(1,countElapsed/COUNT_MS);}
    panels(c);
    label(c, 2, won ? "Victory!" : "Defeat", title, won ? 4 : 2, 1);
    String[] tabs = {"Overview", "Units", "Structures", "Resources"};
    for (int i = 0; i < 4; i++) label(c, 3+i, tabs[i], small, i == tab || hot == 3+i ? 4 : 2, 1);
    String[][] headings = {{"Units", "Structures", "Resources"}, {"Produced", "Killed", "Lost"},
        {"Constructed", "Razed", "Lost"}, {"Minerals", "Vespene Gas", "Spent"}};
    for (int i = 0; i < 3; i++) label(c, 10+i, headings[tab][i], small, 2, 1);
    label(c, 8, "Total Score", title, 2, 1);
    int max = 1;
    for (int[] r : rows) for (int v : values(r)) max = Math.max(max, v);
    for (int i = 0; i < rows.size(); i++) {
      int[] r = rows.get(i); int base = 13 + i * 6;
      NativeArt.Widget name = layout.get(base+1);
      if (name != null) {
        // The BIN name widget extends under score columns; its content must not.
        NativeArt.Widget firstScore = layout.get(base+2);
        int width = Math.max(1, Math.min(name.w,
            firstScore != null ? firstScore.x-name.x-8 : 144));
        String player = rowName(i);
        nameLine(c, player, nameFont(player, width), r[0] != 0 ? 4 : 2,
            name.x, name.y, width, 19);
        String subtitle=r[0]!=0&&!factionNames.get(i).isEmpty()?factionNames.get(i)
            :new String[]{"Zerg","Terran","Protoss"}[Math.max(0,Math.min(2,r[1]))];
        nameLine(c, subtitle, tiny, 2, name.x, name.y+19, width, 14);
      }
      int[] v = values(r);
      for (int j = 0; j < 3; j++) {
        NativeArt.Widget w = layout.get(base+2+j);
        label(c, base+2+j, Integer.toString((int)(v[j]*progress)), small, 2, 1);
        if (w != null) {
          float fraction=(float)Math.max(0,v[j])/max*(float)progress;
          scoreBar(c,r[2],w.x,w.y+17,w.w,fraction);
        }
      }
      label(c, base+5, Long.toString((long)(((long)r[12]+r[13]+r[5]+r[6])*progress)), large, 2, 1);
    }
    NativeArt.Widget time = layout.get(9);
    if (time != null) line(c, "Elapsed Time: " + elapsed/60 + ":" + String.format(Locale.ROOT,"%02d",elapsed%60),
        large,2,0,time.x,time.y,218,time.h);
    label(c,7,"OK",title,hot == 7 ? 4 : 3,1);
    label(c,61,"Save Replay",title,canSave ? hot == 61 ? 4 : 3 : 5,1);
    c.restore();
  }
}

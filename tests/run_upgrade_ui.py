#!/usr/bin/env python3
"""Render real locked upgrade cards through the existing original-art HUD harness."""
from pathlib import Path
import hashlib, json, subprocess

r = Path(__file__).resolve().parents[1]
out = r/'build-native/upgrades65'
hud = r/'build-native/hud59'
src = r/'app/src/main/java/org/openbw/androidtest'
surface = (src/'NativeHud.java').read_text()
start = surface.index('  void tooltip(Canvas canvas, String text, int width, int supplyRace)')
end = surface.index('\n  RectF commandRect',start)
tooltip = surface[start:end]
java = r'''package org.openbw.androidtest;
import android.graphics.*;import java.nio.file.*;import java.util.*;import javax.imageio.ImageIO;import org.json.*;
public class UpgradeUiHarness {
 static int checks;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static class Recording extends Canvas {Bitmap expected;int disabledDraws;Recording(Bitmap b,Bitmap target){super(b);expected=target;}
  public void drawBitmap(Bitmap b,float x,float y,Paint p){if(b==expected)disabledDraws++;super.drawBitmap(b,x,y,p);}}
 public static void main(String[]args)throws Exception {
  NativeBridge.root=Paths.get(args[0]);NativeArt art=new NativeArt();Path out=Paths.get(args[1]);
  JSONObject maps=new JSONObject(new String(Files.readAllBytes(Paths.get(args[2])),"UTF-8"));
  int[] races={1,1,1,0,0,2,2,1,1,1,0,0,0,2,2,2},producers={122,123,123,139,141,166,164,122,123,123,139,139,141,166,164,166};
  for(int id=0;id<16;id++)for(int width:new int[]{640,1000})for(float scale:new float[]{1,1.5f}){
   String[] lines=new String(Files.readAllBytes(out.resolve("upgrade-"+id+".tsv")),"UTF-8").split("\n");
   NativeHud h=new NativeHud(art,races[id],maps);h.commandScale=scale;String[] target=null;
   for(int n=1;n<lines.length;n++){String[] f=lines[n].split("\t",-1);if(f.length>11&&f[11].equals(""+id))target=f;}
   check(target!=null&&target[2].equals("0")&&!target[7].isEmpty(),"Native locked upgrade metadata missing");
   Bitmap image=Bitmap.createBitmap(width,480,Bitmap.Config.ARGB_8888);Recording c=new Recording(image,h.icon(Integer.parseInt(target[10]),1));
   c.drawBitmap(h.console.image,width-640,0,NativeArt.PIXELS);h.drawCommands(c,lines,producers[id],lines[0].split("\t")[0],width);
   check(c.disabledDraws>0,"Disabled upgrade did not use grey icon palette");
   NativeHud.Hit hit=null;for(NativeHud.Hit candidate:h.hits){check(!candidate.more,"Upgrade card unexpectedly paged");if(candidate.fields[11].equals(""+id))hit=candidate;
    check(candidate.rect.left>=0&&candidate.rect.top>=0&&candidate.rect.right<=width&&candidate.rect.bottom<=480,"Command outside viewport");}
   check(hit!=null,"Upgrade has no inspection hit target");
   if(scale==1){RectF expected=h.commandRect(maps.getJSONObject("upgradeSlots").getInt(""+id),width);check(hit.rect.left==expected.left&&hit.rect.top==expected.top,"Upgrade moved from original slot");}
   String help=CommandHint.describe(hit.fields,hit.fields[7]);check(help.contains("(Level 2)")&&help.contains("Requires "+target[7]),"Tooltip lost next level or prerequisite");
   UpgradeTooltip tip=new UpgradeTooltip();tip.small=h.small;tip.commandScale=scale;
   for(float size:new float[]{1,1.5f}){tip.descriptionScale=size;tip.tooltip(c,help,width,races[id]);}
   if(width==640&&scale==1)ImageIO.write(image.image,"png",out.resolve("upgrade-ui-"+id+".png").toFile());
  }
  System.out.println("PASS "+checks+" checks: all 16 actual native upgrade cards, grey palette, stable slots, next-level/prerequisite text, two widths and button/text sizes");
 }
}
class UpgradeTooltip {
 NativeArt.Font small;float commandScale=1,descriptionScale=1;Bitmap[]resources=new Bitmap[3],supplyIcons=new Bitmap[3];
 static void image(Canvas c,Bitmap b,float x,float y){if(b!=null)c.drawBitmap(b,x,y,NativeArt.PIXELS);}
''' + tooltip + '}\n'
harness = out/'UpgradeUiHarness.java'
harness.write_text(java)
jar = r/'build-native/json-20240303.jar'
cp = str(hud/'classes')+':'+str(jar)
subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn',
                '-classpath',cp,'-d',str(out/'ui-classes'),str(harness),str(src/'CommandHint.java')],check=True)
p = subprocess.run(['java','-Djava.awt.headless=true','-cp',str(out/'ui-classes')+':'+cp,
                    'org.openbw.androidtest.UpgradeUiHarness',str(hud/'assets'),str(out),str(r/'app/src/main/assets/native/commands.json')],capture_output=True,text=True)
print(p.stdout+p.stderr)
p.check_returncode()
files = [src/n for n in ['NativeHud.java','NativeArt.java','CommandHint.java','CommandSlots.java']]
files += [r/'patches/native-upgrades1.patch',r/'tests/native_upgrades.cpp',r/'tests/run_hud59.py',Path(__file__)]
(r/'validation/upgrade-ui-v1.0.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'output':p.stdout.strip(),
 'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},indent=2)+'\n')

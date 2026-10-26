#!/usr/bin/env python3
"""Exercise actual command-feedback routing and original-font overlay rendering.

Uses the established AWT Canvas shim; this is not a physical Android test.
"""
from pathlib import Path
import ast,hashlib,json,os,re,shutil,subprocess
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest'
b=r/'build-native/hover-errors11';b.mkdir(parents=True,exist_ok=True)
jdk=r/'.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64/bin'
if (jdk/'javac').is_file():os.environ['PATH']=str(jdk)+os.pathsep+os.environ['PATH']
assets=b/'assets';shutil.copytree(r/'build-native/replay-ui81/assets',assets,dirs_exist_ok=True)
metadata=assets/'0/font/font.gid';metadata.parent.mkdir(parents=True,exist_ok=True)
subprocess.run([str(r/'build-native/reign79/extract'),str(r/'build-native/reign79/core/STARDAT.MPQ'),'font/font.gid',str(metadata)],check=True,stdout=subprocess.DEVNULL)
for name in ['game/tfontgam.pcx','game/icons.grp','tileset/badlands.wpe']+['game/'+race+'console.pcx'for race in 'ztp']:
 for slot,archive in [(0,'STARDAT.MPQ'),(1,'BROODAT.MPQ'),(2,'patch_rt.mpq')]:
  target=assets/str(slot)/name;target.parent.mkdir(parents=True,exist_ok=True)
  call=subprocess.run([str(r/'build-native/reign79/extract'),str(r/'build-native/reign79/core'/archive),name,str(target)],capture_output=True)
  if call.returncode:target.unlink(missing_ok=True)
# Reuse shared drawing stubs without executing unrelated suites.
active=False
for node in ast.parse((r/'tests/run_gamepad81.py').read_text()).body:
 if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='old'for t in node.targets):active=True
 if active:
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='harness'for t in node.targets):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<hover error Canvas shim>','exec'),globals())
sources.pop('org/openbw/androidtest/MapScroll79Test.java',None)
sources['android/graphics/Canvas.java']=sources['android/graphics/Canvas.java'].replace('public int save(){','public AffineTransform transform(){return g.getTransform();}public int save(){')
sources['android/os/SystemClock.java']='package android.os;public class SystemClock{public static long now;public static long uptimeMillis(){return now;}}'
sources['org/openbw/androidtest/NativeBridge.java']=re.sub(r'static int value\([^}]+}', 'static int targeting;static int value(int kind,int index){return kind==0?targeting:0;}',sources['org/openbw/androidtest/NativeBridge.java'])
if 'static int targeting' not in sources['org/openbw/androidtest/NativeBridge.java']:
 sources['org/openbw/androidtest/NativeBridge.java']=sources['org/openbw/androidtest/NativeBridge.java'].replace('class NativeBridge{','class NativeBridge{static int targeting;static int value(int kind,int index){return kind==0?targeting:0;}')
def method(text,signature):
 start=text.index(signature);pos=text.index('{',start)+1;depth=1;end=pos
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[start:end]
hud=(src/'NativeHud.java').read_text();surface=(src/'NativeSurface.java').read_text()
feedback=method(surface,'  private void drawCommandFeedback(Canvas c)')
assert 'drawCommandFeedback(c);' in method(surface,'  private void draw(Canvas c, double dt)'), 'Game render does not call tested feedback'
methods='\n'.join(method(hud,s)for s in ['  static int number(','  String hotkey(', '  String hint(','  float commandErrorTop(','  void commandError(','  void tooltip(Canvas canvas, String text, int width) {','  void tooltip(Canvas canvas, String text, int width, int supplyRace) {','  void tooltip(Canvas canvas, String text, int width, int supplyRace, float bottomLimit) {'])
sources['org/openbw/androidtest/NativeHud.java']='''package org.openbw.androidtest;import android.graphics.*;import java.util.*;
class NativeHud {
 static final int WORLD_BOTTOM=376;int race;boolean gridHotkeys;float commandScale=1,descriptionScale=1;NativeArt.Font small,errorShadow;NativeArt.PCX console;final Bitmap[]resources=new Bitmap[3],supplyIcons=new Bitmap[3];final List<Hit>hits=new ArrayList<>();
 static final class Hit{RectF rect;String[]fields;int slot=-1,cancel=-1,selectUnit=-1,unload=-1;boolean more;String help;}
 NativeHud(NativeArt art,int race){this.race=race;console=art.pcx("game/"+new String[]{"z","t","p"}[race]+"console.pcx",true,-1);int[]palette=console.palette.clone();byte[]wpe=art.read("tileset/badlands.wpe");for(int i=0;i<256;i++)palette[i]=Color.rgb(wpe[i*4]&255,wpe[i*4+1]&255,wpe[i*4+2]&255);NativeArt.PCX colors=art.pcx("game/tfontgam.pcx",false,-1);small=art.font("10",colors,palette,0);errorShadow=small.withShadedColor(0xff000000);byte[]icons=art.read("game/icons.grp");int[]ids={0,1+race,4+race};for(int i=0;i<3;i++){resources[i]=NativeArt.grp(icons,ids[i],palette,true,false);supplyIcons[i]=NativeArt.grp(icons,4+i,palette,true,false);}}
 String requirement(String[]fields){return "";}
 static void image(Canvas c,Bitmap b,float x,float y){if(b!=null)c.drawBitmap(b,x,y,NativeArt.PIXELS);}
'''+methods+'\n}\n'
sources['org/openbw/androidtest/HoverErrors11Test.java']=r'''package org.openbw.androidtest;
import android.graphics.*;import java.util.*;import java.nio.file.*;import javax.imageio.ImageIO;import java.awt.geom.*;
public class HoverErrors11Test {
 static int checks,renders;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static final class Recording extends Canvas {
  Rectangle2D tooltip;Recording(Bitmap b){super(b);}
  public void drawRect(float l,float t,float r,float b,Paint p){if(p.color==0xf5081010)tooltip=transform().createTransformedShape(new Rectangle2D.Float(l,t,r-l,b-t)).getBounds2D();super.drawRect(l,t,r,b,p);}
 }
 static class CheckedHud extends NativeHud {
  int errorCalls,tooltipCalls,shownSupply;String errorText,tooltipText;
  CheckedHud(NativeArt a,int race){super(a,race);}
  void reset(){errorCalls=tooltipCalls=0;errorText=tooltipText="";}
  @Override void commandError(Canvas c,String text,int width){errorCalls++;errorText=text;super.commandError(c,text,width);}
  @Override void tooltip(Canvas c,String text,int width,int supply,float bottom){tooltipCalls++;tooltipText=text;shownSupply=supply;super.tooltip(c,text,width,supply,bottom);}
 }
 NativeHud hud;CommandHover commandHover=new CommandHover();String modal="",commandError="",hint="";double clock=1000,commandErrorUntil=2000,hintUntil=2000;int logicalWidth=640,hintSupplyRace=-1;
'''+feedback+r'''
 static Bitmap blank(int width){return Bitmap.createBitmap(width,480,Bitmap.Config.ARGB_8888);}
 static void same(Bitmap a,Bitmap z,int x,int y,int w,int h,String why){checks++;for(int yy=y;yy<y+h;yy++)for(int xx=x;xx<x+w;xx++)if(a.image.getRGB(xx,yy)!=z.image.getRGB(xx,yy))throw new AssertionError(why+" at "+xx+","+yy);}
 static boolean ink(Bitmap b){for(int y=0;y<b.getHeight();y++)for(int x=0;x<b.getWidth();x++)if((b.image.getRGB(x,y)>>>24)!=0)return true;return false;}
 static NativeHud.Hit hit(int width,int supply){NativeHud.Hit h=new NativeHud.Hit();h.slot=0;h.rect=new RectF(width-100,400,width-60,438);h.fields=new String[]{"m","Train Marine","1","0","50","25","","","Ranged ground combat unit.","0","0","-1","-1","0","2",String.valueOf(supply)};return h;}
 static void stateCases(NativeArt art)throws Exception{
  HoverErrors11Test v=new HoverErrors11Test();CheckedHud hud=new CheckedHud(art,1);v.hud=hud;NativeHud.Hit hit=hit(640,2);hud.hits.add(hit);v.commandHover.hover(550,410,false);v.commandError="Not enough minerals";
  Bitmap both=blank(640);v.drawCommandFeedback(new Recording(both));check(hud.errorCalls==1&&hud.tooltipCalls==1,"Error replaced mouse hover");check(hud.shownSupply==2,"Command supply race changed");
  hud.reset();v.modal="menu";Bitmap paused=blank(640);v.drawCommandFeedback(new Recording(paused));check(hud.errorCalls==0&&hud.tooltipCalls==0&&!ink(paused),"Modal leaks feedback");v.modal="";
  hud.reset();v.clock=2000;v.drawCommandFeedback(new Recording(blank(640)));check(hud.errorCalls==0&&hud.tooltipCalls==1,"Expired error hides hover");
  hud.reset();NativeBridge.targeting=1;v.drawCommandFeedback(new Recording(blank(640)));check(hud.errorText.equals("Select target")&&hud.tooltipCalls==1,"Target prompt replaces hover");
  hud.reset();NativeBridge.targeting=4;v.commandErrorUntil=3000;v.drawCommandFeedback(new Recording(blank(640)));check(hud.errorText.equals(v.commandError)&&hud.tooltipCalls==1,"Live error/target priority changed");
  hud.reset();v.commandHover.cancel();v.hint="Held command information";v.hintSupplyRace=0;v.hintUntil=3000;v.drawCommandFeedback(new Recording(blank(640)));check(hud.tooltipText.equals(v.hint)&&hud.shownSupply==0&&hud.errorCalls==1,"Stored hint replaced by error");
  hud.reset();v.hintUntil=2000;v.drawCommandFeedback(new Recording(blank(640)));check(hud.tooltipCalls==0&&hud.errorCalls==1,"Expired hint remains visible");
  hud.reset();v.hint="";NativeBridge.targeting=0;v.commandHover.begin(hit,550,410,1000);android.os.SystemClock.now=1219;v.drawCommandFeedback(new Recording(blank(640)));check(hud.tooltipCalls==0&&hud.errorCalls==1,"Hold starts early");
  hud.reset();android.os.SystemClock.now=1220;v.drawCommandFeedback(new Recording(blank(640)));check(hud.tooltipCalls==1&&hud.errorCalls==1,"Error hides touch hold");check(v.commandHover.release(hud.hits,550,410,1300)==null,"Inspection executes command");
  hud.reset();v.commandHover.enabled=false;v.commandHover.hover(550,410,false);v.drawCommandFeedback(new Recording(blank(640)));check(hud.tooltipCalls==0&&hud.errorCalls==1,"Disabled descriptions hide error or leak hover");
  hud.reset();v.commandHover.enabled=true;v.commandHover.hover(550,410,false);v.hint="Old hint";v.hintUntil=3000;v.drawCommandFeedback(new Recording(blank(640)));check(hud.tooltipText.startsWith("Train Marine"),"Stored hint overrides live hover");
  v.commandHover.hover(0,0,true);hud.reset();v.drawCommandFeedback(new Recording(blank(640)));check(hud.tooltipText.equals("Old hint"),"Hover exit loses valid held hint");
 }
 public static void main(String[]args)throws Exception{
  NativeBridge.root=Paths.get(args[0]);Path out=Paths.get(args[1]);PortText.load(Files.newInputStream(Paths.get(args[2])));NativeArt art=new NativeArt();stateCases(art);
  String[]messages={"Not enough minerals","Select target","Not enough Vespene Gas.\nBuild more supply to train this unit.","Недостаточно минералов.\nПостройте больше повелителей."};
  String longHint="Hive\n200 minerals · 150 Vespene Gas · 4 supply\nStructure. Receives gathered resources. Spawns larvae. Produces creep.\nRequires Zerg Queen's Nest";
  for(int race=0;race<3;race++){CheckedHud hud=new CheckedHud(art,race);
   for(int width:new int[]{640,960})for(float scale:new float[]{1,1.25f,1.5f})for(float command:new float[]{1,1.2f})for(String language:new String[]{"en","ru","de","es","fr"}){
    PortText.select(language);hud.descriptionScale=scale;hud.commandScale=command;
    for(String message:messages)for(boolean held:new boolean[]{false,true}){
     HoverErrors11Test v=new HoverErrors11Test();v.hud=hud;v.logicalWidth=width;v.commandError=message;hud.hits.clear();NativeHud.Hit hit=hit(width,(race+1)%3);hit.help=longHint;hit.fields=null;hud.hits.add(hit);
     if(held){v.commandHover.begin(hit,width-80,410,1000);android.os.SystemClock.now=1300;}else v.commandHover.hover(width-80,410,false);
     hud.reset();Bitmap image=blank(width);Recording c=new Recording(image);v.drawCommandFeedback(c);renders++;
     check(hud.errorCalls==1&&hud.tooltipCalls==1,"Concurrent feedback missing");check(c.tooltip!=null,"Tooltip panel missing");
     float errorTop=hud.commandErrorTop(message,width);check(c.tooltip.getMaxY()<=errorTop-7.9,"Tooltip covers error text");check(c.tooltip.getMinY()>=7.9&&c.tooltip.getMinX()>=7.9&&c.tooltip.getMaxX()<=width-7.9,"Tooltip leaves viewport");
     Bitmap only=blank(width);hud.commandError(new Canvas(only),message,width);int top=Math.max(0,(int)Math.floor(errorTop));same(image,only,0,top,width,480-top,"Tooltip changed status pixels");check(ink(only),"Error text empty");
     v.commandError="";hud.reset();Bitmap noError=blank(width);Recording normal=new Recording(noError);v.drawCommandFeedback(normal);check(hud.tooltipCalls==1&&hud.errorCalls==0,"Tooltip disappears when error ends");check(normal.tooltip.getMaxY()>=c.tooltip.getMaxY(),"Tooltip did not restore normal position");
     Bitmap direct=blank(width);hud.tooltip(new Canvas(direct),longHint,width,race);same(noError,direct,0,0,width,480,"No-error tooltip placement changed");
     if(!held&&message.equals(messages[0])&&scale==1&&command==1&&language.equals("en")){
      Bitmap scene=blank(width);Canvas display=new Canvas(scene);Paint terrain=new Paint();terrain.setColor(0xff272b25);display.drawRect(0,0,width,480,terrain);display.drawBitmap(hud.console.image,width-640,0,NativeArt.PIXELS);v.commandError=message;v.drawCommandFeedback(display);ImageIO.write(scene.image,"png",out.resolve("hover-error-"+race+"-"+width+".png").toFile());
     }
    }
   }
  }
  System.out.println("PASS "+checks+" checks; "+renders+" concurrent error/hover or touch-hold renders; three races, two widths, three description scales, two command scales, five UI languages; expiry/target/modal/disabled guards; status pixels unchanged");
 }
}'''
for name,text in sources.items():
 target=b/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
real=[src/n for n in ['NativeArt.java','CommandHint.java','CommandHover.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
subprocess.run(['javac','-d',str(b/'classes'),*[str(b/n)for n in sources],*map(str,real)],check=True)
call=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes'),'org.openbw.androidtest.HoverErrors11Test',str(assets),str(b),str(r/'app/src/main/assets/native/ui-languages.tsv')],capture_output=True,text=True)
print(call.stdout+call.stderr,end='');call.check_returncode()
files=[src/'NativeSurface.java',src/'NativeHud.java',*real,r/'app/src/main/assets/native/ui-languages.tsv',Path(__file__)]
(r/'validation/hover-errors11.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'scope':'Production feedback dispatch, original-font Canvas rendering and CommandHover input; status/tooltip bounds and pixel preservation','output':call.stdout.strip(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

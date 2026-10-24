#!/usr/bin/env python3
"""Exercise actual tooltip/font/hover code through a host Canvas with recorded glyph positions."""
from pathlib import Path
import ast,subprocess,json,hashlib,re,sys
r=Path(__file__).resolve().parents[1];b=r/'build-native/tooltip55';b.mkdir(parents=True,exist_ok=True);src=r/'app/src/main/java/org/openbw/androidtest'
old=ast.parse((r/'tests/run_results46.py').read_text());sources=next(ast.literal_eval(n.value)for n in old.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='sources'for t in n.targets));sources.pop('org/openbw/androidtest/Results46Harness.java')
sources['android/graphics/Paint.java']=sources['android/graphics/Paint.java'].replace('public int color=', 'public enum Style{FILL,STROKE}public Style style=Style.FILL;public void setStyle(Style s){style=s;}public void setStrokeWidth(float w){}public int color=')
sources['android/graphics/Canvas.java']=sources['android/graphics/Canvas.java'].replace('public void translate(float','public void scale(float x,float y){g.scale(x,y);}public void translate(float').replace('g.fill(new Rectangle2D.Float(l,t,r-l,b-t));','if(p.style==Paint.Style.STROKE)g.draw(new Rectangle2D.Float(l,t,r-l,b-t));else g.fill(new Rectangle2D.Float(l,t,r-l,b-t));')
s=(src/'NativeHud.java').read_text();start=s.index('  void tooltip(Canvas canvas, String text, int width, int supplyRace)');end=s.index('\n  RectF commandRect',start);method=s[start:end]
sources['org/openbw/androidtest/NativeHud.java']='''package org.openbw.androidtest;import android.graphics.*;import java.util.*;
final class NativeHud {float commandScale=1,descriptionScale=1;NativeArt.Font small;final Bitmap[]resources=new Bitmap[3],supplyIcons=new Bitmap[3];
 static final class Hit{RectF rect;String[]fields;int cancel=-1,selectUnit=-1,unload=-1;boolean more;String help;}
 static int number(String[]s,int i,int d){try{return Integer.parseInt(s[i]);}catch(Exception e){return d;}}
 static void image(Canvas c,Bitmap b,float x,float y){if(b!=null)c.drawBitmap(b,x,y,NativeArt.PIXELS);}
'''+method+'}\n'
sources['org/openbw/androidtest/Tooltip55Harness.java']='''package org.openbw.androidtest;import android.graphics.*;import java.util.*;import java.nio.file.*;import javax.imageio.ImageIO;
public class Tooltip55Harness{
 static int checks;static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
 static class Recording extends Canvas {final Set<Bitmap> glyphs;final TreeSet<Float>ys=new TreeSet<>();int height;float top,scale;boolean sawTranslate;
  Recording(Bitmap b,NativeArt.Font font){super(b);glyphs=new HashSet<>();for(int i=32;i<256;i++){Bitmap g=font.glyph(i,2);if(g!=null)glyphs.add(g);}}
  @Override public void translate(float x,float y){top=y;sawTranslate=true;super.translate(x,y);}
  @Override public void scale(float x,float y){scale=y;super.scale(x,y);}
  @Override public void drawRect(float l,float t,float rr,float bb,Paint p){if(l==0&&t==0)height=(int)bb;super.drawRect(l,t,rr,bb,p);}
  @Override public void drawBitmap(Bitmap b,float x,float y,Paint p){if(glyphs.contains(b)){check(x>=7&&x+b.getWidth()<=255,"Text extends past tooltip width");check(y>=7&&y+b.getHeight()<=height-3,"Text extends past tooltip height");ys.add(y);}super.drawBitmap(b,x,y,p);}
 }
 static NativeHud.Hit hit(float x,String label){NativeHud.Hit h=new NativeHud.Hit();h.rect=new RectF(x,380,x+40,420);h.fields=new String[]{"1",label,"1","0"};return h;}
 public static void main(String[]args)throws Exception{
  NativeBridge.root=Paths.get(args[0]);NativeArt art=new NativeArt();NativeArt.PCX tint=art.pcx("glue/paltv/tfont.pcx",false,-1),bg=art.pcx("glue/paltv/backgnd.pcx",false,-1);NativeHud hud=new NativeHud();hud.small=art.font("10",tint,bg.palette,0);
  for(int i=0;i<3;i++){hud.resources[i]=Bitmap.createBitmap(13,13,Bitmap.Config.ARGB_8888);Paint ink=new Paint();ink.setColor(0xff40bb88+i*0x00220000);new Canvas(hud.resources[i]).drawRect(0,0,13,13,ink);hud.supplyIcons[i]=hud.resources[i];}
  ArrayList<String> help=new ArrayList<>();help.add("Hive\\n200 minerals · 150 Vespene Gas\\nStructure. Receives gathered resources. Spawns larvae. Produces creep.\\nRequires Zerg Queen's Nest");help.add("Nuclear Strike\\n9999 minerals · 9999 Vespene Gas · 200 energy · 200 supply\\nSelect a target for a nuclear strike.\\nRequires a nuclear missile and a completed Nuclear Silo.");help.add("AnExtremelyLongUnbrokenUnitNameThatMustWrapCorrectly\\nA description with several explicit lines.\\nRequires AnExtremelyLongUnbrokenRequirementThatMustWrapCorrectly");
  help.addAll(Files.readAllLines(Paths.get(args[1])));int renders=0;
  for(String text:help)for(float scale:new float[]{1,1.25f,1.5f})for(float command:new float[]{1,1.5f})for(int width:new int[]{320,640,1000}){
   hud.descriptionScale=scale;hud.commandScale=command;Bitmap bitmap=Bitmap.createBitmap(width,480,Bitmap.Config.ARGB_8888);Recording c=new Recording(bitmap,hud.small);hud.tooltip(c,text,width,0);
   check(c.sawTranslate&&c.top>=7.9f&&c.height*c.scale<=346,"Tooltip leaves viewport");Float last=null;for(float y:c.ys){if(last!=null)check(y-last>=hud.small.height+3,"Tooltip lines overlap");last=y;}
   if(renders==6)ImageIO.write(bitmap.image,"png",Paths.get(args[2],"hive.png").toFile());renders++;
  }
  NativeHud.Hit a=hit(500,"Hive"),z=hit(545,"Drone");List<NativeHud.Hit>hits=Arrays.asList(a,z);CommandHover hover=new CommandHover();hover.hover(542,390,false);check(hover.tooltip(hits,0)==a,"Command gutter hover is missing");hover.hover(0,0,true);
  hover.begin(a,510,390,1000);check(hover.tooltip(hits,1219)==null&&hover.tooltip(hits,1220)==a,"Default hold response");check(hover.release(hits,510,390,1300)==null,"Inspection executes command");
  hover.begin(a,510,390,2000);hover.move(553,390,2030,10);check(hover.tooltip(hits,2030)==z,"Early slide lost tooltip");check(hover.release(hits,553,390,2040)==null,"Slide executes command");
  hover.begin(a,510,390,3000);check(hover.release(hits,510,390,3100)==a,"Quick tap failed");hover.holdMs=600;hover.begin(a,510,390,4000);check(hover.tooltip(hits,4599)==null&&hover.tooltip(hits,4600)==a,"Stored hold preference changed");hover.enabled=false;hover.begin(a,510,390,5000);check(hover.tooltip(hits,6000)==null&&hover.release(hits,510,390,6001)==a,"Disabled inspection blocks input");
  System.out.println("PASS "+checks+" checks; "+renders+" tooltip layouts across three widths and text sizes, two command sizes; Hive, long descriptions/requirements and responsive hover/hold/slide");
 }
}'''
# Collect all command description literals from the production engine, plus realistic compound forms.
engine=r/'native-engine/web/sandbox.h';text=engine.read_text();section=text[text.index('a_string command_description'):text.index('a_string command_description')+13000] if 'a_string command_description'in text else text[40000:75000]
helps=re.findall(r'return "([^"\\]*(?:\\.[^"\\]*)*)";',section);(b/'help.txt').write_text('\n'.join(helps)+'\n')
for name,text in sources.items():p=b/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
real=[src/'NativeArt.java',src/'CommandHover.java'];p=subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn','-d',str(b/'classes'),*[str(b/n)for n in sources],*map(str,real)],capture_output=True,text=True);print(p.stdout+p.stderr);p.check_returncode()
p=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes'),'org.openbw.androidtest.Tooltip55Harness',str(r/'build-native/assets55'),str(b/'help.txt'),str(b)],capture_output=True,text=True);print(p.stdout+p.stderr);p.check_returncode()
files=real+[src/'NativeHud.java',Path(__file__)];(r/'validation/tooltip-v55.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'descriptionFixtures':len(helps)+3,'output':p.stdout,'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

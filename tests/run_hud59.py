#!/usr/bin/env python3
"""Render actual HUD command/status methods and check stable positions with disappearing upgrades."""
from pathlib import Path
import ast,subprocess,json,hashlib,sys,re
r=Path(__file__).resolve().parents[1];b=r/'build-native/hud59';assets=b/'assets';b.mkdir(exist_ok=True)
src=r/'app/src/main/java/org/openbw/androidtest';data=Path(sys.argv[1])
extract=r/'build-native/ui58/extract-interface'
def get(name):
 p=assets/name;p.parent.mkdir(parents=True,exist_ok=True)
 for a in ['patch_rt.mpq','BROODAT.MPQ','STARDAT.MPQ']:
  if subprocess.run([str(extract),str(data/a),name,str(p)],capture_output=True).returncode==0:return
 raise RuntimeError('Missing '+name)
for race in 'ztp':
 for n in [f'game/{race}console.pcx',f'unit/cmdbtns/{race}cmdbtns.grp',f'rez/statbtn{race}.bin']:get(n)
for n in ['unit/cmdbtns/cmdicons.grp','unit/cmdbtns/ticon.pcx','game/tfontgam.pcx','rez/stat_txt.tbl']:get(n)
for size in ['8','10','16']:get('font/font'+size+'.fnt')
old=ast.parse((r/'tests/run_results46.py').read_text());sources=next(ast.literal_eval(n.value)for n in old.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='sources'for t in n.targets));sources.pop('org/openbw/androidtest/Results46Harness.java')
sources['android/graphics/RectF.java']=sources['android/graphics/RectF.java'].replace('public float width()', 'public void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}public float width()')
sources['android/graphics/Paint.java']=sources['android/graphics/Paint.java'].replace('public int color=', 'public enum Style{FILL,STROKE}public Style style=Style.FILL;public void setStyle(Style s){style=s;}public void setStrokeWidth(float w){}public int color=')
sources['android/graphics/Canvas.java']=sources['android/graphics/Canvas.java'].replace('public void translate(float','public void scale(float x,float y){g.scale(x,y);}public void translate(float')
sources['org/openbw/androidtest/NativeBridge.java']=sources['org/openbw/androidtest/NativeBridge.java'].replace('static int value(', 'static int value(')
if 'int value(' not in sources['org/openbw/androidtest/NativeBridge.java']:
 sources['org/openbw/androidtest/NativeBridge.java']=re.sub(r'(class NativeBridge\s*\{)',r'\1static int value(int a,int b){return 0;}',sources['org/openbw/androidtest/NativeBridge.java'])
text=(src/'NativeHud.java').read_text()
def method(name):
 import re
 m=re.search(r'^  (?:static )?(?:void|int|Bitmap|String|RectF) '+name+r'\(',text,re.M);start=m.start();pos=text.index('{',m.end());level=1;end=pos+1
 while level:
  if text[end]=='{':level+=1
  elif text[end]=='}':level-=1
  end+=1
 return text[start:end]
methods='\n'.join(method(n)for n in ['drawCommands','drawUnitStatus','commandRect','map','number','image','frame','icon','string'])
sources['org/openbw/androidtest/NativeHud.java']='''package org.openbw.androidtest;import android.graphics.*;import java.util.*;import org.json.*;
class NativeHud {
 int race,page;float commandScale=1;String previous="";RectF pressedCommand;
 NativeArt.Font small,tiny;NativeArt.Dialog commandLayout;NativeArt.PCX tint,console;int[]palette;
 byte[]commandGrp,framesGrp;String[]names;JSONObject maps;
 Map<Integer,Bitmap>frames=new HashMap<>();Map<String,Bitmap>icons=new HashMap<>();List<Hit>hits=new ArrayList<>();
 static class Hit {RectF rect;String[]fields;String help;boolean more;}
 NativeHud(NativeArt art,int race,JSONObject maps){this.race=race;this.maps=maps;String letter=new String[]{"z","t","p"}[race];console=art.pcx("game/"+letter+"console.pcx",true,-1);palette=console.palette;NativeArt.PCX colors=art.pcx("game/tfontgam.pcx",false,-1);small=art.font("10",colors,palette,0);tiny=art.font("8",colors,palette,0);tint=art.pcx("unit/cmdbtns/ticon.pcx",false,-1);commandGrp=art.read("unit/cmdbtns/cmdicons.grp");framesGrp=art.read("unit/cmdbtns/"+letter+"cmdbtns.grp");commandLayout=new NativeArt.Dialog(art.read("rez/statbtn"+letter+".bin"));names=NativeArt.tbl(art.read("rez/stat_txt.tbl"));}
'''+methods+'}\n'
sources['org/openbw/androidtest/Hud59Harness.java']='''package org.openbw.androidtest;import android.graphics.*;import java.util.*;import java.nio.file.*;import javax.imageio.ImageIO;import org.json.*;
public class Hud59Harness {
 static int checks;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static String command(int type,int up,String name){return "x\\t"+name+"\\t1\\t"+type+"\\t0\\t0\\t\\t\\t\\t0\\t"+(type<0?0:type)+"\\t"+up+"\\t-1";}
 static class Recording extends Canvas {int glyphs;boolean red;NativeHud hud;Set<Bitmap>text=new HashSet<>(),reds=new HashSet<>();
  Recording(Bitmap b,NativeHud h){super(b);hud=h;for(NativeArt.Font f:new NativeArt.Font[]{h.small,h.tiny})for(int i=32;i<256;i++)for(int color:new int[]{2,3,6}){Bitmap g=f.glyph(i,color);if(g!=null){text.add(g);if(color==6)reds.add(g);}}}
  public void drawBitmap(Bitmap b,float x,float y,Paint p){if(text.contains(b)){glyphs++;check(x>=239&&x+b.getWidth()<=393,"Status outside horizontal bounds");check(y>=402&&y+b.getHeight()<=417,"Status overlaps title or statistics");red|=reds.contains(b);}super.drawBitmap(b,x,y,p);}
 }
 public static void main(String[]args)throws Exception {
  NativeBridge.root=Paths.get(args[0]);JSONObject maps=new JSONObject(new String(Files.readAllBytes(Paths.get(args[1])),"UTF-8"));Path out=Paths.get(args[2]);NativeArt art=new NativeArt();
  int[][]heroes={{48,51,53,54,55,104},{16,19,20,23,28,99},{75,77,78,79,82,88}};
  int[][]upgrades={{10,11,3},{7,0},{13,5,15}};int[]buildings={139,122,166};
  for(int race=0;race<3;race++)for(int width:new int[]{640,1000})for(float scale:new float[]{1,1.5f}){
   NativeHud hud=new NativeHud(art,race,maps);hud.commandScale=scale;Map<Integer,RectF>base=new HashMap<>();
   for(int mask=0;mask<(1<<upgrades[race].length);mask++){
    List<String> lines=new ArrayList<>();lines.add("Hero producer");for(int h:heroes[race])lines.add(command(h,-1,"Hero "+h));
    for(int i=0;i<upgrades[race].length;i++)if((mask&(1<<i))!=0)lines.add(command(-1,upgrades[race][i],"Upgrade"));
    if(race==1)lines.add(command(-1,-1,"Lift Off"));
    Bitmap bitmap=Bitmap.createBitmap(width,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(bitmap);c.drawBitmap(hud.console.image,width-640,0,NativeArt.PIXELS);hud.hits.clear();hud.drawCommands(c,lines.toArray(new String[0]),buildings[race],"Hero producer",width);
    int count=0;for(NativeHud.Hit hit:hud.hits){check(!hit.more,"Hero card pages unexpectedly");int id=Integer.parseInt(hit.fields[3]);RectF a=hit.rect;check(a.left>=0&&a.top>=0&&a.right<=width&&a.bottom<=480,"Command outside screen");if(id<0)continue;count++;if(mask==0)base.put(id,a);else {RectF z=base.get(id);check(a.left==z.left&&a.top==z.top,"Hero moved when an upgrade disappeared");}}
    check(count==6,"Hero icon missing");for(int i=0;i<hud.hits.size();i++)for(int j=i+1;j<hud.hits.size();j++){RectF a=hud.hits.get(i).rect,z=hud.hits.get(j).rect;check(!(a.left<z.right&&z.left<a.right&&a.top<z.bottom&&z.top<a.bottom),"Command collision");}
    if(width==640&&scale==1&&(mask==0||mask==(1<<upgrades[race].length)-1))ImageIO.write(bitmap.image,"png",out.resolve("commands-"+race+"-"+mask+".png").toFile());
   }
  }
  for(int race=0;race<3;race++)for(String status:new String[]{"","Locked Down","Stasis","Maelstrom","Matrix · Irradiated · Locked Down · Blind · Parasited","\\u0006Unpowered"})for(boolean detector:new boolean[]{false,true}){
   NativeHud hud=new NativeHud(art,race,maps);Bitmap bitmap=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas bg=new Canvas(bitmap);bg.drawBitmap(hud.console.image,0,0,NativeArt.PIXELS);hud.small.draw(bg,"Science Vessel",240,388,152,1,2,0);hud.small.draw(bg,"Kills: 0",240,418,152,1,2,0);Recording c=new Recording(bitmap,hud);hud.drawUnitStatus(c,status,detector,240);
   if(!status.isEmpty()||detector){check(c.glyphs>0&&hud.hits.size()==1,"Status missing");check(hud.hits.get(0).help.contains(NativeArt.clean(status)),"Full effects missing from tooltip");if(detector)check(hud.hits.get(0).help.contains("Detector"),"Detector missing from status tooltip");}
   if(status.startsWith("\\u0006"))check(c.red,"Unpowered original red color lost");
   if(status.equals("Locked Down")&&detector)ImageIO.write(bitmap.image,"png",out.resolve("lockdown-detector-"+race+".png").toFile());
  }
  System.out.println("PASS "+checks+" checks: fixed six-hero command positions across every upgrade combination, two widths/scales; bounded status/detector row, full inspection text, original red Unpowered");
 }
}'''
for name,text in sources.items():p=b/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
real=[src/'NativeArt.java',src/'CommandSlots.java'];jar=r/'build-native/json-20240303.jar'
p=subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn','-classpath',str(jar),'-d',str(b/'classes'),*[str(b/n)for n in sources],*map(str,real)],capture_output=True,text=True);print(p.stdout+p.stderr);p.check_returncode()
p=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.Hud59Harness',str(assets),str(r/'app/src/main/assets/native/commands.json'),str(b)],capture_output=True,text=True);print(p.stdout+p.stderr);p.check_returncode()
files=real+[src/'NativeHud.java',r/'app/src/main/assets/native/commands.json',Path(__file__)]
(r/'validation/hud-v59.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'output':p.stdout,'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

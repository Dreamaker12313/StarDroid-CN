#!/usr/bin/env python3
"""Check placement geometry, persisted settings and actual confirmation callbacks; render HUD controls."""
from pathlib import Path
import ast, hashlib, json, re, subprocess, sys

r = Path(__file__).resolve().parents[1]
b = r / 'build-native/placement60'
assets = b / 'assets'
src = r / 'app/src/main/java/org/openbw/androidtest'
data = Path(sys.argv[1])
b.mkdir(parents=True, exist_ok=True)
extract = r / 'build-native/ui58/extract-interface'

def get(name):
    p = assets / name
    p.parent.mkdir(parents=True, exist_ok=True)
    for archive in ['patch_rt.mpq', 'BROODAT.MPQ', 'STARDAT.MPQ']:
        if subprocess.run([str(extract), str(data/archive), name, str(p)], capture_output=True).returncode == 0:
            return
    raise RuntimeError('Missing ' + name)

for race, name in zip('ztp', ['zerg', 'terran', 'protoss']):
    get('game/' + race + 'console.pcx')
    get('dlgs/' + name + '.grp')
for name in ['game/tfontgam.pcx', 'font/font10.fnt', 'font/font16.fnt']:
    get(name)

old = ast.parse((r/'tests/run_results46.py').read_text())
sources = next(ast.literal_eval(n.value) for n in old.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == 'sources' for t in n.targets))
sources.pop('org/openbw/androidtest/Results46Harness.java')
sources['android/graphics/Paint.java'] = sources['android/graphics/Paint.java'].replace('public int color=',
    'public enum Style{FILL,STROKE}public Style style=Style.FILL;public float stroke=1;'
    'public void setStyle(Style s){style=s;}public void setStrokeWidth(float w){stroke=w;}public int color=')
sources['android/graphics/Canvas.java'] = sources['android/graphics/Canvas.java'].replace('public void drawRect(',
    'private void shape(Shape s,Paint p){g.setColor(new java.awt.Color(p.color,true));'
    'g.setStroke(new BasicStroke(p.stroke));if(p.style==Paint.Style.STROKE)g.draw(s);else g.fill(s);}'
    'public void drawLine(float x,float y,float x2,float y2,Paint p){g.setColor(new java.awt.Color(p.color,true));'
    'g.setStroke(new BasicStroke(p.stroke));g.draw(new Line2D.Float(x,y,x2,y2));}'
    'public void drawRoundRect(RectF r,float rx,float ry,Paint p){shape(new RoundRectangle2D.Float(r.left,r.top,r.width(),r.height(),rx*2,ry*2),p);}'
    'public void drawRect(').replace('g.fill(new Rectangle2D.Float(l,t,r-l,b-t));',
    'shape(new Rectangle2D.Float(l,t,r-l,b-t),p);')
sources['android/content/SharedPreferences.java'] = '''package android.content;
public interface SharedPreferences {String getString(String key,String fallback);Editor edit();
 interface Editor {Editor putString(String key,String value);void apply();}}'''
sources['org/openbw/androidtest/NativeBridge.java'] = sources['org/openbw/androidtest/NativeBridge.java'].replace(
    'static Path root;', 'static Path root;static java.util.List<int[]>calls=new java.util.ArrayList<>();'
    'static void command(int a,int b,int c,int d,int e){calls.add(new int[]{a,b,c,d,e});}')

def method(file, name):
    text = (src/file).read_text()
    match = re.search(r'^  (?:private )?(?:void|Bitmap) ' + name + r'\(', text, re.M)
    assert match, name
    end = text.index('{', match.end()) + 1
    level = 1
    while level:
        if text[end] == '{': level += 1
        elif text[end] == '}': level -= 1
        end += 1
    return text[match.start():end]

sources['org/openbw/androidtest/NativeHud.java'] = '''package org.openbw.androidtest;
import android.graphics.*;import java.util.*;
class NativeHud {
 NativeArt.Font small,large;NativeArt.PCX console;int[]palette;byte[]dialogGrp;
 Map<String,Bitmap>panels=new HashMap<>();List<Hit>hits=new ArrayList<>();
 RectF minimap=new RectF(0,338,136,480);
 static class Hit {RectF rect;Hit(RectF r){rect=r;}}
 NativeHud(NativeArt art,int race){String letter=new String[]{"z","t","p"}[race];
  console=art.pcx("game/"+letter+"console.pcx",true,-1);palette=console.palette;
  NativeArt.PCX colors=art.pcx("game/tfontgam.pcx",false,-1);
  small=art.font("10",colors,palette,0);large=art.font("16",colors,palette,0);
  dialogGrp=art.read("dlgs/"+new String[]{"zerg","terran","protoss"}[race]+".grp");}
''' + method('NativeHud.java', 'panel') + '}\n'
sources['org/openbw/androidtest/NativeGlue.java'] = '''package org.openbw.androidtest;
import android.graphics.*;class NativeGlue {Bitmap panel(int w,int h,boolean b){throw new AssertionError();}}'''

methods = '\n'.join(method('NativeSurface.java', name) for name in [
    'drawPlacementButtons', 'placeBuilding', 'aim', 'drawControls', 'controlOption', 'changeControls',
    'button', 'add', 'option', 'toggle', 'panel'])
sources['org/openbw/androidtest/Placement60Harness.java'] = '''package org.openbw.androidtest;
import android.graphics.*;import android.content.*;import java.util.*;import java.nio.file.*;import javax.imageio.ImageIO;
public class Placement60Harness {
 static int checks,positions;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static boolean overlaps(RectF a,RectF b){return a.left<b.right&&b.left<a.right&&a.top<b.bottom&&b.top<a.bottom;}
 static class Prefs implements SharedPreferences,SharedPreferences.Editor {
  Map<String,String>map=new HashMap<>();public String getString(String k,String v){return map.getOrDefault(k,v);}
  public Editor edit(){return this;}public Editor putString(String k,String v){map.put(k,v);return this;}public void apply(){}
 }
 static class Button {RectF rect;Runnable action;boolean enabled;Button(RectF r,Runnable a,boolean e){rect=r;action=a;enabled=e;}}
 ControlSettings controls=new ControlSettings();Prefs prefs=new Prefs();NativeHud hud;NativeGlue glue;
 List<Button>buttons=new ArrayList<>();Button pressed;Paint paint=new Paint();String page="game",modal="";
 int logicalWidth=640,placeX,placeY;float zoom=1,scale=1;boolean placement;
 Placement60Harness(NativeArt art,int race){hud=new NativeHud(art,race);}
 float physicalScale(){return scale;}void applyControls(){controls.save(prefs);}NativeArt.Font font(){return hud.large;}
 void text(Canvas c,String s,float x,float y,int w,int align,int color){font().draw(c,s,x,y,w,align,color,0);}
 void setup(int width,int side,float size){logicalWidth=width;buttons.clear();hud.hits.clear();
  float x=side==1?8:width-size-8;
  add(new RectF(x,218,x+size,218+size),()->{},true);
  add(new RectF(x,202-size,x+size,202),()->{},true);
  add(new RectF(8,8,width-8,38),()->{},true);
  add(new RectF(width-212,376,width,480),()->{},true);
  hud.hits.add(new NativeHud.Hit(new RectF(width-188,310,width,480)));
 }
 List<RectF>obstacles(){List<RectF>a=new ArrayList<>();a.add(hud.minimap);for(Button bt:buttons)a.add(bt.rect);for(NativeHud.Hit h:hud.hits)a.add(h.rect);return a;}
 void renderControls(Canvas c){modal="control-orders";float x=(logicalWidth-368)/2f,y=32;
  panel(c,x,y,368,330);text(c,"Command Settings",x+16,y+8,336,1,3);drawControls(c,x,y);
  button(c,"Previous",x+72,y+290,224,28,()->{},true);}
''' + methods + '''
 public static void main(String[]args)throws Exception {
  NativeBridge.root=Paths.get(args[0]);Path out=Paths.get(args[1]);NativeArt art=new NativeArt();
  for(String preset:new String[]{"Comfortable","Precise","Drag to select"}){ControlSettings s=new ControlSettings();s.preset(preset);check(s.placementButtonsFollow,"Preset default off");}
  Prefs old=new Prefs();old.putString("touch-controls","{\\"version\\":2,\\"preset\\":\\"Custom\\",\\"radius\\":8,\\"confirmBuild\\":false,\\"groundOrders\\":false,\\"placementOffset\\":80}");
  ControlSettings migrated=new ControlSettings();migrated.load(old);check(migrated.placementButtonsFollow,"Migration default off");
  check(migrated.radius==8&&!migrated.confirmBuild&&!migrated.groundOrders&&migrated.placementOffset==80,"Migration overwrote preferences");
  for(int race=0;race<3;race++){
   Placement60Harness h=new Placement60Harness(art,race);Bitmap settings=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas sc=new Canvas(settings);
   sc.drawBitmap(h.hud.console.image,0,0,NativeArt.PIXELS);h.renderControls(sc);check(h.buttons.size()==9,"Command settings missing row");
   for(int i=0;i<h.buttons.size();i++){RectF a=h.buttons.get(i).rect;check(a.left>=136&&a.right<=504&&a.top>=64&&a.bottom<=362,"Settings hit out of panel");
    for(int j=i+1;j<h.buttons.size();j++)check(!overlaps(a,h.buttons.get(j).rect),"Settings rows overlap");}
   check(h.hud.small.lines("Build buttons follow placement",296).size()==1,"Setting label wraps");
   h.buttons.get(5).action.run();check(!h.controls.placementButtonsFollow&&h.controls.preset.equals("Custom"),"Toggle not applied");
   ControlSettings restored=new ControlSettings();restored.load(h.prefs);check(!restored.placementButtonsFollow&&restored.confirmBuild,"Toggle persistence or confirmation changed");
   h.buttons.get(5).action.run();restored.load(h.prefs);check(restored.placementButtonsFollow,"Re-enable persistence");
   ImageIO.write(settings.image,"png",out.resolve("settings-"+race+".png").toFile());
   for(int sample=0;sample<4;sample++){
    h.zoom=sample==3?2:1;h.scale=1.5f;h.controls.placementOffset=48;h.setup(640,sample==2?2:1,66);
    float px=new float[]{310,52,607,330}[sample],py=new float[]{185,168,290,210}[sample];h.aim(px,py);
    check(h.placeX==Math.round(px/h.zoom)&&h.placeY==Math.round((py-32)/h.zoom),"Placement coordinate conversion");
    List<RectF>blocked=h.obstacles();Bitmap frame=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(frame);
    h.paint.setColor(0xff172522);c.drawRect(0,0,640,376,h.paint);c.drawBitmap(h.hud.console.image,0,0,NativeArt.PIXELS);
    h.paint.setStyle(Paint.Style.STROKE);h.paint.setColor(0xff64cf55);float ax=h.placeX*h.zoom,ay=h.placeY*h.zoom;
    c.drawRect(ax-48*h.zoom,ay-32*h.zoom,ax+48*h.zoom,ay+32*h.zoom,h.paint);h.paint.setStyle(Paint.Style.FILL);
    for(int i=0;i<2;i++){RectF a=h.buttons.get(i).rect;c.drawBitmap(h.hud.panel((int)a.width(),(int)a.height(),true,true),a.left,a.top,NativeArt.PIXELS);}
    h.drawPlacementButtons(c);Button build=h.buttons.get(h.buttons.size()-2),cancel=h.buttons.get(h.buttons.size()-1);
    check(build.rect.right+6==cancel.rect.left&&!overlaps(build.rect,cancel.rect),"Confirmation pair overlaps");
    for(RectF obstacle:blocked){check(!overlaps(build.rect,obstacle)&&!overlaps(cancel.rect,obstacle),"Placement covers controls");}
    int x=h.placeX,y=h.placeY;NativeBridge.calls.clear();build.action.run();check(NativeBridge.calls.size()==3,"Build command count");
    check(Arrays.equals(NativeBridge.calls.get(0),new int[]{0,x,y,0,0})&&Arrays.equals(NativeBridge.calls.get(1),new int[]{1,1,1,x,y})&&Arrays.equals(NativeBridge.calls.get(2),new int[]{1,0,1,x,y}),"Build used button position instead of target");
    check(h.placeX==x&&h.placeY==y,"Confirmation moved placement");NativeBridge.calls.clear();cancel.action.run();
    check(!h.placement&&NativeBridge.calls.size()==1&&Arrays.equals(NativeBridge.calls.get(0),new int[]{2,27,41,0,0}),"Cancel failed");
    ImageIO.write(frame.image,"png",out.resolve("placement-"+race+"-"+sample+".png").toFile());
   }
   h.controls.placementButtonsFollow=false;
   for(int x:new int[]{30,320,610}){h.setup(640,1,44);h.aim(x,190);Bitmap f=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);h.drawPlacementButtons(new Canvas(f));
    RectF a=h.buttons.get(h.buttons.size()-2).rect;check(a.left==213&&a.top==268&&a.right==317&&a.bottom==296,"Fixed mode moved");}
  }
  Placement60Harness h=new Placement60Harness(art,1);
  for(int width:new int[]{640,1000,1280})for(float zoom:new float[]{.5f,1,2,3})for(int side:new int[]{1,2})for(float size:new float[]{44,66}){
   h.setup(width,side,size);List<RectF>blocked=h.obstacles();
   for(float x:new float[]{0,40,width/3f,width/2f,width-40,width})for(float y:new float[]{1,48,130,200,300,375}){
    RectF a=PlacementButtons.position(width,x,y,zoom,blocked);positions++;
    check(a.left>=8&&a.right<=width-8&&a.top>=48&&a.bottom<=336,"Confirmation outside safe area");
    for(RectF obstacle:blocked)check(!overlaps(a,obstacle),"Confirmation collides at screen edge/zoom");
   }
  }
  List<RectF>none=new ArrayList<>();RectF a=PlacementButtons.position(1000,300,170,1,none),b=PlacementButtons.position(1000,500,200,1,none);
  check(Math.abs(b.left-a.left-200)<.01&&Math.abs(b.top-a.top-30)<.01,"Buttons do not follow unobstructed preview");
  System.out.println("PASS "+checks+" checks, "+positions+" edge/zoom/side-control positions: migration, setting persistence, fixed fallback, placement coordinates, actual Build/Cancel callbacks and three-race renders");
 }
}'''

for name, text in sources.items():
    p = b/name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
real = [src/name for name in ['NativeArt.java', 'ControlSettings.java', 'PlacementButtons.java']]
jar = r/'build-native/json-20240303.jar'
p = subprocess.run(['java', '-jar', str(r/'.tools/ecj.jar'), '-source', '1.8', '-target', '1.8',
                    '-proc:none', '-nowarn', '-classpath', str(jar), '-d', str(b/'classes'),
                    *[str(b/n) for n in sources], *map(str, real)], capture_output=True, text=True)
print(p.stdout+p.stderr)
p.check_returncode()
p = subprocess.run(['java', '-Djava.awt.headless=true', '-cp', str(b/'classes')+':'+str(jar),
                    'org.openbw.androidtest.Placement60Harness', str(assets), str(b)], capture_output=True, text=True)
print(p.stdout+p.stderr)
p.check_returncode()
files = real+[src/'NativeSurface.java', src/'NativeHud.java', Path(__file__)]
(r/'validation/placement-v60.json').write_text(json.dumps({
    'passed': True, 'physicalAndroid': False,
    'canvas': 'AWT compatibility shim; real NativeArt, ControlSettings, PlacementButtons and extracted production Surface/HUD methods',
    'output': p.stdout.strip(), 'sourceSha256': {str(f.relative_to(r)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
}, indent=2)+'\n')

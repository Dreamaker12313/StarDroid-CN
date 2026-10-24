#!/usr/bin/env python3
"""Exercise production touch routing under overlapping placement controls and render the HUD."""
from pathlib import Path
import ast, hashlib, json, re, subprocess, sys

r = Path(__file__).resolve().parents[1]
b = r / 'build-native/scroll70'
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
sources['android/view/MotionEvent.java'] = '''package android.view;
public class MotionEvent {public static final int ACTION_DOWN=0,ACTION_UP=1,ACTION_MOVE=2,ACTION_CANCEL=3,ACTION_POINTER_DOWN=5;
 int action;public int pointers=1;float x,y;long time;public MotionEvent(int a,float x,float y,long t){action=a;this.x=x;this.y=y;time=t;}
 public int getActionMasked(){return action;}public float getX(){return x;}public float getY(){return y;}
 public float getX(int i){return x;}public float getY(int i){return y;}public long getEventTime(){return time;}public int getPointerCount(){return pointers;}}'''
sources['org/openbw/androidtest/NativeBridge.java'] = sources['org/openbw/androidtest/NativeBridge.java'].replace(
    'static Path root;', 'static Path root;static java.util.List<int[]>calls=new java.util.ArrayList<>();'
    'static void command(int a,int b,int c,int d,int e){calls.add(new int[]{a,b,c,d,e});}'
    'static int value(int a,int b){return 2;}static void frame(Bitmap b,int steps,double clock){}')

def method(file, name):
    text = (src/file).read_text()
    match = re.search(r'^  (?:private )?(?:void|Bitmap|boolean|float) ' + name + r'\(', text, re.M)
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
 static final int WORLD_BOTTOM=376;int page,race;
 NativeArt.Font small,large;NativeArt.PCX console;int[]palette;byte[]dialogGrp;
 Map<String,Bitmap>panels=new HashMap<>();List<Hit>hits=new ArrayList<>();
 RectF minimap=new RectF(0,338,136,480);
 static class Hit {RectF rect;int unload=-1,cancel=-1,selectUnit=-1;boolean more;String help;String[]fields;Hit(RectF r){rect=r;}}
 Hit hit(float x,float y){for(Hit h:hits)if(h.rect.contains(x,y))return h;return null;}
 String requirement(String[]f){return "";}static int number(String[]f,int i,int def){return def;}
 NativeHud(NativeArt art,int race){this.race=race;String letter=new String[]{"z","t","p"}[race];
  console=art.pcx("game/"+letter+"console.pcx",true,-1);palette=console.palette;
  NativeArt.PCX colors=art.pcx("game/tfontgam.pcx",false,-1);
  small=art.font("10",colors,palette,0);large=art.font("16",colors,palette,0);
  dialogGrp=art.read("dlgs/"+new String[]{"zerg","terran","protoss"}[race]+".grp");}
''' + method('NativeHud.java', 'panel') + '}\n'
sources['org/openbw/androidtest/NativeGlue.java'] = '''package org.openbw.androidtest;
import android.graphics.*;class NativeGlue {int hot;NativeArt.Dialog layout;Bitmap panel(int w,int h,boolean b){throw new AssertionError();}}'''

methods = '\n'.join(method('NativeSurface.java', name) for name in [
    'drawPlacementButtons', 'placementButtonAt', 'blockPlacementTouch', 'touch', 'cancelGesture',
    'placeBuilding', 'aim', 'cameraBottom', 'panCamera', 'advanceCamera', 'drawControls', 'controlOption', 'changeControls',
    'button', 'add', 'option', 'toggle', 'panel'])
sources['org/openbw/androidtest/Placement70Harness.java'] = '''package org.openbw.androidtest;
import android.graphics.*;import android.content.*;import android.view.*;import java.util.*;import java.nio.file.*;import javax.imageio.ImageIO;
public class Placement70Harness {
 static int checks,positions;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static boolean overlaps(RectF a,RectF b){return a.left<b.right&&b.left<a.right&&a.top<b.bottom&&b.top<a.bottom;}
 static class Prefs implements SharedPreferences,SharedPreferences.Editor {
  Map<String,String>map=new HashMap<>();public String getString(String k,String v){return map.getOrDefault(k,v);}
  public Editor edit(){return this;}public Editor putString(String k,String v){map.put(k,v);return this;}public void apply(){}
 }
 static class Button {RectF rect;Runnable action,longAction;boolean enabled,vertical,placementButton;java.util.function.Consumer<Float>slider;Button(RectF r,Runnable a,boolean e){rect=r;action=a;enabled=e;}}
 ControlSettings controls=new ControlSettings();Prefs prefs=new Prefs();NativeHud hud;NativeGlue glue;
 List<Button>buttons=new ArrayList<>();Button pressed;Paint paint=new Paint();String page="game",modal="";
 int logicalWidth=640,placeX,placeY,commandPercent=100;float zoom=1,scale=1;boolean placement;final CameraPan cameraPan=new CameraPan();
 RectF placementButtonRow;CommandHover commandHover=new CommandHover();
 String gesture="",scrollingList="",hint="";Object pendingScreen;boolean oneShotSelect,targeting,zoomOut=true,activeGame=true;
 long downAt,lastTapAt,listMoveTime;float downX,downY,lastX,lastY,lastTapX,lastTapY,pinchDistance,pinchZoom;
 float listVelocity,listStart,missionOffset,mapOffset,profileOffset,briefManual,briefScroll;double clock,briefManualUntil,hintUntil;
 int hoverButton,hintSupplyRace;RectF missionViewport=new RectF(0,0,0,0),mapViewport=missionViewport,profileViewport=missionViewport;
 Bitmap world;int miniCalls;
 Placement70Harness(NativeArt art,int race){hud=new NativeHud(art,race);}
 float lx(float x){return x;}float ly(float y){return y;}void resizeWorld(){}void saveSettings(){}void sfx(String s){}
 void updateHover(float x,float y,boolean leave){}float briefScrollLimit(NativeArt.Widget w){return 0;}void setListOffset(float v){}
 void mini(float x,float y,boolean right){miniCalls++;}
 float physicalScale(){return scale;}void applyControls(){controls.save(prefs);}NativeArt.Font font(){return hud.large;}
 void text(Canvas c,String s,float x,float y,int w,int align,int color){font().draw(c,s,x,y,w,align,color,0);}
 void setup(int width,int side,float size){logicalWidth=width;buttons.clear();hud.hits.clear();modal="";gesture="";pressed=null;placementButtonRow=null;commandHover.cancel();
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
 static void touchTests(NativeArt art,Path out)throws Exception {
  for(int race=0;race<3;race++)for(String layer:new String[]{"button","command","minimap"})for(int target=0;target<3;target++){
   Placement70Harness h=new Placement70Harness(art,race);h.controls.placementOffset=0;
   h.setup(640,1,66);h.aim(layer.equals("minimap")?50:layer.equals("command")?590:50,layer.equals("button")?150:300);
   RectF row=PlacementButtons.position(640,h.placeX,h.placeY,1);int[]activated={0};
   NativeHud.Hit under=new NativeHud.Hit(row);under.fields=new String[]{"m","Move","1","-1"};
   h.hud.minimap=layer.equals("minimap")?row:new RectF(0,338,136,480);
   Bitmap frame=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(frame);
   Runnable redraw=()->{
    h.buttons.clear();h.hud.hits.clear();
    c.drawBitmap(h.hud.console.image,0,0,NativeArt.PIXELS);
    if(layer.equals("button")){h.button(c,"Underlying control",row.left,row.top,row.width(),row.height(),()->activated[0]++,true);h.buttons.get(0).longAction=()->activated[0]++;}
    if(layer.equals("command"))h.hud.hits.add(under);
    h.drawPlacementButtons(c);
   };
   redraw.run();check(h.placementButtonAt(row.left+107,row.top+14),"Gap not protected");
   float x=target==0?row.left+20:target==1?row.right-20:row.left+107,y=row.top+14;
   NativeBridge.calls.clear();h.touch(new MotionEvent(MotionEvent.ACTION_DOWN,x,y,1000));
   check(h.gesture.equals("button")&&h.pressed!=null&&h.pressed.placementButton,"Overlay did not capture DOWN over "+layer);
   redraw.run(); // Redrawing replaces hit objects while the original press stays captured.
   h.touch(new MotionEvent(MotionEvent.ACTION_UP,x,y,1700));
   check(activated[0]==0&&h.miniCalls==0,"Tap reached underlying "+layer);
   check(NativeBridge.calls.size()==(target==0?3:target==1?1:0),"Wrong action through overlay/gap");
   if(target==0)check(Arrays.equals(NativeBridge.calls.get(1),new int[]{1,1,1,h.placeX,h.placeY}),"Build target changed on touch");
   if(target==1)check(!h.placement&&Arrays.equals(NativeBridge.calls.get(0),new int[]{2,27,41,0,0}),"Touch did not cancel");
   if(target==0)ImageIO.write(frame.image,"png",out.resolve("overlap-"+race+"-"+layer+".png").toFile());
  }
  for(String layer:new String[]{"button","command","minimap"})for(boolean move:new boolean[]{false,true}){
   Placement70Harness h=new Placement70Harness(art,1);h.controls.placementOffset=0;h.aim(320,180);
   RectF row=PlacementButtons.position(640,320,180,1),under=new RectF(row.left,row.top-24,row.right,row.bottom+24);
   int[]activated={0};h.hud.minimap=layer.equals("minimap")?under:new RectF(0,338,136,480);
   if(layer.equals("button"))h.add(under,()->activated[0]++,true);
   if(layer.equals("command")){NativeHud.Hit hit=new NativeHud.Hit(under);hit.fields=new String[]{"m","Move","1","-1"};h.hud.hits.add(hit);}
   Bitmap frame=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);h.drawPlacementButtons(new Canvas(frame));
   float x=row.left+20,y=row.top+8;
   h.touch(new MotionEvent(MotionEvent.ACTION_DOWN,x,row.top-10,1000));
   check(h.gesture.equals(layer.equals("minimap")?"mini":layer),"Underlying exposed control not reachable");
   NativeBridge.calls.clear();int before=h.miniCalls;
   if(move){h.touch(new MotionEvent(MotionEvent.ACTION_MOVE,x,y,1040));check(h.gesture.equals("placement-blocked"),"Covered drag not consumed");}
   h.touch(new MotionEvent(MotionEvent.ACTION_UP,x,move?row.top-10:y,1100));
   check(activated[0]==0&&h.miniCalls==before&&NativeBridge.calls.isEmpty(),"Release/drag activated covered "+layer);
   check(h.gesture.isEmpty(),"Blocked gesture did not end");
  }
  Placement70Harness h=new Placement70Harness(art,1);h.controls.placementOffset=0;h.aim(320,180);
  Bitmap frame=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);h.drawPlacementButtons(new Canvas(frame));
  h.touch(new MotionEvent(MotionEvent.ACTION_DOWN,320,120,1000));check(h.gesture.equals("place"),"Placement drag lost");
  NativeBridge.calls.clear();h.touch(new MotionEvent(MotionEvent.ACTION_MOVE,320,265,1050));
  h.touch(new MotionEvent(MotionEvent.ACTION_UP,320,265,1100));
  check(h.placeY==265&&NativeBridge.calls.size()==2&&NativeBridge.calls.get(0)[0]==0&&NativeBridge.calls.get(1)[0]==0,"Dragging through buttons confirmed/moved wrong target");
  h.buttons.clear();h.drawPlacementButtons(new Canvas(frame));RectF row=h.placementButtonRow;
  h.touch(new MotionEvent(MotionEvent.ACTION_DOWN,row.left+20,row.top+14,2000));
  h.touch(new MotionEvent(MotionEvent.ACTION_CANCEL,row.left+20,row.top+14,2010));
  check(!h.placement&&h.gesture.isEmpty()&&!h.placementButtonAt(row.left+20,row.top+14),"Cancelled overlay still captures input");
  h.buttons.clear();int[]pressed={0};h.add(row,()->pressed[0]++,true);
  h.touch(new MotionEvent(MotionEvent.ACTION_DOWN,row.left+20,row.top+14,2100));
  h.touch(new MotionEvent(MotionEvent.ACTION_UP,row.left+20,row.top+14,2150));
  check(pressed[0]==1,"Underlying controls stayed disabled after placement");
  h.buttons.clear();h.aim(320,180);h.drawPlacementButtons(new Canvas(frame));row=h.placementButtonRow;
  h.touch(new MotionEvent(MotionEvent.ACTION_DOWN,row.left+20,row.top+14,2200));
  h.placement=false;h.placementButtonRow=null;NativeBridge.calls.clear();
  h.touch(new MotionEvent(MotionEvent.ACTION_UP,row.left+20,row.top+14,2250));
  check(NativeBridge.calls.isEmpty(),"Disappearing placement confirmed a stale target");
 }


 static void placementSettingTests(NativeArt art,Path out)throws Exception {
  ControlSettings fresh=new ControlSettings();check(fresh.placementScroll,"New install disabled placement scrolling");
  Prefs prefs=new Prefs();prefs.putString("touch-controls","{\\"version\\":2,\\"radius\\":8,\\"confirmBuild\\":false,\\"groundOrders\\":false,\\"placementOffset\\":80}");
  ControlSettings old=new ControlSettings();old.load(prefs);
  check(old.placementScroll&&old.radius==8&&!old.confirmBuild&&!old.groundOrders&&old.placementOffset==80,"Migration changed other controls or disabled scrolling");
  old.placementScroll=false;old.save(prefs);ControlSettings loaded=new ControlSettings();loaded.load(prefs);
  check(!loaded.placementScroll&&loaded.radius==8&&!loaded.confirmBuild&&loaded.placementOffset==80,"Off setting did not persist");
  old.placementScroll=true;old.save(prefs);loaded.load(prefs);check(loaded.placementScroll,"On setting did not persist");
  for(int race=0;race<3;race++){
   Placement70Harness h=new Placement70Harness(art,race);Bitmap frame=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(frame);
   c.drawBitmap(h.hud.console.image,0,0,NativeArt.PIXELS);h.modal="control-camera";h.panel(c,136,32,368,330);h.text(c,"Camera Settings",152,40,336,1,3);
   h.drawControls(c,136,32);h.button(c,"Previous",208,322,224,28,()->{},true);
   check(h.buttons.size()==8,"Camera settings missing a control");
   for(int i=0;i<h.buttons.size();i++){RectF a=h.buttons.get(i).rect;check(a.left>=136&&a.right<=504&&a.top>=64&&a.bottom<=362,"Camera control outside panel");
    for(int j=i+1;j<h.buttons.size();j++)check(!overlaps(a,h.buttons.get(j).rect),"Camera controls overlap");}
   check(h.hud.small.lines("Scroll while placing",296).size()==1,"New setting label wraps");
   h.buttons.get(4).action.run();check(!h.controls.placementScroll&&h.controls.preset.equals("Custom"),"Setting button did not disable scrolling");
   ControlSettings restored=new ControlSettings();restored.load(h.prefs);check(!restored.placementScroll,"Setting button did not save preference");
   ImageIO.write(frame.image,"png",out.resolve("camera-settings-"+race+".png").toFile());
   h.modal="";h.placement=true;h.gesture="place";h.lastX=0;h.lastY=0;
   NativeBridge.calls.clear();for(int i=0;i<60;i++)h.advanceCamera(1000./60);check(NativeBridge.calls.isEmpty()&&h.placement,"Off setting scrolled or dismissed placement");
   h.controls.placementScroll=true;for(int i=0;i<60;i++)h.advanceCamera(1000./60);check(panTotal(1)<0&&panTotal(2)<0,"Re-enabling did not restore scrolling");
   h.controls.placementScroll=false;NativeBridge.calls.clear();h.advanceCamera(16);check(NativeBridge.calls.isEmpty(),"Disabling retained scroll momentum");
   for(String mode:new String[]{"box","aim"}){h.gesture=mode;NativeBridge.calls.clear();for(int i=0;i<30;i++)h.advanceCamera(1000./60);check(panTotal(1)<0&&panTotal(2)<0,"Setting disabled selection/target scrolling");}
   h.cameraPan.reset();NativeBridge.calls.clear();h.panCamera(12,-8);check(panTotal(1)==12&&panTotal(2)==-8,"Setting disabled ordinary camera drag");
   h.gesture="place";h.aim(320,470);int px=h.placeX,py=h.placeY;NativeBridge.calls.clear();h.placeBuilding();
   check(Arrays.equals(NativeBridge.calls.get(1),new int[]{1,1,1,px,py}),"Off setting changed Build target");
  }
 }
 static int panTotal(int axis){int sum=0;for(int[]c:NativeBridge.calls)if(c[0]==3)sum+=c[axis];return sum;}
 static void scrollTests(NativeArt art)throws Exception {
  for(float z:new float[]{.5f,1,1.4f,3})for(int width:new int[]{640,1000,1600})for(int scale:new int[]{75,100,150})for(boolean follow:new boolean[]{false,true}){
   Placement70Harness h=new Placement70Harness(art,1);h.setup(width,1,44);h.zoom=z;h.commandPercent=scale;h.controls.placementButtonsFollow=follow;
   h.controls.placementOffset=48;h.scale=3;float x=width-12;
   h.touch(new MotionEvent(MotionEvent.ACTION_DOWN,width/2,200,1000));
   check(h.gesture.equals("place"),"Placement drag was not captured");
   h.touch(new MotionEvent(MotionEvent.ACTION_MOVE,x,470,1100));
   check(h.placeY*z<h.cameraBottom(x)&&h.placeX>=0&&h.placeX<Math.round(width/z),"Preview left visible target bounds");
   NativeBridge.calls.clear();for(int i=0;i<120;i++)h.advanceCamera(1000./120);
   check(panTotal(2)>0&&panTotal(1)>0,"Held placement below command bar did not scroll diagonally");
   check(h.miniCalls==0,"Placement drag reached underlying HUD");
   for(int[]call:NativeBridge.calls)check(call[0]==3,"Scrolling activated a game command");
   h.touch(new MotionEvent(MotionEvent.ACTION_UP,x,470,2200));NativeBridge.calls.clear();h.advanceCamera(16);
   check(NativeBridge.calls.isEmpty()&&h.placement,"Finger release kept scrolling or dismissed confirmation");
   int px=h.placeX,py=h.placeY;h.placeBuilding();check(Arrays.equals(NativeBridge.calls.get(1),new int[]{1,1,1,px,py}),"Build changed the preview target");
   h.gesture="place";NativeBridge.calls.clear();h.modal="menu";h.advanceCamera(16);check(NativeBridge.calls.isEmpty(),"Paused menu kept scrolling");
   h.modal="";h.pendingScreen=new Object();h.advanceCamera(16);check(NativeBridge.calls.isEmpty(),"Screen transition kept scrolling");h.pendingScreen=null;
   h.cancelGesture();NativeBridge.calls.clear();h.advanceCamera(16);check(NativeBridge.calls.isEmpty(),"Cancel retained scroll velocity");
  }
  Placement70Harness h=new Placement70Harness(art,1);h.setup(640,1,44);h.controls.placementOffset=96;
  h.touch(new MotionEvent(MotionEvent.ACTION_DOWN,320,200,1000));h.touch(new MotionEvent(MotionEvent.ACTION_MOVE,-30,180,1100));
  NativeBridge.calls.clear();for(int i=0;i<60;i++)h.advanceCamera(1000./60);
  check(panTotal(1)<0&&h.placeX==0,"Left overshoot stalls or sends negative preview coordinate");
  h.touch(new MotionEvent(MotionEvent.ACTION_MOVE,320,180,2200));NativeBridge.calls.clear();h.advanceCamera(16);
  check(NativeBridge.calls.isEmpty(),"Leaving edge continues scrolling");
  h.touch(new MotionEvent(MotionEvent.ACTION_MOVE,320,470,2300));h.touch(new MotionEvent(MotionEvent.ACTION_CANCEL,320,470,2310));
  NativeBridge.calls.clear();h.advanceCamera(16);check(NativeBridge.calls.isEmpty(),"Android CANCEL kept scrolling");
  h.touch(new MotionEvent(MotionEvent.ACTION_DOWN,320,200,2400));MotionEvent second=new MotionEvent(MotionEvent.ACTION_POINTER_DOWN,320,470,2450);second.pointers=2;h.touch(second);
  NativeBridge.calls.clear();h.advanceCamera(16);check(NativeBridge.calls.isEmpty()&&h.gesture.equals("pinch"),"Pinch continued edge scrolling");
  for(String mode:new String[]{"box","aim"}){h.cancelGesture();h.gesture=mode;h.lastX=0;h.lastY=0;NativeBridge.calls.clear();for(int i=0;i<60;i++)h.advanceCamera(1000./60);check(panTotal(1)<0&&panTotal(2)<0,"Selection/target drag lost edge scrolling");}
 }

 public static void main(String[]args)throws Exception {
  NativeBridge.root=Paths.get(args[0]);Path out=Paths.get(args[1]);NativeArt art=new NativeArt();
  for(String preset:new String[]{"Comfortable","Precise","Drag to select"}){ControlSettings s=new ControlSettings();s.preset(preset);check(s.placementButtonsFollow,"Preset default off");}
  Prefs old=new Prefs();old.putString("touch-controls","{\\"version\\":2,\\"preset\\":\\"Custom\\",\\"radius\\":8,\\"confirmBuild\\":false,\\"groundOrders\\":false,\\"placementOffset\\":80}");
  ControlSettings migrated=new ControlSettings();migrated.load(old);check(migrated.placementButtonsFollow,"Migration default off");
  check(migrated.radius==8&&!migrated.confirmBuild&&!migrated.groundOrders&&migrated.placementOffset==80,"Migration overwrote preferences");
  for(int race=0;race<3;race++){
   Placement70Harness h=new Placement70Harness(art,race);Bitmap settings=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas sc=new Canvas(settings);
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
    check(build.rect.top>Math.min(NativeHud.WORLD_BOTTOM,h.placeY*h.zoom+64*h.zoom),"Placement row is not below preview");
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
  Placement70Harness h=new Placement70Harness(art,1);
  for(int width:new int[]{640,1000,1280})for(float zoom:new float[]{.5f,1,2,3})for(int side:new int[]{1,2})for(float size:new float[]{44,66}){
   h.setup(width,side,size);
   for(float x:new float[]{0,40,width/3f,width/2f,width-40,width})for(float y:new float[]{1,48,130,200,300,375}){
    RectF a=PlacementButtons.position(width,x,y,zoom);positions++;
    check(a.left>=8&&a.right<=width-8&&a.bottom<=480,"Confirmation outside screen");
    check(a.top>Math.min(NativeHud.WORLD_BOTTOM,y+64*zoom),"Row moved above preview to avoid HUD");
   }
  }
  RectF a=PlacementButtons.position(1000,300,170,1),b=PlacementButtons.position(1000,500,200,1);
  check(Math.abs(b.left-a.left-200)<.01&&Math.abs(b.top-a.top-30)<.01,"Buttons do not follow unobstructed preview");
  touchTests(art,out);scrollTests(art);placementSettingTests(art,out);
  System.out.println("PASS "+checks+" checks, "+positions+" edge/zoom/control positions: always below visible preview, overlap allowed, real touch routing blocks underlying buttons/commands/minimap and the gap, drag capture, migration/persistence and three-race renders");
 }
}'''

for name, text in sources.items():
    p = b/name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
real = [src/name for name in ['NativeArt.java', 'ControlSettings.java', 'PlacementButtons.java', 'CommandHover.java', 'CameraPan.java', 'CommandHint.java']]
real += [r/'tests/CameraPanTest.java']
jar = r/'build-native/json-20240303.jar'
p = subprocess.run(['java', '-jar', str(r/'.tools/ecj.jar'), '-source', '1.8', '-target', '1.8',
                    '-proc:none', '-nowarn', '-classpath', str(jar), '-d', str(b/'classes'),
                    *[str(b/n) for n in sources], *map(str, real)], capture_output=True, text=True)
print(p.stdout+p.stderr)
p.check_returncode()
timing = subprocess.run(['java', '-cp', str(b/'classes'), 'org.openbw.androidtest.CameraPanTest'], capture_output=True, text=True)
print(timing.stdout+timing.stderr);timing.check_returncode()
p = subprocess.run(['java', '-Djava.awt.headless=true', '-cp', str(b/'classes')+':'+str(jar),
                    'org.openbw.androidtest.Placement70Harness', str(assets), str(b)], capture_output=True, text=True)
print(p.stdout+p.stderr)
p.check_returncode()
files = real+[src/'NativeSurface.java', src/'NativeHud.java', Path(__file__)]
(r/'validation/placement-scroll-v1.0.json').write_text(json.dumps({
    'passed': True, 'physicalAndroid': False,
    'canvas': 'AWT compatibility shim; real NativeArt, ControlSettings, PlacementButtons and extracted production Surface/HUD methods',
    'version': '1.0', 'versionCode': 70, 'timing': timing.stdout.strip(), 'output': p.stdout.strip(), 'sourceSha256': {str(f.relative_to(r)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
}, indent=2)+'\n')

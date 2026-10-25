#!/usr/bin/env python3
"""Render the original map scrollbar and exercise production map/touch methods.

Usage: run_map_scroll79.py CORE_DIR [--extract PATH]
Caller-owned artwork remains in build-native. This uses an AWT Canvas shim,
not an Android device, and needs javac/java plus the prepared native MPQ extractor.
"""
from pathlib import Path
import argparse,ast,hashlib,json,re,subprocess
r=Path(__file__).resolve().parents[1];b=r/'build-native/map-scroll79';b.mkdir(parents=True,exist_ok=True)
src=r/'app/src/main/java/org/openbw/androidtest'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path)
p.add_argument('--extract',type=Path,default=r/'build-native/reign79/extract');a=p.parse_args()
assets=b/'assets'
names={'rez/glucustm.bin'}|{'glue/palnl/'+x for x in ['backgnd.pcx','tfont.pcx','teffect.pcx','dlg.grp','tile.grp']}
names|={prefix+'font'+size+'.fnt' for prefix in ['font/','files/font/'] for size in ['8','10','14','16','16x']}
def get(name):
 for slot,archive in [(0,'STARDAT.MPQ'),(1,'BROODAT.MPQ'),(2,'patch_rt.mpq')]:
  target=assets/str(slot)/name;target.parent.mkdir(parents=True,exist_ok=True)
  result=subprocess.run([str(a.extract),str(a.data/archive),name,str(target)],capture_output=True)
  if result.returncode:target.unlink(missing_ok=True)
for name in names:get(name)
more=set()
for binary in assets.rglob('*.bin'):
 more|={name.decode('cp1252').replace('\\','/').lower() for name in re.findall(rb'(?:glue|GLUE)[^\x00]*?\.[pP][cC][xX]',binary.read_bytes())}
for name in more-names:get(name)
# Reuse the project's established AWT shim, without running its unrelated tests.
old=ast.parse((r/'tests/run_menu_recovery.py').read_text())
active=False
for node in old.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tree' for t in node.targets):active=True
 if active:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.slice,ast.Constant) and t.slice.value=='org/openbw/androidtest/MenuRecoveryTest.java' for t in node.targets):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<canvas shim>','exec'))
sources['android/graphics/Canvas.java']=sources['android/graphics/Canvas.java'].replace('public void drawRect(',
 'public void drawCircle(float x,float y,float radius,Paint p){g.setColor(new java.awt.Color(p.color,true));g.fill(new Ellipse2D.Float(x-radius,y-radius,radius*2,radius*2));}public void clipRect(RectF r){clipRect(r.left,r.top,r.right,r.bottom);}public void drawRect(')
sources['android/view/MotionEvent.java']='''package android.view;public class MotionEvent {
 public static final int ACTION_DOWN=0,ACTION_UP=1,ACTION_MOVE=2,ACTION_CANCEL=3,ACTION_POINTER_DOWN=5;
 int action;float x,y;long time;public MotionEvent(int a,float x,float y,long t){action=a;this.x=x;this.y=y;time=t;}
 public int getActionMasked(){return action;}public float getX(){return x;}public float getY(){return y;}
 public float getX(int i){return x;}public float getY(int i){return y;}public long getEventTime(){return time;}public int getPointerCount(){return 1;}}'''
sources['org/openbw/androidtest/NativeBridge.java']=sources['org/openbw/androidtest/NativeBridge.java'].replace('static Path root;',
 'static Path root;static int commands;static void command(int a,int b,int c,int d,int e){commands++;}static int value(int a,int b){return 0;}static void frame(Bitmap b,int f,double clock){}')
sources['org/openbw/androidtest/NativeHud.java']='''package org.openbw.androidtest;import android.graphics.*;import java.util.*;class NativeHud {
 static final int WORLD_BOTTOM=376;int page,race;RectF minimap=new RectF(0,338,136,480);List<Hit>hits=new ArrayList<>();
 static class Hit{RectF rect;int unload=-1,cancel=-1,selectUnit=-1;boolean more;String help;String[]fields;}
 Hit hit(float x,float y){return null;}String requirement(String[]f){return "";}static int number(String[]f,int i,int d){return d;}}
'''
def method(name):
 text=(src/'NativeSurface.java').read_text();m=re.search(r'^  private (?:void|float) '+name+r'\(',text,re.M);assert m,name
 end=text.index('{',m.end())+1;depth=1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[m.start():end]
sources['org/openbw/androidtest/MapScroll79Test.java']='''package org.openbw.androidtest;
import android.graphics.*;import android.view.*;import java.util.*;import java.io.*;import java.nio.file.*;import javax.imageio.ImageIO;
public class MapScroll79Test {
 static int checks;static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static void near(float a,float b,String why){check(Math.abs(a-b)<.05f,why+" "+a+" vs "+b);}
 static class Button {RectF rect;Runnable action,longAction;boolean enabled,vertical,placementButton;java.util.function.Consumer<Float>slider;
 Button(RectF r,Runnable a,boolean e){rect=r;action=a;enabled=e;}}
 static class Activity{void runOnUiThread(Runnable r){r.run();}void pickNativeMap(){}}
 static class Controls{float pinchSpeed=1;boolean pinchZoom,confirmBuild,minimapOrders,doubleTap,holdSelect;long miniHoldMs=400,doubleTapMs=250,holdMs=450;
 float panFactor(){return 1;}String dragGesture(long t){return "pan";}}
 static class Hover{void cancel(){}void begin(NativeHud.Hit h,float x,float y,long t){}void move(float x,float y,long t,float d){}NativeHud.Hit release(List<NativeHud.Hit>h,float x,float y,long t){return null;}}
 static class Camera{void reset(){}}
 NativeGlue glue;NativeHud hud=new NativeHud();List<File>customMaps=new ArrayList<>();File customMap;float mapOffset,missionOffset,profileOffset;
 final RectF mapViewport=new RectF(60,130,328,240),missionViewport=new RectF(0,0,0,0),profileViewport=new RectF(0,0,0,0);
 List<String>profiles=new ArrayList<>();List<Button>buttons=new ArrayList<>();Button pressed;boolean importingMaps;
 Activity activity=new Activity();Controls controls=new Controls();Hover commandHover=new Hover();Camera cameraPan=new Camera();
 String gesture="",scrollingList="",page="custom",modal="",hint="";Object pendingScreen;
 float downX,lastX,downY,lastY,listStart,listVelocity,pinchDistance,pinchZoom,zoom=1,lastTapX,lastTapY,briefManual,briefScroll;
 long downAt,listMoveTime,lastTapAt;double clock,briefManualUntil,hintUntil;int hoverButton,hintSupplyRace;boolean oneShotSelect,placement,targeting,zoomOut,activeGame;Bitmap world;
 int selections,imports;
 MapScroll79Test(NativeGlue g){glue=g;}
 void selectCustomMap(File f){customMap=f;selections++;}
 void add(RectF r,Runnable action,boolean enabled){buttons.add(new Button(r,action,enabled));}
 void redButton(Canvas c,String s,float x,float y,float w,float h,Runnable action,boolean enabled){add(new RectF(x,y,x+w,y+h),()->imports++,enabled);}
 float lx(float x){return x;}float ly(float y){return y;}float physicalScale(){return 1;}
 void cancelGesture(){gesture="";pressed=null;listVelocity=0;}boolean blockPlacementTouch(int a,float x,float y){return false;}
 boolean placementButtonAt(float x,float y){return false;}void panCamera(float x,float y,float factor){}void panCamera(float x,float y){}
 void resizeWorld(){}void saveSettings(){}void updateHover(float x,float y,boolean l){}void sfx(String s){}
 void mini(float x,float y,boolean r){}void aim(float x,float y){}void placeBuilding(){}
 float briefScrollLimit(NativeArt.Widget w){return 0;}float missionMaxOffset(){return 0;}
'''+'\n'.join(method(n) for n in ['mapMaxOffset','drawMapBrowser','touch','setListOffset','advanceLists'])+'''
 Bitmap redraw(){buttons.clear();Bitmap result=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(result);
 glue.draw(c,1000);drawMapBrowser(c);return result;}
 void touch(int type,float x,float y,long time){touch(new MotionEvent(type,x,y,time));}
 void tap(float x,float y,long time){touch(0,x,y,time);touch(1,x,y,time+50);}
 void setup(int count){customMaps.clear();for(int i=0;i<count;i++)customMaps.add(new File(String.format(Locale.ROOT,"Map %05d.scx",i)));
 customMap=customMaps.isEmpty()?null:customMaps.get(0);mapOffset=0;selections=imports=0;cancelGesture();redraw();}
 public static void main(String[] args)throws Exception{
 NativeBridge.root=Paths.get(args[0]);Path out=Paths.get(args[1]);NativeArt art=new NativeArt();NativeGlue glue=new NativeGlue(art,"glucustm","palnl",false);
 MapScroll79Test h=new MapScroll79Test(glue);long now=1000;
 for(int count:new int[]{0,3,5,6,2001,10000}){
  h.setup(count);check(h.buttons.size()<=10,"List is not virtualized");
  h.tap(340,234,now+=100);near(h.mapOffset,Math.min(22,h.mapMaxOffset()),"Down arrow does not step one row");h.redraw();
  h.tap(340,136,now+=100);near(h.mapOffset,0,"Up arrow does not step one row");h.redraw();
  h.tap(340,185,now+=100);near(h.mapOffset,h.mapMaxOffset()/2,"Track tap must reach middle");
  for(float grip:new float[]{-8,0,8}){
   h.mapOffset=h.mapMaxOffset()*.4f;h.redraw();float y=153+.4f*64+grip,before=h.mapOffset;
   h.touch(0,340,y,now+=100);near(h.mapOffset,before,"Grabbing thumb jumps the list");
   h.redraw(); // Frame replacement must not reset the active grab offset.
   h.touch(2,340,y+10,now+20);near(h.mapOffset,Math.min(h.mapMaxOffset(),before+10*h.mapMaxOffset()/64),"Thumb drag distance mismatches rendering");
   h.touch(2,340,250,now+40);near(h.mapOffset,h.mapMaxOffset(),"Drag cannot reach final maps");
   h.touch(2,340,120,now+60);near(h.mapOffset,0,"Drag cannot reach first map");h.touch(1,340,120,now+80);
  }
  check(h.selections==0,"Scrolling selected a map");check(h.imports==0,"Scrollbar activated import");
  h.mapOffset=h.mapMaxOffset();h.redraw();if(count>0){h.tap(90,130+Math.min(count*22,110)-11,now+=100);check(h.customMap.equals(h.customMaps.get(count-1)),"Last map not selectable");}
 }
 h.setup(2001);h.touch(0,90,175,now+=100);h.touch(2,90,140,now+20);h.touch(1,90,140,now+30);
 near(h.mapOffset,35,"List swipe no longer scrolls");check(h.selections==0,"Swipe became map click");
 h.advanceLists(40);check(h.mapOffset>35,"List inertia stopped working");
 h.redraw();h.touch(0,340,185,now+=100);h.touch(3,340,185,now+20);float cancelled=h.mapOffset;
 h.touch(2,340,220,now+40);h.touch(1,340,220,now+50);near(h.mapOffset,cancelled,"Canceled slider still drags");
 check(NativeBridge.commands==0,"Map scrollbar issued a game command");
 for(float v:new float[]{0,.5f,1}){h.setup(2001);h.mapOffset=h.mapMaxOffset()*v;Bitmap image=h.redraw();
  ImageIO.write(image.image,"png",out.resolve("map-list-"+(int)(v*100)+".png").toFile());
  int y=Math.round(153+v*64);check((image.getPixel(340,y)&0xffffff)==0x475435,"Circular thumb is absent at its input position");}
 Bitmap arrows=glue.selectors.get("scroll:19");int visible=0,bright=0;
 for(int y=0;y<arrows.getHeight();y++)for(int x=0;x<arrows.getWidth();x++){int c=arrows.getPixel(x,y);if((c>>>24)!=0){visible++;if((c>>8&255)>=110)bright++;}}
 check(visible>10&&visible==bright,"Original arrow remains too dark");
 System.out.println("PASS "+checks+" map scrollbar checks: original bright arrows/circular thumb, 0–10000 maps, single-row arrows, jump/drag with stable grip through redraw, endpoints, last-map selection, swipe/inertia, cancel and no accidental actions");
 }
}
class NativeMaps{static String label(File f){return f==null?"Practice map":f.getName();}}
'''
for name,text in sources.items():
 target=b/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
real=[src/n for n in ['NativeArt.java','NativeGlue.java','NativeResults.java','CommandHint.java','MenuLabels.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
subprocess.run(['javac','-d',str(b/'classes'),*[str(b/n) for n in sources],*map(str,real)],check=True)
result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes'),'org.openbw.androidtest.MapScroll79Test',str(assets),str(b)],capture_output=True,text=True)
print(result.stdout+result.stderr,end='');result.check_returncode()
files=[src/'NativeGlue.java',src/'NativeSurface.java',Path(__file__)]
(r/'validation/map-scroll-v79.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'canvas':'AWT shim using original NativeArt/NativeGlue and production NativeSurface map browser/touch methods','result':result.stdout.strip(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},indent=2)+'\n')

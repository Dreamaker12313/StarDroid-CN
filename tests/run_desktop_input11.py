#!/usr/bin/env python3
"""Run production Android mouse/keyboard routing through deterministic host shims.

The Android event/value classes and engine boundary are bounded test doubles;
NativeSurface methods, DesktopControls, CommandHover and CameraPan are compiled
from production source. This does not emulate an Android device or native engine.
"""
from pathlib import Path
import hashlib,json,os,re,subprocess

r=Path(__file__).resolve().parents[1]
src=r/'app/src/main/java/org/openbw/androidtest'
b=r/'build-native/desktop-input11';b.mkdir(parents=True,exist_ok=True)
jdk=r/'.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64/bin'
if (jdk/'javac').is_file():os.environ['PATH']=str(jdk)+os.pathsep+os.environ['PATH']
sdk=r/'.tools/android-35/android.jar'

def constants(kind):
 text=subprocess.check_output(['javap','-constants','-cp',str(sdk),'android.view.'+kind],text=True)
 return '\n'.join('public static final int '+m.group(1)+'='+m.group(2)+';' for m in re.finditer(r'public static final int (\w+) = (-?\d+);',text))

def method(text,name):
 m=re.search(r'^  +(?:@Override )?(?:(?:public|private|protected|static|final|synchronized) )*(?:void|boolean|int|float|double) '+name+r'\(',text,re.M)
 assert m,'Production method missing: '+name
 end=text.index('{',m.end())+1;depth=1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[m.start():end]

sources={
 'android/graphics/RectF.java':'''package android.graphics;public class RectF{
 public float left,top,right,bottom;public RectF(){this(0,0,0,0);}public RectF(float l,float t,float r,float b){set(l,t,r,b);}public void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}public void set(RectF r){set(r.left,r.top,r.right,r.bottom);}public float width(){return right-left;}public float height(){return bottom-top;}public boolean contains(float x,float y){return x>=left&&x<right&&y>=top&&y<bottom;}public void offset(float x,float y){left+=x;right+=x;top+=y;bottom+=y;}}
''',
 'android/graphics/Rect.java':'''package android.graphics;public class Rect{
 public int left,top,right,bottom;public Rect(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}public int width(){return right-left;}public int height(){return bottom-top;}}
''',
 'android/graphics/Bitmap.java':'package android.graphics;public class Bitmap{}',
 'android/content/SharedPreferences.java':'''package android.content;public class SharedPreferences{public final java.util.Map<String,String>values=new java.util.HashMap<>();public String getString(String k,String d){return values.getOrDefault(k,d);}public Editor edit(){return new Editor();}public class Editor{public Editor putString(String k,String v){values.put(k,v);return this;}public void apply(){}}}''',
 'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long now;public static long uptimeMillis(){return now;}}',
 'android/view/InputDevice.java':'''package android.view;public class InputDevice{'''+constants('InputDevice')+'''
 public static final java.util.Map<Integer,InputDevice> devices=new java.util.HashMap<>();public int sources,keyboardType=KEYBOARD_TYPE_ALPHABETIC;public InputDevice(int s){sources=s;}public int getKeyboardType(){return keyboardType;}public int getSources(){return sources;}public static InputDevice getDevice(int id){return devices.get(id);}public MotionRange getMotionRange(int axis,int source){return new MotionRange();}public static class MotionRange{public float getFlat(){return .1f;}}}
''',
 'android/view/KeyEvent.java':'''package android.view;public class KeyEvent{'''+constants('KeyEvent')+'''
 public int key,action,repeat,source=InputDevice.SOURCE_KEYBOARD,device=1,unicode,meta;public KeyEvent(int a,int k){action=a;key=k;}public KeyEvent(KeyEvent e){key=e.key;action=e.action;repeat=e.repeat;source=e.source;device=e.device;unicode=e.unicode;meta=e.meta;}public int getKeyCode(){return key;}public int getAction(){return action;}public int getRepeatCount(){return repeat;}public int getSource(){return source;}public int getDeviceId(){return device;}public InputDevice getDevice(){return InputDevice.getDevice(device);}public int getUnicodeChar(){return unicode;}public int getUnicodeChar(int flags){return unicode;}public int getMetaState(){return meta;}public boolean isCtrlPressed(){return(meta&META_CTRL_ON)!=0;}public boolean isShiftPressed(){return(meta&META_SHIFT_ON)!=0;}public boolean isAltPressed(){return(meta&META_ALT_ON)!=0;}public static boolean isGamepadButton(int k){return k>=KEYCODE_BUTTON_A&&k<=KEYCODE_BUTTON_MODE||k>=KEYCODE_BUTTON_1&&k<=KEYCODE_BUTTON_16;}}
''',
 'android/view/MotionEvent.java':'''package android.view;public class MotionEvent{'''+constants('MotionEvent')+'''
 public int action,source=InputDevice.SOURCE_MOUSE,device=2,buttons,actionButton,meta,tool=TOOL_TYPE_MOUSE;public float x,y;public long time,downTime;public java.util.Map<Integer,Float>axes=new java.util.HashMap<>();
 public MotionEvent(int a,float x,float y,long time){action=a;this.x=x;this.y=y;this.time=time;downTime=time;}
 public static MotionEvent obtain(MotionEvent e){MotionEvent n=new MotionEvent(e.action,e.x,e.y,e.time);n.source=e.source;n.device=e.device;n.buttons=e.buttons;n.actionButton=e.actionButton;n.meta=e.meta;n.tool=e.tool;n.axes.putAll(e.axes);n.downTime=e.downTime;return n;}
 public static MotionEvent obtain(long start,long end,int action,float x,float y,int flags){MotionEvent e=new MotionEvent(action,x,y,end);e.downTime=start;e.source=InputDevice.SOURCE_TOUCHSCREEN;return e;}public void recycle(){}
 public int getToolType(int i){return tool;}public int getActionMasked(){return action;}public int getAction(){return action;}public float getX(){return x;}public float getY(){return y;}public float getX(int i){return x;}public float getY(int i){return y;}public long getEventTime(){return time;}public long getDownTime(){return downTime;}public int getPointerCount(){return 1;}public int getSource(){return source;}public int getDeviceId(){return device;}public InputDevice getDevice(){return InputDevice.getDevice(device);}public int getButtonState(){return buttons;}public int getActionButton(){return actionButton;}public int getMetaState(){return meta;}public float getAxisValue(int axis){return axes.getOrDefault(axis,0f);}public boolean isFromSource(int s){return(source&s)==s;}}
''',
 'org/openbw/androidtest/NativeBridge.java':'''package org.openbw.androidtest;import java.util.*;import android.graphics.*;class NativeBridge{
 static final List<int[]>calls=new ArrayList<>();static int cursorX,cursorY,target,build,order,selected=1;static String card="";static boolean replay;static int frames,pause=1,framePause,frameCommandCount;static Runnable onFrame;
 static void command(int op,int a,int b,int c,int d){calls.add(new int[]{op,a,b,c,d,cursorX,cursorY});if(op==0){cursorX=a;cursorY=b;}if(op==6)pause=a;}
 static int value(int kind,int index){return kind==0?target:kind==9?build:kind==3?order:kind==1?selected:0;}static String text(int kind){return card;}static void frame(Bitmap b,int n,double clock){frames++;framePause=pause;frameCommandCount=calls.size();if(onFrame!=null)onFrame.run();}
 static void clear(){calls.clear();}static int count(int op){int n=0;for(int[]c:calls)if(c[0]==op)n++;return n;}static int count(int op,int a,int b){int n=0;for(int[]c:calls)if(c[0]==op&&c[1]==a&&c[2]==b)n++;return n;}static int[]last(int op){for(int i=calls.size()-1;i>=0;i--)if(calls.get(i)[0]==op)return calls.get(i);throw new AssertionError("No native operation "+op);}}
''',
 'org/openbw/androidtest/NativeHud.java':'''package org.openbw.androidtest;import java.util.*;import android.graphics.*;class NativeHud{
 static final int WORLD_BOTTOM=376;int page,race,lookupCalls,lookupFrame;boolean gridHotkeys;String lookupCard;final Map<Integer,Hit>slots=new HashMap<>();final RectF minimap=new RectF(0,338,136,480);final Rect miniSource=new Rect(0,338,136,480);final List<Hit>hits=new ArrayList<>();
 static class Hit{RectF rect;int slot=-1;int unload=-1,cancel=-1,selectUnit=-1;boolean more;String help;String[]fields;}
 Hit commandHitForSlot(int slot,String card,int type){lookupCalls++;lookupCard=card;lookupFrame=NativeBridge.frames;return slots.get(slot);}String hint(Hit h){return h.fields==null?h.help:h.fields[1];}Hit hit(float x,float y){for(Hit h:hits)if(h.rect.contains(x,y))return h;return null;}String requirement(String[]f){return "";}static int number(String[]f,int i,int d){return f!=null&&i<f.length?Integer.parseInt(f[i]):d;}}
''',
 'org/openbw/androidtest/NativeArt.java':'''package org.openbw.androidtest;import android.graphics.*;class NativeArt{static class Widget{int type,id;RectF rect=new RectF();RectF hit(){return rect;}RectF rect(){return rect;}}}
''',
 'org/openbw/androidtest/NativeGlue.java':'''package org.openbw.androidtest;import java.util.*;class NativeGlue{static final int ENTER_MS=500;int hot;boolean exiting;double elapsed=1000;Layout layout=new Layout();float shift(NativeArt.Widget w){return 0;}static class Layout{List<NativeArt.Widget>widgets=new ArrayList<>();NativeArt.Widget get(int id){for(NativeArt.Widget w:widgets)if(w.id==id)return w;return null;}}}
''',
 'org/openbw/androidtest/CommandHint.java':'package org.openbw.androidtest;class CommandHint{static String describe(String[]f,String requirement){return f[1];}}',
}

# The integration fixture below is deliberately bounded to event routing and
# action recording. Rendering, OS device delivery and native game results are
# covered by separate suites and must not be inferred from these host checks.
surface=(src/'NativeSurface.java').read_text()
names=['physicalScale','lx','ly','onTouchEvent','onKeyUp','onKeyDown','onHoverEvent','onGenericMotionEvent','touch','setListOffset','placeBuilding','placementButtonAt','blockPlacementTouch','cameraBottom','panCamera','aim','mini','handleGamepadMotion','handleGamepadKey','gamepadDirection','activateGamepad','gamepadActionHeld','gamepadButton','gamepadWorld','gamepadClick','gamepadTouch','resetGamepadDrag','resetGamepad','advanceGamepad']
names+=['resetDesktopInput','resetGamepadInput','resetDesktop','syncDesktopModifiers','handleDesktopMotion','desktopMotion','desktopCursor','desktopPrimary','desktopSecondary','activateDesktopHud','desktopTouch','desktopWheel','handleDesktopKey','desktopKey','advanceDesktop','desktopGridCommand','changeDesktop','openDesktopSettings','desktopSettingsBack','openGamepadSettings']
harness=r'''package org.openbw.androidtest;
import android.view.*;import android.graphics.*;import java.util.*;
class SurfaceBase{public boolean onTouchEvent(MotionEvent e){return false;}public boolean onHoverEvent(MotionEvent e){return false;}public boolean onGenericMotionEvent(MotionEvent e){return false;}public boolean onKeyDown(int key,KeyEvent e){return false;}public boolean onKeyUp(int key,KeyEvent e){return false;}}
public class DesktopInput11Test extends SurfaceBase{
 static int checks,failures;static void run(String name,Runnable test){try{test.run();System.out.println("PASS "+name);}catch(AssertionError e){failures++;System.err.println("FAIL "+name+": "+e.getMessage());}}static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}static void near(double a,double b,String why){check(Math.abs(a-b)<.01,why+": "+a+" != "+b);}
 final List<Runnable>queue=new ArrayList<>();void enqueue(Runnable a){queue.add(a);}void flush(){while(!queue.isEmpty())queue.remove(0).run();}
 static class Button{RectF rect;Runnable action,longAction;boolean enabled=true,vertical,placementButton,controlGroup;java.util.function.Consumer<Float>slider;Button(RectF r,Runnable a){rect=r;action=a;}}
 static class Controls{float pinchSpeed=1,panSpeed=1,placementOffset;boolean pinchZoom=true,confirmBuild,minimapOrders,doubleTap,holdSelect,placementScroll;long miniHoldMs=400,doubleTapMs=250,holdMs=450;float panFactor(){return 1;}String dragGesture(long t){return "pan";}}
 static class Activity{void runOnUiThread(Runnable r){r.run();}void requestAppOptions(){}void requestGamepadSettings(){}}
 final Activity activity=new Activity();final Controls controls=new Controls();final CommandHover commandHover=new CommandHover();final CameraPan cameraPan=new CameraPan();final DesktopControls desktop=new DesktopControls();final DesktopSettings desktopSettings=new DesktopSettings();final android.content.SharedPreferences prefs=new android.content.SharedPreferences();
 NativeHud hud=new NativeHud();NativeGlue glue;Bitmap world=new Bitmap();List<Button>buttons=new ArrayList<>();List<String>profiles=new ArrayList<>();
 String page="game",modal="",gesture="",scrollingList="",hint="";Object pendingScreen;Button pressed;
 int physicalWidth=1920,physicalHeight=1440,logicalWidth=640,commandPercent=100,hoverButton=-1,hintSupplyRace=-1,placeX,placeY;
 float zoom=1,downX,lastX,downY,lastY,lastTapX,lastTapY,pinchDistance,pinchZoom,listVelocity,listStart,mapOffset,missionOffset,profileOffset,briefManual,briefScroll,menuHoverX,menuHoverY;
 long downAt,lastTapAt,listMoveTime;double clock,hintUntil,briefManualUntil;boolean activeGame=true,replayGame,oneShotSelect,placement,targeting,zoomOut;
 RectF placementButtonRow,mapViewport=new RectF(50,130,350,240),missionViewport=new RectF(100,100,500,300),profileViewport=new RectF(100,100,500,300);
 int resized,saved,backs,menus,actions,confirms,cancels,chats;void resizeWorld(){resized++;}void saveSettings(){saved++;}void back(){backs++;}void openMenu(){menus++;modal="menu";}void modalBack(){modal="";}
 float mapMaxOffset(){return 1000;}float missionMaxOffset(){return 1000;}float briefScrollLimit(NativeArt.Widget w){return 1000;}void sfx(String s){}
 void cancelGesture(){gesture="";pressed=null;commandHover.cancel();listVelocity=0;NativeBridge.command(5,0,0,0,0);}
 void updateHover(float x,float y,boolean leave){menuHoverX=leave?-1:x;menuHoverY=leave?-1:y;commandHover.hover(x,y,leave);}
 boolean profileEditing,chatEditing;StringBuilder profileInput=new StringBuilder(),chatInput=new StringBuilder();String profileDraft="",chatDraft="";
 void confirmProfileDialog(){confirms++;}void cancelProfileDialog(){cancels++;profileEditing=false;}void sendChat(){chats++;}void closeChat(){chatEditing=false;}void publishChatInput(){chatDraft=chatInput.toString();}void openChat(){chatEditing=true;}
 final GamepadControls gamepad=new GamepadControls();final Map<Integer,Integer>gamepadHeld=new HashMap<>();
 float padX=320,padY=200,padPointerX,padPointerY,padCameraX,padCameraY,padHatX,padHatY;boolean padActive,padPrecision,padNativeDrag,padTouchDrag;int padDevice=-1,padGroup=1;long padClickAt;String padDragPage="",padDragModal="",gamepadReturnModal="",desktopReturnModal="";
 int desktopMouseDevice=-1,desktopKeyboardDevice=-1,desktopNativeButtons,desktopClicks=1;
 boolean desktopMouseActive,desktopInside,desktopShift,desktopCtrl,desktopTextEditing;
 float desktopX,desktopY,desktopLastClickX,desktopLastClickY,replayOffset;
 long desktopDownAt,desktopLastClickAt;String desktopPrimary="",desktopPage="",desktopModal="";NativeHud.Hit desktopHudHit;
 RectF replayListBounds(){return new RectF(50,130,350,240);}float replayMaxOffset(){return 1000;}
 void gamepadSettingsBack(){modal="";}void controlGroup(int n,boolean assign){NativeBridge.command(25,n,assign?1:0,0,0);}

'''

harness+='\n'.join(method(surface,n)for n in names)

def finish():
 for name,content in sources.items():
  target=b/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
 real=[src/n for n in ['DesktopControls.java','DesktopSettings.java','CommandHover.java','CameraPan.java','GamepadControls.java']]
 jar=r/'build-native/json-20240303.jar'
 subprocess.run(['javac','-cp',str(jar),'-d',str(b/'classes'),*[str(b/n)for n in sources],*map(str,real)],check=True)
 call=subprocess.run(['java','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.DesktopInput11Test'],capture_output=True,text=True)
 print(call.stdout+call.stderr,end='');call.check_returncode()
 files=[src/'NativeSurface.java',src/'MainActivity.java',*real,Path(__file__)]
 (r/'validation/desktop-input11.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'nativeEngine':False,'scope':'Production Java physical mouse and keyboard event routing with recorded native calls; Android event-delivery and native simulation are not emulated','methods':names,'activityMethods':activity_names,'output':call.stdout.strip(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

harness+=r'''
 static MotionEvent pointer(DesktopInput11Test h,int action,float x,float y,int buttons,int actionButton,long time){float scale=h.physicalScale();MotionEvent e=new MotionEvent(action,x*scale+(h.physicalWidth-h.logicalWidth*scale)/2,y*scale+(h.physicalHeight-480*scale)/2,time);e.buttons=buttons;e.actionButton=actionButton;return e;}
 static void touch(DesktopInput11Test h,int action,float x,float y,long time){MotionEvent e=pointer(h,action,x,y,0,0,time);e.source=InputDevice.SOURCE_TOUCHSCREEN;h.onTouchEvent(e);h.flush();}
 static void touchRegression(){
  DesktopInput11Test h=new DesktopInput11Test();NativeBridge.clear();touch(h,MotionEvent.ACTION_DOWN,300,200,100);touch(h,MotionEvent.ACTION_UP,300,200,120);check(NativeBridge.count(4)==1,"Touch tap no longer uses touch selection/order semantics");check(NativeBridge.count(33)==0,"Touch tap went through physical mouse backend");
  h.buttons.add(new Button(new RectF(500,20,600,50),()->h.actions++));NativeBridge.clear();touch(h,MotionEvent.ACTION_DOWN,550,30,200);touch(h,MotionEvent.ACTION_UP,550,30,250);check(h.actions==1&&NativeBridge.count(4)==0,"Touch menu activated world order");
  NativeHud.Hit hit=new NativeHud.Hit();hit.rect=new RectF(500,400,540,440);hit.cancel=1;h.hud.hits.add(hit);NativeBridge.clear();touch(h,MotionEvent.ACTION_DOWN,520,420,500);touch(h,MotionEvent.ACTION_UP,520,420,900);check(NativeBridge.count(7)==0,"Touch hold inspection became activation");
  NativeBridge.clear();touch(h,MotionEvent.ACTION_DOWN,520,420,1000);touch(h,MotionEvent.ACTION_UP,520,420,1100);check(NativeBridge.count(7)==1,"Touch quick command click stopped working");
 }
 static void padKey(DesktopInput11Test h,int key,boolean down){KeyEvent e=new KeyEvent(down?KeyEvent.ACTION_DOWN:KeyEvent.ACTION_UP,key);e.source=InputDevice.SOURCE_GAMEPAD;e.device=3;check(h.handleGamepadKey(e),"Gamepad key unhandled");h.flush();}
 static void typingRegression(){
  DesktopInput11Test h=new DesktopInput11Test();h.profileEditing=true;NativeBridge.clear();KeyEvent a=new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_A);a.unicode=0x444;check(h.onKeyDown(a.key,a),"Profile typing unhandled");h.flush();check(h.profileDraft.equals("ф")&&NativeBridge.count(2)==0&&NativeBridge.count(32)==0,"Profile foreign-layout text became game hotkey");
  KeyEvent enter=new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_ENTER);h.onKeyDown(enter.key,enter);h.flush();check(h.confirms==1&&NativeBridge.count(32)==0,"Profile Enter leaked to game");
  h.profileEditing=false;h.chatEditing=true;a.unicode='A';h.onKeyDown(a.key,a);h.flush();check(h.chatDraft.equals("A")&&NativeBridge.count(2)==0&&NativeBridge.count(32)==0,"Chat text became game hotkey");
  h.onKeyDown(enter.key,enter);h.flush();check(h.chats==1,"Chat Enter did not send draft");
 }
 static void gamepadRegression(){
  DesktopInput11Test h=new DesktopInput11Test();NativeBridge.clear();android.os.SystemClock.now=1000;padKey(h,KeyEvent.KEYCODE_BUTTON_A,true);check(h.padNativeDrag&&NativeBridge.count(1,1,1)==1,"Gamepad selection no longer holds native drag");padKey(h,KeyEvent.KEYCODE_BUTTON_A,false);check(!h.padNativeDrag&&NativeBridge.count(1,0,1)==1,"Gamepad selection release missing");
  NativeBridge.clear();padKey(h,KeyEvent.KEYCODE_BUTTON_B,true);padKey(h,KeyEvent.KEYCODE_BUTTON_B,false);check(NativeBridge.count(1,1,3)==1&&NativeBridge.count(1,0,3)==1,"Gamepad right-click order changed");
  h.buttons.add(new Button(new RectF(500,20,600,60),()->h.actions++));h.padX=550;h.padY=40;NativeBridge.clear();padKey(h,KeyEvent.KEYCODE_BUTTON_A,true);android.os.SystemClock.now=1050;padKey(h,KeyEvent.KEYCODE_BUTTON_A,false);check(h.actions==1&&NativeBridge.count(1,1,1)==0,"Gamepad UI click escaped into world");
  NativeBridge.clear();padKey(h,KeyEvent.KEYCODE_DPAD_RIGHT,true);h.advanceGamepad(100);check(NativeBridge.count(3)>0,"Controller D-pad no longer pans");padKey(h,KeyEvent.KEYCODE_DPAD_RIGHT,false);
  MotionEvent stick=pointer(h,MotionEvent.ACTION_MOVE,0,0,0,0,1100);stick.source=InputDevice.SOURCE_JOYSTICK;stick.device=3;stick.axes.put(MotionEvent.AXIS_X,1f);check(h.handleGamepadMotion(stick),"Gamepad stick unhandled");h.flush();near(h.padPointerX,1,"Gamepad stick magnitude changed");
  MotionEvent finger=pointer(h,MotionEvent.ACTION_MOVE,20,20,0,0,1200);finger.source=InputDevice.SOURCE_TOUCHSCREEN;check(!h.handleGamepadMotion(finger),"Touch became gamepad input");
 }

 static void mouse(DesktopInput11Test h,int action,float x,float y,int buttons,int actionButton,long time){
  MotionEvent e=pointer(h,action,x,y,buttons,actionButton,time);boolean handled;
  if(action==MotionEvent.ACTION_HOVER_MOVE||action==MotionEvent.ACTION_HOVER_ENTER||action==MotionEvent.ACTION_HOVER_EXIT)handled=h.onHoverEvent(e);
  else if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_MOVE||action==MotionEvent.ACTION_CANCEL)handled=h.onTouchEvent(e);
  else handled=h.onGenericMotionEvent(e);
  check(handled,"Physical mouse event unhandled "+action);h.flush();
 }
 static void click(DesktopInput11Test h,float x,float y,int button,long time){mouse(h,MotionEvent.ACTION_DOWN,x,y,button,button,time);mouse(h,MotionEvent.ACTION_UP,x,y,0,button,time+40);}
 static void keyboard(DesktopInput11Test h,int key,boolean down,int unicode,int meta,int repeat){
  KeyEvent e=new KeyEvent(down?KeyEvent.ACTION_DOWN:KeyEvent.ACTION_UP,key);e.unicode=unicode;e.meta=meta;e.repeat=repeat;
  check(down?h.onKeyDown(key,e):h.onKeyUp(key,e),"Physical key unhandled "+key);h.flush();
 }
 static void worldMouseChecks(){
  DesktopInput11Test h=new DesktopInput11Test();h.zoom=2;NativeBridge.clear();
  mouse(h,MotionEvent.ACTION_HOVER_ENTER,300,200,0,0,100);mouse(h,MotionEvent.ACTION_HOVER_EXIT,300,200,0,0,110);
  mouse(h,MotionEvent.ACTION_DOWN,300,200,MotionEvent.BUTTON_PRIMARY,MotionEvent.BUTTON_PRIMARY,120);
  mouse(h,MotionEvent.ACTION_BUTTON_PRESS,300,200,MotionEvent.BUTTON_PRIMARY,MotionEvent.BUTTON_PRIMARY,120);
  check(NativeBridge.count(33,1,1)==1&&NativeBridge.count(4)==0,"Duplicate Android DOWN/PRESS creates duplicate order or touch tap");
  int[] down=NativeBridge.last(33);check(down[5]==150&&down[6]==100,"Mouse world position does not account for zoom");
  mouse(h,MotionEvent.ACTION_MOVE,400,240,MotionEvent.BUTTON_PRIMARY,0,150);
  check(NativeBridge.count(33,0,1)==0&&h.desktopPrimary.equals("world"),"Mouse drag released before button-up");
  mouse(h,MotionEvent.ACTION_UP,400,240,0,MotionEvent.BUTTON_PRIMARY,180);
  mouse(h,MotionEvent.ACTION_BUTTON_RELEASE,400,240,0,MotionEvent.BUTTON_PRIMARY,180);
  int[] up=NativeBridge.last(33);check(NativeBridge.count(33,0,1)==1&&up[5]==200&&up[6]==120,"Mouse release lost position or duplicated");
  NativeBridge.clear();click(h,300,200,MotionEvent.BUTTON_PRIMARY,1000);click(h,300,200,MotionEvent.BUTTON_PRIMARY,1200);
  check(NativeBridge.last(33)[3]==2&&NativeBridge.count(33,1,1)==2&&NativeBridge.count(33,0,1)==2,"Double-click count did not reach both native edges");
  NativeBridge.clear();click(h,400,200,MotionEvent.BUTTON_SECONDARY,2000);check(NativeBridge.count(33,1,3)==1&&NativeBridge.count(33,0,3)==1&&NativeBridge.count(33,1,1)==0&&h.backs==0&&h.menus==0,"Right click selects or opens menu");
  NativeBridge.clear();mouse(h,MotionEvent.ACTION_DOWN,300,200,MotionEvent.BUTTON_PRIMARY,1,2300);mouse(h,MotionEvent.ACTION_MOVE,700,600,MotionEvent.BUTTON_PRIMARY,0,2310);mouse(h,MotionEvent.ACTION_UP,700,600,0,1,2320);
  check(h.desktopNativeButtons==0&&h.desktop.buttons==0&&NativeBridge.count(33,0,1)==1,"Dragging outside viewport leaves left button held");
  NativeBridge.clear();click(h,-10,200,MotionEvent.BUTTON_PRIMARY,2500);check(NativeBridge.count(33)==0&&NativeBridge.count(4)==0,"Letterbox click reached world");
  h.logicalWidth=960;h.physicalWidth=3200;h.physicalHeight=1200;h.zoom=2;NativeBridge.clear();click(h,700,200,MotionEvent.BUTTON_PRIMARY,3000);int[] wide=NativeBridge.last(33);check(wide[5]==350&&wide[6]==100,"Widescreen letterbox and zoom coordinates differ from the viewport");
  NativeBridge.clear();MotionEvent queued=pointer(h,MotionEvent.ACTION_DOWN,500,250,1,1,3500);check(h.handleDesktopMotion(queued),"Queue mouse not accepted");check(NativeBridge.count(33)==0,"Mouse input bypassed worker queue");queued.x=queued.y=-999;queued.buttons=0;h.flush();int[] snapshot=NativeBridge.last(33);check(snapshot[5]==250&&snapshot[6]==125,"Queued event did not preserve its coordinate snapshot");h.resetDesktopInput();h.flush();
 }
 static void hudMenuChecks(){
  DesktopInput11Test h=new DesktopInput11Test();h.buttons.add(new Button(new RectF(500,20,600,60),()->h.actions++));NativeBridge.clear();
  mouse(h,MotionEvent.ACTION_DOWN,550,40,1,1,100);mouse(h,MotionEvent.ACTION_UP,550,40,0,1,1100);
  check(h.actions==1&&NativeBridge.count(33)==0&&NativeBridge.count(4)==0,"Held mouse menu click invoked world or lost action");
  NativeHud.Hit hit=new NativeHud.Hit();hit.rect=new RectF(500,400,540,440);hit.cancel=2;h.hud.hits.add(hit);NativeBridge.clear();
  mouse(h,MotionEvent.ACTION_DOWN,520,420,1,1,2000);mouse(h,MotionEvent.ACTION_UP,520,420,0,1,3000);
  check(NativeBridge.count(7,2,0)==1&&NativeBridge.count(33)==0,"Held mouse HUD click became touch inspection");
  NativeBridge.clear();click(h,520,420,MotionEvent.BUTTON_SECONDARY,3100);click(h,550,40,MotionEvent.BUTTON_SECONDARY,3300);click(h,300,420,MotionEvent.BUTTON_PRIMARY,3500);
  check(h.actions==1&&NativeBridge.count(7)==0&&NativeBridge.count(33)==0&&NativeBridge.count(4)==0,"HUD/right click or blank console issued action");
  NativeBridge.clear();mouse(h,MotionEvent.ACTION_DOWN,520,420,1,1,3700);mouse(h,MotionEvent.ACTION_UP,560,420,0,1,3750);check(NativeBridge.count(7)==0,"Mouse HUD action activated after release outside target");
  NativeBridge.clear();click(h,60,400,MotionEvent.BUTTON_PRIMARY,4000);check(NativeBridge.count(1,1,1)==1&&NativeBridge.count(1,0,1)==1&&NativeBridge.count(33)==0,"Minimap click did not use minimap transform");
  NativeBridge.clear();click(h,60,400,MotionEvent.BUTTON_SECONDARY,4200);check(NativeBridge.count(1,1,3)==1&&NativeBridge.count(1,0,3)==1&&NativeBridge.count(33)==0,"Minimap right order became camera/select action");
  for(int target:new int[]{1,2,3}){NativeBridge.clear();NativeBridge.target=target;click(h,300,200,MotionEvent.BUTTON_SECONDARY,4500+target*100);check(NativeBridge.count(2,27,41)==1&&NativeBridge.count(33)==0,"Right click did not cancel pending target mode "+target);}NativeBridge.target=0;
  for(String card:new String[]{"Build\t","Advanced Build\t"}){NativeBridge.card=card;NativeBridge.clear();click(h,300,200,MotionEvent.BUTTON_SECONDARY,5000);check(NativeBridge.count(2,27,41)==1&&NativeBridge.count(33)==0,"Right click did not cancel build submenu");}NativeBridge.card="";
  h.modal="menu";NativeBridge.clear();click(h,300,200,MotionEvent.BUTTON_PRIMARY,5500);click(h,300,200,MotionEvent.BUTTON_SECONDARY,5700);check(NativeBridge.count(33)==0&&NativeBridge.count(4)==0,"Modal background click issued battlefield input");
  h.modal="";h.pendingScreen=new Object();NativeBridge.clear();click(h,300,200,MotionEvent.BUTTON_PRIMARY,6000);click(h,300,200,MotionEvent.BUTTON_SECONDARY,6200);check(NativeBridge.count(33)==0,"Transition click reached world");
 }
 static void wheel(DesktopInput11Test h,float x,float y,float amount){MotionEvent e=pointer(h,MotionEvent.ACTION_SCROLL,x,y,0,0,100);e.axes.put(MotionEvent.AXIS_VSCROLL,amount);check(h.onGenericMotionEvent(e),"Wheel not handled");h.flush();}
 static void navigationChecks(){
  DesktopInput11Test h=new DesktopInput11Test();h.page="custom";wheel(h,100,180,-1);near(h.mapOffset,66,"Map wheel row scroll");wheel(h,100,180,50);near(h.mapOffset,0,"Map wheel upper clamp");wheel(h,100,180,-100);near(h.mapOffset,1000,"Map wheel lower clamp");near(h.zoom,1,"Menu wheel changed game zoom");
  h.page="campaign";h.modal="missions";wheel(h,200,180,-1);near(h.missionOffset,57,"Mission wheel scroll");h.modal="";h.page="replays";wheel(h,100,180,-1);near(h.replayOffset,66,"Replay wheel scroll");
  h.page="registry";for(int n=0;n<20;n++)h.profiles.add("p"+n);wheel(h,200,180,-1);near(h.profileOffset,69,"Profile wheel scroll");
  h.page="game";h.modal="";wheel(h,300,200,1);near(h.zoom,1.1,"World wheel zoom");check(h.resized==1&&h.saved==1,"Zoom did not resize/persist");wheel(h,300,200,-100);near(h.zoom,1,"Zoom lower clamp");h.zoomOut=true;wheel(h,300,200,-100);near(h.zoom,.5,"Zoom-out preference ignored");wheel(h,300,200,100);near(h.zoom,3,"Zoom upper clamp");
  wheel(h,300,430,-1);near(h.zoom,3,"HUD wheel changed game zoom");mouse(h,MotionEvent.ACTION_DOWN,300,200,1,1,100);wheel(h,300,200,-1);near(h.zoom,3,"Wheel changed zoom during selection drag");mouse(h,MotionEvent.ACTION_UP,300,200,0,1,150);
  h.zoom=2;NativeBridge.clear();mouse(h,MotionEvent.ACTION_DOWN,300,200,MotionEvent.BUTTON_TERTIARY,MotionEvent.BUTTON_TERTIARY,300);mouse(h,MotionEvent.ACTION_MOVE,280,180,MotionEvent.BUTTON_TERTIARY,0,330);int[] pan=NativeBridge.last(3);check(pan[1]==10&&pan[2]==10&&NativeBridge.count(33)==0,"Middle drag did not pan with zoom");mouse(h,MotionEvent.ACTION_UP,280,180,0,MotionEvent.BUTTON_TERTIARY,350);
  NativeBridge.clear();mouse(h,MotionEvent.ACTION_HOVER_MOVE,639,200,0,0,400);h.advanceDesktop(100);check(NativeBridge.count(3)>0&&NativeBridge.last(3)[1]>0,"Mouse edge does not pan camera");NativeBridge.clear();mouse(h,MotionEvent.ACTION_HOVER_EXIT,639,200,0,0,410);h.advanceDesktop(100);check(NativeBridge.count(3)==0,"Hover exit kept camera edge scrolling");
  mouse(h,MotionEvent.ACTION_HOVER_MOVE,300,200,0,0,500);NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_DPAD_LEFT,true,0,0,0);h.advanceDesktop(100);check(NativeBridge.last(3)[1]<0,"Keyboard arrow did not pan camera");keyboard(h,KeyEvent.KEYCODE_DPAD_LEFT,false,0,0,0);NativeBridge.clear();h.advanceDesktop(100);check(NativeBridge.count(3)==0,"Released keyboard arrow kept scrolling");
  h.modal="menu";keyboard(h,KeyEvent.KEYCODE_DPAD_RIGHT,true,0,0,0);NativeBridge.clear();h.advanceDesktop(100);check(NativeBridge.count(3)==0,"Keyboard arrow panned behind menu");
 }
 static void keyboardChecks(){
  DesktopInput11Test h=new DesktopInput11Test();
  for(int unicode:new int[]{'A','a',0x444,0}){NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_A,true,unicode,0,0);keyboard(h,KeyEvent.KEYCODE_A,true,unicode,0,1);keyboard(h,KeyEvent.KEYCODE_A,false,0,0,0);check(NativeBridge.count(32,1,'a')==1&&NativeBridge.count(32,0,'a')==1,"Case/layout/repeat changed hotkey edges");check(NativeBridge.last(32)[3]==4,"A uses incorrect SDL scan code");}
  NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_CTRL_LEFT,true,0,KeyEvent.META_CTRL_ON,0);keyboard(h,KeyEvent.KEYCODE_2,true,'@',KeyEvent.META_CTRL_ON,0);keyboard(h,KeyEvent.KEYCODE_2,false,0,KeyEvent.META_CTRL_ON,0);keyboard(h,KeyEvent.KEYCODE_CTRL_LEFT,false,0,0,0);
  check(NativeBridge.calls.size()==4,"Ctrl+group added unintended input");int[] c=NativeBridge.calls.get(0),g=NativeBridge.calls.get(1),u=NativeBridge.calls.get(3);check(c[0]==32&&c[1]==1&&c[3]==224&&g[2]=='2'&&u[1]==0&&u[3]==224,"Control group modifier ordering wrong");check(!h.desktop.ctrl()&&!h.desktopCtrl,"Ctrl release stays held");
  NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_SHIFT_RIGHT,true,0,KeyEvent.META_SHIFT_ON,0);keyboard(h,KeyEvent.KEYCODE_3,true,'#',KeyEvent.META_SHIFT_ON,0);keyboard(h,KeyEvent.KEYCODE_3,false,0,KeyEvent.META_SHIFT_ON,0);keyboard(h,KeyEvent.KEYCODE_SHIFT_RIGHT,false,0,0,0);check(NativeBridge.calls.get(0)[3]==225&&NativeBridge.last(32)[3]==225&&!h.desktopShift,"Right Shift not normalized/released");
  for(int[] k:new int[][]{{KeyEvent.KEYCODE_ESCAPE,27,41},{KeyEvent.KEYCODE_SPACE,32,44},{KeyEvent.KEYCODE_TAB,9,43}}){NativeBridge.clear();keyboard(h,k[0],true,0,0,0);keyboard(h,k[0],false,0,0,0);check(NativeBridge.count(32,1,k[1])==1&&NativeBridge.last(32)[3]==k[2],"Esc/Space/Tab not sent as native command");}
  NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_F10,true,0,0,0);keyboard(h,KeyEvent.KEYCODE_F10,false,0,0,0);check(h.modal.equals("menu")&&h.menus==1&&NativeBridge.count(32)==0,"F10 did not open game menu exclusively");keyboard(h,KeyEvent.KEYCODE_F10,true,0,0,0);keyboard(h,KeyEvent.KEYCODE_F10,false,0,0,0);check(h.modal.isEmpty(),"F10 did not close menu");
  NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_ENTER,true,13,0,0);check(h.chatEditing&&NativeBridge.count(32)==0,"Enter did not open chat without order");h.chatEditing=false;h.resetDesktopInput();h.flush();
  NativeBridge.clear();h.pendingScreen=new Object();keyboard(h,KeyEvent.KEYCODE_A,true,'a',0,0);keyboard(h,KeyEvent.KEYCODE_A,false,0,0,0);check(NativeBridge.count(32)==0,"Hotkey reached engine during menu transition");
 }
 static void lifecycleChecks(){
  DesktopInput11Test h=new DesktopInput11Test();keyboard(h,KeyEvent.KEYCODE_SHIFT_LEFT,true,0,KeyEvent.META_SHIFT_ON,0);mouse(h,MotionEvent.ACTION_DOWN,300,200,1,1,100);NativeBridge.clear();h.resetDesktopInput();h.flush();check(NativeBridge.count(34)==1&&h.desktop.buttons==0&&h.desktopNativeButtons==0&&!h.desktop.shift()&&!h.desktopMouseActive,"Focus cleanup left native buttons/modifiers held");
  keyboard(h,KeyEvent.KEYCODE_CTRL_LEFT,true,0,KeyEvent.META_CTRL_ON,0);h.modal="menu";NativeBridge.clear();h.advanceDesktop(50);check(NativeBridge.count(34)==1&&!h.desktopCtrl&&!h.desktop.ctrl(),"Modal transition retained modifier");h.modal="";
  keyboard(h,KeyEvent.KEYCODE_DPAD_RIGHT,true,0,0,0);InputDevice.devices.remove(1);NativeBridge.clear();h.advanceDesktop(50);check(NativeBridge.count(34)==1&&h.desktop.cameraX()==0&&NativeBridge.count(3)==0,"Disconnected keyboard left camera moving");InputDevice.devices.put(1,new InputDevice(InputDevice.SOURCE_KEYBOARD));
  mouse(h,MotionEvent.ACTION_DOWN,300,200,1,1,200);InputDevice.devices.remove(2);NativeBridge.clear();h.advanceDesktop(50);check(NativeBridge.count(34)==1&&h.desktopNativeButtons==0&&!h.desktopMouseActive,"Disconnected mouse leaves held drag");InputDevice.devices.put(2,new InputDevice(InputDevice.SOURCE_MOUSE));
  mouse(h,MotionEvent.ACTION_DOWN,300,200,1,1,300);NativeBridge.clear();mouse(h,MotionEvent.ACTION_CANCEL,300,200,0,0,310);check(NativeBridge.count(34)==1&&h.desktopPrimary.isEmpty(),"Mouse cancel did not clear held input");
  h.profileEditing=true;NativeBridge.clear();click(h,300,200,MotionEvent.BUTTON_PRIMARY,400);check(NativeBridge.count(33)==0,"Text editing leaked physical click into world");h.profileEditing=false;
  MotionEvent stylus=pointer(h,MotionEvent.ACTION_HOVER_MOVE,200,150,0,0,500);stylus.source=InputDevice.SOURCE_STYLUS;stylus.tool=MotionEvent.TOOL_TYPE_STYLUS;check(!h.handleDesktopMotion(stylus),"Stylus misclassified as physical mouse");check(h.onHoverEvent(stylus),"Stylus hover stopped working");h.flush();near(h.menuHoverX,200,"Stylus hover coordinates changed");
 }


 static void transitionChecks(){
  DesktopInput11Test h=new DesktopInput11Test();NativeBridge.clear();click(h,300,200,1,100);check(h.desktop.buttons==0&&h.desktopNativeButtons==0,"Completed mouse click remains held");NativeBridge.clear();h.resetDesktopInput();h.flush();check(NativeBridge.count(34)==1,"Completed but undrained mouse events survive focus reset");NativeBridge.clear();h.resetDesktopInput();h.flush();check(NativeBridge.count(34)==0,"Repeated focus reset flushes unrelated input");
  keyboard(h,KeyEvent.KEYCODE_A,true,'a',0,0);keyboard(h,KeyEvent.KEYCODE_A,false,0,0,0);NativeBridge.clear();h.resetDesktopInput();h.flush();check(NativeBridge.count(34)==1,"Completed but undrained keyboard events survive focus reset");
  mouse(h,MotionEvent.ACTION_DOWN,300,200,1,1,1000);mouse(h,MotionEvent.ACTION_MOVE,400,200,1,0,1050);mouse(h,MotionEvent.ACTION_UP,300,200,0,1,1100);NativeBridge.clear();click(h,300,200,1,1200);check(NativeBridge.last(33)[3]==1,"Mouse drag did not break double-click sequence");
  h.resetDesktopInput();h.flush();NativeBridge.clear();MotionEvent meta=pointer(h,MotionEvent.ACTION_DOWN,300,200,1,1,2000);meta.meta=KeyEvent.META_SHIFT_ON|KeyEvent.META_CTRL_ON;h.onTouchEvent(meta);h.flush();int firstButton=-1;boolean shift=false,ctrl=false;for(int i=0;i<NativeBridge.calls.size();i++){int[]c=NativeBridge.calls.get(i);if(c[0]==32&&c[1]==1&&c[3]==225)shift=true;if(c[0]==32&&c[1]==1&&c[3]==224)ctrl=true;if(c[0]==33){firstButton=i;check(shift&&ctrl,"Mouse metadata modifiers applied after click");break;}}check(firstButton>=0,"Metadata click did not reach native input");
  meta.action=MotionEvent.ACTION_UP;meta.buttons=0;meta.meta=0;h.onTouchEvent(meta);h.flush();check(!h.desktopShift&&!h.desktopCtrl&&NativeBridge.count(32,0,0)==2,"Mouse metadata modifiers remain held after release");
  keyboard(h,KeyEvent.KEYCODE_SHIFT_LEFT,true,0,KeyEvent.META_SHIFT_ON,0);NativeBridge.clear();touch(h,MotionEvent.ACTION_DOWN,300,200,3000);touch(h,MotionEvent.ACTION_UP,300,200,3100);check(NativeBridge.count(34)==1&&!h.desktop.shift()&&NativeBridge.count(4)==1,"Touch takeover lost tap or kept mouse modifiers");
  mouse(h,MotionEvent.ACTION_DOWN,300,200,1,1,4000);NativeBridge.clear();padKey(h,KeyEvent.KEYCODE_BUTTON_A,true);check(NativeBridge.count(34)==1&&h.desktopNativeButtons==0&&h.padNativeDrag,"Gamepad takeover left desktop drag held");NativeBridge.clear();padKey(h,KeyEvent.KEYCODE_BUTTON_A,false);check(NativeBridge.count(34)==0,"Gamepad release unnecessarily clears native queued events");
  padKey(h,KeyEvent.KEYCODE_BUTTON_A,true);NativeBridge.clear();mouse(h,MotionEvent.ACTION_DOWN,300,200,1,1,4200);check(NativeBridge.count(5)==1&&!h.padActive&&h.gamepadHeld.isEmpty()&&h.desktopNativeButtons==1,"Mouse takeover failed to release gamepad drag");mouse(h,MotionEvent.ACTION_UP,300,200,0,1,4300);
  Button slider=new Button(new RectF(200,400,400,430),()->h.actions++);final float[]value={-1};slider.slider=n->value[0]=n;h.buttons.add(slider);NativeBridge.clear();mouse(h,MotionEvent.ACTION_DOWN,250,415,1,1,5000);near(value[0],.25,"Mouse slider press location");mouse(h,MotionEvent.ACTION_MOVE,350,415,1,0,5050);near(value[0],.75,"Mouse slider drag");mouse(h,MotionEvent.ACTION_UP,350,415,0,1,5100);check(h.actions==0&&NativeBridge.count(33)==0,"Slider release became game/button action");
 }
 static void activityChecks(){
  DesktopInput11Test h=new DesktopInput11Test();DesktopActivity11 a=new DesktopActivity11();a.game=h;NativeBridge.clear();KeyEvent key=new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_A);key.unicode='A';check(a.dispatchKeyEvent(key),"Activity did not route physical keyboard");check(NativeBridge.count(32)==0,"Activity bypassed input worker");h.flush();check(NativeBridge.count(32,1,'a')==1,"Activity routed keyboard zero or multiple times");key.action=KeyEvent.ACTION_UP;a.dispatchKeyEvent(key);h.flush();
  KeyEvent back=new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_BACK);back.source=InputDevice.SOURCE_MOUSE;back.device=2;check(a.dispatchKeyEvent(back),"Mouse Back did not get consumed");h.flush();check(h.backs==0&&h.menus==0,"Mouse right-button Back opened app/game menu");
  h.profileEditing=true;NativeBridge.clear();key.action=KeyEvent.ACTION_DOWN;key.unicode=0x444;check(!a.dispatchKeyEvent(key),"Activity intercepted profile input");h.onKeyDown(key.key,key);h.flush();check(h.profileDraft.equals("ф")&&NativeBridge.count(32)==0,"Profile activity fallback did not preserve typed character");
  h.page="registry";h.modal="profile-create";h.buttons.add(new Button(new RectF(200,250,300,280),()->h.actions++));mouse(h,MotionEvent.ACTION_DOWN,250,265,1,1,100);h.advanceDesktop(100);mouse(h,MotionEvent.ACTION_UP,250,265,0,1,220);check(h.actions==1,"Profile dialog mouse button stopped working while typing");
  h.profileEditing=false;h.page="game";h.modal="";h.resetDesktopInput();h.flush();a.optionsVisible=true;NativeBridge.clear();key.action=KeyEvent.ACTION_DOWN;check(!a.dispatchKeyEvent(key),"App Options still intercepted physical game hotkey");MotionEvent m=pointer(h,MotionEvent.ACTION_BUTTON_PRESS,300,200,1,1,300);check(!a.dispatchGenericMotionEvent(m),"App Options still intercepted physical game pointer");h.flush();check(NativeBridge.count(32)==0&&NativeBridge.count(33)==0,"Input routed to hidden game");a.optionsVisible=false;
  KeyEvent pad=new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_RIGHT);pad.source=InputDevice.SOURCE_KEYBOARD;pad.device=3;check(a.dispatchKeyEvent(pad),"Controller D-pad stopped working through Activity");h.flush();check(h.padActive&&h.desktop.cameraX()==0,"Controller D-pad was taken by keyboard camera");pad.action=KeyEvent.ACTION_UP;a.dispatchKeyEvent(pad);h.flush();
  keyboard(h,KeyEvent.KEYCODE_CTRL_LEFT,true,0,KeyEvent.META_CTRL_ON,0);mouse(h,MotionEvent.ACTION_DOWN,300,200,1,1,400);NativeBridge.clear();a.onWindowFocusChanged(false);h.flush();check(NativeBridge.count(34)==1&&!h.desktop.ctrl()&&h.desktop.buttons==0&&!h.padActive,"Activity focus loss did not release physical inputs");a.onWindowFocusChanged(true);check(a.fullscreens==1,"Focus gain lost fullscreen restore");
  keyboard(h,KeyEvent.KEYCODE_DPAD_LEFT,true,0,0,0);NativeBridge.clear();a.onInputDeviceRemoved(1);h.flush();check(NativeBridge.count(34)==1&&h.desktop.cameraX()==0,"Activity device disconnect did not reset held keys");
 }
 static NativeHud.Hit slot(int n,int ordinal,int token){NativeHud.Hit h=new NativeHud.Hit();h.slot=n;h.fields=new String[18];Arrays.fill(h.fields,"0");h.fields[0]="v";h.fields[1]="Build Vulture";h.fields[2]="1";h.fields[16]=String.valueOf(ordinal);h.fields[17]=String.valueOf(token);return h;}
 static void gridChecks(){
  DesktopInput11Test h=new DesktopInput11Test();h.desktopSettings.gridHotkeys=true;
  int[] keys={KeyEvent.KEYCODE_Q,KeyEvent.KEYCODE_W,KeyEvent.KEYCODE_E,KeyEvent.KEYCODE_A,KeyEvent.KEYCODE_S,KeyEvent.KEYCODE_D,KeyEvent.KEYCODE_Z,KeyEvent.KEYCODE_X,KeyEvent.KEYCODE_C};
  for(int i=0;i<keys.length;i++)h.hud.slots.put(i,slot(i,100+i,900+i));
  for(int i=0;i<keys.length;i++)for(int unicode:new int[]{0,'Q',0x439}){
   NativeBridge.clear();NativeBridge.pause=1;int before=NativeBridge.frames;keyboard(h,keys[i],true,unicode,0,0);keyboard(h,keys[i],true,unicode,0,1);keyboard(h,keys[i],false,0,0,0);
   check(NativeBridge.count(35,100+i,900+i)==1,"Grid slot uses wrong identity or repeats: "+i);
   check(NativeBridge.count(32)==0&&NativeBridge.count(2)==0,"Grid slot falls through to an original letter");
   check(NativeBridge.frames>before&&h.hud.lookupFrame>before,"Grid uses a stale card before pending native input is processed");
   check(NativeBridge.count(6,0,0)==1&&NativeBridge.framePause==0&&NativeBridge.frameCommandCount>0,"Grid preflush keeps a just-closed menu paused");
  }
  NativeBridge.clear();for(int k=KeyEvent.KEYCODE_A;k<=KeyEvent.KEYCODE_Z;k++)if(DesktopSettings.gridSlot('a'+k-KeyEvent.KEYCODE_A)<0){keyboard(h,k,true,'A'+k-KeyEvent.KEYCODE_A,0,0);keyboard(h,k,false,0,0,0);}check(NativeBridge.count(32)==0&&NativeBridge.count(35)==0,"Non-grid letter triggers original command in grid mode");
  h.hud.slots.clear();NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_Q,true,'q',0,0);keyboard(h,KeyEvent.KEYCODE_Q,false,0,0,0);check(NativeBridge.count(35)==0&&NativeBridge.count(32)==0,"Empty grid slot triggered original hotkey");
  NativeHud.Hit disabled=slot(0,12,34);disabled.fields[2]="0";h.hud.slots.put(0,disabled);NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_Q,true,'q',0,0);keyboard(h,KeyEvent.KEYCODE_Q,false,0,0,0);check(NativeBridge.count(32)==0&&NativeBridge.count(2)==0,"Unavailable grid command falls back to V hotkey");
  NativeHud.Hit more=new NativeHud.Hit();more.slot=0;more.more=true;h.hud.slots.put(0,more);NativeBridge.clear();int page=h.hud.page;keyboard(h,KeyEvent.KEYCODE_Q,true,'q',0,0);keyboard(h,KeyEvent.KEYCODE_Q,false,0,0,0);check(h.hud.page==page+1&&NativeBridge.count(35)==0&&NativeBridge.count(32)==0,"Grid More button does not advance local command page");
  NativeHud.Hit cancel=slot(8,-1,0);cancel.fields=Arrays.copyOf(cancel.fields,16);cancel.fields[0]="\u001b";h.hud.slots.put(8,cancel);NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_C,true,'c',0,0);keyboard(h,KeyEvent.KEYCODE_C,false,0,0,0);check(NativeBridge.count(2,27,41)==1&&NativeBridge.count(32)==0&&NativeBridge.count(35)==0,"Synthetic grid Cancel is not Escape-only");
  NativeBridge.card="old";NativeBridge.onFrame=()->{NativeBridge.card="fresh";h.hud.slots.put(0,slot(0,22,3300));};NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_Q,true,'q',0,0);keyboard(h,KeyEvent.KEYCODE_Q,false,0,0,0);NativeBridge.onFrame=null;
  check(h.hud.lookupCard.equals("fresh")&&NativeBridge.count(35,22,3300)==1,"Same-frame submenu action uses preceding command card");
  NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_SHIFT_LEFT,true,0,KeyEvent.META_SHIFT_ON,0);keyboard(h,KeyEvent.KEYCODE_Q,true,'Q',KeyEvent.META_SHIFT_ON,0);keyboard(h,KeyEvent.KEYCODE_Q,false,0,KeyEvent.META_SHIFT_ON,0);keyboard(h,KeyEvent.KEYCODE_SHIFT_LEFT,false,0,0,0);
  check(NativeBridge.calls.get(0)[0]==32&&NativeBridge.calls.get(0)[3]==225&&NativeBridge.count(35,22,3300)==1&&NativeBridge.last(32)[1]==0,"Grid Shift order lost modifier ordering/release");
  for(int[] g:new int[][]{{KeyEvent.KEYCODE_2,'2'},{KeyEvent.KEYCODE_ESCAPE,27},{KeyEvent.KEYCODE_SPACE,32},{KeyEvent.KEYCODE_TAB,9}}){NativeBridge.clear();keyboard(h,g[0],true,g[1],0,0);keyboard(h,g[0],false,0,0,0);check(NativeBridge.count(32,1,g[1])==1&&NativeBridge.count(32,0,g[1])==1,"Grid swallowed global group/Esc/Space/Tab key");}
  for(int guard=0;guard<5;guard++){h.replayGame=guard==0;h.modal=guard==1?"menu":"";h.pendingScreen=guard==2?new Object():null;h.page=guard==3?"main":"game";h.activeGame=guard!=4;NativeBridge.clear();int before=NativeBridge.frames;h.desktopGridCommand('q');check(NativeBridge.count(35)==0&&NativeBridge.count(6)==0&&NativeBridge.frames==before,"Grid helper unpauses or executes through guard "+guard);}h.replayGame=false;h.modal="";h.pendingScreen=null;h.page="game";h.activeGame=true;
  for(int invalid=0;invalid<3;invalid++){NativeHud.Hit broken=slot(0,22,3300);if(invalid<2)broken.fields[16+invalid]="invalid";else broken.fields=Arrays.copyOf(broken.fields,16);h.hud.slots.put(0,broken);NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_Q,true,'q',0,0);keyboard(h,KeyEvent.KEYCODE_Q,false,0,0,0);check(NativeBridge.count(35)==0&&NativeBridge.count(32)==0&&NativeBridge.count(2)==0,"Invalid/missing grid identity falls through to another command");}
  h.profileEditing=true;NativeBridge.clear();KeyEvent typed=new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_Q);typed.unicode=0x439;check(!h.handleDesktopKey(typed),"Grid intercepted profile text");h.onKeyDown(typed.key,typed);h.flush();check(h.profileDraft.equals("й")&&NativeBridge.count(35)==0&&NativeBridge.count(32)==0,"Grid profile letter issued gameplay action");h.profileEditing=false;h.chatEditing=true;typed.unicode='Q';check(!h.handleDesktopKey(typed),"Grid intercepted chat text");h.onKeyDown(typed.key,typed);h.flush();check(h.chatDraft.equals("Q")&&NativeBridge.count(35)==0&&NativeBridge.count(32)==0,"Grid chat letter issued gameplay action");h.chatEditing=false;
  h.desktopSettings.gridHotkeys=false;NativeBridge.clear();keyboard(h,KeyEvent.KEYCODE_V,true,'V',0,0);keyboard(h,KeyEvent.KEYCODE_V,false,0,0,0);check(NativeBridge.count(32,1,'v')==1&&NativeBridge.count(32,0,'v')==1&&NativeBridge.count(35)==0,"Original mode no longer emits native original hotkeys");NativeBridge.card="";
 }
 static void optionChecks(){
  DesktopInput11Test h=new DesktopInput11Test();h.desktopSettings.edgeScroll=false;mouse(h,MotionEvent.ACTION_HOVER_MOVE,639,200,0,0,100);NativeBridge.clear();h.advanceDesktop(100);check(NativeBridge.count(3)==0,"Disabled mouse edge scroll still pans");
  h.desktopSettings.edgeScroll=true;NativeBridge.clear();h.advanceDesktop(100);check(NativeBridge.count(3)>0&&NativeBridge.last(3)[1]>0,"Enabled mouse edge scroll does not pan");
  mouse(h,MotionEvent.ACTION_HOVER_MOVE,300,200,0,0,200);h.desktopSettings.arrowPan=false;keyboard(h,KeyEvent.KEYCODE_DPAD_RIGHT,true,0,0,0);NativeBridge.clear();h.advanceDesktop(100);check(NativeBridge.count(3)==0,"Disabled keyboard arrows still pan");h.desktopSettings.arrowPan=true;NativeBridge.clear();h.advanceDesktop(100);check(NativeBridge.count(3)>0,"Enabled keyboard arrow does not pan");keyboard(h,KeyEvent.KEYCODE_DPAD_RIGHT,false,0,0,0);
  h.desktopSettings.wheelZoom=false;wheel(h,300,200,1);near(h.zoom,1,"Disabled mouse wheel zoom changed zoom");h.page="custom";wheel(h,100,180,-1);near(h.mapOffset,66,"Disabling wheel zoom disabled list scrolling");h.page="game";h.desktopSettings.wheelZoom=true;wheel(h,300,200,1);near(h.zoom,1.1,"Enabled mouse wheel zoom does not zoom");
  h.zoom=1;h.desktopSettings.middlePan=false;mouse(h,MotionEvent.ACTION_DOWN,300,200,MotionEvent.BUTTON_TERTIARY,MotionEvent.BUTTON_TERTIARY,300);NativeBridge.clear();mouse(h,MotionEvent.ACTION_MOVE,280,180,MotionEvent.BUTTON_TERTIARY,0,330);check(NativeBridge.count(3)==0,"Disabled middle drag still pans");mouse(h,MotionEvent.ACTION_UP,280,180,0,MotionEvent.BUTTON_TERTIARY,350);h.desktopSettings.middlePan=true;mouse(h,MotionEvent.ACTION_DOWN,300,200,MotionEvent.BUTTON_TERTIARY,MotionEvent.BUTTON_TERTIARY,400);NativeBridge.clear();mouse(h,MotionEvent.ACTION_MOVE,280,180,MotionEvent.BUTTON_TERTIARY,0,430);check(NativeBridge.count(3)>0,"Enabled middle drag cannot pan");mouse(h,MotionEvent.ACTION_UP,280,180,0,MotionEvent.BUTTON_TERTIARY,450);
  DesktopInput11Test normal=new DesktopInput11Test(),fast=new DesktopInput11Test();fast.desktopSettings.cameraSpeed=2;keyboard(normal,KeyEvent.KEYCODE_DPAD_RIGHT,true,0,0,0);keyboard(fast,KeyEvent.KEYCODE_DPAD_RIGHT,true,0,0,0);NativeBridge.clear();normal.advanceDesktop(100);int speed1=NativeBridge.last(3)[1];NativeBridge.clear();fast.advanceDesktop(100);check(NativeBridge.last(3)[1]==speed1*2,"Desktop camera speed has no effect on arrow panning");
 }
 static void settingsChecks(){
  android.content.SharedPreferences prefs=new android.content.SharedPreferences();prefs.values.put("unrelated","keep");DesktopSettings s=new DesktopSettings();s.load(prefs);
  check(!s.gridHotkeys&&s.edgeScroll&&s.wheelZoom&&s.middlePan&&s.arrowPan,"New settings change existing defaults");near(s.cameraSpeed,1,"Default desktop camera speed");
  for(int mask=0;mask<32;mask++)for(float speed:new float[]{.25f,1f,1.75f,2.5f}){
   s.gridHotkeys=(mask&1)!=0;s.edgeScroll=(mask&2)!=0;s.wheelZoom=(mask&4)!=0;s.middlePan=(mask&8)!=0;s.arrowPan=(mask&16)!=0;s.cameraSpeed=speed;s.save(prefs);
   DesktopSettings read=new DesktopSettings();read.load(prefs);check(read.gridHotkeys==s.gridHotkeys&&read.edgeScroll==s.edgeScroll&&read.wheelZoom==s.wheelZoom&&read.middlePan==s.middlePan&&read.arrowPan==s.arrowPan,"Desktop settings lost on reopen "+mask);near(read.cameraSpeed,speed,"Camera speed lost on reopen");check(prefs.values.get("unrelated").equals("keep"),"Desktop save overwrote unrelated preference");
  }
  for(String malformed:new String[]{"broken","[]","{","null"}){prefs.values.put("desktop-controls",malformed);s.load(prefs);check(!s.gridHotkeys&&s.edgeScroll&&s.wheelZoom&&s.middlePan&&s.arrowPan&&s.cameraSpeed==1,"Malformed preferences do not restore defaults");}
  prefs.values.put("desktop-controls","{\"gridHotkeys\":true}");s.load(prefs);check(s.gridHotkeys&&s.edgeScroll&&s.wheelZoom&&s.middlePan&&s.arrowPan&&s.cameraSpeed==1,"Partial stored preferences lose defaults");
  for(double[]sample:new double[][]{{-100,.25},{0,.25},{.25,.25},{1,1},{2.5,2.5},{100,2.5},{Double.NaN,1},{Double.POSITIVE_INFINITY,1},{Double.NEGATIVE_INFINITY,1}}){near(DesktopSettings.speed(sample[0]),sample[1],"Camera clamp");s.cameraSpeed=(float)sample[0];s.save(prefs);DesktopSettings read=new DesktopSettings();read.load(prefs);near(read.cameraSpeed,sample[1],"Invalid saved speed persists");}
  String grid="qweasdzxc";for(int i=0;i<grid.length();i++){check(DesktopSettings.gridSlot(grid.charAt(i))==i&&DesktopSettings.gridSlot(Character.toUpperCase(grid.charAt(i)))==i,"Grid physical order/case mapping "+i);}for(int key:new int[]{0,9,27,32,'m','v','b','r','0','9',0x444})check(DesktopSettings.gridSlot(key)==-1,"Non-grid character gets a command slot");
  DesktopInput11Test h=new DesktopInput11Test();keyboard(h,KeyEvent.KEYCODE_A,true,'a',0,0);h.hint="Old tooltip";h.hintUntil=1000;NativeBridge.clear();h.changeDesktop(()->h.desktopSettings.gridHotkeys=true);check(NativeBridge.count(34)==1&&!h.desktop.held(KeyEvent.KEYCODE_A)&&h.hud.gridHotkeys&&h.hint.isEmpty()&&h.hintUntil==0,"Changing hotkey mode retains held input or stale tooltip");keyboard(h,KeyEvent.KEYCODE_A,false,0,0,0);check(NativeBridge.count(32)==0,"Mode change sends unmatched old letter key-up");DesktopSettings read=new DesktopSettings();read.load(h.prefs);check(read.gridHotkeys,"Settings action did not persist hotkey mode");
  h.hud.slots.put(0,slot(0,20,30));keyboard(h,KeyEvent.KEYCODE_Q,true,'q',0,0);NativeBridge.clear();h.changeDesktop(()->h.desktopSettings.gridHotkeys=false);keyboard(h,KeyEvent.KEYCODE_Q,false,0,0,0);check(NativeBridge.count(34)==1&&NativeBridge.count(32)==0&&!h.hud.gridHotkeys,"Grid-to-original switch leaks held Q into original command");
  h.modal="controls";h.openDesktopSettings();h.flush();check(h.modal.equals("control-desktop")&&h.desktopReturnModal.equals("controls"),"In-game desktop settings do not open/remember parent");h.desktopSettingsBack();check(h.modal.equals("controls"),"Desktop settings Previous does not return to Controls");h.modal="";h.page="main";h.openDesktopSettings();h.openGamepadSettings();h.flush();check(h.modal.isEmpty()&&h.page.equals("main"),"Desktop/gamepad settings remain accessible outside a game");
  h.page="game";h.activeGame=false;h.openDesktopSettings();h.openGamepadSettings();h.flush();check(h.modal.isEmpty(),"Desktop/gamepad settings open without active engine");h.activeGame=true;h.modal="controls";h.openGamepadSettings();h.flush();check(h.modal.equals("gamepad")&&h.gamepadReturnModal.equals("controls"),"In-game gamepad settings route changed");
 }
 public static void main(String[]args){InputDevice.devices.put(1,new InputDevice(InputDevice.SOURCE_KEYBOARD));InputDevice.devices.put(2,new InputDevice(InputDevice.SOURCE_MOUSE));InputDevice.devices.put(3,new InputDevice(InputDevice.SOURCE_GAMEPAD|InputDevice.SOURCE_JOYSTICK));run("touch regression",DesktopInput11Test::touchRegression);run("gamepad regression",DesktopInput11Test::gamepadRegression);run("typing",DesktopInput11Test::typingRegression);run("mouse world",DesktopInput11Test::worldMouseChecks);run("HUD and menus",DesktopInput11Test::hudMenuChecks);run("navigation",DesktopInput11Test::navigationChecks);run("keyboard",DesktopInput11Test::keyboardChecks);run("lifecycle",DesktopInput11Test::lifecycleChecks);run("Activity routing",DesktopInput11Test::activityChecks);run("input transitions",DesktopInput11Test::transitionChecks);run("grid hotkeys",DesktopInput11Test::gridChecks);run("desktop options",DesktopInput11Test::optionChecks);run("settings persistence and access",DesktopInput11Test::settingsChecks);if(failures>0)throw new AssertionError(failures+" groups failed after "+checks+" checks");System.out.println("PASS "+checks+" production Java routing checks");}
}
'''
sources['org/openbw/androidtest/DesktopInput11Test.java']=harness
activity=(src/'MainActivity.java').read_text()
activity_names=['dispatchGenericMotionEvent','dispatchKeyEvent','resetPhysicalInput','onWindowFocusChanged','onInputDeviceRemoved']
sources['org/openbw/androidtest/DesktopActivity11.java']='''package org.openbw.androidtest;
class BaseActivity11{int fallbacks;public boolean dispatchKeyEvent(android.view.KeyEvent e){fallbacks++;return false;}public boolean dispatchGenericMotionEvent(android.view.MotionEvent e){fallbacks++;return false;}public void onWindowFocusChanged(boolean focus){}public void onInputDeviceRemoved(int id){}}
class DesktopActivity11 extends BaseActivity11{DesktopInput11Test game;boolean optionsVisible;int fullscreens;void fullscreen(){fullscreens++;}
'''+ '\n'.join(method(activity,n)for n in activity_names)+'\n}\n'

if __name__=='__main__':finish()

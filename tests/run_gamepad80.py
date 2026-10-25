#!/usr/bin/env python3
"""Execute production controller/group input methods through bounded Android/Canvas shims.
No physical controller or Android device is simulated; tests verify routing and lifecycle.
"""
from pathlib import Path
import ast,hashlib,json,re,subprocess,shutil
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest'
b=r/'build-native/gamepad80';b.mkdir(parents=True,exist_ok=True)
assets=b/'assets';shutil.copytree(r/'build-native/map-scroll79/assets',assets,dirs_exist_ok=True)
for asset in ['dlgs/terran.grp','tileset/badlands.wpe','game/tfontgam.pcx','game/icons.grp']:
 for slot,archive in [(0,'STARDAT.MPQ'),(1,'BROODAT.MPQ'),(2,'patch_rt.mpq')]:
  target=assets/str(slot)/asset;target.parent.mkdir(parents=True,exist_ok=True)
  result=subprocess.run([str(r/'build-native/reign79/extract'),str(r/'build-native/reign79/core'/archive),asset,str(target)],capture_output=True)
  if result.returncode:target.unlink(missing_ok=True)

# Reuse the same drawing/input shims as the actual map-browser regression suite.
old=ast.parse((r/'tests/run_map_scroll79.py').read_text());collecting=False
for node in old.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='old' for t in node.targets):collecting=True
 if collecting:
  if isinstance(node,ast.For) and isinstance(node.target,ast.Tuple):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<input shim>','exec'))
sources['android/graphics/Canvas.java']=sources['android/graphics/Canvas.java'].replace('public void drawRect(', 'public void drawRoundRect(RectF r,float rx,float ry,Paint p){drawRect(r.left,r.top,r.right,r.bottom,p);}public void drawRect(')
sources['android/graphics/Paint.java']=sources['android/graphics/Paint.java'].replace('public class Paint{','public class Paint{public enum Style{STROKE,FILL}public void setStyle(Style style){}')
harness=sources.pop('org/openbw/androidtest/MapScroll79Test.java')
harness=harness[:harness.index(' public static void main(String[] args)')]
harness=harness.replace('public class MapScroll79Test','public class Controls80Test').replace(' MapScroll79Test(NativeGlue g)',' Controls80Test(NativeGlue g)')
harness=harness.replace('boolean pinchZoom,','boolean controlGroups=true,pinchZoom,')
harness=harness.replace('void pickNativeMap(){}','void pickNativeMap(){}void requestGamepadSettings(){}')
harness=harness.replace('float physicalScale(){return 1;}','float physicalScale(){return 3;}')
harness=harness.replace('void panCamera(float x,float y){}','double panX,panY;void panCamera(double x,double y){panX+=x;panY+=y;}')
harness=harness.replace('void cancelGesture(){gesture="";pressed=null;listVelocity=0;}','void cancelGesture(){gesture="";pressed=null;listVelocity=0;NativeBridge.command(5,0,0,0,0);}')
harness=harness.replace('String gesture="",scrollingList="",page="custom",modal="",hint="";','String gesture="",scrollingList="",page="game",modal="",hint="";')
harness=harness.replace('int selections,imports;','''int selections,imports,commandPercent=100,resourcePercent=100,logicalWidth=640,physicalWidth=1920,physicalHeight=1440;
 android.content.SharedPreferences prefs=new android.content.SharedPreferences();
 final GamepadControls gamepad=new GamepadControls();final HashMap<Integer,Integer>gamepadHeld=new HashMap<>();
 float padX=320,padY=200,padPointerX,padPointerY,padCameraX,padCameraY,padHatX,padHatY;
 boolean padActive,padPrecision,padNativeDrag,padTouchDrag;int padDevice=-1,padGroup=1;long padClickAt;
 String padDragPage="",padDragModal="";ArrayList<Runnable>queue=new ArrayList<>();int backs,menus;
 void enqueue(Runnable action){queue.add(action);}void flush(){while(!queue.isEmpty())queue.remove(0).run();}
 void back(){backs++;}void openMenu(){menus++;modal="menu";}
 float cameraBottom(float x){return 376;}boolean gamepadWorldOverride;
''')
# Existing touch coordinates are logical in this shim. Gamepad uses physical-coordinate events.
harness=harness.replace('float lx(float x){return x;}float ly(float y){return y;}','float lx(float x){return x/3;}float ly(float y){return y/3;}')
harness=harness.replace('void touch(int type,float x,float y,long time){touch(new MotionEvent(type,x,y,time));}','void touch(int type,float x,float y,long time){touch(new MotionEvent(type,x*3,y*3,time));}')
text=(src/'NativeSurface.java').read_text()
def production(name):
 m=re.search(r'^  (?:private )?(?:static )?(?:void|boolean|int|float) '+name+r'\(',text,re.M);assert m,name
 end=text.index('{',m.end())+1;depth=1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[m.start():end]
names=['controlGroup','controlGroupRows','drawControlGroups','reloadGamepadSettings','handleGamepadKey','handleGamepadMotion','gamepadDirection','activateGamepad','gamepadActionHeld','gamepadButton','gamepadWorld','gamepadClick','gamepadTouch','resetGamepadDrag','resetGamepad','advanceGamepad']
harness+='\n'.join(production(n) for n in names)
key_start=text.index('    if (!modal.isEmpty() || !page.equals("game")) return super.onKeyDown(key, event);')
key_end=text.index('    int chr = event.getUnicodeChar();',key_start)
harness+='\n boolean keyboardGroup(int key,KeyEvent event){\n'+text[key_start:key_end].replace('super.onKeyDown(key, event)','false')+'return false;}\n'

harness+='''
 void redrawGroups(){buttons.clear();drawControlGroups(new Canvas(Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888)));}
 static void key(Controls80Test h,int key,boolean down){check(h.handleGamepadKey(new KeyEvent(key,down?0:1,0)),"Controller key unhandled");h.flush();}
 public static void main(String[]args)throws Exception{
 NativeBridge.root=Paths.get(args[0]);NativeArt art=new NativeArt();NativeGlue glue=new NativeGlue(art,"glucustm","palnl",false);
 Controls80Test h=new Controls80Test(glue);h.hud.large=glue.large;h.hud.small=glue.small;h.activeGame=true;h.hud.minimap=new RectF(0,338,136,480);
 byte[] wpe=art.read("tileset/badlands.wpe");for(int i=0;i<256;i++)h.hud.palette[i]=Color.rgb(wpe[i*4]&255,wpe[i*4+1]&255,wpe[i*4+2]&255);
 h.hud.dialogGrp=art.read("dlgs/terran.grp");NativeArt.PCX colors=art.pcx("game/tfontgam.pcx",false,-1);
 h.hud.large=art.font("16",colors,h.hud.palette,1);h.hud.small=art.font("10",colors,h.hud.palette,0);
 byte[] icons=art.read("game/icons.grp");h.hud.resources[0]=NativeArt.grp(icons,0,h.hud.palette,true,false);h.hud.resources[1]=NativeArt.grp(icons,2,h.hud.palette,true,false);
 for(int i=0;i<3;i++)h.hud.supplyIcons[i]=NativeArt.grp(icons,4+i,h.hud.palette,true,false);
 // Regression: a 24px physical finger wobble inside the same small button must not lose the hold.
 h.redrawGroups();NativeBridge.selection=3;h.touch(0,20,14,1000);h.redrawGroups();h.touch(2,28,14,1300);h.touch(1,28,14,1600);
 check(NativeBridge.groups[1]==3,"Group hold lost to in-button jitter/redraw");
 NativeBridge.selection=7;h.redrawGroups();h.tap(20,14,2000);check(NativeBridge.selection==3,"Assigned group tap did not recall");
 h.redrawGroups();h.tap(52,14,3000);check(NativeBridge.groups[2]==3,"Empty group tap did not assign selection");
 NativeBridge.selection=6;h.redrawGroups();h.touch(0,20,14,4000);h.touch(3,20,14,4700);check(NativeBridge.groups[1]==3,"Cancelled hold changed group");
 h.redrawGroups();h.touch(0,20,14,5000);h.touch(2,70,14,5300);h.touch(1,20,14,5700);check(NativeBridge.groups[1]==3,"Moving outside then back assigned group");
 for(int command:new int[]{100,110,120})for(int resource:new int[]{100,125,150}){
  h.commandPercent=command;h.resourcePercent=resource;h.redrawGroups();check(h.buttons.size()==10,"Missing group buttons");
  for(Button bt:h.buttons){near(bt.rect.width(),28*command/100f,"Group width ignores command scaling");near(bt.rect.height(),30*command/100f,"Group height ignores command scaling");check(bt.rect.right<640-204*resource/100f,"Group overlaps resources");}
 }
 for(int[] size:new int[][]{{100,100},{120,150}}){
  h.commandPercent=size[0];h.resourcePercent=size[1];h.hud.resourceScale=size[1]/100f;
  Bitmap screen=Bitmap.createBitmap(640,110,Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(screen);Paint bg=new Paint();bg.setColor(0xff141d19);canvas.drawRect(0,0,640,110,bg);
  h.hud.drawResources(canvas,640);h.buttons.clear();h.drawControlGroups(canvas);
  ImageIO.write(screen.image,"png",Paths.get(args[1],"groups-"+size[0]+"-resources-"+size[1]+".png").toFile());
 }
 h.controls.controlGroups=false;h.redrawGroups();check(h.buttons.isEmpty(),"Hidden groups still receive input");
 h.controls.controlGroups=true;h.commandPercent=h.resourcePercent=100;
 // The actual keyboard group branch must preserve Ctrl, suppress repeat, and obey modals.
 NativeBridge.selection=9;KeyEvent keyboard=new KeyEvent(KeyEvent.KEYCODE_4,0,0);keyboard.ctrl=true;
 check(h.keyboardGroup(KeyEvent.KEYCODE_4,keyboard),"Ctrl+digit not handled");h.flush();check(NativeBridge.groups[4]==9,"Ctrl modifier lost while assigning");
 NativeBridge.selection=1;keyboard.ctrl=false;check(h.keyboardGroup(KeyEvent.KEYCODE_4,keyboard),"Digit recall not handled");h.flush();check(NativeBridge.selection==9,"Keyboard group recall failed");
 h.modal="menu";check(!h.keyboardGroup(KeyEvent.KEYCODE_4,keyboard),"Keyboard group bypassed modal");h.modal="";
 // Controller prefs, limits, and every physical binding survive a round-trip.
 GamepadControls c=new GamepadControls();c.pointerSpeed=2.5f;c.cameraSpeed=.5f;c.deadZone=.3f;c.swapSticks=true;
 for(int i=0;i<c.bindings.length;i++)c.bindings[i]=(i+3)%GamepadControls.ACTION_LABELS.length;c.save(h.prefs);
 GamepadControls loaded=new GamepadControls();loaded.load(h.prefs);check(Arrays.equals(c.bindings,loaded.bindings),"Bindings did not persist");
 near(loaded.pointerSpeed,2.5f,"Pointer speed persistence");near(loaded.deadZone,.3f,"Dead zone persistence");check(loaded.swapSticks,"Swap sticks persistence");
 for(float v:new float[]{-.18f,-.1f,0,.1f,.18f,Float.NaN,Float.POSITIVE_INFINITY})near(GamepadControls.axis(v,.18f),0,"Stick drift/dead zone");
 near(GamepadControls.axis(-1,.18f),-1,"Negative full axis");near(GamepadControls.axis(1,.18f),1,"Positive full axis");
 check(GamepadControls.nextGroup(9,1)==0&&GamepadControls.nextGroup(0,-1)==9,"Group wrap");
 // A must act as a real left mouse button, not touch contextual attack/move.
 h.buttons.clear();NativeBridge.calls.clear();key(h,KeyEvent.KEYCODE_BUTTON_A,true);
 check(h.padNativeDrag&&NativeBridge.matches(1,1,1)==1,"A did not press left mouse in world");
 h.padPointerX=1;h.advanceGamepad(100);check(h.padX>320,"Stick did not move pointer during held selection");
 key(h,KeyEvent.KEYCODE_BUTTON_A,false);check(!h.padNativeDrag&&NativeBridge.matches(1,0,1)==1,"A release did not finish box selection");
 check(NativeBridge.count(4)==0,"Controller click used touch contextual orders");
 NativeBridge.calls.clear();key(h,KeyEvent.KEYCODE_BUTTON_B,true);key(h,KeyEvent.KEYCODE_BUTTON_B,false);
 check(NativeBridge.matches(1,1,3)==1&&NativeBridge.matches(1,0,3)==1,"B did not issue one right click");
 // Digital key plus trigger axis reports are one press, including staggered releases.
 h.padGroup=1;key(h,KeyEvent.KEYCODE_BUTTON_R2,true);h.gamepadButton(KeyEvent.KEYCODE_BUTTON_R2,true,2);
 check(h.padGroup==2,"Duplicate analog trigger press advanced twice");key(h,KeyEvent.KEYCODE_BUTTON_R2,false);
 h.gamepadButton(KeyEvent.KEYCODE_BUTTON_R2,false,2);h.gamepadButton(KeyEvent.KEYCODE_BUTTON_R2,true,2);check(h.padGroup==3,"Trigger release did not rearm");h.gamepadButton(KeyEvent.KEYCODE_BUTTON_R2,false,2);
 // Rebinding updates real action dispatch; repeated key events do not double invoke.
 h.gamepad.bindings[0]=GamepadControls.STOP;NativeBridge.calls.clear();key(h,KeyEvent.KEYCODE_BUTTON_A,true);key(h,KeyEvent.KEYCODE_BUTTON_A,false);
 check(NativeBridge.matches(2,'s',0)==1,"A rebind did not execute Stop");
 h.gamepad.reset();h.modal="menu";NativeBridge.calls.clear();key(h,KeyEvent.KEYCODE_BUTTON_B,true);key(h,KeyEvent.KEYCODE_BUTTON_B,false);
 check(NativeBridge.count(1)==0,"Controller ordered units through modal menu");
 // A over UI must use the same button action, and holding a group must assign.
 h.modal="";h.padX=20;h.padY=14;h.redrawGroups();NativeBridge.selection=8;android.os.SystemClock.now=10000;
 key(h,KeyEvent.KEYCODE_BUTTON_A,true);check(h.padTouchDrag,"A over group bypassed UI");android.os.SystemClock.now=10600;
 key(h,KeyEvent.KEYCODE_BUTTON_A,false);check(NativeBridge.groups[1]==8,"Controller hold could not assign group");
 // Reset, focus loss and disconnect cancel input; no stale mouse-button/camera state.
 h.buttons.clear();h.padX=320;h.padY=200;key(h,KeyEvent.KEYCODE_BUTTON_A,true);h.padCameraX=1;h.resetGamepad();
 check(!h.padNativeDrag&&!h.padActive&&h.gamepadHeld.isEmpty()&&h.padCameraX==0,"Reset left held input");check(NativeBridge.lastOp==0,"Reset failed to park cursor");
 key(h,KeyEvent.KEYCODE_BUTTON_A,true);InputDevice.connected=false;h.advanceGamepad(16);check(!h.padActive&&!h.padNativeDrag,"Disconnected controller kept dragging");InputDevice.connected=true;
 // D-pad events can advertise SOURCE_DPAD while the device itself is a controller.
 KeyEvent dpad=new KeyEvent(KeyEvent.KEYCODE_DPAD_RIGHT,0,0);dpad.source=513;
 check(h.handleGamepadKey(dpad),"Controller D-pad source ignored");h.flush();check(h.gamepadHeld.containsKey(KeyEvent.KEYCODE_DPAD_RIGHT),"D-pad press lost");
 key(h,KeyEvent.KEYCODE_DPAD_RIGHT,false);
 // Android motion source filtering, stick swap, camera pan, hat pan, bounds.
 MotionEvent motion=new MotionEvent(2,0,0,20000);motion.axes.put(MotionEvent.AXIS_X,1f);motion.axes.put(MotionEvent.AXIS_RZ,-1f);
 check(h.handleGamepadMotion(motion),"Joystick motion ignored");h.flush();near(h.padPointerX,1,"Left stick pointer mapping");near(h.padCameraY,-1,"Right stick camera mapping");
 h.padX=639;h.padY=0;h.advanceGamepad(100);near(h.padX,639,"Pointer left viewport");check(h.panY<0,"Right stick did not pan camera");
 h.gamepad.swapSticks=true;check(h.handleGamepadMotion(motion),"Swapped motion ignored");h.flush();near(h.padPointerY,-1,"Swap did not map right stick to pointer");near(h.padCameraX,1,"Swap did not map left stick to camera");
 motion.source=2;check(!h.handleGamepadMotion(motion),"Touchscreen misidentified as gamepad");
 h.gamepad.enabled=false;check(!h.handleGamepadKey(new KeyEvent(KeyEvent.KEYCODE_BUTTON_A,0,0)),"Disabled controller consumed key");
 System.out.println("PASS "+checks+" production group/controller checks: redraw and touch jitter, assign/recall/cancel, UI scale/resource overlap, preferences, sticks/deadzone/swap, left-drag/right-click, HUD routing, rebinding, duplicate trigger lifecycle, modal isolation, reset and disconnect");
 }
}
class NativeMaps{static String label(File f){return f==null?"Practice map":f.getName();}}
'''
sources['org/openbw/androidtest/Controls80Test.java']=harness
sources['android/content/SharedPreferences.java']='''package android.content;import java.util.*;public class SharedPreferences{HashMap<String,String>data=new HashMap<>();public String getString(String k,String d){return data.getOrDefault(k,d);}public Editor edit(){return new Editor();}public class Editor{public Editor putString(String k,String v){data.put(k,v);return this;}public void apply(){}}}'''
sources['android/os/SystemClock.java']='package android.os;public class SystemClock{public static long now;public static long uptimeMillis(){return now;}}'
# Constants come from the exact Android SDK used by the APK, not a private mapping.
constants=subprocess.check_output(['javap','-constants','-cp',str(r/'.tools/android-35/android.jar'),'android.view.KeyEvent'],text=True)
keys='\n'.join('public static final int '+m.group(1)+'='+m.group(2)+';' for m in re.finditer(r'public static final int (KEYCODE_\w+|ACTION_DOWN|ACTION_UP) = (\d+);',constants))
sources['android/view/KeyEvent.java']='''package android.view;public class KeyEvent{'''+keys+'''
 public boolean ctrl;public boolean isCtrlPressed(){return ctrl;}int key,action,repeat;public KeyEvent(int k,int a,int r){key=k;action=a;repeat=r;}public int getKeyCode(){return key;}public int getAction(){return action;}public int getRepeatCount(){return repeat;}public int getDeviceId(){return 1;}public InputDevice getDevice(){return InputDevice.getDevice(1);}public int source=InputDevice.SOURCE_GAMEPAD;public int getSource(){return source;}}'''
constants=subprocess.check_output(['javap','-constants','-cp',str(r/'.tools/android-35/android.jar'),'android.view.MotionEvent'],text=True)
axes='\n'.join('public static final int '+m.group(1)+'='+m.group(2)+';' for m in re.finditer(r'public static final int (AXIS_\w+) = (\d+);',constants))
sources['android/view/MotionEvent.java']=sources['android/view/MotionEvent.java'].replace(' int action;',axes+'''public java.util.Map<Integer,Float>axes=new java.util.HashMap<>();public int source=InputDevice.SOURCE_JOYSTICK;
 public static MotionEvent obtain(MotionEvent e){MotionEvent r=new MotionEvent(e.action,e.x,e.y,e.time);r.axes.putAll(e.axes);r.source=e.source;return r;}
 public static MotionEvent obtain(long start,long end,int action,float x,float y,int flags){return new MotionEvent(action,x,y,end);}
 public void recycle(){}public int getDeviceId(){return 1;}public InputDevice getDevice(){return InputDevice.getDevice(1);}
 public int getSource(){return source;}public float getAxisValue(int a){return axes.getOrDefault(a,0f);}
 int action;''')
sources['android/view/InputDevice.java']='''package android.view;public class InputDevice{public static final int SOURCE_GAMEPAD=1025,SOURCE_JOYSTICK=16777232;public static boolean connected=true;public int getSources(){return SOURCE_GAMEPAD|SOURCE_JOYSTICK;}public static InputDevice getDevice(int id){return connected?new InputDevice():null;}public MotionRange getMotionRange(int axis,int source){return new MotionRange();}public static class MotionRange{public float getFlat(){return .1f;}}}'''
hud_source=(src/'NativeHud.java').read_text()
def hud_method(name):
 m=re.search(r'^  (?:static )?(?:void|Bitmap) '+name+r'\(',hud_source,re.M);assert m,name
 end=hud_source.index('{',m.end())+1;depth=1
 while depth:
  if hud_source[end]=='{':depth+=1
  elif hud_source[end]=='}':depth-=1
  end+=1
 return hud_source[m.start():end]
sources['org/openbw/androidtest/NativeHud.java']=sources['org/openbw/androidtest/NativeHud.java'].replace(' static final int WORLD_BOTTOM=376;',
 ' NativeArt.Font large,small;byte[]dialogGrp;int[]palette=new int[256];Map<String,Bitmap>panels=new HashMap<>();float resourceScale=1;Bitmap[]resources=new Bitmap[3],supplyIcons=new Bitmap[3];\n'+
 '\n'.join(hud_method(n) for n in ['panel','image','drawResources'])+'\n static final int WORLD_BOTTOM=376;')

bridge=sources['org/openbw/androidtest/NativeBridge.java']
bridge=bridge.replace('static int commands;static void command(int a,int b,int c,int d,int e){commands++;}static int value(int a,int b){return 0;}', '''static int commands,lastOp,selection;static int[]groups=new int[10];static ArrayList<int[]>calls=new ArrayList<>();
 static void command(int a,int b,int c,int d,int e){commands++;lastOp=a;calls.add(new int[]{a,b,c,d,e});if(a==25){if(c==1)groups[b]=selection;else selection=groups[b];}}
 static String text(int id){return "800\\t600\\t24\\t60\\t2\\t0\\t0\\t24\\t60";}static int value(int a,int b){return a==21?groups[b]:0;}static int matches(int op,int a,int b){int n=0;for(int[]x:calls)if(x[0]==op&&x[1]==a&&x[2]==b)n++;return n;}
 static int count(int op){int n=0;for(int[]x:calls)if(x[0]==op)n++;return n;}''')
sources['org/openbw/androidtest/NativeBridge.java']=bridge
for name,text in sources.items():
 target=b/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
real=[src/n for n in ['GamepadControls.java','NativeArt.java','NativeGlue.java','NativeResults.java','CommandHint.java','MenuLabels.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
jar=r/'build-native/json-20240303.jar'
subprocess.run(['javac','-cp',str(jar),'-d',str(b/'classes'),*[str(b/n) for n in sources],*map(str,real)],check=True)
result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.Controls80Test',str(assets),str(b)],capture_output=True,text=True)
print(result.stdout+result.stderr,end='');result.check_returncode()
files=[src/'NativeSurface.java',src/'GamepadControls.java',src/'GamepadSettings.java',src/'NativeBridge.java',Path(__file__)]
(r/'validation/gamepad-v80.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'methods':names+['touch'],'result':result.stdout.strip(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},indent=2)+'\n')

#!/usr/bin/env python3
"""Execute production controller/group input methods through bounded Android/Canvas shims.
No physical controller or Android device is simulated; tests verify routing and lifecycle.
"""
from pathlib import Path
import ast,hashlib,json,os,re,subprocess,shutil
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest'
jdk=r/'.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64/bin'
if (jdk/'javac').is_file():os.environ['PATH']=str(jdk)+os.pathsep+os.environ['PATH']
b=r/'build-native/gamepad81';b.mkdir(parents=True,exist_ok=True)
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
sources['android/graphics/Paint.java']=sources['android/graphics/Paint.java'].replace('public class Paint{','public class Paint{public enum Style{STROKE,FILL}public Style style=Style.FILL;public float stroke=1;public void setStyle(Style s){style=s;}public void setStrokeWidth(float w){stroke=w;}')
sources['android/graphics/Typeface.java']=sources['android/graphics/Typeface.java'].replace('DEFAULT=new Typeface(),','DEFAULT=new Typeface(),SANS_SERIF=new Typeface(),')
sources['android/graphics/Canvas.java']=sources['android/graphics/Canvas.java'].replace('public void drawRect(', 'public void drawLine(float x1,float y1,float x2,float y2,Paint p){g.setColor(new java.awt.Color(p.color,true));g.setStroke(new BasicStroke(p.stroke));g.draw(new Line2D.Float(x1,y1,x2,y2));}public void drawRect(').replace('g.fill(new Rectangle2D.Float(l,t,r-l,b-t));','if(p.style==Paint.Style.STROKE){g.setStroke(new BasicStroke(p.stroke));g.draw(new Rectangle2D.Float(l,t,r-l,b-t));}else g.fill(new Rectangle2D.Float(l,t,r-l,b-t));')
harness=sources.pop('org/openbw/androidtest/MapScroll79Test.java')
harness=harness[:harness.index(' public static void main(String[] args)')]
harness=harness.replace('public class MapScroll79Test','public class Controls81Test').replace(' MapScroll79Test(NativeGlue g)',' Controls81Test(NativeGlue g)')
harness=harness.replace('boolean pinchZoom,','boolean controlGroups=true,pinchZoom,')
harness=harness.replace('void pickNativeMap(){}','void pickNativeMap(){}void requestGamepadSettings(){}int appOptions;void requestAppOptions(){appOptions++;}')
harness=harness.replace('float physicalScale(){return 1;}','float physicalScale(){return 3;}')
harness=harness.replace('void panCamera(float x,float y){}','double panX,panY;void panCamera(double x,double y){panX+=x;panY+=y;}')
harness=harness.replace('void cancelGesture(){gesture="";pressed=null;listVelocity=0;}','void cancelGesture(){gesture="";pressed=null;listVelocity=0;NativeBridge.command(5,0,0,0,0);}')
harness=harness.replace('String gesture="",scrollingList="",page="custom",modal="",hint="";','String gesture="",scrollingList="",page="game",modal="",hint="";')
harness=harness.replace('boolean enabled,vertical,placementButton,controlGroup;', 'boolean enabled,vertical,placementButton,controlGroup;int key;String page,modal;')
harness=harness.replace('int selections,imports;','''int selections,imports,commandPercent=100,resourcePercent=100,logicalWidth=640,physicalWidth=1920,physicalHeight=1440;
 android.content.SharedPreferences prefs=new android.content.SharedPreferences();
 final DesktopSettings desktopSettings=new DesktopSettings();final GamepadControls gamepad=new GamepadControls();final HashMap<Integer,Integer>gamepadHeld=new HashMap<>();
 float padX=320,padY=200,padPointerX,padPointerY,padCameraX,padCameraY,padHatX,padHatY;
 boolean padActive,padPrecision,padNativeDrag,padTouchDrag;int padDevice=-1,padGroup=1;long padClickAt;
 String padDragPage="",padDragModal="",gamepadReturnModal="";boolean gamepadReturnAppOptions;int gamepadBinding;Paint paint=new Paint();ArrayList<Runnable>queue=new ArrayList<>();int backs,menus,suspends;void suspend(){suspends++;}
 void enqueue(Runnable action){queue.add(action);}void flush(){while(!queue.isEmpty())queue.remove(0).run();}
 void back(){backs++;}void openMenu(){menus++;modal="menu";}
 float cameraBottom(float x){return 376;}boolean gamepadWorldOverride;
 boolean replayGame;
 static class MenuCaption{final Button button;final MenuHotkeys.Entry entry;final boolean highlight;final java.util.function.Consumer<String>draw;MenuCaption(Button b,MenuHotkeys.Entry e,boolean h,java.util.function.Consumer<String>d){button=b;entry=e;highlight=h;draw=d;}}
 final MenuHotkeys menuHotkeys=new MenuHotkeys(),backgroundMenuHotkeys=new MenuHotkeys();boolean menuBehindModal;final ArrayList<MenuCaption>menuCaptions=new ArrayList<>();
''')
# Existing touch coordinates are logical in this shim. Gamepad uses physical-coordinate events.
harness=harness.replace('float lx(float x){return x;}float ly(float y){return y;}','float lx(float x){return x/3;}float ly(float y){return y/3;}')
harness=harness.replace('void touch(int type,float x,float y,long time){touch(new MotionEvent(type,x,y,time));}','void touch(int type,float x,float y,long time){touch(new MotionEvent(type,x*3,y*3,time));}')
text=(src/'NativeSurface.java').read_text()
def production(name):
 m=re.search(r'^  (?:private )?(?:static )?(?:void|boolean|int|float|NativeArt.Font) '+name+r'\(',text,re.M);assert m,name
 end=text.index('{',m.end())+1;depth=1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[m.start():end]
names=['font','text','panel','body','fallback','uiLine','queueMenuButton','queueMenuButtonVisual','flushMenuButtons','fallbackMenu','openGamepadSettings','gamepadSettingsBack','changeGamepad','gamepadLine','gamepadOption','gamepadToggle','gamepadSlider','drawGamepadSettings','controlGroupScale','controlGroup','controlGroupRows','drawControlGroups','reloadGamepadSettings','handleGamepadKey','handleGamepadMotion','gamepadDirection','activateGamepad','gamepadActionHeld','gamepadButton','gamepadWorld','gamepadClick','gamepadTouch','resetGamepadDrag','resetGamepad','advanceGamepad']
harness+='\n'.join(production(n) for n in names)
# Physical keyboard routing moved to the production event suite in
# run_desktop_input11.py; do not emulate the old instantaneous group shortcut.
harness+='\n void resetDesktop(boolean hide){} boolean drawDesktopSettings(Canvas c){return false;}\n'

harness+='''
 void redrawGroups(){buttons.clear();drawControlGroups(new Canvas(Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888)));}
 static void key(Controls81Test h,int key,boolean down){check(h.handleGamepadKey(new KeyEvent(key,down?0:1,0)),"Controller key unhandled");h.flush();}

 Bitmap redrawSettings(){buttons.clear();menuCaptions.clear();Bitmap b=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);glue.draw(c,1000);check(drawGamepadSettings(c),"Settings modal not handled");flushMenuButtons();return b;}
 static void at(Controls81Test h,int index){h.buttons.get(index).action.run();h.flush();}
 static void menuChecks(Controls81Test h,String[]args)throws Exception{
  h.gamepad.reset();h.gamepad.save(h.prefs);h.modal="controls";h.page="game";
  h.padCameraX=1;h.padNativeDrag=true;h.openGamepadSettings();h.flush();
  check(h.modal.equals("gamepad")&&!h.padActive&&!h.padNativeDrag&&h.padCameraX==0,"Opening settings retained game input");
  h.redrawSettings();check(h.buttons.size()==9,"Main gamepad sheet lacks controls");
  // Actual production slider handlers preserve the full old range and save values.
  h.buttons.get(2).slider.accept(0f);near(h.gamepad.pointerSpeed,.25f,"Pointer minimum");
  h.buttons.get(2).slider.accept(1f);near(h.gamepad.pointerSpeed,3f,"Pointer maximum");
  h.buttons.get(3).slider.accept(.6f);near(h.gamepad.cameraSpeed,1.9f,"Camera slider range");
  h.buttons.get(4).slider.accept(1f);near(h.gamepad.deadZone,.5f,"Dead zone maximum");
  h.buttons.get(4).slider.accept(0f);near(h.gamepad.deadZone,.05f,"Dead zone minimum");
  GamepadControls saved=new GamepadControls();saved.load(h.prefs);near(saved.pointerSpeed,3,"Slider persistence");
  h.gamepad.reset();h.gamepad.save(h.prefs);h.redrawSettings();
  h.padX=380;h.padY=212;android.os.SystemClock.now=22000;
  key(h,KeyEvent.KEYCODE_BUTTON_A,true);check(h.padTouchDrag,"Gamepad slider press lost drag");
  float oldSpeed=h.gamepad.cameraSpeed;h.padPointerX=.5f;h.advanceGamepad(30);
  check(h.padTouchDrag&&h.gamepad.cameraSpeed>oldSpeed,"Changing slider resets held controller drag");
  key(h,KeyEvent.KEYCODE_BUTTON_A,false);h.padPointerX=0;
  h.gamepad.pointerSpeed=3;h.gamepad.save(h.prefs);
  h.redrawSettings();at(h,1);check(h.gamepad.swapSticks,"Native swap toggle did not change preference");
  h.redrawSettings();at(h,0);check(!h.gamepad.enabled,"Enable toggle did not disable");
  h.redrawSettings();at(h,0);check(h.gamepad.enabled,"Touch cannot re-enable gamepad");
  for(int binding=0;binding<GamepadControls.BUTTONS.length;binding++){
   h.modal="gamepad-bindings";h.redrawSettings();check(h.buttons.size()==13,"Not all twelve bindings visible");at(h,binding);
   check(h.modal.equals("gamepad-action")&&h.gamepadBinding==binding,"Binding opens wrong chooser");
   for(int action=0;action<GamepadControls.ACTION_LABELS.length;action++){
    h.modal="gamepad-action";h.redrawSettings();check(h.buttons.size()==17,"Action chooser is incomplete");at(h,action);
    check(h.gamepad.bindings[binding]==action&&h.modal.equals("gamepad-bindings"),"Action assignment did not persist/return");
    saved.load(h.prefs);check(saved.bindings[binding]==action,"Binding lost on reload");
   }
  }
  h.modal="gamepad-action";h.gamepadSettingsBack();check(h.modal.equals("gamepad-bindings"),"Action back skips binding list");
  h.gamepadSettingsBack();check(h.modal.equals("gamepad"),"Binding back does not return to settings");
  h.modal="gamepad-reset";h.redrawSettings();at(h,1);check(h.gamepad.pointerSpeed==3&&h.modal.equals("gamepad"),"Cancel reset changed preferences");
  h.modal="gamepad-reset";h.redrawSettings();at(h,0);near(h.gamepad.pointerSpeed,1,"Reset pointer speed");check(h.gamepad.bindings[0]==GamepadControls.CLICK,"Reset bindings");
  h.gamepadSettingsBack();check(h.modal.equals("controls")&&h.page.equals("game"),"In-game settings did not return to Controls");
  h.modal="menu";h.openGamepadSettings();h.flush();h.gamepadSettingsBack();
  check(h.modal.equals("menu")&&h.activity.appOptions==0&&h.suspends==0&&h.activeGame,"In-game return unexpectedly opens App Options");
  h.modal="";h.page="main";h.openGamepadSettings();h.flush();
  check(h.modal.isEmpty()&&h.page.equals("main")&&h.activity.appOptions==0,"Main-menu can still open gamepad settings");
  // Fixed-size sheets expose every choice without scrolling or off-screen hit boxes.
  PortText.load(Files.newInputStream(Paths.get(args[2])));
  for(String lang:new String[]{"en","ru","de","es","fr"})for(String page:new String[]{"main","game"}){
   PortText.select(lang);h.page=page;
   for(String modal:new String[]{"gamepad","gamepad-bindings","gamepad-action","gamepad-help","gamepad-reset"}){
    h.modal=modal;Bitmap shot=h.redrawSettings();
    for(Button bt:h.buttons){check(bt.rect.left>=100&&bt.rect.right<=540&&bt.rect.top>=40&&bt.rect.bottom<=440,"Settings hit target leaves panel");}
    for(int i=0;i<h.buttons.size();i++)for(int j=i+1;j<h.buttons.size();j++){
     RectF a=h.buttons.get(i).rect,b=h.buttons.get(j).rect;
     check(a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top,"Settings hit targets overlap");
    }
    ImageIO.write(shot.image,"png",Paths.get(args[1],"settings-"+page+"-"+modal+"-"+lang+".png").toFile());
   }
  }
  PortText.select("en");h.modal="";h.page="game";
  check(GamepadSettings.sliderPercent(Float.NaN,25,300)==25,"Nonfinite slider");
 }
 public static void main(String[]args)throws Exception{
 NativeBridge.root=Paths.get(args[0]);NativeArt art=new NativeArt();NativeGlue glue=new NativeGlue(art,"glucustm","palnl",false);
 Controls81Test h=new Controls81Test(glue);h.hud.large=glue.large;h.hud.small=glue.small;h.activeGame=true;h.hud.minimap=new RectF(0,338,136,480);
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
  for(Button bt:h.buttons){near(bt.rect.width(),28*1.2f*command/100f,"Group width ignores command scaling");near(bt.rect.height(),30*1.2f*command/100f,"Group height ignores command scaling");check(bt.rect.right<640-204*resource/100f,"Group overlaps resources");}
 }
 for(int[] size:new int[][]{{100,100},{120,150}}){
  h.commandPercent=size[0];h.resourcePercent=size[1];h.hud.resourceScale=size[1]/100f;
  Bitmap screen=Bitmap.createBitmap(640,110,Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(screen);Paint bg=new Paint();bg.setColor(0xff141d19);canvas.drawRect(0,0,640,110,bg);
  h.hud.drawResources(canvas,640);h.buttons.clear();h.drawControlGroups(canvas);
  ImageIO.write(screen.image,"png",Paths.get(args[1],"groups-"+size[0]+"-resources-"+size[1]+".png").toFile());
 }
 // The timer and network overlay must begin below both rows of enlarged groups.
 for(int command:new int[]{100,110,120})for(int resource:new int[]{100,125,150}){
  h.commandPercent=command;h.resourcePercent=resource;h.redrawGroups();
  float bottom=0;for(Button bt:h.buttons)bottom=Math.max(bottom,bt.rect.bottom);
  float timer=Math.round(6+(h.controlGroupRows()*32-2)*h.controlGroupScale());
  float network=Math.max(70,6+(h.controlGroupRows()*32-2)*h.controlGroupScale());
  check(timer>=bottom+3,"Timer overlaps enlarged groups");check(network>=bottom+3,"Network overlay overlaps enlarged groups");
 }
 h.controls.controlGroups=false;h.redrawGroups();check(h.buttons.isEmpty(),"Hidden groups still receive input");
 h.controls.controlGroups=true;h.commandPercent=h.resourcePercent=100;
 // Keyboard groups are covered by run_desktop_input11.py and native-desktop11.
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
 menuChecks(h,args);
 System.out.println("PASS "+checks+" production group/controller checks: redraw and touch jitter, assign/recall/cancel, UI scale/resource overlap, preferences, sticks/deadzone/swap, left-drag/right-click, HUD routing, rebinding, duplicate trigger lifecycle, modal isolation, reset and disconnect, native settings and all bindings, five languages, in-game-only settings access");
 }
}
class NativeMaps{static String label(File f){return f==null?"Practice map":f.getName();}}
'''
sources['org/openbw/androidtest/Controls81Test.java']=harness
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
sources['org/openbw/androidtest/NativeHud.java']=sources['org/openbw/androidtest/NativeHud.java'].replace('class NativeHud {','class NativeHud {boolean gridHotkeys;String hint(Hit h){return h.fields==null?h.help:h.fields[1];}')
sources['org/openbw/androidtest/NativeHud.java']=sources['org/openbw/androidtest/NativeHud.java'].replace('boolean more;', 'boolean more,terrainToggle;')
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
# Desktop/controller settings intentionally have no App Options entry anymore.
activity_source=(src/'MainActivity.java').read_text()
for callback in ['requestDesktopSettings','requestGamepadSettings','requestControlSettings']:
 assert callback not in activity_source, 'Removed App Options control route still present: '+callback
for name,text in sources.items():
 target=b/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
real=[src/n for n in ['DesktopSettings.java','GamepadControls.java','GamepadSettings.java','NativeArt.java','NativeGlue.java','NativeResults.java','CommandHint.java','MenuLabels.java','MenuHotkeys.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
jar=r/'build-native/json-20240303.jar'
subprocess.run(['javac','-cp',str(jar),'-d',str(b/'classes'),*[str(b/n) for n in sources],*map(str,real)],check=True)
result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.Controls81Test',str(assets),str(b),str(r/'app/src/main/assets/native/ui-languages.tsv')],capture_output=True,text=True)
print(result.stdout+result.stderr,end='');result.check_returncode()
files=[src/'MainActivity.java',r/'app/src/main/assets/native/ui-languages.tsv',src/'NativeSurface.java',src/'NativeBridge.java',src/'NativeHud.java',*real,Path(__file__)]
(r/'validation/gamepad-v81.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'methods':names+['touch'],'result':result.stdout.strip(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},indent=2)+'\n')

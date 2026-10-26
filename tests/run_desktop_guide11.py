#!/usr/bin/env python3
"""Check the combined desktop settings/help screen with original fonts.

Uses production font wrapping with the established desktop Canvas shim. This is
a text/layout check, not a physical Android mouse or keyboard integration test.
"""
from pathlib import Path
import ast, hashlib, json, os, re, shutil, subprocess

r = Path(__file__).resolve().parents[1]
src = r / 'app/src/main/java/org/openbw/androidtest'
b = r / 'build-native/desktop-guide11'
b.mkdir(parents=True, exist_ok=True)
fixtures = r / 'build-native/gamepad81/assets'
assert fixtures.is_dir(), 'Prepare the gamepad81 artwork fixtures first'
assets = b / 'assets'
shutil.copytree(fixtures, assets, dirs_exist_ok=True)
# The installed fonts are encrypted; without local installation metadata the
# renderer would silently use the styled system font instead of these fixtures.
metadata = assets / '0/font/font.gid'
subprocess.run([str(r / 'build-native/reign79/extract'),str(r / 'build-native/reign79/core/STARDAT.MPQ'),'font/font.gid',str(metadata)],check=True,stdout=subprocess.DEVNULL)
for race in ['zerg', 'protoss']:
    target = assets / '0/dlgs' / (race + '.grp')
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(r / 'build-native/reign79/extract'),str(r / 'build-native/reign79/core/STARDAT.MPQ'),'dlgs/' + race + '.grp',str(target)],check=True,stdout=subprocess.DEVNULL)
jdk = r / '.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64/bin'
if (jdk / 'javac').is_file():
    os.environ['PATH'] = str(jdk) + os.pathsep + os.environ['PATH']

# Reuse Android drawing stubs only, without running unrelated controller tests.
context = globals()
tree = ast.parse((r / 'tests/run_gamepad81.py').read_text())
active = False
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'old' for t in node.targets):
        active = True
    if active:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'harness' for t in node.targets):
            break
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<desktop guide Canvas shim>', 'exec'), context)
sources.pop('org/openbw/androidtest/MapScroll79Test.java', None)
surface = (src / 'NativeSurface.java').read_text()
def production(name, text=surface):
    match = re.search(r'^  (?:private |public |protected )?(?:static )?[\w.<>]+ ' + name + r'\(', text, re.M)
    assert match, name
    end = text.index('{', match.end()) + 1
    depth = 1
    while depth:
        if text[end] == '{': depth += 1
        elif text[end] == '}': depth -= 1
        end += 1
    return text[match.start():end]
sources['org/openbw/androidtest/NativeHud.java'] = '''package org.openbw.androidtest;
import android.graphics.*;import java.util.*;
class NativeHud {
 boolean gridHotkeys;NativeArt.Font small,large;byte[]dialogGrp;int[]palette;Map<String,Bitmap>panels=new HashMap<>();
 NativeHud(NativeArt art,int race){byte[]wpe=art.read("tileset/badlands.wpe");palette=new int[256];
  for(int i=0;i<256;i++)palette[i]=Color.rgb(wpe[i*4]&255,wpe[i*4+1]&255,wpe[i*4+2]&255);
  NativeArt.PCX colors=art.pcx("game/tfontgam.pcx",false,-1);small=art.font("10",colors,palette,0);large=art.font("16",colors,palette,1);
  dialogGrp=art.read("dlgs/"+new String[]{"zerg","terran","protoss"}[race]+".grp");}
 static int number(String[]f,int i,int d){try{return Integer.parseInt(f[i]);}catch(Exception e){return d;}}
''' + production('panel', (src / 'NativeHud.java').read_text()) + '\n}'
sources['org/openbw/androidtest/NativeResults.java'] = 'package org.openbw.androidtest;class NativeResults{\n' + production('fit', (src / 'NativeResults.java').read_text()) + '\n}'
sources['org/openbw/androidtest/DesktopGuide11Test.java'] = r'''package org.openbw.androidtest;
import java.nio.file.*;import java.util.*;import android.graphics.*;import javax.imageio.ImageIO;
public class DesktopGuide11Test {
 static int checks, screens;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 public static void main(String[]args)throws Exception {
  NativeBridge.root=Paths.get(args[0]);Path output=Paths.get(args[1]);
  PortText.load(Files.newInputStream(Paths.get(args[2])));NativeArt art=new NativeArt();
  NativeArt.PCX background=art.pcx("glue/palnl/backgnd.pcx",false,-1),tint=art.pcx("glue/palnl/tfont.pcx",false,-1);
  NativeArt.Font menu=art.font("10",tint,background.palette,1);
  check(!menu.fallback,"Original menu font fixture missing");
  byte[] wpe=art.read("tileset/badlands.wpe");int[] palette=new int[256];
  for(int i=0;i<256;i++)palette[i]=Color.rgb(wpe[i*4]&255,wpe[i*4+1]&255,wpe[i*4+2]&255);
  NativeArt.Font hud=art.font("10",art.pcx("game/tfontgam.pcx",false,-1),palette,0);
  for(String language:new String[]{"en","ru","de","es","fr"}) {
   PortText.select(language);
   for(String label:new String[]{"Mouse & keyboard","Mouse","Keyboard","Command hotkeys","Grid (QWE/ASD/ZXC)","Mouse edge scrolling","Mouse wheel zoom","Middle-button camera drag","Arrow-key camera","Camera speed"})
    check(language.equals("en")||!PortText.text(label).equals(label),"Missing title translation: "+language+" / "+label);
   for(int page=0;page<1;page++) {
    String text="Mouse\n"+DesktopGuide.MOUSE_GUIDE+"\nKeyboard\n"+DesktopGuide.KEYBOARD_GUIDE;
    check(!DesktopGuide.MOUSE_GUIDE.contains("Arrow"),"Mouse help describes keyboard arrows");
    check(DesktopGuide.KEYBOARD_GUIDE.contains("Arrow keys")&&DesktopGuide.KEYBOARD_GUIDE.contains("QWE / ASD / ZXC"),"Keyboard help omits arrows or grid hotkeys");
    for(String line:text.split("\n"))check(language.equals("en")||!PortText.text(line).equals(line),"Missing help translation: "+language+" / "+line);
    for(int style=0;style<2;style++) {
     NativeArt.Font font=style==0?menu:hud;List<String> lines=font.lines(text,560);
     int height=lines.size()*Math.max(16,font.height+1);
     check(height<=228,"Help clips vertically: "+language+" page "+page+" style "+style+" height="+height);
     for(String line:lines)check(font.measure(line)<=560,"Help exceeds width: "+language+" / "+line);
     Bitmap image=Bitmap.createBitmap(592,260,Bitmap.Config.ARGB_8888);
     Canvas c=new Canvas(image);Paint p=new Paint();p.setColor(0xff080b0b);c.drawRect(0,0,592,260,p);
     font.draw(c,text,16,16,560,0,2,16);
     ImageIO.write(image.image,"png",output.resolve(language+"-"+(page==0?"mouse":"keyboard")+"-"+(style==0?"menu":"game")+".png").toFile());
     screens++;System.out.println(language+" "+page+" "+style+": "+lines.size()+" lines / "+height+" px");
    }
   }
  }
  System.out.println("PASS "+checks+" translated guide checks; "+screens+" original-font renderings; all fit 560 x 228");
 }
}'''
settings = '''package org.openbw.androidtest;
import java.nio.file.*;import java.util.*;import android.graphics.*;import javax.imageio.ImageIO;
public class DesktopSettings11Test {
 static int checks,screens;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static class Button {RectF rect;Runnable action;boolean enabled;java.util.function.Consumer<Float>slider;Button(RectF r,Runnable a,boolean e){rect=r;action=a;enabled=e;}}
 static class Controls {int selectionButton,dragMode,holdMs,radius,doubleTapMs,miniHoldMs,tooltipMs,placementOffset;float panSpeed,pinchSpeed;
 boolean originalLarvae,singleLarvaMorph,holdSelect,doubleTap,controlGroups,pinchZoom,reversePan,placementScroll,minimapOrders,groundOrders,attackTap,tooltips,confirmBuild,placementButtonsFollow,commandModeButton;}
 static class Settings {boolean gridHotkeys,edgeScroll=true,wheelZoom=true,middlePan=true,arrowPan=true;float cameraSpeed=1;int saves;void save(Object p){saves++;}}
 final Controls controls=new Controls();final Settings desktopSettings=new Settings();final Object prefs=new Object();NativeGlue glue;NativeHud hud;Paint paint=new Paint();Button pressed;List<Button>buttons=new ArrayList<>();
 String page="game",modal="control-desktop",hint="";int logicalWidth=640,returns;double hintUntil;String language="en";
 void openDesktopSettings(){modal="control-desktop";}
 void openGamepadSettings(){modal="gamepad";}
 void desktopSettingsBack(){returns++;modal="controls";}void modalBack(){modal="options";}
 void resetDesktop(boolean hidePointer){}
 void changeControls(Runnable r){r.run();}
'''
for name in ['font','text','panel','fallback','body','gamepadLine','gamepadOption','gamepadSlider','menuButton','add','desktopToggle','changeDesktop','drawDesktopSettings','drawControls','option','controlOption','toggle','uiLine']:
    code = production(name)
    if name == 'uiLine':
        brace = code.index('{') + 1
        code = code[:brace] + '\ncheck(NativeResults.fit(font,label,width).equals(NativeArt.clean(PortText.text(label)).replace(\'\\n\',\' \')), "Truncated button: "+language+" / "+label+" in "+width);\n' + code[brace:]
    settings += code + '\n'
classic = production('drawClassicMenu')
x = classic[classic.index('    float x = (logicalWidth - (sheet ?'):classic.index('    if (modal.equals("outcome"))')]
header = classic[classic.index('    panel(c, x, y, sheet ?'):classic.index('    if (modal.equals("menu") && replayGame)')]
footer = classic[classic.index('    if (!modal.equals("menu")) menuButton'):classic.rindex('    return true;')]
settings += 'void controlsSheet(Canvas c){boolean sheet=true;\n' + x + header + 'drawControls(c,x,y);\n' + footer + '}\n'
settings += r'''
 Bitmap draw(boolean controlsScreen){buttons.clear();Bitmap b=Bitmap.createBitmap(logicalWidth,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);
  Paint bg=new Paint();bg.setColor(0xff080b0b);c.drawRect(0,0,logicalWidth,480,bg);
  if(controlsScreen)controlsSheet(c);else check(drawDesktopSettings(c),"Desktop settings not handled");return b;}
 void geometry(boolean controlsScreen){
  check(buttons.size()==(controlsScreen?7:8),"Wrong number of settings buttons");int width=controlsScreen?368:604;float left=(logicalWidth-width)/2f,top=controlsScreen?32:8,bottom=top+(controlsScreen?330:464);
  for(int i=0;i<buttons.size();i++){RectF r=buttons.get(i).rect;check(r.left>=left&&r.right<=left+width&&r.top>=top&&r.bottom<=bottom,"Button escapes panel");
   for(int j=0;j<i;j++){RectF o=buttons.get(j).rect;check(r.right<=o.left||r.left>=o.right||r.bottom<=o.top||r.top>=o.bottom,"Buttons overlap");}}
 }
 void actions(){
  int saved=desktopSettings.saves;
  buttons.get(1).action.run();check(desktopSettings.gridHotkeys&&hud.gridHotkeys,"Grid radio did not select grid");
  buttons.get(0).action.run();check(!desktopSettings.gridHotkeys&&!hud.gridHotkeys,"Original radio did not restore original");
  boolean before=desktopSettings.edgeScroll;buttons.get(2).action.run();check(desktopSettings.edgeScroll!=before,"Edge toggle failed");
  before=desktopSettings.wheelZoom;buttons.get(3).action.run();check(desktopSettings.wheelZoom!=before,"Wheel toggle failed");
  before=desktopSettings.middlePan;buttons.get(4).action.run();check(desktopSettings.middlePan!=before,"Middle toggle failed");
  before=desktopSettings.arrowPan;buttons.get(5).action.run();check(desktopSettings.arrowPan!=before,"Arrow toggle failed");
  check(buttons.get(6).slider!=null,"Camera slider not interactive");buttons.get(6).slider.accept(0f);check(desktopSettings.cameraSpeed==.25f,"Minimum camera speed wrong");
  buttons.get(6).slider.accept(1f);check(desktopSettings.cameraSpeed==2.5f,"Maximum camera speed wrong");
  check(desktopSettings.saves==saved+8,"Settings actions failed to persist");
  buttons.get(7).action.run();check(modal.equals("controls"),"Settings footer did not return");
 }
 public static void main(String[]args)throws Exception{
  NativeBridge.root=Paths.get(args[0]);Path output=Paths.get(args[1]);PortText.load(Files.newInputStream(Paths.get(args[2])));NativeArt art=new NativeArt();
  for(String language:new String[]{"en","ru","de","es","fr"})for(int width:new int[]{640,854})for(int style=0;style<3;style++){
   PortText.select(language);DesktopSettings11Test h=new DesktopSettings11Test();h.language=language;h.logicalWidth=width;
   h.hud=new NativeHud(art,style);check(!h.hud.small.fallback,"Original HUD font missing");
   for(boolean grid:new boolean[]{false,true}){h.modal="control-desktop";h.desktopSettings.gridHotkeys=grid;
    h.desktopSettings.edgeScroll=h.desktopSettings.wheelZoom=h.desktopSettings.middlePan=h.desktopSettings.arrowPan=!grid;h.desktopSettings.cameraSpeed=grid?2.5f:.25f;
    Bitmap b=h.draw(false);h.geometry(false);
    NativeArt.Font body=h.hud.small;String text="Mouse\n"+DesktopGuide.MOUSE_GUIDE+"\nKeyboard\n"+DesktopGuide.KEYBOARD_GUIDE;
    check(body.lines(text,560).size()*Math.max(16,body.height+1)<=228,"Combined help crosses its clip or footer");
    h.actions();screens++;
    ImageIO.write(b.image,"png",output.resolve("settings-"+language+"-"+width+"-"+style+"-"+(grid?"grid":"original")+".png").toFile());
   }
   h.modal="controls";Bitmap b=h.draw(true);h.geometry(true);h.buttons.get(5).action.run();check(h.modal.equals("control-desktop"),"Sixth row did not open desktop settings");screens++;
   ImageIO.write(b.image,"png",output.resolve("controls-"+language+"-"+width+"-"+style+".png").toFile());
  }
  System.out.println("PASS "+checks+" full settings-sheet checks; "+screens+" renders across five languages, three race styles, both hotkey modes and two aspect ratios; labels and combined help fit, settings controls persist and remain inside panels");
 }
}'''
sources['org/openbw/androidtest/DesktopSettings11Test.java'] = settings
for name, text in sources.items():
    target = b / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
real = [src / n for n in ['NativeArt.java','NativeGlue.java','CommandHint.java','MenuLabels.java','ClassicFontCipher.java','GameLanguage.java','PortText.java','DesktopGuide.java','GamepadSettings.java']]
subprocess.run(['javac','-d',str(b / 'classes'),*[str(b / n) for n in sources],*map(str,real)],check=True)
result = subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b / 'classes'),'org.openbw.androidtest.DesktopGuide11Test',str(assets),str(b),str(r / 'app/src/main/assets/native/ui-languages.tsv')],capture_output=True,text=True)
print(result.stdout + result.stderr,end='')
result.check_returncode()
panels = subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b / 'classes'),'org.openbw.androidtest.DesktopSettings11Test',str(assets),str(b),str(r / 'app/src/main/assets/native/ui-languages.tsv')],capture_output=True,text=True)
print(panels.stdout + panels.stderr,end='');panels.check_returncode()
files = [src / 'DesktopGuide.java',src / 'NativeSurface.java',src / 'NativeHud.java',src / 'NativeArt.java',src / 'PortText.java',r / 'app/src/main/assets/native/ui-languages.tsv',Path(__file__)]
(r / 'validation/desktop-guide11.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'canvas':'AWT shim using production font drawing, extracted production settings helpers and original local font/artwork fixtures','result':result.stdout.strip(),'fullPanels':panels.stdout.strip(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},indent=2)+'\n')

#!/usr/bin/env python3
"""Check original BIN menu mnemonics with real fonts and bounded Canvas rendering.

Uses only already-imported local game assets; does not bundle copyrighted data.
No physical Android/device coverage is claimed.
"""
from pathlib import Path
import ast, hashlib, json, os, re, shutil, struct, subprocess
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest'
b=r/'build-native/menu-hotkeys11';b.mkdir(parents=True,exist_ok=True)
jdk=r/'.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64/bin'
if (jdk/'javac').is_file():os.environ['PATH']=str(jdk)+os.pathsep+os.environ['PATH']
assets=b/'assets';shutil.copytree(r/'build-native/desktop-guide11/assets',assets,dirs_exist_ok=True)
extract=r/'build-native/reign79/extract'
archives=[(0,r.parent/'reign-data/StarDat.mpq'),(1,r.parent/'reign-data/BrooDat.mpq'),(2,r.parent/'reign-data/patch_rt.mpq'),(4,r.parent/'reign-data/StarCraft.mpq'),(4,r.parent/'reign-data/BroodWar.mpq')]
names={'font/font.gid'}
menus=['glumain','glucmpgn','gluexpcmpgn','glulogin','gamemenu','options','abrtmenu','glucustm','gluload']
names.update('rez/'+name+'.bin' for name in menus+['glurdyt'])
names.update('glue/'+pal+'/'+name for pal in ['palmm','palcs','palnl','palrt']for name in ['backgnd.pcx','tfont.pcx','teffect.pcx','dlg.grp','tile.grp'])
def load(name):
 for slot,archive in archives:
  target=assets/str(slot)/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.is_file():continue
  subprocess.run([str(extract),str(archive),name,str(target)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for name in sorted(names):load(name)
# Include the authored menu panels referenced by each BIN. Movie timing is
# outside this text-render regression and the movie boundary is stubbed out.
for path in sorted(assets.glob('*/rez/*.bin')):
 data=path.read_bytes();p=struct.unpack_from('<I',data,66)[0]
 while p:
  n=struct.unpack_from('<I',data,p+20)[0]
  if n:
   text=data[n:data.index(b'\0',n)].decode('cp1252')
   if text.lower().endswith('.pcx'):load(text.replace('\\','/').lower())
  p=struct.unpack_from('<I',data,p)[0]
active=False
for node in ast.parse((r/'tests/run_gamepad81.py').read_text()).body:
 if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='old'for t in node.targets):active=True
 if active:
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='harness'for t in node.targets):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<menu Canvas shim>','exec'),globals())
sources.pop('org/openbw/androidtest/MapScroll79Test.java',None)
sources['org/openbw/androidtest/NativeBridge.java']='''package org.openbw.androidtest;import java.nio.file.*;import android.graphics.*;
class NativeBridge{static Path root;static byte[]asset(int slot,String name){try{return Files.readAllBytes(root.resolve(String.valueOf(slot)).resolve(name));}catch(Exception e){return null;}}
static byte[]archiveText(String path){return null;}static int[]movieOpen(byte[]b,boolean a){throw new UnsupportedOperationException();}static int[]movieOpenAsset(int s,String p,boolean a){throw new UnsupportedOperationException();}static void movieFrame(int i,double t,boolean l,Bitmap b){}static void movieClose(int i){}
}'''
sources['org/openbw/androidtest/MenuHotkeys11Test.java']=r'''package org.openbw.androidtest;
import android.graphics.*;import java.nio.file.*;import java.util.*;import javax.imageio.ImageIO;
public class MenuHotkeys11Test {
 static int checks,renders,labels,highlighted;
 static void check(boolean value,String why){checks++;if(!value)throw new AssertionError(why);}
 static String plain(String value){return NativeArt.clean(value);}
 static NativeArt.Font font(NativeGlue g,NativeArt.Widget w){return(w.flags&0x4000)!=0?g.button:(w.flags&0x800)!=0||w.type==14?g.large:(w.flags&0x400)!=0?g.small:g.tiny;}
 static class Recorded extends Canvas {
  final IdentityHashMap<Bitmap,Integer> colors=new IdentityHashMap<>();int bright,normal;
  Recorded(Bitmap image,NativeArt.Font f,String label){super(image);for(char ch:plain(label).toCharArray())if(ch>32)for(int color:new int[]{2,3,4,5})colors.put(f.glyph(ch,color),color);}
  public void drawBitmap(Bitmap image,float x,float y,Paint paint){Integer color=colors.get(image);if(color!=null){if(color==4)bright++;else normal++;}super.drawBitmap(image,x,y,paint);}
 }
 static void textCases() throws Exception {
  PortText.select("en");
  check(MenuLabels.applyMnemonic("View \u0004I\u0001ntro","View Intro").equals("View \u0004I\u0001ntro"),"Unchanged original marker moved");
  check(MenuLabels.applyMnemonic("\u0004P\u0001rotoss\n\u0002Episode III\u0001","Protoss\nEpisode III").equals("\u0004P\u0001rotoss\n\u0002Episode III\u0001"),"Episode color lost");
  check(MenuLabels.applyMnemonic("Show C\u0004r\u0001edits","Credits").equals("C\u0004r\u0001edits"),"Credit mnemonic reset to arbitrary index");
  check(MenuLabels.applyMnemonic("\u0004C\u0001ampaign Editor","App Options").equals("App Options"),"Old action key moved to new action");
  check(MenuLabels.applyMnemonic("\u0004C\u0001ampaign Editor","\u0004A\u0001pp Options").equals("\u0004A\u0001pp Options"),"Explicit App Options key lost");
  check(MenuLabels.applyMnemonic("View \u0004I\u0001ntro","View...").equals("View..."),"Truncated key highlighted wrong character");
  check(MenuLabels.mnemonic("Return (\u0004Esc\u0001)")==27,"Escape key missing");
  check(MenuLabels.mnemonic("\u0004С\u0001етевая игра")==0,"Cyrillic label advertised unrelated ASCII key");
  for(String lang:new String[]{"en","ru","de","es","fr"}){
   PortText.select(lang);
   for(String label:new String[]{"\u0004S\u0001ingle Player","\u0004M\u0001ultiplayer","\u0004C\u0001ancel","View \u0004I\u0001ntro","Show C\u0004r\u0001edits","\u0004A\u0001pp Options"}){
    String translated=PortText.text(label),unmarked=PortText.text(plain(label));
    check(plain(translated).equals(unmarked),"Highlight changed translated text: "+lang);
    check(PortText.text(translated).equals(translated),"Repeated font translation drops marker: "+lang);
    int original=MenuLabels.mnemonic(label),result=MenuLabels.mnemonic(translated);
    check(result==0||result==original,"Translation changed key binding: "+lang);
   }
   String bracket="Build Vulture [\u0003V\u0002]";
   String translated=PortText.preserveHotkey(bracket,"Vulture construit [V]");
   check(translated.equals("Vulture construit [\u0003V\u0002]"),"Yellow key relocated into command name: "+lang);
  }
  PortText.select("fr");check(PortText.text("\u0004C\u0001ancel").equals("Annuler"),"Missing French mnemonic reused English offset");
 }
 static void screens(NativeArt art,Path output) throws Exception {
  String[] names={"glumain","glucmpgn","gluexpcmpgn","glulogin","gamemenu","options","abrtmenu","glucustm","gluload"};
  for(String name:names)try(NativeGlue glue=new NativeGlue(art,name,name.equals("glumain")?"palmm":name.contains("cmpgn")?"palcs":"palnl",false)){
   check(!glue.large.fallback&&!glue.button.fallback,"Original FONT not loaded: "+name);
   glue.elapsed=1000;glue.animationElapsed=1000;
   for(String lang:new String[]{"en","ru","de","es","fr"}){
    PortText.select(lang);Bitmap screen=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(screen);c.drawBitmap(glue.background.image,0,0,NativeArt.PIXELS);
    for(NativeArt.Widget w:glue.layout.widgets){
     if(w.type==5) {NativeArt.PCX panel=glue.panels.get(w.id);if(panel!=null)c.drawBitmap(panel.image,w.x,w.y,NativeArt.PIXELS);continue;}
     if((w.flags&8)==0||w.type!=14&&w.type!=1&&w.type!=2)continue;
     String override=name.equals("glumain")&&w.id==5?"\u0004A\u0001pp Options":null;
     String label=MenuLabels.forWidget(name,w.id,w,override);
     int key=MenuLabels.mnemonic(label);labels++;
     check(label.equals(PortText.text(label)),"Translated label is not stable: "+name+"/"+w.id+"/"+lang);
     String source=(w.flags&0x200)!=0?w.text.substring(1):w.text;
     if(lang.equals("en")&&plain(source).equals(plain(label)))check(label.equals(source),"Authored marker position/colors changed: "+name+"/"+w.id);
     if(key!=0){highlighted++;check(key==Character.toLowerCase(w.text.charAt(0))||name.equals("glumain")&&w.id==5&&key=='a',"Visible key differs from BIN metadata: "+name+"/"+w.id+"/"+lang);}
     for(boolean enabled:new boolean[]{true,false})for(boolean hover:new boolean[]{false,true}){
      glue.hot=hover?w.id:-1;Bitmap image=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Recorded draw=new Recorded(image,font(glue,w),label);glue.label(draw,w.id,override,enabled);
      if(!enabled)check(draw.bright==0,"Disabled button keeps active mnemonic color: "+name+"/"+w.id);
      else if(!hover&&key!=0){check(draw.bright>0,"Original key glyph was not rendered in highlight ramp: "+name+"/"+w.id+"/"+lang);check(draw.normal>0,"Whole caption highlighted instead of its mnemonic");}
      renders++;
     }
     glue.hot=-1;glue.label(c,w.id,override,true);
    }
    if(Arrays.asList("glumain","glucmpgn","glulogin").contains(name)&&Arrays.asList("en","ru").contains(lang))ImageIO.write(screen.image,"png",output.resolve(name+"-"+lang+".png").toFile());
   }
  }
 }
 static void replayTint(NativeArt art,Path output)throws Exception {
  byte[]wpe=art.read("tileset/badlands.wpe");int[]palette=new int[256];
  for(int i=0;i<256;i++)palette[i]=Color.rgb(wpe[i*4]&255,wpe[i*4+1]&255,wpe[i*4+2]&255);
  NativeArt.Font font=art.font("16",art.pcx("game/tfontgam.pcx",false,-1),palette,1).withShadedColor(0xff76b948);
  for(char letter:new char[]{'P','R','E','x'}){
   Bitmap normal=font.glyph(letter,3),key=font.glyph(letter,4);int ink=0,different=0;long normalLight=0,keyLight=0;
   for(int y=0;y<normal.getHeight();y++)for(int x=0;x<normal.getWidth();x++){
    int a=normal.image.getRGB(x,y),b=key.image.getRGB(x,y);
    if((a>>>24)>0){ink++;if(a!=b)different++;normalLight+=Color.red(a)+Color.green(a)+Color.blue(a);keyLight+=Color.red(b)+Color.green(b)+Color.blue(b);
     check(Color.green(b)>Color.red(b)&&Color.green(b)>Color.blue(b),"Replay key loses the existing green tint");}
   }
   check(ink>0&&different==ink,"Tint collapses the replay shortcut brightness ramp: "+letter);
   check(keyLight>normalLight,"Replay shortcut is not brighter than its caption: "+letter);
  }
  PortText.select("en");Bitmap preview=Bitmap.createBitmap(220,48,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(preview);
  Paint bg=new Paint();bg.setColor(0xff000000);c.drawRect(0,0,220,48,bg);
  font.draw(c,"\u0004P\u0001ause   1\u0004x\u0001   \u0004R\u0001estart",5,16,210,0,3,0);
  ImageIO.write(preview.image,"png",output.resolve("replay-shortcut-tint.png").toFile());
 }
 static void resolvedCaption(NativeArt art)throws Exception {
  try(NativeGlue glue=new NativeGlue(art,"glurdyt","palrt",false)){
   glue.elapsed=1000;glue.animationElapsed=1000;glue.hot=-1;NativeArt.Widget replay=glue.layout.get(20);
   check(replay!=null&&glue.labelVisible(20),"Actual briefing Replay fixture missing");NativeArt.Font f=font(glue,replay);
   check(!f.fallback,"Briefing replay uses substitute font");
   for(String language:new String[]{"en","ru","de","es","fr"}){PortText.select(language);
    String authored=MenuLabels.forWidget("glurdyt",20,replay,null),plain=NativeArt.clean(authored);
    Bitmap normal=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Recorded rendered=new Recorded(normal,f,plain);glue.labelCaption(rendered,20,plain,true);
    check(rendered.bright==0&&rendered.normal>0,"Resolved plain Replay restores the authored shortcut: "+language);
    Bitmap original=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Recorded nativeLabel=new Recorded(original,f,authored);glue.label(nativeLabel,20,null,true);
    if(MenuLabels.mnemonic(authored)!=0)check(nativeLabel.bright>0,"Legacy label no longer preserves authored mnemonic: "+language);
    Bitmap resolved=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);glue.labelCaption(new Canvas(resolved),20,authored,true);
    int changed=0;for(int y=0;y<480;y++)for(int x=0;x<640;x++)if(original.image.getRGB(x,y)!=resolved.image.getRGB(x,y))changed++;
    check(changed==0,"Exact caption drawing changed legacy original label pixels: "+language);
   }
  }
 }
 public static void main(String[]args)throws Exception {
  NativeBridge.root=Paths.get(args[0]);PortText.load(Files.newInputStream(Paths.get(args[2])));textCases();NativeArt art=new NativeArt();screens(art,Paths.get(args[1]));replayTint(art,Paths.get(args[1]));resolvedCaption(art);
  System.out.println("PASS "+checks+" checks; "+labels+" real BIN captions; "+highlighted+" surviving mnemonics; "+renders+" original-font renders; nine dialogs plus actual briefing Replay, five UI languages, exact resolved captions do not restore excluded shortcuts, enabled/disabled/hover, exact authored colors, overrides, fitting, bracket preservation and distinct green replay shortcut ramps");
 }
}'''
for name,text in sources.items():
 target=b/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
real=[src/n for n in ['NativeArt.java','NativeGlue.java','MenuLabels.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
subprocess.run(['javac','-d',str(b/'classes'),*[str(b/n)for n in sources],*map(str,real)],check=True)
result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes'),'org.openbw.androidtest.MenuHotkeys11Test',str(assets),str(b),str(r/'app/src/main/assets/native/ui-languages.tsv')],capture_output=True,text=True)
print(result.stdout+result.stderr,end='');result.check_returncode()
files=real+[r/'app/src/main/assets/native/ui-languages.tsv',Path(__file__)]
(r/'validation/menu-hotkeys11.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'canvas':'AWT shim; production NativeGlue/NativeArt methods; actual imported BIN and FONT/font.gid assets; movie boundary stubbed','result':result.stdout.strip(),'sourceSha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}},indent=2)+'\n')

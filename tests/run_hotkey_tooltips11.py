#!/usr/bin/env python3
"""Exercise shared command-slot binding and original-font highlighted hotkey tooltips.

The bounded Canvas/native boundary shims execute actual production HUD methods;
this is not a physical Android test. User-owned assets stay in build-native.
"""
from pathlib import Path
import ast, hashlib, json, os, re, shutil, subprocess
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest'
b=r/'build-native/hotkey-tooltips11';b.mkdir(parents=True,exist_ok=True)
jdk=r/'.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64/bin'
if (jdk/'javac').is_file():os.environ['PATH']=str(jdk)+os.pathsep+os.environ['PATH']
manifest=r/'build-native/hotkey-command11/cards.json'
assert manifest.is_file(), 'Run tests/run_hotkeys_native11.py to generate actual native command cards first.'
corpus=json.loads(manifest.read_text());corpus_hash=hashlib.sha256(manifest.read_bytes())
for entry in corpus:corpus_hash.update((r/'build-native/hotkey-command11/cards'/entry['file']).read_bytes())
assets=b/'assets';shutil.copytree(r/'build-native/desktop-guide11/assets',assets,dirs_exist_ok=True)
extract=r/'build-native/reign79/extract';core=r/'build-native/reign79/core'
names=['font/font.gid','game/tfontgam.pcx','game/icons.grp','tileset/badlands.wpe','unit/cmdbtns/ticon.pcx','unit/cmdbtns/cmdicons.grp','rez/stat_txt.tbl']
for race in 'ztp':names += [f'game/{race}console.pcx',f'unit/cmdbtns/{race}cmdbtns.grp',f'rez/statbtn{race}.bin']
for name in names:
 target=assets/'0'/name;target.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run([str(extract),str(core/'STARDAT.MPQ'),name,str(target)],check=True,stdout=subprocess.DEVNULL)
active=False
for node in ast.parse((r/'tests/run_gamepad81.py').read_text()).body:
 if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='old'for t in node.targets):active=True
 if active:
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='harness'for t in node.targets):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<hotkey Canvas shim>','exec'),globals())
sources.pop('org/openbw/androidtest/MapScroll79Test.java',None)
sources['android/graphics/RectF.java']=sources['android/graphics/RectF.java'].replace('public float width()', 'public void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}public float width()')
sources['org/openbw/androidtest/NativeBridge.java']='''package org.openbw.androidtest;import java.nio.file.*;import android.graphics.*;class NativeBridge{
 static Path root;static int target,race;static byte[]asset(int slot,String name){try{return Files.readAllBytes(root.resolve(String.valueOf(slot)).resolve(name));}catch(Exception e){return null;}}
 static byte[]archiveText(String path){return null;}static int value(int kind,int index){return kind==0?target:kind==5?race:0;}static int[]movieOpen(byte[]b,boolean a){throw new UnsupportedOperationException();}static int[]movieOpenAsset(int s,String p,boolean a){throw new UnsupportedOperationException();}static void movieFrame(int i,double t,boolean l,Bitmap b){}static void movieClose(int i){}
}'''
def method(text,name):
 match=re.search(r'^  (?:private |public |protected )?(?:static )?[\w.<>]+ '+re.escape(name)+r'\(',text,re.M);assert match,name
 end=text.index('{',match.end())+1;depth=1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[match.start():end]
hud=(src/'NativeHud.java').read_text()
methods='\n'.join(method(hud,name)for name in ['number','frame','icon','image','string','requirement','commandBindings','commandHitForSlot','hotkey','drawCommands','hint','commandRect','map','commandErrorTop','commandError'])
# Include all overloads, up to commandRect, without reimplementing tooltip layout.
tooltip=hud[hud.index('  void tooltip(Canvas canvas, String text, int width) {'):hud.index('  RectF commandRect(')]
hit=method(hud,'hotkey')
sources['org/openbw/androidtest/NativeHud.java']='''package org.openbw.androidtest;import android.graphics.*;import java.util.*;import org.json.*;
class NativeHud {
 static final int WORLD_BOTTOM=376;int race,page;float commandScale=1,descriptionScale=1;String previous="";RectF pressedCommand;boolean gridHotkeys;
 NativeArt.Font small,tiny,errorShadow;NativeArt.Dialog commandLayout;NativeArt.PCX tint,console;int[]palette;
 byte[]commandGrp,framesGrp;String[]names;JSONObject maps;
 final Bitmap[]resources=new Bitmap[3],supplyIcons=new Bitmap[3];
 Map<Integer,Bitmap>frames=new HashMap<>();Map<String,Bitmap>icons=new HashMap<>();List<Hit>hits=new ArrayList<>();
 static class Hit{RectF rect;String[]fields;int slot=-1,cancel=-1,selectUnit=-1,unload=-1;boolean more;String help;}
 NativeHud(NativeArt art,int race,JSONObject maps){this.race=race;NativeBridge.race=race;this.maps=maps;String letter=new String[]{"z","t","p"}[race];
  console=art.pcx("game/"+letter+"console.pcx",true,-1);palette=console.palette.clone();byte[]wpe=art.read("tileset/badlands.wpe");
  for(int i=0;i<256;i++)palette[i]=Color.rgb(wpe[i*4]&255,wpe[i*4+1]&255,wpe[i*4+2]&255);
  NativeArt.PCX colors=art.pcx("game/tfontgam.pcx",false,-1);small=art.font("10",colors,palette,0);tiny=art.font("8",colors,palette,0);errorShadow=small.withShadedColor(0xff000000);
  tint=art.pcx("unit/cmdbtns/ticon.pcx",false,-1);commandGrp=art.read("unit/cmdbtns/cmdicons.grp");framesGrp=art.read("unit/cmdbtns/"+letter+"cmdbtns.grp");
  commandLayout=new NativeArt.Dialog(art.read("rez/statbtn"+letter+".bin"));names=NativeArt.tbl(art.read("rez/stat_txt.tbl"));byte[]grp=art.read("game/icons.grp");
  int[]ids={0,1+race,4+race};for(int i=0;i<3;i++){resources[i]=NativeArt.grp(grp,ids[i],palette,true,false);supplyIcons[i]=NativeArt.grp(grp,4+i,palette,true,false);}}
'''+methods+'\n'+tooltip+'}\n'
sources['org/openbw/androidtest/HotkeyTooltips11Test.java']=r'''package org.openbw.androidtest;
import java.nio.file.*;import java.util.*;import android.graphics.*;import javax.imageio.ImageIO;import org.json.*;
public class HotkeyTooltips11Test {
 static int checks,renders;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static String cmd(String key,String title,int unit,int upgrade,int research,int index){return String.join("\t",new String[]{key,title,"1",""+unit,"75","25","","","","0",""+(unit<0?0:unit),""+upgrade,""+research,"0","4","1",""+index,""+(100000+index)});}
 static String card(String title,String...commands){return title+"\tHP 100/100\n"+String.join("\n",commands);}
 static String clean(String value){return NativeArt.clean(value);}
 static Bitmap blank(int width){return Bitmap.createBitmap(width,480,Bitmap.Config.ARGB_8888);}
 static List<NativeHud.Hit> bindings(NativeHud h,String card,int type,int width){h.hits.clear();String[]lines=card.split("\n");h.drawCommands(new Canvas(blank(width)),lines,type,lines[0].split("\t",2)[0],width);return new ArrayList<>(h.hits);}
 static void sameSlots(NativeHud h,String card,int type,int width){
  List<NativeHud.Hit>hits=bindings(h,card,type,width);Set<Integer>slots=new HashSet<>();
  for(NativeHud.Hit hit:hits){check(slots.add(hit.slot),"Duplicate grid slot");NativeHud.Hit fresh=h.commandHitForSlot(hit.slot,card,type);check(fresh!=null,"Drawn hit absent in fresh lookup");check(fresh.more==hit.more&&Arrays.equals(fresh.fields,hit.fields),"Fresh slot differs from rendered command");
   check(hit.rect.left>=0&&hit.rect.right<=width&&hit.rect.top>=0&&hit.rect.bottom<=480,"Grid hit clipped");
   h.gridHotkeys=true;check(h.hotkey(hit).equals(""+"QWEASDZXC".charAt(hit.slot)),"Grid hotkey mismatch");
   check(clean(h.hint(hit)).split("\n")[0].endsWith("["+h.hotkey(hit)+"]"),"Grid tooltip key absent");
   h.gridHotkeys=false;check(h.hotkey(hit).equals(hit.more?"":CommandHint.originalHotkey(hit.fields)),"Original hotkey changed");
  }
  for(int slot=0;slot<9;slot++)check((h.commandHitForSlot(slot,card,type)!=null)==slots.contains(slot),"Empty slot activates command");
 }
 static void slotCases(NativeArt art,JSONObject maps){
  NativeHud h=new NativeHud(art,1,maps);String worker=card("SCV",cmd("m","Move",-1,-1,-1,0),cmd("s","Stop",-1,-1,-1,1),cmd("a","Attack",-1,-1,-1,2),cmd("p","Patrol",-1,-1,-1,3),cmd("h","Hold",-1,-1,-1,4),cmd("g","Gather",-1,-1,-1,5),cmd("r","Repair",-1,-1,-1,6),cmd("b","Build",-1,-1,-1,7),cmd("v","Advanced",-1,-1,-1,8));
  for(int type:new int[]{7,41,64}){sameSlots(h,worker,type,640);for(NativeHud.Hit hit:h.hits)check(!hit.fields[1].equals("Patrol")&&!hit.fields[1].equals("Hold"),"Worker hidden commands gained grid keys");}
  String build=card("Build",cmd("c","Build Command Center",106,-1,-1,0),cmd("s","Build Supply Depot",109,-1,-1,1),cmd("r","Build Refinery",110,-1,-1,2));sameSlots(h,build,7,640);check(h.commandHitForSlot(8,build,7).fields[0].equals("\u001b"),"Synthetic Escape missing");
  String factory=card("Factory",cmd("v","Build Vulture",2,-1,-1,0),cmd("t","Build Siege Tank",5,-1,-1,1),cmd("g","Build Goliath",3,-1,-1,2));sameSlots(h,factory,113,640);
  String duplicates=card("Mixed",cmd("q","A",0,-1,-1,0),cmd("q","B",1,-1,-1,1),cmd("q","C",2,-1,-1,2));sameSlots(h,duplicates,0,640);check(!h.commandHitForSlot(0,duplicates,0).fields[17].equals(h.commandHitForSlot(1,duplicates,0).fields[17]),"Duplicate original keys collapsed identities");
  for(String section:new String[]{"buildSlots","upgradeSlots","researchSlots"}){JSONObject object=maps.getJSONObject(section);for(String key:object.keySet()){
   int id=Integer.parseInt(key);String text=card(section.equals("buildSlots")?"Build":"Producer",cmd("x","Command",section.equals("buildSlots")?id:-1,section.equals("upgradeSlots")?id:-1,section.equals("researchSlots")?id:-1,0));
   int expected=object.getInt(key);NativeHud.Hit hit=h.commandHitForSlot(expected,text,122);check(hit!=null&&hit.fields[16].equals("0"),"Declared map slot changed: "+section+" "+key);sameSlots(h,text,122,640);
  }}
  int[][]heroes={{48,51,53,54,55,104},{16,19,20,23,28,99},{75,77,78,79,82,88}};int[]producers={139,122,166};
  for(int race=0;race<3;race++)for(int width:new int[]{640,960})for(float scale:new float[]{1,1.2f,1.5f}){
   h=new NativeHud(art,race,maps);h.commandScale=scale;String[]rows=new String[6];for(int i=0;i<6;i++)rows[i]=cmd(""+(char)('a'+i),"Hero "+heroes[race][i],heroes[race][i],-1,-1,i);sameSlots(h,card("Hero building",rows),producers[race],width);
  }
  h=new NativeHud(art,1,maps);String[]rows=new String[15];for(int i=0;i<15;i++)rows[i]=cmd("x","Command "+i,i,-1,-1,i);String many=card("Many",rows);sameSlots(h,many,0,640);check(h.commandHitForSlot(8,many,0).more,"C is not pager");h.page++;sameSlots(h,many,0,640);check(h.commandHitForSlot(0,many,0).fields[16].equals("8"),"Fresh lookup resets current page");h.commandHitForSlot(0,factory,113);check(h.page==0,"New card did not reset page");
  for(int kind=0;kind<4;kind++){NativeHud.Hit hit=new NativeHud.Hit();if(kind==0)hit.help="Armor";if(kind==1)hit.cancel=0;if(kind==2)hit.selectUnit=0;if(kind==3){hit.unload=0;hit.help="Marine — cargo";}h.gridHotkeys=true;check(!h.hint(hit).contains("["),"Informational/queue hit advertises unsupported key");}
  check(h.commandHitForSlot(-1,factory,113)==null&&h.commandHitForSlot(9,factory,113)==null&&h.commandHitForSlot(0,"",113)==null,"Invalid lookup accepted");
 }
 static class Recording extends Canvas {
  NativeHud h;Map<Bitmap,Integer>yellow=new IdentityHashMap<>();int keys,leftBracket,rightBracket,resources;List<Integer>codes=new ArrayList<>();
  Recording(Bitmap image,NativeHud hud){super(image);h=hud;for(int c=32;c<127;c++)yellow.put(h.small.glyph(c,3),c);}
  public void drawBitmap(Bitmap image,float x,float y,Paint paint){Integer key=yellow.get(image);if(key!=null){keys++;codes.add(key);}if(image==h.small.glyph('[',2))leftBracket++;if(image==h.small.glyph(']',2))rightBracket++;for(Bitmap icon:h.resources)if(image==icon)resources++;super.drawBitmap(image,x,y,paint);}
 }
 static void renderCases(NativeArt art,JSONObject maps,Path out)throws Exception{
  for(String language:new String[]{"en","ru","de","es","fr"})for(int race=0;race<3;race++)for(boolean grid:new boolean[]{false,true})for(int width:new int[]{640,960})for(float size:new float[]{1,1.5f}){
   PortText.select(language);NativeHud h=new NativeHud(art,race,maps);check(!h.small.fallback,"Original font unavailable");h.gridHotkeys=grid;h.descriptionScale=size;h.commandScale=size;
   String card=card("Factory",cmd("v","Build Vulture",2,-1,-1,0));NativeHud.Hit hit=h.commandHitForSlot(0,card,113);check(hit!=null,"Vulture slot missing");
   Bitmap bitmap=blank(width);Recording canvas=new Recording(bitmap,h);h.tooltip(canvas,h.hint(hit),width,1);
   String expected=h.hotkey(hit);check(canvas.keys==expected.length(),"Highlighted key lost or duplicated: "+language+" / "+expected+" got"+canvas.codes);check(canvas.leftBracket==1&&canvas.rightBracket==1,"Brackets not ordinary text color");check(canvas.resources>=2,"Resource/supply row lost");
   h.gridHotkeys=!grid;check(!h.hotkey(hit).equals(expected),"Setting change did not update existing hover key");
   if(width==640&&size==1)ImageIO.write(bitmap.image,"png",out.resolve(language+"-race"+race+"-"+(grid?"grid":"original")+".png").toFile());renders++;
  }
  for(String language:new String[]{"en","ru","de","es","fr"})for(boolean grid:new boolean[]{false,true}){
   PortText.select(language);NativeHud fallback=new NativeHud(art,1,maps);fallback.small=new NativeArt.Font(null,art.pcx("game/tfontgam.pcx",false,-1),fallback.palette,0,10);fallback.gridHotkeys=grid;
   NativeHud.Hit hit=fallback.commandHitForSlot(0,card("Factory",cmd("v","Build Vulture",2,-1,-1,0)),113);Bitmap image=blank(640);Recording c=new Recording(image,fallback);fallback.tooltip(c,fallback.hint(hit),640);
   check(fallback.small.fallback&&c.keys==1&&c.leftBracket==1&&c.rightBracket==1,"Missing-font fallback loses yellow hotkey");renders++;
  }
  PortText.select("en");NativeHud h=new NativeHud(art,1,maps);NativeHud.Hit escape=h.commandHitForSlot(8,card("Build",cmd("b","Command Center",106,-1,-1,0)),7);Recording canvas=new Recording(blank(640),h);h.tooltip(canvas,h.hint(escape),640);check(canvas.keys==3,"Escape key missing");
  String[]longNames={"Research an intentionally very long command name that wraps before its hotkey","Build Vulture"};
  for(String name:longNames){String[]fields=cmd("v",name,2,-1,-1,0).split("\t",-1);fields[2]="0";fields[7]="Very long prerequisite text that must wrap safely";String info=CommandHint.describe(fields,fields[7]);Recording c=new Recording(blank(640),h);h.tooltip(c,info,640,1,200);check(c.keys==1&&c.leftBracket==1&&c.rightBracket==1,"Wrapped heading loses colored key");}
 }
 static void nativeCorpus(NativeArt art,JSONObject maps,Path directory)throws Exception{
  Path manifest=directory.resolve("cards.json");if(!Files.isRegularFile(manifest))manifest=directory.getParent().resolve("cards.json");check(Files.isRegularFile(manifest),"Native command-card corpus missing");
  JSONArray entries=new JSONArray(new String(Files.readAllBytes(manifest),"UTF-8"));
  for(int i=0;i<entries.length();i++){JSONObject entry=entries.getJSONObject(i);int race=entry.optInt("race",1),type=entry.getInt("type");Path file=directory.resolve(entry.getString("file"));if(!Files.isRegularFile(file))file=directory.getParent().resolve(entry.getString("file"));String card=new String(Files.readAllBytes(file),"UTF-8");NativeHud h=new NativeHud(art,race,maps);sameSlots(h,card,type,640);}
  System.out.println("PASS "+entries.length()+" native-generated command cards share fresh grid/render slots");
 }
 public static void main(String[]args)throws Exception{
  NativeBridge.root=Paths.get(args[0]);Path out=Paths.get(args[1]);PortText.load(Files.newInputStream(Paths.get(args[2])));JSONObject maps=new JSONObject(new String(Files.readAllBytes(Paths.get(args[3])),"UTF-8"));NativeArt art=new NativeArt();
  check(CommandHint.originalHotkey(null).isEmpty()&&CommandHint.originalHotkey(new String[]{""}).isEmpty()&&CommandHint.originalHotkey(new String[]{" "}).isEmpty(),"No-key command gains a shortcut");
  slotCases(art,maps);renderCases(art,maps,out);nativeCorpus(art,maps,Paths.get(args[4]));
  System.out.println("PASS "+checks+" slot/heading/color checks; "+renders+" original/fallback-font renders; three races, five UI languages, Original/Grid, widths/scales, paging, cancellation and non-command exclusions");
 }
}'''
for name,text in sources.items():
 target=b/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
real=[src/n for n in ['NativeArt.java','NativeGlue.java','CommandHint.java','CommandSlots.java','MenuLabels.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
jar=r/'build-native/json-20240303.jar'
subprocess.run(['javac','-cp',str(jar),'-d',str(b/'classes'),*[str(b/n)for n in sources],*map(str,real)],check=True)
result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes')+os.pathsep+str(jar),'org.openbw.androidtest.HotkeyTooltips11Test',str(assets),str(b),str(r/'app/src/main/assets/native/ui-languages.tsv'),str(r/'app/src/main/assets/native/commands.json'),str(r/'build-native/hotkey-command11/cards')],capture_output=True,text=True)
print(result.stdout+result.stderr,end='');result.check_returncode()
files=[src/n for n in ['NativeHud.java','CommandHint.java','CommandSlots.java','NativeArt.java','PortText.java']]+[r/'app/src/main/assets/native/commands.json',r/'app/src/main/assets/native/ui-languages.tsv',Path(__file__)]
(r/'validation/hotkey-tooltips11.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'canvas':'AWT shim, production slot/tooltip/font methods, local original artwork and font.gid','result':result.stdout.strip(),'nativeCardCount':len(corpus),'nativeCorpusSha256':corpus_hash.hexdigest(),'sourceSha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}},indent=2)+'\n')

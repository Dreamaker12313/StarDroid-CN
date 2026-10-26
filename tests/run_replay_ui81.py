#!/usr/bin/env python3
"""Render and exercise the production replay browser, delete confirmation and playback UI.
Uses original locally imported artwork through the existing bounded AWT/Android shim.
Native replay parsing/playback are covered separately; metadata/clock are mocked here.
"""
from pathlib import Path
import ast,hashlib,json,re,subprocess,shutil,tempfile
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest'
b=r/'build-native/replay-ui81';b.mkdir(parents=True,exist_ok=True)
assets=b/'assets';shutil.copytree(r/'build-native/gamepad81/assets',assets,dirs_exist_ok=True)
archives=[(0,r/'build-native/reign79/core/STARDAT.MPQ'),(1,r/'build-native/reign79/core/BROODAT.MPQ'),(2,r/'build-native/reign79/core/patch_rt.mpq'),(4,r.parent/'reign-data/StarCraft.mpq')]
def get(name):
 found=[]
 for slot,archive in archives:
  target=assets/str(slot)/name;target.parent.mkdir(parents=True,exist_ok=True)
  call=subprocess.run([str(r/'build-native/reign79/extract'),str(archive),name,str(target)],capture_output=True)
  if call.returncode:target.unlink(missing_ok=True)
  else:found.append(target.read_bytes())
 return found
for data in get('rez/gluload.bin'):
 for name in {s.decode('cp1252').replace('\\','/').lower() for s in re.findall(rb'(?:glue|GLUE)[^\x00]*?\.[pP][cC][xX]',data)}:get(name)
for name in ['glue/load/pinfo.pcx','dlgs/zerg.grp','dlgs/protoss.grp']:get(name)
# Reuse the exact Canvas/input shims from controller verification, without running it.
tree=ast.parse((r/'tests/run_gamepad81.py').read_text());active=False
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='old' for t in node.targets):active=True
 if active:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='harness' for t in node.targets):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<replay canvas shim>','exec'))
harness=sources.pop('org/openbw/androidtest/MapScroll79Test.java')
harness=harness[:harness.index(' public static void main(String[] args)')]
harness=harness.replace('MapScroll79Test','ReplayUi81Test')
harness=re.sub(r' void redButton\(Canvas c[^\n]+\n','',harness)
harness=harness.replace('void pickNativeMap(){}','void pickNativeMap(){}int imports,exports;void pickReplay(){imports++;}void saveReplay(byte[] bytes){exports++;}')
harness=harness.replace('int selections,imports;','''int selections,imports,logicalWidth=640,starts;File started;
 Path fixtureRoot;NativeReplays replays;List<File>replayFiles=Collections.emptyList();File selectedReplay,playingReplay;
 List<Integer>replayPlayers=new ArrayList<>(),replayRaces=new ArrayList<>();NativeArt art;Object commandMaps;int missionRace=1,musicCalls;void music(String phase){musicCalls++;}String replayDetails="",replayNotice="";boolean replayValid,replayExpansion,replayPaused;
 float replayOffset,menuHoverX=-1,menuHoverY=-1;int replayRate=1;double accumulator;Paint paint=new Paint();
 void startReplay(File f){started=f;starts++;}void showCampaign(){}void navigate(Runnable action){action.run();}void drawMenuUnavailable(Canvas c,Runnable action){}
''')
text=(src/'NativeSurface.java').read_text()
def production(name):
 m=re.search(r'^  (?:private )?(?:static )?(?:void|boolean|int|float|String|NativeArt.Font) '+name+r'\(',text,re.M);assert m,name
 end=text.index('{',m.end())+1;depth=1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[m.start():end]
names=['font','text','panel','body','fallback','uiLine','redBorder','menuHot','menuColor','redButton','glueButton','button','menuButton','replayMaxOffset','replayTime','selectReplay','refreshReplays','drawReplayBrowser','drawReplayDialog','replayButton','drawReplayControls']
harness+='\n'.join(production(n) for n in names)
harness+='''
 Bitmap browser(){buttons.clear();Bitmap b=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);glue.draw(c,1000);drawReplayBrowser(c);
  if(!modal.isEmpty()){buttons.clear();check(drawReplayDialog(c),"Delete modal unhandled");}return b;}
 Button target(float x,float y){for(int i=buttons.size()-1;i>=0;i--)if(buttons.get(i).rect.contains(x,y))return buttons.get(i);throw new AssertionError("No target at "+x+","+y);}
 void activate(float x,float y){Button b=target(x,y);if(b.enabled)b.action.run();}
 static void save(Bitmap b,Path path)throws Exception{ImageIO.write(b.image,"png",path.toFile());}
 Bitmap playback(){buttons.clear();Bitmap b=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);Paint ground=new Paint();ground.setColor(0xff1d231b);c.drawRect(0,0,640,480,ground);drawReplayControls(c);return b;}
 void fixtures(Path out,int count)throws Exception{replays=new NativeReplays(fixtureRoot.resolve("fixtures-"+count).toFile());
  for(int i=0;i<count;i++){byte[] bytes=new byte[32];bytes[0]=(byte)i;File f=replays.save(bytes,String.format(Locale.ROOT,"Replay %02d on Lost Temple",i));f.setLastModified(100000+i);}
  selectedReplay=null;replayOffset=0;modal="";refreshReplays();page="replays";}
 public static void main(String[]args)throws Exception{
 NativeBridge.root=Paths.get(args[0]);Path out=Paths.get(args[1]);NativeArt art=new NativeArt();NativeGlue glue=new NativeGlue(art,"gluload","palnl",false);
 ReplayUi81Test h=new ReplayUi81Test(glue);h.fixtureRoot=Paths.get(args[3]);h.art=art;h.hud.large=glue.large;h.hud.small=glue.small;
 check(glue.layout.get(4)!=null&&glue.layout.get(5)!=null&&glue.layout.get(7)!=null,"Missing original replay controls");
 long now=1000;
 for(int count:new int[]{0,1,9,10,40}){
  h.fixtures(out,count);h.browser();check(h.replayFiles.size()==count,"Wrong replay count");check(h.buttons.size()<=19,"Replay list is not virtualized");
  check(h.replayValid==(count>0),"Empty/populated validity");
  if(count==0){int starts=h.starts;h.activate(500,393);check(h.starts==starts,"Empty list starts a replay");continue;}
  h.tap(358,302,now+=100);near(h.replayOffset,Math.min(22,h.replayMaxOffset()),"Down arrow does not step");h.browser();
  h.tap(358,99,now+=100);near(h.replayOffset,0,"Up arrow does not step");h.browser();
  h.tap(358,201,now+=100);near(h.replayOffset,h.replayMaxOffset()/2,"Track midpoint wrong");h.browser();
  h.touch(0,358,201,now+=100);h.touch(2,358,310,now+20);h.touch(1,358,310,now+40);near(h.replayOffset,h.replayMaxOffset(),"Drag cannot reach final replay");h.browser();
  h.tap(100,300,now+=100);if(count>=10)check(h.selectedReplay.equals(h.replayFiles.get(count-1)),"Final replay not selectable");
  check(!h.replayDetails.isEmpty()&&h.replayPlayers.equals(Arrays.asList(0,1))&&h.replayRaces.equals(Arrays.asList(1,2)),"Replay metadata/player/race list missing");
 }
 h.fixtures(out,40);save(h.browser(),out.resolve("replay-list-top.png"));
 h.replayOffset=h.replayMaxOffset();save(h.browser(),out.resolve("replay-list-bottom.png"));
 File selected=h.selectedReplay;int count=h.replays.list().size();NativeArt.Widget delete=glue.layout.get(7);
 h.activate(delete.x+delete.w/2f,delete.y+delete.h/2f);check(h.modal.equals("replay-delete"),"DELETE opens no confirmation");
 save(h.browser(),out.resolve("replay-delete.png"));h.activate(420,296);check(selected.exists()&&h.modal.isEmpty(),"Cancel deleted replay");
 h.browser();h.activate(delete.x+delete.w/2f,delete.y+delete.h/2f);h.browser();h.activate(220,296);
 check(!selected.exists()&&h.replays.list().size()==count-1&&h.modal.isEmpty(),"DELETE did not remove selected replay");check(h.selectedReplay!=null&&h.selectedReplay.exists(),"Deletion failed to select next entry");
 h.browser();h.activate(280,340);check(h.activity.imports==1,"Import routing");h.activate(100,375);check(h.activity.exports==1,"Export routing");
 NativeArt.Widget ok=glue.layout.get(4);h.activate(ok.x+ok.w/2f,ok.y+ok.h/2f);check(h.started.equals(h.selectedReplay),"OK starts wrong replay");
 byte[] bad=new byte[32];bad[0]=(byte)255;File invalid=h.replays.save(bad,"Broken replay");h.selectReplay(invalid);h.browser();int starts=h.starts;h.activate(ok.x+ok.w/2f,ok.y+ok.h/2f);check(!h.replayValid&&h.starts==starts&&!h.replayNotice.isEmpty(),"Invalid replay can start");
 PortText.load(Files.newInputStream(Paths.get(args[2])));h.refreshReplays();h.selectReplay(h.replayFiles.get(1));
 for(String lang:new String[]{"en","ru","de","es","fr"}){PortText.select(lang);h.modal="";save(h.browser(),out.resolve("replay-list-"+lang+".png"));h.modal="replay-delete";save(h.browser(),out.resolve("replay-delete-"+lang+".png"));}
 PortText.select("en");h.modal="";h.page="game";h.replayPlayers.clear();h.replayPlayers.addAll(Arrays.asList(0,1));
 byte[] wpe=art.read("tileset/badlands.wpe");for(int i=0;i<256;i++)h.hud.palette[i]=Color.rgb(wpe[i*4]&255,wpe[i*4+1]&255,wpe[i*4+2]&255);
 h.hud.dialogGrp=art.read("dlgs/terran.grp");NativeArt.PCX colors=art.pcx("game/tfontgam.pcx",false,-1);h.hud.large=art.font("16",colors,h.hud.palette,1);h.hud.small=art.font("10",colors,h.hud.palette,0);
 Bitmap playback=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(playback);Paint ground=new Paint();ground.setColor(0xff1d231b);c.drawRect(0,0,640,480,ground);h.buttons.clear();h.drawReplayControls(c);save(playback,out.resolve("replay-controls.png"));
 check(h.buttons.size()==4,"Missing playback controls");h.activate(520,389);check(h.replayPaused,"Pause not set");h.activate(520,389);check(!h.replayPaused,"Play not resumed");
 for(int rate:new int[]{2,4,8,1}){h.accumulator=100;h.activate(616,389);check(h.replayRate==rate&&h.accumulator==0,"Speed cycle/accumulator");}
 for(int owner:new int[]{0,1,-1}){
  NativeHud previous=h.hud;int previousMusic=h.musicCalls;h.activate(550,420);check(NativeBridge.owner==owner,"Player view cycle");
  int expectedRace=owner==0?1:2;check(h.missionRace==expectedRace,"View did not choose the player's race");
  if(owner==1)check(previous.closed&&h.hud!=previous&&h.hud.race==2&&h.musicCalls==previousMusic+1,"Race switch did not replace HUD/music");
  else check(h.hud==previous&&!previous.closed&&h.musicCalls==previousMusic,"Same race/everyone unnecessarily replaced HUD");
  h.playback();
 }
 for(String lang:new String[]{"en","ru","de","es","fr"}){PortText.select(lang);
  for(boolean paused:new boolean[]{false,true}){h.replayPaused=paused;check(h.hud.small.measure(paused?"Play":"Pause")<=96,"Localized playback action needs truncation");check(h.hud.small.measure("Everyone")<=134&&h.hud.small.measure("Player 2")<=134&&h.hud.small.measure("Restart")<=134,"Localized playback labels need truncation");save(h.playback(),out.resolve("replay-controls-"+lang+(paused?"-paused":"")+".png"));
   for(Button bt:h.buttons)check(bt.rect.left>=484&&bt.rect.right<=640&&bt.rect.top>=348&&bt.rect.bottom<=480,"Playback control leaves its panel");
  }
 }
 PortText.select("en");h.replayPaused=false;h.playback();
 NativeBridge.frame=NativeBridge.end;h.activate(520,389);check(!h.replayPaused,"End-of-replay Play incorrectly resumes");
 h.playingReplay=h.selectedReplay;h.activate(550,454);check(h.started.equals(h.playingReplay),"Restart targets wrong replay");
 System.out.println("PASS "+checks+" replay UI checks: original artwork; virtualized 0–40 files; arrows/track/drag/final selection; metadata; import/export; selected-file DELETE/cancel; invalid-file rejection; pause/speed/player/restart controls; race HUD/music lifecycle; five-language browser and playback captures");
 }
}
class NativeMaps{static String label(File f){return f==null?"Practice map":f.getName();}}
class MatchSetup{static final String[]RACES={"Zerg","Terran","Protoss"};}
'''
sources['org/openbw/androidtest/ReplayUi81Test.java']=harness
hud=(src/'NativeHud.java').read_text()
def hud_method(name):
 m=re.search(r'^  (?:static )?(?:void|Bitmap) '+name+r'\(',hud,re.M);assert m,name
 end=hud.index('{',m.end())+1;depth=1
 while depth:
  if hud[end]=='{':depth+=1
  elif hud[end]=='}':depth-=1
  end+=1
 return hud[m.start():end]
sources['org/openbw/androidtest/NativeHud.java']=sources['org/openbw/androidtest/NativeHud.java'].replace(' static final int WORLD_BOTTOM=376;',
 ''' NativeArt.Font large,small;byte[]dialogGrp;int[]palette=new int[256];Map<String,Bitmap>panels=new HashMap<>();boolean closed;NativeHud(){}void close(){closed=true;}
 NativeHud(NativeArt art,int selectedRace,Object maps){race=selectedRace;byte[] wpe=art.read("tileset/badlands.wpe");for(int i=0;i<256;i++)palette[i]=Color.rgb(wpe[i*4]&255,wpe[i*4+1]&255,wpe[i*4+2]&255);dialogGrp=art.read("dlgs/"+new String[]{"zerg","terran","protoss"}[race]+".grp");NativeArt.PCX colors=art.pcx("game/tfontgam.pcx",false,-1);large=art.font("16",colors,palette,1);small=art.font("10",colors,palette,0);}
'''+hud_method('panel')+'\n static final int WORLD_BOTTOM=376;')
sources['org/openbw/androidtest/NativeBridge.java']=sources['org/openbw/androidtest/NativeBridge.java'].replace('static int commands;static void command(int a,int b,int c,int d,int e){commands++;}static int value(int a,int b){return 0;}',r'''static int commands,owner=-1,frame=480,end=17280;
 static void command(int a,int b,int c,int d,int e){commands++;if(a==31)owner=b;}static int value(int a,int b){return a==8?frame:a==26?end:a==27?owner:0;}
 static byte[] replayInfo(byte[] bytes){if(bytes[0]==(byte)255)throw new IllegalArgumentException("Invalid replay data");return "17280\t1\t2\tLost Temple\n0\t1\tPlayer One\n1\t2\tPlayer Two".getBytes(java.nio.charset.StandardCharsets.ISO_8859_1);}''')
for name,text in sources.items():
 target=b/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
real=[src/n for n in ['NativeReplays.java','NativeArt.java','NativeGlue.java','NativeResults.java','CommandHint.java','MenuLabels.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
subprocess.run(['javac','-d',str(b/'classes'),*[str(b/n) for n in sources],*map(str,real)],check=True)
with tempfile.TemporaryDirectory(prefix='stardroid-replay-ui81-') as fixture_root:
 result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes'),'org.openbw.androidtest.ReplayUi81Test',str(assets),str(b),str(r/'app/src/main/assets/native/ui-languages.tsv'),fixture_root],capture_output=True,text=True)
print(result.stdout+result.stderr,end='');result.check_returncode()
files=[src/'NativeSurface.java',src/'NativeReplays.java',src/'NativeArt.java',src/'NativeGlue.java',r/'app/src/main/assets/native/ui-languages.tsv',Path(__file__)]
(r/'validation/replay-ui-v81.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'canvas':'AWT shim using production native artwork/menu/input methods; replay parser/clock mocked','methods':names+['touch'],'result':result.stdout.strip(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},indent=2)+'\n')

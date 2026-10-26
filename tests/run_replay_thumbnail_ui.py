#!/usr/bin/env python3
"""Render and exercise the production replay browser, delete confirmation and playback UI.
Uses original locally imported artwork through the existing bounded AWT/Android shim.
Native replay parsing/playback are covered separately; metadata/clock are mocked here.
"""
from pathlib import Path
import argparse,ast,hashlib,json,re,subprocess,shutil,tempfile
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest'
parser=argparse.ArgumentParser()
parser.add_argument('--report-prefix',default='replay-thumbnail-ui')
args=parser.parse_args()
assert re.fullmatch(r'[a-z0-9-]+',args.report_prefix), 'Invalid report prefix'
b=r/'build-native'/args.report_prefix;b.mkdir(parents=True,exist_ok=True)
assets=b/'assets';shutil.copytree(r/'build-native/replay-ui81/assets',assets,dirs_exist_ok=True)
archives=[(0,r/'build-native/reign79/core/STARDAT.MPQ'),(1,r/'build-native/reign79/core/BROODAT.MPQ'),(2,r/'build-native/reign79/core/patch_rt.mpq'),(4,r.parent/'reign-data/StarCraft.mpq')]
def get(name):
 found=[]
 for slot,archive in archives:
  target=assets/str(slot)/name;target.parent.mkdir(parents=True,exist_ok=True)
  call=subprocess.run([str(r/'build-native/reign79/extract'),str(archive),name,str(target)],capture_output=True)
  if call.returncode:target.unlink(missing_ok=True)
  else:found.append(target.read_bytes())
 return found
for data in get('rez/gluload.bin')+get('rez/glucustm.bin'):
 for name in {s.decode('cp1252').replace('\\','/').lower() for s in re.findall(rb'(?:glue|GLUE)[^\x00]*?\.[pP][cC][xX]',data)}:get(name)
for name in ['glue/load/pinfo.pcx','glue/chatroom/plist.pcx','glue/chatroom/pjoin.pcx','dlgs/zerg.grp','dlgs/protoss.grp','rez/gluscore.bin','glue/scoretv/pmain.pcx','glue/scoretv/pinset.pcx','glue/scoretv/scorebox.pcx','glue/scoretv/untab.pcx','glue/scoretv/iscore.grp','glue/paltv/backgnd.pcx','glue/paltv/tfont.pcx','glue/paltv/teffect.pcx']:get(name)
for tileset in ['badlands','platform','install','ashworld','jungle','desert','ice','twilight']:
 for ext in ['cv5','vx4','vr4','wpe']:get('tileset/'+tileset+'.'+ext)
preview=assets/'0/preview/scenario.chk';preview.parent.mkdir(parents=True,exist_ok=True)
subprocess.run([str(r/'build-native/reign79/extract'),str(r/'app/src/main/assets/native/weave.scx'),'staredit/scenario.chk',str(preview)],check=True)
# A separate asset tree really omits replay assets, as older imports do.
legacy=b/'legacy-assets';shutil.copytree(assets,legacy,dirs_exist_ok=True)
for file in legacy.glob('*/rez/gluload.bin'):file.unlink()
for file in legacy.glob('*/glue/load/*'):file.unlink()

# Reuse the exact Canvas/input shims from controller verification, without running it.
tree=ast.parse((r/'tests/run_gamepad81.py').read_text());active=False
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='old' for t in node.targets):active=True
 if active:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='harness' for t in node.targets):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<replay canvas shim>','exec'))
harness=sources.pop('org/openbw/androidtest/MapScroll79Test.java')
harness=harness[:harness.index(' public static void main(String[] args)')]
harness=harness.replace('MapScroll79Test','ReplayThumbnailUiTest')
harness=re.sub(r' void redButton\(Canvas c[^\n]+\n','',harness)
harness=harness.replace('void pickNativeMap(){}','void pickNativeMap(){}int imports,exports;void pickReplay(){imports++;}void saveReplay(byte[] bytes,ReplayThumbnailUiTest view,long request){exports++;}void recordReplay(byte[] bytes,ReplayThumbnailUiTest view,long request){view.replayRecorded(request,\"Replay saved\");}')
harness=harness.replace('int selections,imports;','''int selections,imports,logicalWidth=640,starts;File started;
 Path fixtureRoot;NativeReplays replays;List<File>replayFiles=Collections.emptyList();File selectedReplay,playingReplay;
 List<Integer>replayPlayers=new ArrayList<>(),replayRaces=new ArrayList<>();NativeArt art;Object commandMaps;int missionRace=1,musicCalls;void music(String phase){musicCalls++;}String replayDetails="",replayNotice="";boolean replayValid,replayExpansion,replayPaused;
 float replayOffset,menuHoverX=-1,menuHoverY=-1;int replayRate=1;double accumulator;Paint paint=new Paint();
 NativeResults results,replaySaveScreen;long replaySaveRequest,replayBrowserGeneration;Runnable replayAcknowledgement;boolean replayGame=true,replaySeeking;
 NativeArt.Font replayLargeSource,replaySmallSource,replayLargeGreen,replaySmallGreen;Bitmap replayThumbnail;boolean replayPreviewUnavailable;final NativeMapPreview mapPreviews=new NativeMapPreview();
 void enqueue(Runnable r){r.run();}
 float padX,padY;boolean padNativeDrag,padTouchDrag;long padClickAt;String padDragPage="",padDragModal="";int physicalWidth=640,physicalHeight=480;
 float cameraBottom(float x){return 376;}

 void startReplay(File f){started=f;starts++;}void showCampaign(){}void navigate(Runnable action){action.run();}void drawMenuUnavailable(Canvas c,Runnable action){}
''')
text=(src/'NativeSurface.java').read_text()
def production(name):
 m=re.search(r'^  (?:private )?(?:static )?(?:void|boolean|int|float|String|RectF|NativeArt.Font) '+name+r'\(',text,re.M);assert m,name
 end=text.index('{',m.end())+1;depth=1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[m.start():end]
names=['font','text','panel','body','fallback','uiLine','redBorder','menuHot','menuColor','redButton','glueButton','button','menuButton','replayListBounds','replayMaxOffset','replayTime','selectReplay','refreshReplays','drawReplayBrowser','drawReplayDetails','drawReplayScrollbar','replayFont','replayPanel','replayMessage','drawReplayDialog','replayImported','saveCurrentReplay','replayRecorded','replayExported','presentReplayAcknowledgement','replayMenuAction','replayButton','openSelectedReplay','seekReplay','drawReplayControls','gamepadWorld','gamepadClick','gamepadTouch','resetGamepadDrag']
harness+='\n'.join(production(n) for n in names)
harness+='''
 Bitmap browser(){presentReplayAcknowledgement();buttons.clear();Bitmap b=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);glue.draw(c,1000);drawReplayBrowser(c);
  if(!modal.isEmpty()){buttons.clear();check(drawReplayDialog(c),"Replay modal unhandled");}return b;}
 Button target(float x,float y){for(int i=buttons.size()-1;i>=0;i--)if(buttons.get(i).rect.contains(x,y))return buttons.get(i);throw new AssertionError("No target at "+x+","+y);}
 void activate(float x,float y){Button b=target(x,y);if(b.enabled)b.action.run();}
 static void save(Bitmap b,Path path)throws Exception{ImageIO.write(b.image,"png",path.toFile());}
 Bitmap playback(){buttons.clear();Bitmap b=Bitmap.createBitmap(logicalWidth,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);Paint ground=new Paint();ground.setColor(0xff1d231b);c.drawRect(0,0,640,480,ground);drawReplayControls(c);return b;}
 void fixtures(Path out,int count)throws Exception{replays=new NativeReplays(fixtureRoot.resolve("fixtures-"+count).toFile());
  for(int i=0;i<count;i++){byte[] bytes=new byte[32];bytes[0]=(byte)i;File f=replays.save(bytes,String.format(Locale.ROOT,"Replay %02d on Lost Temple",i));f.setLastModified(100000+i);}
  selectedReplay=null;replayOffset=0;modal="";refreshReplays();page="replays";}
 static boolean inside(RectF inner,RectF outer){return inner.left>=outer.left&&inner.right<=outer.right&&inner.top>=outer.top&&inner.bottom<=outer.bottom;}
 static void unchanged(Bitmap before,Bitmap after,RectF area,String why){for(int y=(int)area.top;y<area.bottom;y++)for(int x=(int)area.left;x<area.right;x++)check(before.image.getRGB(x,y)==after.image.getRGB(x,y),why+" "+x+","+y);}
 static Bitmap base(NativeGlue glue){Bitmap b=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);glue.draw(new Canvas(b),1000);return b;}
 public static void main(String[]args)throws Exception{
 Path out=Paths.get(args[1]);PortText.load(Files.newInputStream(Paths.get(args[2])));long now=1000;
 for(boolean legacy:new boolean[]{false,true}){
  NativeBridge.root=Paths.get(legacy?args[4]:args[0]);NativeArt art=new NativeArt();NativeGlue glue=new NativeGlue(art,legacy?"glucustm":"gluload","palnl",false);
  ReplayThumbnailUiTest h=new ReplayThumbnailUiTest(glue);h.fixtureRoot=Paths.get(args[3]).resolve(legacy?"legacy":"new");h.art=art;h.hud.large=glue.large;h.hud.small=glue.small;
  if(legacy){boolean absent=false;try{new NativeGlue(art,"gluload","palnl",false);}catch(Exception expected){absent=true;}check(absent,"Legacy fixture unexpectedly contains gluload");}
  RectF box=h.replayListBounds();near(box.top,legacy?130:92,"Wrong original list placement");near(box.height(),legacy?118:218,"Wrong original list height");
  for(int count:new int[]{0,1,5,6,9,10,40}){
   h.fixtures(out,count);Bitmap baseline=base(glue),browser=h.browser();check(h.replayFiles.size()==count,"Wrong replay count");check(h.buttons.size()<=Math.ceil(box.height()/22)+10,"List is not virtualized");
   check(h.replayValid==(count>0),"Empty/populated validity");
   if(legacy)unchanged(baseline,browser,new RectF(60,92,348,125),"Filename leaked above original legacy red window");
   unchanged(baseline,browser,new RectF(box.right,box.top,374,box.bottom),"Scrollbar left original list window");
   for(Button bt:h.buttons)if(bt.rect.top>=box.top&&bt.rect.top<box.bottom)check(inside(bt.rect,box),"List/rail touch target leaves original window");
   if(count==0){int starts=h.starts;h.activate(500,393);check(h.starts==starts,"Empty list starts replay");continue;}
   float sx=box.right-10;
   h.tap(sx,box.bottom-8,now+=100);near(h.replayOffset,Math.min(22,h.replayMaxOffset()),"Down arrow step");h.browser();
   h.tap(sx,box.top+8,now+=100);near(h.replayOffset,0,"Up arrow step");h.browser();
   h.tap(sx,box.top+box.height()/2,now+=100);near(h.replayOffset,h.replayMaxOffset()/2,"Track midpoint");h.browser();
   float thumb=box.top+23+(box.height()-46)*.5f;
   h.touch(0,sx,thumb+3,now+=100);near(h.replayOffset,h.replayMaxOffset()/2,"Grabbing thumb jumps");h.browser();
   h.touch(2,sx,box.bottom+20,now+20);near(h.replayOffset,h.replayMaxOffset(),"Drag cannot reach final replay");h.touch(1,sx,box.bottom+20,now+40);h.browser();
   h.tap(box.left+20,box.bottom-3,now+=100);if(count*22>box.height())check(h.selectedReplay.equals(h.replayFiles.get(count-1)),"Final replay not selectable");
  }
  h.fixtures(out,40);check(h.replayThumbnail!=null&&!h.replayPreviewUnavailable,"No embedded map thumbnail");
  for(String lang:new String[]{"en","ru","de","es","fr"}){
   PortText.select(lang);Bitmap browser=h.browser();
   Button deletion=h.target(180,430);near((deletion.rect.left+deletion.rect.right)/2,180,"Delete not centered in left panel");
   check(deletion.rect.top>h.target(100,343).rect.bottom&&deletion.rect.top>h.target(280,343).rect.bottom,"Delete not below Import/Export");
   check(deletion.rect.bottom<460,"Delete leaves lower artwork");
   Bitmap expected=base(glue);int ok=legacy?12:4,cancel=legacy?13:5;
   glue.label(new Canvas(expected),ok,"OK",true);glue.label(new Canvas(expected),cancel,"Cancel",true);
   unchanged(expected,browser,glue.layout.get(ok).rect(),"Replay OK differs from original button font/artwork");
   unchanged(expected,browser,glue.layout.get(cancel).rect(),"Replay Cancel differs from original button font/artwork");
   save(browser,out.resolve((legacy?"legacy-":"new-")+"buttons-"+lang+".png"));
   for(boolean enabled:new boolean[]{false,true})for(boolean hover:new boolean[]{false,true})
    for(String label:new String[]{"Import Replay","Export","Delete"}){
     int x=44,y=332,w=164,hh=22;h.buttons.clear();h.menuHoverX=hover?x+10:-1;h.menuHoverY=hover?y+10:-1;
     Bitmap actual=base(glue);h.replayButton(new Canvas(actual),label,x,y,w,hh,()->{},enabled);
     // Independent reference: the original menu's BIN-style label renderer.
     NativeArt.Widget reference=new NativeArt.Widget();reference.id=32000;reference.type=14;
     reference.x=x;reference.y=y;reference.w=w;reference.h=hh;reference.tx=4;reference.rw=w-4;reference.rh=hh;
     reference.flags=0x2204008;glue.layout.widgets.add(reference);glue.hot=hover?reference.id:-1;
     Bitmap referenceShot=base(glue);glue.label(new Canvas(referenceShot),reference.id,label,enabled);
     unchanged(referenceShot,actual,new RectF(x+4,y+1,x+w-4,y+hh-1),"Replay button is filled or differs from original font/color");
     glue.layout.widgets.remove(reference);glue.hot=-1;
    }
   h.menuHoverX=h.menuHoverY=-1;
  }
  PortText.select("en");h.browser();
  int reads=NativeBridge.scenarioReads;Bitmap held=h.replayThumbnail;for(int i=0;i<20;i++)h.browser();check(NativeBridge.scenarioReads==reads&&held==h.replayThumbnail,"Preview regenerated on render");
  h.selectReplay(null);check(h.replayThumbnail==null&&!h.replayValid,"Empty selection retained thumbnail");h.refreshReplays();
  byte[] unavailable=new byte[32];unavailable[0]=(byte)253;File noPreview=h.replays.save(unavailable,"No preview");h.selectReplay(noPreview);check(h.replayThumbnail==null&&h.replayPreviewUnavailable&&h.replayValid,"Missing preview prevents playback or retains previous map");h.replays.delete(noPreview);h.refreshReplays();
  File selected=h.selectedReplay;h.browser();h.activate(180,430);check(h.modal.equals("replay-delete"),"DELETE opens no confirmation");
  save(h.browser(),out.resolve((legacy?"legacy-":"new-")+"delete.png"));h.activate(420,296);check(selected.exists()&&h.modal.isEmpty(),"Cancel deleted replay");
  h.browser();h.activate(180,430);h.browser();h.activate(220,296);check(!selected.exists()&&h.replays.list().size()==39,"DELETE failed");
  h.browser();h.activate(100,343);h.activate(280,343);check(h.activity.imports==1&&h.activity.exports==1,"Import/export adjacent routing");
  h.activate(500,393);check(h.started.equals(h.selectedReplay),"OK targets wrong file");
  byte[] bad=new byte[32];bad[0]=(byte)255;File invalid=h.replays.save(bad,"Broken replay");h.selectReplay(invalid);check(!h.replayValid&&h.replayThumbnail==null&&h.modal.equals("replay-notice"),"Invalid replay error retained previous thumbnail");h.browser();h.activate(320,296);check(h.modal.isEmpty(),"Error OK did not dismiss");h.replays.delete(invalid);h.refreshReplays();
  byte[] longBytes=new byte[32];longBytes[1]=66;File longFile=h.replays.save(longBytes,"A very long replay filename that must remain entirely within the original red window even in legacy imports and smaller lists");h.refreshReplays();h.selectReplay(longFile);
  h.replayDetails="A very long original map title\\nBrood War\\n12:00";for(int n=0;n<8;n++)h.replayDetails+="\\nPlayer with a long name "+n+" · Protoss";
  int lines=glue.small.lines(h.replayDetails,190).size();if(lines*16>(legacy?244:224))check(glue.tiny.lines(h.replayDetails,190).size()*glue.tiny.height<=(legacy?244:224),"Eight-player metadata cannot fit");
  for(String lang:new String[]{"en","ru","de","es","fr"}){
   PortText.select(lang);h.modal="";h.replayOffset=0;save(h.browser(),out.resolve((legacy?"legacy-":"new-")+"list-"+lang+".png"));
   h.replayOffset=h.replayMaxOffset();save(h.browser(),out.resolve((legacy?"legacy-":"new-")+"list-bottom-"+lang+".png"));
   h.modal="replay-delete";save(h.browser(),out.resolve((legacy?"legacy-":"new-")+"delete-"+lang+".png"));
  }
  PortText.select("en");h.modal="";h.replayExported(h.replayBrowserGeneration,"Replay saved");h.browser();check(h.modal.equals("replay-notice"),"Export saved notice missing");h.activate(320,296);
  h.modal="gamepad";h.replayExported(h.replayBrowserGeneration,"Replay saved");h.presentReplayAcknowledgement();check(h.modal.equals("gamepad"),"Async save steals settings");h.modal="";h.presentReplayAcknowledgement();check(h.modal.equals("replay-notice"),"Deferred save acknowledgment lost");h.modal="";
  h.replayExported(h.replayBrowserGeneration-1,"Replay saved");h.presentReplayAcknowledgement();check(h.modal.isEmpty(),"Stale export request steals browser");
  if(legacy)continue;
  h.results=new NativeResults(art,1,true,"0\t0");h.page="results";h.hud=null;h.glue=null;h.saveCurrentReplay();h.presentReplayAcknowledgement();check(h.modal.equals("replay-notice"),"Saved result does not show in game");
  for(String lang:new String[]{"en","ru","de","es","fr"}){PortText.select(lang);Bitmap shot=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);h.buttons.clear();h.results.draw(new Canvas(shot),1000);h.drawReplayDialog(new Canvas(shot));save(shot,out.resolve("saved-"+lang+".png"));}
  h.activate(320,296);check(h.modal.isEmpty(),"Saved OK does not dismiss");h.modal="gamepad";h.replayRecorded(h.replaySaveRequest,"Replay saved");h.presentReplayAcknowledgement();check(h.modal.equals("gamepad"),"Recording acknowledgment steals settings");h.modal="";h.presentReplayAcknowledgement();check(h.modal.equals("replay-notice"),"Recording acknowledgment lost after settings");h.modal="";
  h.replayRecorded(h.replaySaveRequest,"Replay saved");h.page="game";h.presentReplayAcknowledgement();check(h.modal.isEmpty(),"Late saved notice opens on another screen");
  h.hud=new NativeHud(art,1,null);h.replayPlayers.clear();h.replayPlayers.addAll(Arrays.asList(0,1));h.replayRaces.clear();h.replayRaces.addAll(Arrays.asList(1,2));h.activeGame=true;
  for(int width:new int[]{640,960}){
   h.logicalWidth=width;h.physicalWidth=width;float x=width-156;h.playback();check(h.buttons.size()==5,"Missing working seek control");h.replayPaused=true;h.replayRate=4;
   h.touch(0,x+13,380,now+=100);check(NativeBridge.seekTarget==0,"Seek beginning");h.touch(2,x+77,380,now+20);check(NativeBridge.seekTarget==NativeBridge.end/2,"Seek midpoint");h.touch(2,x+141,380,now+40);h.touch(1,x+141,380,now+60);check(NativeBridge.seekTarget==NativeBridge.end,"Seek end");check(h.replayPaused&&h.replayRate==4,"Seek changed pause/rate");
   h.playback();h.padX=x+13;h.padY=380;android.os.SystemClock.now=now+=100;h.gamepadClick(true);check(h.padTouchDrag&&!h.padNativeDrag,"Gamepad starts world selection over seek");h.padX=x+141;h.gamepadTouch(MotionEvent.ACTION_MOVE,now+20);h.gamepadClick(false);check(NativeBridge.seekTarget==NativeBridge.end,"Gamepad seek drag");
   h.playback();h.activate(x+45,408);check(!h.replayPaused,"Play failed");h.activate(x+45,408);check(h.replayPaused,"Pause failed");
   for(int rate:new int[]{8,1,2,4}){h.accumulator=10;h.activate(x+130,408);check(h.replayRate==rate&&h.accumulator==0,"Speed cycle");}
   for(int owner:new int[]{0,1,-1}){h.activate(x+60,435);check(NativeBridge.owner==owner,"View cycling");h.playback();}
   for(String lang:new String[]{"en","ru","de","es","fr"}){PortText.select(lang);for(int seeking:new int[]{0,1}){NativeBridge.seeking=seeking;save(h.playback(),out.resolve("playback-"+width+"-"+lang+(seeking==1?"-seeking":"")+".png"));for(Button bt:h.buttons)check(inside(bt.rect,new RectF(x,348,width,480)),"Playback target leaves panel");}}
   NativeBridge.seeking=0;h.playingReplay=h.selectedReplay;h.activate(x+60,462);check(h.started.equals(h.playingReplay),"Restart wrong replay");
  }
 }
 System.out.println("PASS "+checks+" replay thumbnail UI checks: transparent original-font buttons, native OK/Cancel pixel equality, centered title-case Delete, five-language enabled/disabled/hover parity; original and legacy import artwork; in-window list/text/rail/touch bounds; long names; 0–40 files; arrows/track/thumb drag; errors/delete/save/export modals; stale/deferred async acknowledgments; real touch and gamepad seek dispatch; pause/rate/view/restart; five languages; 640/960 layouts");
 }

}
class NativeMaps{static String label(File f){return f==null?"Practice map":f.getName();}}
class MatchSetup{static final String[]RACES={"Zerg","Terran","Protoss"};}
'''
sources['org/openbw/androidtest/ReplayThumbnailUiTest.java']=harness
sources['android/graphics/Color.java']=sources['android/graphics/Color.java'].replace('public class Color{','public class Color{public static final int BLACK=0xff000000;')
sources['android/os/SystemClock.java']='package android.os;public class SystemClock{public static long now;public static long uptimeMillis(){return now;}}'
sources['android/view/MotionEvent.java']=sources['android/view/MotionEvent.java'].replace(' int action;', ' public static MotionEvent obtain(long start,long end,int action,float x,float y,int flags){return new MotionEvent(action,x,y,end);}public void recycle(){} int action;')

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
sources['org/openbw/androidtest/NativeBridge.java']=sources['org/openbw/androidtest/NativeBridge.java'].replace('static int commands;static void command(int a,int b,int c,int d,int e){commands++;}static int value(int a,int b){return 0;}',r'''static int commands,owner=-1,frame=480,end=17280,seeking,seekTarget;static void replaySeek(int target){seekTarget=target;seeking=target==frame?0:1;}static byte[] replay(){return new byte[32];}
 static void command(int a,int b,int c,int d,int e){commands++;if(a==31)owner=b;}static int value(int a,int b){return a==8?frame:a==26?end:a==27?owner:a==28?seeking:a==29?seekTarget:0;}
 static int scenarioReads;static byte[] replayScenario(byte[] bytes){scenarioReads++;if(bytes[0]==(byte)253)return null;try{return java.nio.file.Files.readAllBytes(root.resolve("0/preview/scenario.chk"));}catch(Exception e){throw new RuntimeException(e);}}
 static byte[] replayInfo(byte[] bytes){if(bytes[0]==(byte)255)throw new IllegalArgumentException("Invalid replay data");return "17280\t1\t2\tLost Temple\n0\t1\tPlayer One\n1\t2\tPlayer Two".getBytes(java.nio.charset.StandardCharsets.ISO_8859_1);}''')
for name,text in sources.items():
 target=b/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
real=[src/n for n in ['NativeReplays.java','NativeMapPreview.java','NativeArt.java','NativeGlue.java','NativeResults.java','CommandHint.java','MenuLabels.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
subprocess.run(['javac','-d',str(b/'classes'),*[str(b/n) for n in sources],*map(str,real)],check=True)
with tempfile.TemporaryDirectory(prefix='stardroid-replay-thumbnail-ui-') as fixture_root:
 result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes'),'org.openbw.androidtest.ReplayThumbnailUiTest',str(assets),str(b),str(r/'app/src/main/assets/native/ui-languages.tsv'),fixture_root,str(legacy)],capture_output=True,text=True)
print(result.stdout+result.stderr,end='');result.check_returncode()
files=[src/'MainActivity.java',src/'NativeSurface.java',src/'NativeReplays.java',src/'NativeMapPreview.java',src/'NativeArt.java',src/'NativeGlue.java',r/'app/src/main/assets/native/ui-languages.tsv',Path(__file__)]
(r/'validation'/f'{args.report_prefix}.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'canvas':'AWT shim using production native artwork/menu/input methods; replay parser/clock mocked','methods':names+['touch'],'result':result.stdout.strip(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},indent=2)+'\n')

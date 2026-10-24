#!/usr/bin/env python3
"""Render production setup/lobby methods, original assets and actual map previews on AWT."""
from pathlib import Path
import ast,subprocess,json,hashlib,struct,sys
r=Path(__file__).resolve().parents[1];b=r/'build-native/ui56';assets=b/'assets';b.mkdir(parents=True,exist_ok=True)
data=Path(sys.argv[1]);extract=b/'extract-interface'
subprocess.run(['g++','-std=c++17','-O0','-I'+str(r/'native-engine'),str(r/'tests/extract_interface46.cpp'),'-o',str(extract)],check=True,capture_output=True)
old=ast.parse((r/'tests/run_results46.py').read_text());sources=next(ast.literal_eval(n.value)for n in old.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='sources'for t in n.targets));sources.pop('org/openbw/androidtest/Results46Harness.java')
sources['android/graphics/Canvas.java']=sources['android/graphics/Canvas.java'].replace('public void clipRect(float','public void clipRect(RectF r){clipRect(r.left,r.top,r.right,r.bottom);}public void clipRect(float')
def get(name):
 target=assets/name;target.parent.mkdir(parents=True,exist_ok=True)
 for a in ['patch_rt.mpq','BROODAT.MPQ','STARDAT.MPQ']:
  if subprocess.run([str(extract),str(data/a),name,str(target)],capture_output=True).returncode==0:return target.read_bytes()
 return b''
def u32(b,p):return int.from_bytes(b[p:p+4],'little')
for name in ['gluconn','gluchat','glujoin','glucustm']:
 raw=get('rez/'+name+'.bin');pos=u32(raw,66)
 while pos:
  off=u32(raw,pos+20);label=raw[off:raw.index(b'\0',off)].decode('cp1252') if off else ''
  if label.lower().endswith('.pcx'):get(label.replace('\\','/').lower())
  pos=u32(raw,pos)
for name in ['dlg.grp','tile.grp','backgnd.pcx','tfont.pcx','teffect.pcx','pok.pcx','pcancel.pcx']:get('glue/palnl/'+name)
for prefix in ['font/','files/font/']:
 for n in ['8','10','14','16','16x']:get(prefix+'font'+n+'.fnt')
assert get('sound/glue/countdown.wav')[:4]==b'RIFF', 'Original countdown sound missing'
for tileset in ['badlands','platform','install','ashworld','jungle','desert','ice','twilight']:
 for ext in ['cv5','vx4','vr4','wpe']:get('tileset/'+tileset+'.'+ext)
subprocess.run([str(extract),str(r/'app/src/main/assets/native/weave.scx'),'staredit/scenario.chk',str(assets/'weave.chk')],check=True)
src=r/'app/src/main/java/org/openbw/androidtest';surface=(src/'NativeSurface.java').read_text()
def method(name):
 start=surface.index('  private ',surface.index(' '+name+'(')-35) if False else None
 import re
 m=re.search(r'  private [^\n]+\b'+name+r'\(',surface);start=m.start();end=surface.find('\n  private ',m.end())
 return surface[start:end]
methods='\n'.join(method(n)for n in ['drawNearby','drawCustom','drawMapBrowser','drawMapThumbnail','customLabel','customSelect','mapMaxOffset','glueButton','uiLine','redButton','redBorder','menuColor','menuHot'])
sources['org/openbw/androidtest/Ui56Harness.java']='''package org.openbw.androidtest;
import android.graphics.*;import java.util.*;import java.io.*;import java.nio.file.*;import javax.imageio.ImageIO;
public class Ui56Harness {
 float menuHoverX=-1,menuHoverY=-1;NativeGlue glue;RoomMatch nearby;int movingSlot=-1;boolean chatEditing;String chatDraft="";NativeNearby nearbyRadio=new NativeNearby();int customRace=1;boolean expansion,multiplayerSetup,nearbyExpansion=true,multiplayerSaves,nearbyResuming;File customMap;boolean nearbyWifi=true;int nearbyPage;String nearbyTransport="Wi-Fi Direct connected",nearbyStatus="Choose a connection",nearbyStage="connection",selectedNearby="";
 MatchSetup customSetup=new MatchSetup(false),nearbySetup=new MatchSetup(true);String selectedProfile="Player",customName="Weave",mapPreviewError="",mapImportStatus="",hint="",modal="";int customStarts=8,customWidth=64,customHeight=64;String customTileset="Desert";Bitmap mapThumbnail;
 LinkedHashMap<String,String> nearbyGames=new LinkedHashMap<>();ArrayList<Button>buttons=new ArrayList<>();List<File>customMaps=new ArrayList<>();RectF mapViewport=new RectF(60,130,328,240);float mapOffset;Paint paint=new Paint();Runnable pendingScreen;Activity activity=new Activity();
 static class Button {RectF rect;Runnable action;boolean enabled,vertical;java.util.function.Consumer<Float>slider;Button(RectF r,Runnable a,boolean e){rect=r;action=a;enabled=e;}}
 static class Activity{void pickNativeMap(){}void runOnUiThread(Runnable r){}}
 void text(Canvas c,String s,float x,float y,int width,int align,int color){glue.large.draw(c,s,x,y,width,align,color,0);}
 void body(Canvas c,String s,float x,float y,int width,int height){c.save();c.clipRect(x,y,x+width,y+height);glue.small.draw(c,s,x,y,width,0,2,16);c.restore();}
 void button(Canvas c,String s,float x,float y,float w,float h,Runnable action,boolean enabled){c.drawBitmap(glue.panel(Math.round(w),Math.round(h),true),x,y,NativeArt.PIXELS);text(c,s,x+3,y+(h-glue.large.height)/2,(int)w-6,1,enabled?3:5);add(new RectF(x,y,x+w,y+h),action,enabled);}
 void add(RectF r,Runnable action,boolean enabled){buttons.add(new Button(r,action,enabled));}
 void hostCustom(){}void joinNearby(){}void createNearby(){}void showNearby(){}void showMain(){}void showCampaign(){}void navigate(Runnable r){}void openSaves(boolean w){}void lobbySlot(int slot){}void changeLobbySetting(int field){}void openChat(){}void sendChat(){}void startSkirmish(int race,File map){}void selectCustomMap(File map){customMap=map;}
'''+methods+'''
 public static void main(String[] args)throws Exception {
  NativeBridge.root=Paths.get(args[0]);NativeArt art=new NativeArt();Path output=Paths.get(args[1]);byte[] chk=Files.readAllBytes(NativeBridge.root.resolve("weave.chk"));Map<String,byte[]>chunks=new HashMap<>();
  for(int p=0;p+8<=chk.length;){int n=NativeArt.u32(chk,p+4);chunks.put(new String(chk,p,4,NativeArt.CP),Arrays.copyOfRange(chk,p+8,p+8+n));p+=8+n;}
  Bitmap thumbnail=new NativeMapPreview().create(chunks,64,64);ImageIO.write(thumbnail.image,"png",output.resolve("map-preview.png").toFile());
  for(int state=0;state<7;state++) {
   Ui56Harness h=new Ui56Harness();h.mapThumbnail=thumbnail;
   String bin=state==0?"gluconn":state==1?"glujoin":state<5?"gluchat":"glucustm";h.nearbyStage=state==0?"connection":state==1?"join":"lobby";
   h.glue=new NativeGlue(art,bin,"palnl",true);h.glue.elapsed=700;h.customSetup.starts=h.nearbySetup.starts=8;
   for(int i=2;i<8;i++){h.nearbySetup.controllers[i]=2;h.nearbySetup.races[i]=i%3;}
   for(int i=1;i<8;i++){h.customSetup.controllers[i]=2;h.customSetup.races[i]=i%3;}
   if(state>0&&state<5) {
    h.nearby=new RoomMatch(state!=4,1,"Player",null,null,null,()->0);h.nearby.setup=h.nearbySetup;h.nearby.connected=state>1;h.nearby.ready=state>1;h.nearby.peerName="Guest";h.nearby.occupants[0]=0;h.nearby.names[0]="A very long host profile name";h.nearby.occupants[1]=1;h.nearby.names[1]="Guest";h.nearby.chat.add("Guest: Hello everyone!");h.nearby.chat.add("Host: Ready for the match?");h.nearby.status=state==1?"Searching for games…":"Join from other devices. Waiting for players to connect and choose a slot.";
    if(state==3){h.nearby.countdown=5;h.nearby.status="Starting in 5…";}
   }
   h.nearbyGames.put("one","Alice's Game");h.nearbyGames.put("two","A long host profile name");
   h.customMaps.add(null);for(int i=1;i<60;i++)h.customMaps.add(new File("Map "+i+" - Long test map name.scx"));
   if(state==6){h.multiplayerSetup=true;h.mapOffset=52;h.nearbySetup.freeForAll=true;h.nearbySetup.speed=3;}
   Bitmap image=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(image);h.glue.draw(c,0);if(state>=5)h.drawCustom(c);else h.drawNearby(c);
   for(Button button:h.buttons){RectF a=button.rect;if(a.left<0||a.top<0||a.right>640||a.bottom>480||a.right<a.left||a.bottom<a.top)throw new AssertionError("Invalid hit rectangle state="+state);}
   for(int i=0;i<h.buttons.size();i++)for(int j=i+1;j<h.buttons.size();j++){RectF a=h.buttons.get(i).rect,z=h.buttons.get(j).rect;if(a.left<z.right&&z.left<a.right&&a.top<z.bottom&&z.top<a.bottom)throw new AssertionError("Overlapping hits state="+state+" buttons="+i+","+j);}
   ImageIO.write(image.image,"png",output.resolve("screen-"+state+".png").toFile());
   if(state==6)for(Button button:h.buttons)if(button.rect.top>=300&&button.rect.right<=360)throw new AssertionError("Pre-lobby slot editing remains");
   if(state==0){h.menuHoverX=80;h.menuHoverY=120;if(h.menuColor(60,102,264,34,true)!=4||h.menuColor(60,146,264,34,true)!=3)throw new AssertionError("New button hover color");}
   h.buttons.clear();h.glue.elapsed=0;if(state>=5)h.drawCustom(c);else h.drawNearby(c);if(!h.buttons.isEmpty())throw new AssertionError("Touch active during entry");
  }
  System.out.println("PASS original connection/join/lobby/create artwork; seven renders; actual terrain preview; bounded nonoverlapping hit targets; entry gating");
 }
}
class NativeMaps{static String label(File file){return file==null?"Weave":file.getName();}}
class NativeNearby{void refresh(){}void join(String id){}}
'''
for name,text in sources.items():
 p=b/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
real=[src/n for n in ['NativeArt.java','NativeResults.java','NativeGlue.java','NativeMapPreview.java','MatchSetup.java','MatchSnapshot.java','NearbyProtocol.java','NearbyMatch.java','NearbyMapCodec.java','RoomProtocol.java','RoomSnapshot.java','RoomMatch.java']];jar=r/'build-native/json-20240303.jar'
p=subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn','-classpath',str(jar),'-d',str(b/'classes'),*[str(b/n)for n in sources],*map(str,real)],capture_output=True,text=True);print(p.stdout+p.stderr);p.check_returncode()
p=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.Ui56Harness',str(assets),str(b)],capture_output=True,text=True);print(p.stdout+p.stderr);p.check_returncode()
(r/'validation/ui-v56.json').write_text(json.dumps({'passed':True,'physicalPhone':False,'output':p.stdout.strip(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in real+[src/'NativeSurface.java',Path(__file__)]}},indent=2)+'\n')

#!/usr/bin/env python3
"""Test per-ID campaign completion and render/touch the original mission list.

Uses caller-owned artwork with an AWT Canvas shim; no device or game assets bundled.
"""
from pathlib import Path
import argparse, ast, hashlib, json, re, subprocess
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('core',type=Path)
p.add_argument('--starcraft',type=Path,required=True);p.add_argument('--extract',type=Path,default=r/'build-native/reign79/extract');a=p.parse_args()
b=r/'build-native/campaign82';b.mkdir(parents=True,exist_ok=True);assets=b/'assets'
names={'rez/gluhist.bin','rez/glucmpgn.bin','glue/campaign/phist.pcx','font/font.gid'}
for theme in ['palcs','palnl']:
 names|={'glue/'+theme+'/'+name for name in ['backgnd.pcx','tfont.pcx','teffect.pcx','dlg.grp','tile.grp']}
names|={prefix+'font'+size+'.fnt' for prefix in ['font/','files/font/'] for size in ['8','10','14','16','16x']}
def extract(name):
 for slot,archive in [(0,a.core/'STARDAT.MPQ'),(1,a.core/'BROODAT.MPQ'),(2,a.core/'patch_rt.mpq'),(4,a.starcraft)]:
  dest=assets/str(slot)/name;dest.parent.mkdir(parents=True,exist_ok=True)
  q=subprocess.run([str(a.extract),str(archive),name,str(dest)],capture_output=True)
  if q.returncode:dest.unlink(missing_ok=True)
for name in names:extract(name)
more=set()
for path in assets.rglob('*.bin'):
 more|={s.decode('cp1252').replace('\\','/').lower() for s in re.findall(rb'(?:glue|GLUE)[^\x00]*?\.[pP][cC][xX]',path.read_bytes())}
for name in more-names:extract(name)
# Reuse production artwork render shims, not another copy of the menu implementation.
old=ast.parse((r/'tests/run_menu_recovery.py').read_text());active=False
for node in old.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tree' for t in node.targets):active=True
 if active:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.slice,ast.Constant) and t.slice.value=='org/openbw/androidtest/MenuRecoveryTest.java' for t in node.targets):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<art shim>','exec'))
sources['android/graphics/Color.java']=sources['android/graphics/Color.java'].replace('public class Color{','public class Color{public static final int BLACK=0xff000000;')
sources['android/graphics/RectF.java']=sources['android/graphics/RectF.java'].replace('public RectF(float', 'public RectF(){this(0,0,0,0);}public void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}public boolean intersect(RectF r){float l=Math.max(left,r.left),t=Math.max(top,r.top),rr=Math.min(right,r.right),b=Math.min(bottom,r.bottom);if(l>=rr||t>=b)return false;set(l,t,rr,b);return true;}public RectF(float')
sources['android/graphics/Paint.java']=sources['android/graphics/Paint.java'].replace('public class Paint{','public class Paint{public enum Style{STROKE,FILL}public Style style=Style.FILL;public float strokeWidth=1;public void setStyle(Style s){style=s;}public void setStrokeWidth(float w){strokeWidth=w;}')
sources['android/graphics/Canvas.java']=sources['android/graphics/Canvas.java'].replace('public void drawRect(','''public void clipRect(RectF r){clipRect(r.left,r.top,r.right,r.bottom);}
 public void drawCircle(float x,float y,float radius,Paint p){g.setColor(new java.awt.Color(p.color,true));g.setStroke(new BasicStroke(p.strokeWidth));Ellipse2D.Float shape=new Ellipse2D.Float(x-radius,y-radius,radius*2,radius*2);if(p.style==Paint.Style.STROKE)g.draw(shape);else g.fill(shape);}
 public void drawLine(float x,float y,float xx,float yy,Paint p){g.setColor(new java.awt.Color(p.color,true));g.setStroke(new BasicStroke(p.strokeWidth));g.draw(new Line2D.Float(x,y,xx,yy));}
 public void drawRect(''')
sources['org/openbw/androidtest/NativeBridge.java']=sources['org/openbw/androidtest/NativeBridge.java'].replace('static Path root;', 'static int outcome;static int value(int a,int b){return outcome;}static void sound(byte[] b,int c,boolean d){}static Path root;')
text=(src/'NativeSurface.java').read_text()
def method(name):
 m=re.search(r'^  private (?:void|float|boolean|String) '+name+r'\(',text,re.M);assert m,name
 end=text.index('{',m.end())+1;depth=1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[m.start():end]
methods=['saveCampaignProgress','saveProfiles','recordCampaignCompletion','missionCompleted','drawMissionCheck','historyLabel','missionMaxOffset','drawHistory','drawMissionScrollbar','uiLine']
start=text.index('      int outcome = replayGame?0:NativeBridge.value(7, 0);')
end=text.index('      if (musicPhase.equals("game")',start)
outcome=text[start:end]
assert 'recordCampaignCompletion(outcome);' in outcome
assert 'campaignProfile = campaignProgress.playerId(selectedProfile);' in text
assert 'info.put("campaignProfile",campaignProfile)' in text
assert text.index('campaignProfile=campaignProgress.savedOwner(info);')>text.index('NativeBridge.restoreState(saved.state);')
assert 'recordCampaignCompletion(lastOutcome);' in text
sources['org/openbw/androidtest/Campaign82Test.java']='''package org.openbw.androidtest;
import android.graphics.*;import java.util.*;import java.nio.file.*;import javax.imageio.ImageIO;import org.json.*;
public class Campaign82Test {
 static int checks;static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static void near(float a,float b,String why){check(Math.abs(a-b)<.05f,why+" "+a+" != "+b);}
 static class Prefs{String json="";int writes;Prefs edit(){return this;}Prefs putString(String key,String value){if(key.equals(CampaignProgress.KEY))json=value;return this;}void apply(){writes++;}}
 static class Button{RectF rect;Runnable action;boolean enabled,vertical;java.util.function.Consumer<Float>slider;Button(RectF r,Runnable a,boolean e){rect=r;action=a;enabled=e;}}
 static class Nearby{void finish(){}}
 Prefs prefs=new Prefs();CampaignProgress campaignProgress;String campaignProfile,selectedProfile="Alice",modal="missions",musicPhase="game";boolean replayGame,multiplayerGame;
 Object campaign=new Object();JSONObject currentMission;int lastOutcome;Nearby nearby;Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
 ArrayList<String>profiles=new ArrayList<>(Arrays.asList("Alice","Bob"));ArrayList<JSONObject>visibleMissions=new ArrayList<>();ArrayList<Button>buttons=new ArrayList<>();
 NativeArt art;NativeGlue glue;RectF missionViewport=new RectF();float missionOffset,listVelocity;int listScroll,chosenMission;long downAt;
 void sfx(String s){}void cancelGesture(){}void chooseMission(JSONObject m){}void navigate(Runnable action){action.run();}
 NativeArt.Dialog dialog(String name){return art.dialog(name);}boolean installed(JSONObject m){return true;}
 void add(RectF rect,Runnable action,boolean enabled){buttons.add(new Button(rect,action,enabled));}
 void button(Canvas c,String label,float x,float y,float w,float h,Runnable action,boolean enabled){
  c.drawBitmap(glue.panel(Math.round(w),Math.round(h),true),x,y,NativeArt.PIXELS);uiLine(c,label,glue.large,x+4,y,(int)w-8,(int)h,1,enabled?3:5);add(new RectF(x,y,x+w,y+h),action,enabled);}
 Campaign82Test(){campaignProgress=new CampaignProgress("",profiles);campaignProfile=campaignProgress.playerId("Alice");}
'''+'\n'.join(method(n) for n in methods)+'\n void tickOutcome(){\n'+outcome+'''\n}
 Bitmap redraw(){buttons.clear();Bitmap image=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(image);glue.draw(c,1000);check(drawHistory(c),"Original history failed to render");return image;}
 Button at(float x,float y){for(int i=buttons.size()-1;i>=0;i--)if(buttons.get(i).rect.contains(x,y))return buttons.get(i);throw new AssertionError("Missing target "+x+","+y);}
 void tap(float x,float y){Button b=at(x,y);if(b.enabled){if(b.slider!=null)b.slider.accept((y-b.rect.top)/b.rect.height());else b.action.run();}}
 static JSONObject mission(String id)throws Exception{return new JSONObject().put("id",id).put("code",101).put("number",1).put("title","Among the Ruins");}
 public static void main(String[]args)throws Exception{
 Campaign82Test h=new Campaign82Test();h.currentMission=mission("zerg01");String alice=h.campaignProfile,bob=h.campaignProgress.playerId("Bob");
 check(!alice.isEmpty()&&!bob.isEmpty()&&!alice.equals(bob),"IDs not separate");check(h.campaignProgress.playerName(alice).equals("Alice"),"Save cannot restore original registered ID");check(h.campaignProgress.playerName("retired").isEmpty(),"Unknown identity returned a registered name");
 for(Object[] m:CampaignCatalog.ALL)check(!h.campaignProgress.completed("Alice",(String)m[1]),"Old unlocks inferred as wins");
 NativeBridge.outcome=1;h.tickOutcome();check(h.campaignProgress.completed("Alice","zerg01"),"Native win hook failed");
 check(!h.campaignProgress.completed("Bob","zerg01"),"Win leaked across IDs");int writes=h.prefs.writes;h.tickOutcome();check(h.prefs.writes==writes,"Same result persisted repeatedly");
 CampaignProgress reloaded=new CampaignProgress(h.prefs.json,h.profiles);check(reloaded.completed("Alice","zerg01"),"Completion lost on restart");check(reloaded.playerId("Alice").equals(alice),"Owner changed on restart");
 h.currentMission=mission("zerg02");for(int outcome:new int[]{0,2,3}){h.lastOutcome=0;NativeBridge.outcome=outcome;h.tickOutcome();check(!h.campaignProgress.completed("Alice","zerg02"),"Non-win marked completed");}
 h.lastOutcome=0;h.replayGame=true;NativeBridge.outcome=1;h.tickOutcome();check(!h.campaignProgress.completed("Alice","zerg02"),"Replay awarded progress");h.replayGame=false;
 h.lastOutcome=0;h.multiplayerGame=true;h.tickOutcome();check(!h.campaignProgress.completed("Alice","zerg02"),"Multiplayer awarded campaign progress");h.multiplayerGame=false;
 h.lastOutcome=0;h.campaign=null;h.tickOutcome();check(!h.campaignProgress.completed("Alice","zerg02"),"Custom game awarded campaign progress");h.campaign=new Object();
 h.lastOutcome=0;h.currentMission.put("cinematic","movie.smk");h.tickOutcome();check(!h.campaignProgress.completed("Alice","zerg02"),"Cinematic awarded mission completion");h.currentMission.remove("cinematic");
 JSONObject save=new JSONObject().put("campaignProfile",alice).put("profile","Bob");
 h.selectedProfile="Bob";h.campaignProfile=h.campaignProgress.savedOwner(save);h.lastOutcome=0;h.tickOutcome();
 check(h.campaignProgress.completed("Alice","zerg02")&&!h.campaignProgress.completed("Bob","zerg02"),"Loaded save changed campaign owner");
 check(h.campaignProgress.savedOwner(new JSONObject().put("profile","alice")).equals(alice),"Existing legacy save owner not recognized");
 check(h.campaignProgress.savedOwner(new JSONObject().put("profile","Nobody")).isEmpty(),"Missing legacy ID given someone else's progress");
 check(h.campaignProgress.savedOwner(new JSONObject().put("campaignProfile","deleted").put("profile","Alice")).isEmpty(),"Deleted immutable owner fell back to name");
 h.campaignProgress.record(bob,"expzerg02",1,true,false,false);h.profiles.remove("Alice");h.saveProfiles();check(h.campaignProgress.savedOwner(save).isEmpty(),"Deleted ID's save still owns progress");
 h.profiles.add("Alice");h.saveProfiles();String newAlice=h.campaignProgress.playerId("Alice");check(!newAlice.equals(alice),"Recreated ID reused identity");
 check(!h.campaignProgress.completed("Alice","zerg01"),"Recreated ID inherited wins");
 check(h.campaignProgress.completed("Bob","expzerg02"),"Deleting ID cleared another ID");
 check(h.campaignProgress.savedOwner(new JSONObject().put("profile","Alice")).isEmpty(),"Deleted/recreated legacy name inherited old save owner");
 check(!h.campaignProgress.record(alice,"zerg03",1,true,false,false),"Retired identity can still earn wins");
 check(!h.campaignProgress.record(newAlice,"cinematic",1,true,false,false),"Unknown map marked complete");
 CampaignProgress malformed=new CampaignProgress("not JSON",h.profiles);check(!malformed.completed("Alice","zerg01"),"Corrupt progress inferred completion");
 CampaignProgress unchanged=new CampaignProgress(h.campaignProgress.serialize(),h.profiles);check(unchanged.completed("Bob","expzerg02"),"Another ID failed round trip");
 // Actual original layout/artwork, clipping and enlarged independent controls.
 NativeBridge.root=Paths.get(args[0]);h.art=new NativeArt();h.glue=new NativeGlue(h.art,"glucmpgn","palcs",false);h.glue.elapsed=1000;
 check(!h.glue.large.fallback,"Original font was not loaded");h.selectedProfile="Bob";h.campaignProfile=bob;
 h.visibleMissions.clear();for(int i=0;i<16;i++){Object[] row=CampaignCatalog.ALL[32+i];h.visibleMissions.add(new JSONObject().put("id",row[1]).put("code",row[0]).put("number",i+1).put("title",i==2?"A very long mission title that should stay inside one row":row[2]));}
 h.campaignProgress.record(bob,h.visibleMissions.get(0).getString("id"),1,true,false,false);
 h.campaignProgress.record(bob,h.visibleMissions.get(3).getString("id"),1,true,false,false);
 h.currentMission=h.visibleMissions.get(0);check(h.missionCompleted(h.currentMission),"Selected ID mark missing");h.selectedProfile="Alice";check(!h.missionCompleted(h.currentMission),"List ignored selected ID");h.selectedProfile="Bob";
 JSONObject film=new JSONObject().put("cinematic","intro.smk").put("id",h.currentMission.getString("id"));check(!h.missionCompleted(film),"Film row shows mission mark");
 Bitmap image=h.redraw();ImageIO.write(image.image,"png",Paths.get(args[1],"mission-history.png").toFile());
 Bitmap tick=Bitmap.createBitmap(24,24,Bitmap.Config.ARGB_8888);h.drawMissionCheck(new Canvas(tick),12,12);int green=0;
 for(int yy=0;yy<24;yy++)for(int xx=0;xx<24;xx++){
  int pixel=tick.getPixel(xx,yy);if(pixel!=0){green++;check(pixel==0xff7cdb58,"Completion tick has blended or non-green pixels");}
 }
 check(green==30,"Completion tick changed silhouette or contains a circular border");
 check(tick.getPixel(7,11)==0xff7cdb58&&tick.getPixel(10,16)==0xff7cdb58&&tick.getPixel(16,8)==0xff7cdb58,"Completion tick lost either arm");
 check(tick.getPixel(12,6)==0&&tick.getPixel(18,12)==0&&tick.getPixel(12,18)==0,"Completion tick still has circular outline");
 ImageIO.write(tick.image,"png",Paths.get(args[1],"mission-completion-pixel-tick.png").toFile());
 Bitmap enlarged=Bitmap.createBitmap(192,192,Bitmap.Config.ARGB_8888);Canvas enlargedCanvas=new Canvas(enlarged);enlargedCanvas.scale(8,8);h.drawMissionCheck(enlargedCanvas,12,12);
 ImageIO.write(enlarged.image,"png",Paths.get(args[1],"mission-completion-pixel-tick-detail.png").toFile());

 NativeArt.Widget box=h.art.dialog("gluhist").get(6);float left=130+box.x+box.w-36,top=114+box.y,center=left+18,bottom=top+box.h;
 near(h.missionViewport.right,left,"List overlaps scroll rail");
 Button up=h.at(center,top+16),down=h.at(center,bottom-16),bar=h.at(center,(top+bottom)/2);
 near(up.rect.width(),36,"Up target too narrow");near(down.rect.width(),36,"Down target too narrow");near(bar.rect.width(),36,"Thumb target too narrow");
 near(up.rect.height(),32,"Up target too short");near(down.rect.height(),32,"Down target too short");
 check(bar.vertical&&bar.slider!=null,"Scrollbar not draggable");
 h.tap(center,bottom-16);near(h.missionOffset,19,"Arrow must step one mission");h.redraw();h.tap(center,top+16);near(h.missionOffset,0,"Up arrow cannot return to first mission");
 for(float offset:new float[]{-7,0,7}){
  h.missionOffset=h.missionMaxOffset()*.4f;h.redraw();bar=h.at(center,(top+bottom)/2);float scale=box.h/(float)Math.round(box.h/1.75f);float travel=(Math.round(box.h/1.75f)-46)*scale;
  float y=top+23*scale+.4f*travel+offset;float before=h.missionOffset;h.downAt++;bar.slider.accept((y-bar.rect.top)/bar.rect.height());near(h.missionOffset,before,"Grabbed circle jumps list");
  h.redraw();bar.slider.accept((y+10-bar.rect.top)/bar.rect.height());near(h.missionOffset,before+10/travel*h.missionMaxOffset(),"Thumb drag mismatches rendering");
  bar.slider.accept(1f);near(h.missionOffset,h.missionMaxOffset(),"Cannot drag to last mission");bar.slider.accept(0f);near(h.missionOffset,0,"Cannot drag to first mission");
 }
 h.missionOffset=0;h.redraw();h.downAt++;h.tap(center,(top+bottom)/2);near(h.missionOffset,h.missionMaxOffset()/2,"Track tap does not jump to midpoint");
 h.missionOffset=h.missionMaxOffset();h.redraw();check(h.buttons.size()<20,"Mission list not virtualized");
 check(h.at(190,340).rect.width()==164&&h.at(370,340).rect.width()==164,"OK/Cancel not widened");
 check(h.at(190,340).rect.height()==34&&h.at(370,340).rect.height()==34,"OK/Cancel not taller");
 System.out.println("PASS "+checks+" campaign progress and original mission UI checks: native outcome hook, persistent separate IDs, save owners, deletion/recreation, replay/custom/cinematic exclusions, opaque green pixel tick without circle, original fonts, widened targets, clipped labels, scroll dragging and end reachability");
 }
}'''
for name,value in sources.items():
 dest=b/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(value)
real=[src/(name+'.java') for name in ['CampaignProgress','CampaignCatalog','NativeArt','NativeGlue','NativeResults','ClassicFontCipher','GameLanguage','PortText','MenuLabels']]
jar=r/'build-native/json-20240303.jar'
subprocess.run(['javac','-cp',str(jar),'-d',str(b/'classes'),*[str(b/name) for name in sources],*map(str,real)],check=True)
q=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.Campaign82Test',str(assets),str(b)],capture_output=True,text=True);print(q.stdout+q.stderr,end='');q.check_returncode()
files=real+[src/'NativeSurface.java',Path(__file__)]
report=dict(passed=True,physicalAndroid=False,checks=q.stdout.strip(),sourceSha256={str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},screenshots=['build-native/campaign82/mission-history.png','build-native/campaign82/mission-completion-pixel-tick.png','build-native/campaign82/mission-completion-pixel-tick-detail.png'],completionHistoryBackfilled=False,saveOwnership='Immutable Player ID; legacy name only while the original ID still exists',scrollTargetWidth=36,arrowTargetHeight=32,missionActionWidth=164,missionActionHeight=34)
(r/'validation/campaign-progress-v82.json').write_text(json.dumps(report,indent=2)+'\n')

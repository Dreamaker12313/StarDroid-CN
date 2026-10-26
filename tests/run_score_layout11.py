#!/usr/bin/env python3
"""Render full campaign score names with original artwork and production Java code.

Uses the established AWT Canvas shim, not an Android device. Original campaign
archives remain local; only aggregate evidence and source hashes are recorded.
"""
from pathlib import Path
import ast,hashlib,json,os,re,shutil,struct,subprocess
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest'
b=r/'build-native/score-layout11';b.mkdir(parents=True,exist_ok=True)
jdk=r/'.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64/bin'
if (jdk/'javac').is_file():os.environ['PATH']=str(jdk)+os.pathsep+os.environ['PATH']
assets=b/'assets';shutil.copytree(r/'build-native/replay-ui81/assets',assets,dirs_exist_ok=True)
archives=[(0,r/'build-native/reign79/core/STARDAT.MPQ'),(1,r/'build-native/reign79/core/BROODAT.MPQ'),(2,r/'build-native/reign79/core/patch_rt.mpq'),(4,r.parent/'reign-data/StarCraft.mpq')]
extract=r/'build-native/reign79/extract'
def get(name):
 for slot,archive in archives:
  target=assets/str(slot)/name;target.parent.mkdir(parents=True,exist_ok=True)
  call=subprocess.run([str(extract),str(archive),name,str(target)],capture_output=True)
  if call.returncode:target.unlink(missing_ok=True)
for name in ['rez/gluscore.bin']+[prefix+'font'+size+'.fnt'for prefix in ['font/','files/font/']for size in ['8','10','14','16','16x']]:get(name)
for key in ['tv','zv','pv','td','zd','pd']:
 for name in ['pmain.pcx','pinset.pcx','scorebox.pcx','untab.pcx','iscore.grp']:get('glue/score'+key+'/'+name)
 for name in ['backgnd.pcx','tfont.pcx','teffect.pcx']:get('glue/pal'+key+'/'+name)
# Extract and decode every original FORC/STR mapping independently of Java/native UI.
names=set();inventory=[]
for mission in json.loads((r/'app/src/main/assets/native/missions.json').read_text()):
 archive=r.parent/'reign-data'/('BroodWar.mpq'if mission['game']=='broodwar'else'StarCraft.mpq');chk=b/(mission['id']+'.chk')
 subprocess.run([str(extract),str(archive),mission['prefix']+'staredit/scenario.chk',str(chk)],check=True,stdout=subprocess.DEVNULL)
 data=chk.read_bytes();chunks={};pos=0
 while pos<len(data):
  tag,size=struct.unpack_from('<4sI',data,pos);pos+=8;assert pos+size<=len(data);chunks[tag]=data[pos:pos+size];pos+=size
 forc=chunks[b'FORC'];strings=chunks[b'STR '];count=struct.unpack_from('<H',strings)[0];map_names=[]
 for index in struct.unpack_from('<4H',forc,8):
  assert index<=count
  if index:
   offset=struct.unpack_from('<H',strings,2+(index-1)*2)[0];assert offset<len(strings);end=strings.index(b'\0',offset)
   name=re.sub(r'[\x00-\x1f]','',strings[offset:end].decode('cp1252')).strip();names.add(name);map_names.append(name)
 inventory.append({'mission':mission['id'],'chkSha256':hashlib.sha256(data).hexdigest(),'forceNames':map_names})
(b/'names.txt').write_text('\n'.join(sorted(names))+'\n')
stats=r/'build-native/score-slots11'
assert (r/'validation/score-slots11.json').is_file(), 'Run tests/run_score_slots11.py first'
fixture_rows=[];fixture_hashes={}
for mission in json.loads((r/'app/src/main/assets/native/missions.json').read_text()):
 file=stats/(mission['id']+'.stats');raw=file.read_bytes();fixture_hashes[mission['id']]=hashlib.sha256(raw).hexdigest()
 fixture_rows.append(mission['id']+'\t'+str(mission['race']))
(b/'fixtures.txt').write_text('\n'.join(fixture_rows)+'\n')
# Reuse only shared Android drawing stubs; no unrelated tests execute.
context=globals();tree=ast.parse((r/'tests/run_gamepad81.py').read_text());active=False
for node in tree.body:
 if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='old'for t in node.targets):active=True
 if active:
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='harness'for t in node.targets):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<score layout Canvas shim>','exec'),context)
sources.pop('org/openbw/androidtest/MapScroll79Test.java',None)
sources['org/openbw/androidtest/NativeHud.java']='package org.openbw.androidtest;class NativeHud{static int number(String[] f,int i,int d){try{return Integer.parseInt(f[i]);}catch(Exception e){return d;}}}'
sources['org/openbw/androidtest/ScoreLayout11Test.java']=r'''package org.openbw.androidtest;
import java.nio.file.*;import java.util.*;import android.graphics.*;import javax.imageio.ImageIO;
public class ScoreLayout11Test {
 static long checks;static int nameCases,screenCases;static int[]fontUses=new int[4];
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static String row(int local,int slot,int race,String faction){return local+"\t"+race+"\t"+slot+"\t10\t20\t300\t400\t5\t6\t7\t8\t9\t100\t200\t120\t130\t"+slot+"\t3\t5\t"+faction;}
 static Bitmap blank(){return Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);}
 static void same(Bitmap a,Bitmap b,int x,int y,int width,int height,String why){checks++;for(int yy=y;yy<y+height;yy++)for(int xx=x;xx<x+width;xx++)if(a.image.getRGB(xx,yy)!=b.image.getRGB(xx,yy))throw new AssertionError(why+" at "+xx+","+yy);}
 static int pixels(Bitmap b){int count=0;for(int y=0;y<b.getHeight();y++)for(int x=0;x<b.getWidth();x++)if((b.image.getRGB(x,y)>>>24)!=0)count++;return count;}
 static int width(NativeResults screen,int row){NativeArt.Widget n=screen.layout.get(14+row*6),v=screen.layout.get(15+row*6);return Math.min(n.w,v.x-n.x-8);}
 static void fullName(NativeResults screen,String text,boolean original){
  int width=width(screen,0);String clean=NativeArt.clean(PortText.text(text)).replace('\n',' ').trim();NativeArt.Font font=screen.nameFont(text,width);
  int measured=font.measure(clean);if(original)check(measured<=width,"Original faction requires scaling: "+text+" ("+measured+" > "+width+")");
  if(font==screen.large)fontUses[0]++;else if(font==screen.medium)fontUses[1]++;else if(font==screen.small)fontUses[2]++;else fontUses[3]++;
  Bitmap actual=Bitmap.createBitmap(210,120,Bitmap.Config.ARGB_8888);screen.nameLine(new Canvas(actual),text,font,2,40,80,width,19);
  float scale=Math.min(1f,width/(float)Math.max(1,measured));
  // Independent full-string reference without clipping or ellipsis. If the
  // production label clips even a glyph edge, total/individual pixels differ.
  Bitmap expected=Bitmap.createBitmap(210,120,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(expected);c.translate(40,80+(19-font.height*scale)/2);c.scale(scale,scale);font.draw(c,clean,0,0,0,0,2,0);
  same(actual,expected,0,0,210,120,"Incomplete full-name pixels for "+text);
  check(pixels(actual)>0,"Blank name: "+text);
  checks++;for(int y=0;y<120;y++)for(int x=0;x<210;x++)if((x<40||x>=40+width||y<80||y>=99)&&(actual.image.getRGB(x,y)>>>24)!=0)throw new AssertionError("Name escapes column/row: "+text);
  nameCases++;
 }
 static void screens(NativeArt art,Path out,List<String>names)throws Exception{
  String[]examples={"Colonial Militia","Unidentified Creatures","Fleet of the Executor","Neutral Hive Clusters","Protoss Reconnaissance Force","General Duke's Battle Fleet","Remnants of the Confederacy","Zerg Swarm"};
  for(int race=0;race<3;race++)for(boolean victory:new boolean[]{true,false}){
   StringBuilder raw=new StringBuilder("1\t2400\n");for(int i=0;i<examples.length;i++)raw.append(row(i==0?1:0,i,(i+race)%3,examples[i])).append('\n');
   NativeResults screen=new NativeResults(art,race,victory,raw.toString());screen.playerName="My Commander";screen.animationElapsed=1000;screen.progress=1;
   for(String language:new String[]{"en","ru","de","es","fr"}){PortText.select(language);
   for(String name:names)fullName(screen,name,true);
   for(String name:new String[]{"Рой зергов","Разведывательные силы протоссов","Flotte des Exekutors","Flotte de l’Exécuteur","Fuerza expedicionaria protoss","A very long custom Player ID that must remain complete without overlapping the score columns"})fullName(screen,name,false);}
   for(String language:new String[]{"en","ru","de","es","fr"}){
    PortText.select(language);
    for(int tab=0;tab<4;tab++){
     screen.tab=tab;Bitmap shot=blank();screen.draw(new Canvas(shot),0);screenCases++;
     // Changing any player name is not allowed to change score numbers/bars,
     // row separators, subtitles or a neighboring row.
     for(int i=0;i<8;i++){
      String old=screen.factionNames.get(i);screen.factionNames.set(i,"A different very long faction name");
      Bitmap changed=blank();screen.draw(new Canvas(changed),0);screen.factionNames.set(i,old);
      NativeArt.Widget first=screen.layout.get(15+i*6);
      same(shot,changed,first.x-1,first.y-2,640-(first.x-1),38,"Name crosses into score columns");
     }
     if(language.equals("en")||tab==0)ImageIO.write(shot.image,"png",out.resolve("score-"+race+(victory?"-victory":"-defeat")+"-"+language+"-tab"+tab+".png").toFile());
    }
   }
   PortText.select("en");
  }
 }
 static void realCampaigns(NativeArt art,Path out,Path fixtures)throws Exception{
  Map<String,Integer> reported=new HashMap<>();reported.put("terran01",2);reported.put("terran02",2);reported.put("protoss05",4);reported.put("expzerg01",3);reported.put("expzerg10",4);
  PortText.select("en");int missions=0;
  for(String entry:Files.readAllLines(out.resolve("fixtures.txt"))){String[] f=entry.split("\\t");String id=f[0];int race=Integer.parseInt(f[1]);
   String raw=new String(Files.readAllBytes(fixtures.resolve(id+".stats")),java.nio.charset.StandardCharsets.ISO_8859_1);String[] lines=raw.split("\\n");
   NativeResults score=new NativeResults(art,race,true,raw);score.playerName="RoCP";score.animationElapsed=1000;score.progress=1;
   check(score.rows.size()==lines.length-1,"Renderer loses participant: "+id);
   if(reported.containsKey(id))check(score.rows.size()==reported.get(id),"Incorrect participant count in reported mission: "+id);
   for(int i=0;i<score.rows.size();i++){
    String[] cells=lines[i+1].split("\\t",-1);String expected=cells[0].equals("1")?"RoCP":NativeArt.clean(cells[19]).trim();if(expected.isEmpty())expected="Computer";
    check(score.rowName(i).equals(expected),"Faction/player identity changed in "+id);fullName(score,score.rowName(i),true);
   }
   for(int tab=0;tab<4;tab++){score.tab=tab;Bitmap shot=blank();score.draw(new Canvas(shot),0);screenCases++;
    if(tab==0&&reported.containsKey(id))ImageIO.write(shot.image,"png",out.resolve(id+"-overview.png").toFile());
   }
   missions++;
  }
  check(missions==64,"Did not render all campaign score screens");
  NativeResults nearby=new NativeResults(art,1,true,new String(Files.readAllBytes(fixtures.resolve("custom-nearby.stats")),java.nio.charset.StandardCharsets.ISO_8859_1));
  nearby.playerName="RoCP";nearby.slotNames[6]="Nearby Partner";nearby.animationElapsed=1000;nearby.progress=1;
  check(nearby.rows.size()==8&&nearby.rowName(6).equals("Nearby Partner"),"Eight-player sparse Nearby identity lost");
  Bitmap shot=blank();nearby.draw(new Canvas(shot),0);ImageIO.write(shot.image,"png",out.resolve("custom-eight-overview.png").toFile());
 }
 public static void main(String[]args)throws Exception{
  NativeBridge.root=Paths.get(args[0]);Path out=Paths.get(args[1]);PortText.load(Files.newInputStream(Paths.get(args[2])));NativeArt art=new NativeArt();
  List<String>names=Files.readAllLines(out.resolve("names.txt"));check(!names.isEmpty(),"No campaign faction names");
  NativeResults identity=new NativeResults(art,1,true,"1\t2400\n"+row(1,0,1,"Sons of Korhal")+"\n"+row(0,6,2,"Fleet of the Executor")+"\n"+row(0,2,1,"")+"\n"+row(0,7,1,""));
  identity.playerName="My Commander";identity.slotNames[2]="Nearby Partner";
  check(identity.rowName(0).equals("My Commander"),"Player ID replaced");check(identity.rowName(1).equals("Fleet of the Executor"),"Campaign faction replaced");check(identity.rowName(2).equals("Nearby Partner"),"Nearby name replaced");check(identity.rowName(3).equals("Computer"),"Empty name lacks fallback");
  GameLanguage.russianData=true;String localized="Рой зергов";String decoded=GameLanguage.decode(("1\t2400\n"+row(0,6,0,localized)).getBytes(GameLanguage.RUSSIAN));NativeResults russian=new NativeResults(art,1,true,decoded);check(russian.rowName(0).equals(localized),"Localized archive name changed");GameLanguage.russianData=false;
  screens(art,out,names);realCampaigns(art,out,Paths.get(args[3]));
  System.out.println("PASS "+checks+" score-layout checks; "+names.size()+" original force names from 64 campaigns; "+nameCases+" full-string pixel checks; "+screenCases+" race/victory/tab/language screens; font use 16/14/10/8="+Arrays.toString(fontUses));
 }
}'''
for name,text in sources.items():
 p=b/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
real=[src/n for n in ['NativeArt.java','NativeGlue.java','NativeResults.java','CommandHint.java','MenuLabels.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
subprocess.run(['javac','-d',str(b/'classes'),*[str(b/n)for n in sources],*map(str,real)],check=True)
result=subprocess.run(['java','-Xmx768m','-Djava.awt.headless=true','-cp',str(b/'classes'),'org.openbw.androidtest.ScoreLayout11Test',str(assets),str(b),str(r/'app/src/main/assets/native/ui-languages.tsv'),str(stats)],capture_output=True,text=True)
print(result.stdout+result.stderr,end='');result.check_returncode()
files=[src/'NativeResults.java',src/'NativeArt.java',src/'GameLanguage.java',src/'PortText.java',r/'app/src/main/assets/native/ui-languages.tsv',Path(__file__)]
(r/'validation/score-layout11.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'canvas':'AWT shim using production score renderer and imported original artwork/fonts','result':result.stdout.strip(),'campaignMapInventory':inventory,'nativeStatsFixtureSha256':fixture_hashes,'nativeStatsProofSha256':hashlib.sha256((r/'validation/score-slots11.json').read_bytes()).hexdigest(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

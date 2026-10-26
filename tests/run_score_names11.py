#!/usr/bin/env python3
"""Check actual campaign score-name transport and the production score renderer."""
from pathlib import Path
import ast,hashlib,json,os,struct,subprocess,sys
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest';out=r/'build-native/score-names11';out.mkdir(exist_ok=True)
core=r/'build-native/reign79/core';stage=r/'native-engine'
jdk=r/'.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64/bin'
if (jdk/'javac').is_file():os.environ['PATH']=str(jdk)+os.pathsep+os.environ['PATH']
subprocess.run(['gcc','-O2','-c',str(r/'vendor/libsmacker/smacker.c'),'-o',str(out/'smacker.o')],check=True)
cmd=['g++','-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER']
cmd+=['-I'+str(p)for p in(stage,stage/'ui',stage/'web')]
cmd+=[str(r/'tests/native_score_names11.cpp'),str(r/'native/generated/wasm_backend.cpp'),str(out/'smacker.o'),'-o',str(out/'native-test')]
if "--skip-build" not in sys.argv:subprocess.run(cmd,check=True)
results=[]
inventory=[]
for mission in json.loads((r/'app/src/main/assets/native/missions.json').read_text()):
 archive=r.parent/'reign-data'/('BroodWar.mpq' if mission['game']=='broodwar' else 'StarCraft.mpq');chk=out/(mission['id']+'.chk')
 subprocess.run([str(r/'build-native/reign79/extract'),str(archive),mission['prefix']+'staredit/scenario.chk',str(chk)],check=True,stdout=subprocess.DEVNULL)
 data=chk.read_bytes();chunks={};pos=0
 while pos<len(data):
  tag,size=struct.unpack_from('<4sI',data,pos);pos+=8;assert pos+size<=len(data);chunks[tag]=data[pos:pos+size];pos+=size
 forc=chunks[b'FORC'];strings=chunks[b'STR '];count=struct.unpack_from('<H',strings)[0];assert len(forc)>=20 and all(n<4 for n in forc[:8])
 names=[]
 for index in struct.unpack_from('<4H',forc,8):
  assert index<=count
  if index:
   offset=struct.unpack_from('<H',strings,2+(index-1)*2)[0];assert offset<len(strings)and strings.find(b'\0',offset)>=offset;names.append(strings[offset:strings.find(b'\0',offset)])
 inventory.append({'mission':mission['id'],'chkSha256':hashlib.sha256(data).hexdigest(),'namedForces':sum(bool(n)for n in names)})
print('PASS original force/string mappings in',len(inventory),'campaign maps')
for code in [5,104,204,303,402,502]:
 archive=r.parent/'reign-data'/('BroodWar.mpq' if code>=300 else 'StarCraft.mpq')
 run=subprocess.run([str(out/'native-test'),str(core),str(archive),str(code)],text=True,capture_output=True);print(run.stdout+run.stderr,end='');run.check_returncode();results.append(run.stdout.strip())
# Restore only the shared production Canvas shims, without running unrelated suites.
context={'__file__':str(r/'tests/run_replay_thumbnail_ui.py'),'__name__':'fixture'}
for node in ast.parse((r/'tests/run_replay_thumbnail_ui.py').read_text()).body:
 if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='harness'for t in node.targets):break
 exec(compile(ast.Module(body=[node],type_ignores=[]),'<score shims>','exec'),context)
sources=context['sources'];sources.pop('org/openbw/androidtest/MapScroll79Test.java',None)
sources['org/openbw/androidtest/NativeHud.java']='package org.openbw.androidtest;class NativeHud{static int number(String[] f,int i,int d){try{return Integer.parseInt(f[i]);}catch(Exception e){return d;}}}'
sources['org/openbw/androidtest/ScoreNames11Test.java']=r'''package org.openbw.androidtest;
import java.nio.file.*;import android.graphics.*;import javax.imageio.ImageIO;
public class ScoreNames11Test {
 static int checks;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static String row(int local,int slot,String faction){return local+"\t1\t"+slot+"\t1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12\t13\t"+slot+"\t3\t5\t"+faction;}
 public static void main(String[]args)throws Exception{
  NativeBridge.root=Paths.get(args[0]);PortText.load(Files.newInputStream(Paths.get(args[2])));NativeArt art=new NativeArt();
  String raw="1\t2400\n"+row(1,0,"Sons of Korhal")+"\n"+row(0,6,"Confederacy")+"\n"+row(0,2,"")+"\n"+row(0,7,"");
  NativeResults score=new NativeResults(art,1,true,raw);score.playerName="My Commander";score.slotNames[2]="Nearby Partner";
  check(score.rows.size()==4,"lost score rows");check(score.rowName(0).equals("My Commander"),"profile lost");check(score.rowName(1).equals("Confederacy"),"campaign faction missing");check(score.rowName(2).equals("Nearby Partner"),"sparse nearby slot name lost");check(score.rowName(3).equals("Computer"),"empty name fallback");
  NativeResults old=new NativeResults(art,1,true,"1\t2400\n"+row(0,6,"").replaceAll("\t$",""));check(old.rowName(0).equals("Computer"),"old score protocol failed");
  GameLanguage.russianData=true;String localized="Рой зергов";String decoded=GameLanguage.decode(("1\t2400\n"+row(0,6,localized)).getBytes(GameLanguage.RUSSIAN));NativeResults russian=new NativeResults(art,1,true,decoded);check(russian.rowName(0).equals(localized),"localized archive name changed");GameLanguage.russianData=false;
  for(String lang:new String[]{"en","ru","de","es","fr"}){PortText.select(lang);Bitmap image=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);score.draw(new Canvas(image),1000);ImageIO.write(image.image,"png",Paths.get(args[1],"score-"+lang+".png").toFile());}
  String label="A very long campaign faction that must stay out of the score columns";check(score.large.measure(NativeResults.fit(score.large,label,144))<=144,"faction clips score columns");
  System.out.println("PASS "+checks+" score UI checks: factions/profile/nearby/default/localized/archive decoding and bounded name width");
 }
}'''
for name,text in sources.items():p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
real=[src/n for n in ['NativeArt.java','NativeGlue.java','NativeResults.java','CommandHint.java','MenuLabels.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
subprocess.run(['javac','-d',str(out/'classes'),*[str(out/n)for n in sources],*map(str,real)],check=True)
run=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(out/'classes'),'org.openbw.androidtest.ScoreNames11Test',str(context['assets']),str(out),str(r/'app/src/main/assets/native/ui-languages.tsv')],capture_output=True,text=True);print(run.stdout+run.stderr,end='');run.check_returncode();results.append(run.stdout.strip())
files=['patches/native-score-names11.patch','app/src/main/java/org/openbw/androidtest/NativeResults.java','app/src/main/java/org/openbw/androidtest/NativeSurface.java','tests/native_score_names11.cpp','tests/run_score_names11.py']
(r/'validation/score-names11.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'results':results,'campaignMapInventory':inventory,'sourceSha256':{f:hashlib.sha256((r/f).read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

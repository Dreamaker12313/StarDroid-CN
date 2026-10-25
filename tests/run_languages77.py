#!/usr/bin/env python3
"""Usage: run_languages77.py EN_CORE_DIR RU_CORE_DIR RUSSIAN_STARCRAFT_MPQ.

Run run_menu_recovery.py first for the host Canvas shim. Caller-owned data stays
in build-native, never in validation reports or the distributed source package.
"""
from pathlib import Path
import hashlib,json,re,subprocess,sys
r=Path(__file__).resolve().parents[1];out=r/'build-native/languages77';out.mkdir(parents=True,exist_ok=True)
en,ru,cd=map(lambda x:Path(x).resolve(),sys.argv[1:4]);src=r/'app/src/main/java/org/openbw/androidtest'
menu=r/'build-native/menu76';jar=r/'build-native/json-20240303.jar';extract=menu/'extract-interface'
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
harness=out/'Import77.java'
harness.write_text('''package org.openbw.androidtest;
import java.io.*;import java.nio.file.*;import java.util.*;
public class Import77 {public static void main(String[] a)throws Exception {
 File root=new File(a[1]);root.mkdirs();String result;
 try(FileInputStream in=new FileInputStream(a[0])){result=GameContent.install(in.getChannel(),root,false,
 id->Files.readAllLines(Paths.get(a[3],id+"-files.txt")),v->{});}
 if(!result.contains("31 maps imported"))throw new AssertionError(result);
 File bundle=new File(root,InterfaceData.NAME);if(!InterfaceData.hasCampaignPalette(bundle))throw new AssertionError("Russian campaign palette missing");
 NativeData.prepare(bundle,new File(a[2]),"interface");
 NativeData.prepare(new File(root,"StarDroid-Terran01.zip"),new File(a[2]),"terran01");
 System.out.println("PASS Russian StarCraft normal import: 31 maps, story/audio and campaign artwork; first mission prepared for the native engine.");}}
''')
real=['GameContent','InterfaceData','MissionBundle','CampaignCatalog','CampaignData','MusicData','StoryData','ProjectFiles','NativeData','CinematicCatalog','NearbyProtocol','MatchSetup']
run(['javac','-cp',jar,'-d',out,*[src/(n+'.java') for n in real],harness])
imported=run(['java','-Xmx256m','-cp',str(out)+':'+str(jar),'org.openbw.androidtest.Import77',cd,out/'installed',out/'cache',r/'app/src/main/assets/missions']);print(imported,flush=True)
run(['javac','-cp',menu/'classes','-d',out,src/'GameLanguage.java',src/'PortText.java',src/'NativeArt.java',src/'NativeGlue.java',src/'MenuLabels.java',r/'tests/Language77Test.java'])
results=[]
for name,core,isRussian in [('english',en,False),('russian',ru,True)]:
 assets=out/name/'assets';names={'rez/'+n+'.bin' for n in ['glumain','glucmpgn','gluexpcmpgn']}
 names|={'glue/'+pal+'/'+n for pal in ['palmm','palcs','palnl'] for n in ['backgnd.pcx','tfont.pcx','teffect.pcx','dlg.grp','tile.grp']}
 names|={prefix+'font'+size+'.fnt' for prefix in ['font/','files/font/'] for size in ['8','10','12','14','16','16x','32','50']}
 names|={'font/font.gid','rez/stat_txt.tbl'}
 archives=[(0,core/'STARDAT.MPQ'),(1,core/'BROODAT.MPQ'),(2,core/'patch_rt.mpq'),(4,out/'cache/interface.mpq')]
 def get(names):
  extra=set()
  for slot,archive in archives:
   for key in names:
    p=assets/str(slot)/key;p.parent.mkdir(parents=True,exist_ok=True)
    cmd=subprocess.run([str(extract),str(archive),key,str(p)],capture_output=True)
    if cmd.returncode:p.unlink(missing_ok=True)
    elif key.endswith('.bin'):extra|={x.decode('cp1251' if isRussian else 'cp1252').replace('\\','/').lower() for x in re.findall(rb'(?:glue|GLUE)[^\0]*?\.[pP][cC][xX]',p.read_bytes())}
  return extra
 get(get(names)-names)
 result=run(['java','-Djava.awt.headless=true','-cp',str(out)+':'+str(menu/'classes'),'org.openbw.androidtest.Language77Test',assets,out/name,r/'app/src/main/assets/native/ui-languages.tsv',str(isRussian).lower()])
 print(result,flush=True);results.append({'data':name,'output':result.strip()})
 for slot,_ in archives:(assets/str(slot)/'font/font.gid').unlink(missing_ok=True)
files=[src/(n+'.java')for n in ['GameLanguage','PortText','NativeArt','NativeGlue','MenuLabels','MainActivity','NativeSurface','NativeBridge']]+[r/'app/src/main/assets/native/ui-languages.tsv',Path(__file__),r/'tests/Language77Test.java']
(r/'validation/languages-v77.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'russianBroodWarTested':False,'import':imported.strip(),'cases':results,'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

#!/usr/bin/env python3
"""Verify renamed imports/exports and upgrade-sensitive branding against real campaign bundles."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, sys

r = Path(__file__).resolve().parents[1]
b = r/'build-native/branding1'
src = r/'app/src/main/java/org/openbw/androidtest'
b.mkdir(parents=True, exist_ok=True)
fixtures = b/'fixtures'
shutil.rmtree(fixtures, ignore_errors=True)
fixtures.mkdir()
harness = b/'Branding1Test.java'
harness.write_text(r'''package org.openbw.androidtest;
import java.io.*;import java.nio.file.*;import java.util.*;import java.util.zip.*;import org.json.*;
public class Branding1Test {
 static int checks;static void check(boolean v,String s){checks++;if(!v)throw new AssertionError(s);}
 static byte[] bytes(File f)throws Exception{return Files.readAllBytes(f.toPath());}
 public static void main(String[]args)throws Exception {
  File root=new File(args[0]),real=new File(args[1]),migration=new File(root,"migration");migration.mkdirs();
  List<String>names=new ArrayList<>();for(Object[] row:CampaignCatalog.ALL)names.add(CampaignData.filename((String)row[1]));
  names.addAll(Arrays.asList(InterfaceData.NAME,MusicData.NAME,"StarDroid-Music-BroodWar.zip",StoryData.NAME,"StarDroid-Story-BroodWar.zip",StoryData.MOVIES,StoryData.EXP_MOVIES));
  for(String name:names){check(name.startsWith("StarDroid-"),"Old filename "+name);String old="OpenBW-"+name.substring("StarDroid-".length());
   File legacy=new File(migration,old);byte[]payload=name.getBytes("UTF-8");Files.write(legacy.toPath(),payload);
   File renamed=ProjectFiles.existing(migration,name);check(renamed.getName().equals(name)&&Arrays.equals(payload,bytes(renamed)),"Migration changed content");
   check(!legacy.exists(),"Old import not renamed");Files.write(legacy.toPath(),new byte[]{9});
   check(Arrays.equals(payload,bytes(ProjectFiles.existing(migration,name)))&&legacy.isFile(),"Newer import overwritten");
  }
  File legacy=new File(migration,"OpenBW-Fallback.zip"),blocked=new File(migration,"StarDroid-Fallback.zip");Files.write(legacy.toPath(),new byte[]{1,2,3});blocked.mkdir();
  check(ProjectFiles.existing(migration,blocked.getName()).equals(legacy),"Failed rename lost import");
  File missing=ProjectFiles.existing(migration,"StarDroid-Missing.zip");check(!missing.exists()&&missing.getName().startsWith("StarDroid-"),"Missing import path");
  check(ProjectFiles.existing(migration,"STARDAT.MPQ").getName().equals("STARDAT.MPQ"),"Original archive renamed");
  File imports=new File(root,"imports"),cache=new File(root,"cache");imports.mkdirs();cache.mkdirs();
  Map<String,File>originals=new HashMap<>();
  for(String id:new String[]{"terran01","expterran01"}){
   String name=CampaignData.filename(id),old="OpenBW-"+name.substring("StarDroid-".length());File original=new File(real,old);originals.put(id,original);
   check(CampaignData.validate(original).equals(id),"Legacy format rejected");
   Files.copy(original.toPath(),new File(imports,old).toPath());
  }
  check(MissionExport.installedCount(imports)==2,"Old campaign imports disappeared");
  MissionExport.Result export=MissionExport.create(imports,cache);check(export.count==2&&MissionExport.NAME.equals("StarDroid-Missions.zip"),"Export identity");
  try(ZipFile zip=new ZipFile(export.file)){
   String readme=new String(NativeData.read(zip.getInputStream(zip.getEntry("README.txt")),65536),"UTF-8");check(readme.startsWith("StarDroid mission maps"),"Old export title");
   for(String id:originals.keySet()){
    String name=CampaignData.filename(id);File installed=new File(imports,name);check(Arrays.equals(bytes(installed),bytes(originals.get(id))),"Installed campaign changed");
    ZipEntry entry=zip.getEntry("missions/"+name);check(entry!=null,"Old name inside mission export");
    File roundtrip=new File(cache,name);try(InputStream in=zip.getInputStream(entry)){CampaignData.copy(in,roundtrip);}
    check(CampaignData.validate(roundtrip).equals(id),"New-name reimport failed");
    try(ZipFile compact=new ZipFile(roundtrip);ZipFile original=new ZipFile(originals.get(id))){
     Enumeration<? extends ZipEntry> entries=compact.entries();while(entries.hasMoreElements()){ZipEntry e=entries.nextElement();
      if(e.getName().equals("manifest.json"))continue;
      check(Arrays.equals(NativeData.read(compact.getInputStream(e),64*1024*1024),NativeData.read(original.getInputStream(original.getEntry(e.getName())),64*1024*1024)),"Original map bytes changed");}
    }
    File wrong=new File(cache,"StarDroid-Zerg01.zip");Files.write(wrong.toPath(),new byte[]{4});
    try(InputStream in=new FileInputStream(originals.get(id))){try{CampaignData.copy(in,wrong);throw new AssertionError("Wrong mission accepted");}catch(IOException expected){}}
    check(Arrays.equals(bytes(wrong),new byte[]{4}),"Rejected import replaced existing data");
   }
  }
  String pattern=args[2];for(String prefix:new String[]{"StarDroid","OpenBW"})check(("DIRECT-SD-"+prefix+"-12ABCDEF").matches(pattern),"Compatible Wi-Fi name rejected");
  for(String name:new String[]{"StarDroid","DIRECT-SD-Other-12ABCDEF","DIRECT-SD-StarDroid-12ABCDEG","DIRECT-SD-StarDroid-12ABCDEF-extra"})check(!name.matches(pattern),"Invalid Wi-Fi name accepted");
  System.out.println("PASS "+checks+" checks: 64 campaign and 7 media names; migration, new-import precedence, fallback; real base/expansion mission export/reimport and exact payload preservation; Wi-Fi invitation names");
 }
}''')
names = ['ProjectFiles.java','CampaignData.java','CampaignCatalog.java','InterfaceData.java','MusicData.java',
         'StoryData.java','CinematicCatalog.java','NativeData.java','NearbyProtocol.java','MissionExport.java']
files = [src/n for n in names]
jar = r/'build-native/json-20240303.jar'
cmd = ['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn',
       '-classpath',str(jar),'-d',str(b/'classes'),*map(str,files),str(harness)]
p = subprocess.run(cmd,capture_output=True,text=True);print(p.stdout+p.stderr);p.check_returncode()
nearby = (src/'NativeNearby.java').read_text()
pattern = re.search(r'ssid.matches\("([^"]+)"\)',nearby).group(1)
p = subprocess.run(['java','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.Branding1Test',
                    str(fixtures),str(Path(sys.argv[1])),pattern],capture_output=True,text=True)
print(p.stdout+p.stderr);p.check_returncode()
assert 'DIRECT-SD-StarDroid-' in nearby
assert 'OpenBW pairing code' in (src/'LocalTransport.java').read_text()
main = (src/'MainActivity.java').read_text()
assert 'StarDroid · ' in main and 'StarDroid " + BuildConfig.VERSION_NAME' in main
assert 'Put together by ToadWarrior.' in main and 'OpenBW contributors; heiner/openbw.' in main
assert "rootProject.name = 'StarDroid'" in (r/'settings.gradle').read_text()
assert "versionCode 65; versionName '1.0'" in (r/'app/build.gradle').read_text()
assert "applicationId 'org.openbw.androidtest'" in (r/'app/build.gradle').read_text()
allowed = {'NativeNearby.java','LocalTransport.java','MainActivity.java','ProjectFiles.java'}
for f in src.glob('*.java'):
    if 'OpenBW' in f.read_text(): assert f.name in allowed, f.name
checked = files+[src/n for n in ['MainActivity.java','NativeSurface.java','MissionBundle.java','GameContent.java',
           'NativeNearby.java','LocalTransport.java','NativeAudio.java','NativePortrait.java']]
checked += [r/n for n in ['settings.gradle','app/build.gradle','app/src/main/AndroidManifest.xml',
           'app/src/main/res/values/styles.xml','scripts/build_nearby.py','scripts/build_hero_report.py']]+[Path(__file__)]
(r/'validation/branding-v1.0.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,
    'output':p.stdout.strip(),'version':'1.0','displayName':'StarDroid','applicationIdentityRetained':True,
    'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in checked}},indent=2)+'\n')

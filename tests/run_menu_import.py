#!/usr/bin/env python3
"""Exercise the production import path with a full-size, synthetic menu background.

No original game assets are generated or distributed. Optional --baseline-source
reproduces the incomplete-font rejection in the supplied 1.0.3 source ZIP.
"""
import argparse, hashlib, json, re, struct, subprocess, sys, zipfile
from pathlib import Path

r = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--baseline-source', type=Path)
a = p.parse_args()
sys.path.insert(0, str(r/'scripts'))
from rebuild_mission_mpq import cipher, hash_name
b = r/'build-native/import76'
b.mkdir(parents=True, exist_ok=True)
src = r/'app/src/main/java/org/openbw/androidtest'
jar = r/'build-native/json-20240303.jar'

def font():
    data = bytearray(b'FONT' + bytes([32,126,8,16]) + bytes(95*4))
    for code in range(32,127):
        struct.pack_into('<I', data, 8+(code-32)*4, len(data))
        data += bytes([1,1,0,0,1])
    return bytes(data)

def pcx(width, height, value):
    header = bytearray(128)
    header[:4] = bytes([10,5,0,8])
    struct.pack_into('<HH', header, 8, width-1, height-1)
    header[65] = 1
    struct.pack_into('<H', header, 66, width)
    return bytes(header) + bytes([value])*(width*height) + b'\x0c' + bytes(range(256))*3

def archive(path, entries, prefix=b''):
    hn = 128
    hashes = bytearray(b'\xff'*(hn*16))
    blocks, payload = bytearray(), bytearray()
    for i,(name,data) in enumerate(entries.items()):
        offset = 32+len(payload)
        slot = hash_name(name,0) & (hn-1)
        while struct.unpack_from('<I',hashes,slot*16+12)[0] != 0xffffffff:
            slot = (slot+1)&(hn-1)
        struct.pack_into('<IIHHI',hashes,slot*16,hash_name(name,1),hash_name(name,2),0,0,i)
        blocks += struct.pack('<IIII',offset,len(data),len(data),0x81000000)
        payload += data
    ht,bt = 32+len(payload),32+len(payload)+len(hashes)
    header = struct.pack('<4sIIHHIIII',b'MPQ\x1a',32,bt+len(blocks),0,3,ht,bt,hn,len(entries))
    path.write_bytes(prefix+header+payload+cipher(hashes,hash_name('(hash table)',3),True)
                     +cipher(blocks,hash_name('(block table)',3),True))

fonts = {f'files\\font\\font{n}.fnt':font() for n in ['8','10','12','14','16','16x','32','50']}
entries = dict(fonts)
entries['glue\\palcs\\backgnd.pcx'] = pcx(640,480,1)
entries['glue\\palcs\\tfont.pcx'] = pcx(8,6,1)
for row in json.loads((r/'missions.json').read_text()):
    # Use the actual catalog's base-game mission allowlists.
    path = r/'app/src/main/assets/missions'/f"{row['id']}-files.txt"
    if path.exists() and not row['id'].startswith('exp'):
        entries[path.read_text().splitlines()[0]] = b'TEST'+bytes(4)
archive(b/'full.mpq',entries)
replacement = dict(entries)
replacement['glue\\palcs\\backgnd.pcx'] = pcx(640,480,2)
archive(b/'replacement.exe',replacement,b'MZ'+bytes(510))
alternate = {name.replace('files\\font\\','font\\'):data for name,data in entries.items()}
archive(b/'alternate.mpq',alternate)
without_unused_font = {name:data for name,data in alternate.items() if not name.endswith('50.fnt')}
archive(b/'missing-unused-font.mpq',without_unused_font)
without_menu_font = {name:data for name,data in alternate.items() if not name.endswith('16x.fnt')}
archive(b/'missing-menu-font.mpq',without_menu_font)
palette_only = {name:data for name,data in alternate.items() if not name.endswith('.fnt')}
archive(b/'palette-only.mpq',palette_only)
archive(b/'font-only.mpq',fonts)
broken = dict(entries)
broken['glue\\palcs\\backgnd.pcx'] = bytes(1048577)
archive(b/'too-large.mpq',broken)

harness = b/'MenuImport74Test.java'
harness.write_text(r'''package org.openbw.androidtest;
import java.io.*;import java.nio.file.*;import java.util.*;import java.util.zip.*;import org.json.*;
public class MenuImport74Test {
 static int checks;static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
 static String normal(File archive,File dir)throws Exception{
  try(FileInputStream in=new FileInputStream(archive)){
   return GameContent.install(in.getChannel(),dir,false,id->Collections.singletonList(CampaignCatalog.prefix(id)+"staredit\\scenario.chk"),p->{});
  }
 }
 static byte[] background(File bundle)throws Exception{
  try(ZipFile zip=new ZipFile(bundle)){
   JSONObject m=new JSONObject(new String(zip.getInputStream(zip.getEntry("manifest.json")).readAllBytes(),"UTF-8"));
   JSONArray entries=m.getJSONArray("entries");
   for(int i=0;i<entries.length();i++){JSONObject e=entries.getJSONObject(i);
    if(e.getString("name").equals("glue\\palcs\\backgnd.pcx"))return zip.getInputStream(zip.getEntry("blocks/"+e.getInt("block")+".bin")).readAllBytes();}
   throw new AssertionError("No imported background");
  }
 }
 public static void main(String[] args)throws Exception{
  File root=new File(args[0]),dir=new File(root,"installed");dir.mkdirs();
  File target=new File(dir,InterfaceData.NAME);Files.deleteIfExists(target.toPath());
  check(InterfaceData.summary(target).contains("missing"),"Fresh status is misleading");
  String result=normal(new File(root,"full.mpq"),dir);
  check(result.contains("31 maps imported"),"Normal importer did not import base campaign: "+result);
  check(!result.contains("Interface:"),"Normal importer rejected interface: "+result);
  InterfaceData.validate(target);check(InterfaceData.hasCampaignPalette(target),"Normal import lost palette");
  byte[] first=background(target);check(first.length==308097&&first[128]==1,"Full-size PCX changed or omitted");
  check(InterfaceData.summary(target).contains("imported"),"Installed status missing");
  check(InterfaceData.details(target).contains("decoded=308097"),"Report omitted decoded entry size");
  result=normal(new File(root,"replacement.exe"),dir);
  check(!result.contains("Interface:"),"Reimport inside Install.exe rejected");
  check(background(target)[128]==2,"Normal reimport did not replace background");
  check(CampaignData.validate(new File(dir,CampaignData.filename("terran01"))).equals("terran01"),"Reimport damaged maps");
  result=normal(new File(root,"alternate.mpq"),dir);
  check(!result.contains("Interface:")&&background(target)[128]==1,"Alternate font path not supported");
  result=normal(new File(root,"missing-unused-font.mpq"),dir);
  check(!result.contains("Interface:"),"Missing unused font rejected usable menu: "+result);
  check(InterfaceData.missingMenuFiles(target).isEmpty(),"Missing font50 incorrectly marked as menu failure");
  check(InterfaceData.details(target).contains("Missing font50.fnt"),"Optional missing font not identified");
  check(background(target)[128]==1,"Optional font omission discarded campaign background");
  byte[] saved=Files.readAllBytes(target.toPath());
  result=normal(new File(root,"missing-menu-font.mpq"),dir);
  check(result.contains("kept")&&result.contains("font16x.fnt"),"Replacement would discard an existing menu font");
  check(Arrays.equals(saved,Files.readAllBytes(target.toPath())),"Incomplete replacement damaged existing menu fonts");
  File partialDir=new File(root,"partial");partialDir.mkdirs();File partial=new File(partialDir,InterfaceData.NAME);Files.deleteIfExists(partial.toPath());
  result=normal(new File(root,"missing-menu-font.mpq"),partialDir);
  check(partial.isFile()&&!result.contains("Interface:")&&!result.contains("font16x.fnt"),"Fresh partial import rejected or treated as a font error");
  check(InterfaceData.missingMenuFiles(partial).equals(Collections.singletonList("font16x.fnt")),"Exact missing menu font not identified");
  check(background(partial)[128]==1,"Missing menu font discarded available background");
  File artDir=new File(root,"art-only");artDir.mkdirs();File art=new File(artDir,InterfaceData.NAME);Files.deleteIfExists(art.toPath());
  result=normal(new File(root,"palette-only.mpq"),artDir);
  check(art.isFile()&&InterfaceData.hasCampaignPalette(art),"Palette-only fresh import rejected");
  check(InterfaceData.missingMenuFiles(art).size()==5,"Palette-only import concealed missing fonts");
  check(!result.contains("Interface:")&&!result.contains("font8.fnt"),"Missing CD font copies should not be a menu repair warning");
  result=normal(new File(root,"too-large.mpq"),dir);
  check(result.contains("glue\\palcs\\backgnd.pcx")&&result.contains("1048576"),"Oversize error lacks filename/limit");
  check(Arrays.equals(saved,Files.readAllBytes(target.toPath())),"Bad reimport destroyed working interface");
  try(FileInputStream input=new FileInputStream(new File(root,"font-only.mpq"))){
   try{InterfaceData.importArchive(input.getChannel(),dir,p->{});throw new AssertionError("Complete theme replaced by font-only archive");}
   catch(IOException expected){check(expected.getMessage().contains("kept"),"Downgrade reason missing");}
  }
  check(Arrays.equals(saved,Files.readAllBytes(target.toPath())),"Font-only replacement lost campaign background");
  check(!new File(dir,"interface-import.tmp").exists(),"Failed import left staging data");
  File fingerprint=new File(root,"fingerprint.txt");Files.write(fingerprint.toPath(),"abc".getBytes("UTF-8"));
  check(DiagnosticFiles.describe(fingerprint).contains("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),"Fingerprint incorrect");
  check(DiagnosticFiles.describe(new File(root,"absent")).contains("MISSING"),"Missing file report ambiguous");
  check(!DiagnosticFiles.describe(fingerprint).contains(root.getAbsolutePath()),"Report exposes private absolute path");
  File prepared=NativeData.prepare(target,new File(root,"cache"),"interface");
  check(prepared.isFile(),"Imported interface failed native preparation");
  check(NativeData.prepare(art,new File(root,"art-cache"),"interface").isFile(),"Palette-only import failed native preparation");
  System.out.println("PASS "+checks+" checks: normal import, 31 maps, full-size background, missing unused font, missing menu font, palette-only import, safe replacements, exact missing-file reports and fingerprints.");
 }
}''')
names = ['MissionBundle.java','InterfaceData.java','GameContent.java','CampaignData.java',
         'CampaignCatalog.java','MusicData.java','StoryData.java','CinematicCatalog.java',
         'ProjectFiles.java','DiagnosticFiles.java','NativeData.java','NearbyProtocol.java']
classes = b/'classes'
subprocess.run(['javac','-cp',str(jar),'-d',str(classes),*[str(src/n) for n in names],str(harness)],check=True)
result = subprocess.run(['java','-Xmx48m','-cp',str(classes)+':'+str(jar),
                         'org.openbw.androidtest.MenuImport74Test',str(b)],capture_output=True,text=True)
print(result.stdout+result.stderr)
result.check_returncode()
report = {'version':'1.0.7','versionCode':77,'passed':True,'physicalAndroid':False,
          'fixtures':'Synthetic MPQs with the real 31-mission allowlist and valid 640x480 PCX; caller-owned actual archives are tested separately by run_encrypted_fonts.py.',
          'output':result.stdout.strip(),'backgroundBytes':len(entries['glue\\palcs\\backgnd.pcx']),
          'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()
                          for f in [src/n for n in names]+[Path(__file__)]}}
# Finish the import -> sparse MPQ -> native decoder -> Java menu handoff.
# The rendering harness must first be run with the caller's real core archives.
menu = r/'build-native/menu76'
if not (menu/'classes/org/openbw/androidtest/NativeArt.class').exists():
    raise RuntimeError('Run tests/run_menu_recovery.py with your classic core archives first.')
decoded = b/'decoded'
for name,data in without_unused_font.items():
    if not name.startswith(('font\\','glue\\')):
        continue
    target=decoded/name.replace('\\','/')
    target.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(menu/'extract-interface'),str(b/'cache/interface.mpq'),name,str(target)],check=True)
    assert target.read_bytes()==data, name
handoff = b/'MenuRestored74Test.java'
handoff.write_text(r'''package org.openbw.androidtest;
import java.nio.file.*;import java.util.*;
public class MenuRestored74Test{public static void main(String[]args)throws Exception{
 NativeBridge.root=Paths.get(args[0]);Path imported=Paths.get(args[1]);
 for(String n:new String[]{"8","10","12","14","16","16x","32"}){
  String path="font/font"+n+".fnt";NativeBridge.overrides.put("4/"+path,Files.readAllBytes(imported.resolve(path)));
 }
 for(String n:new String[]{"backgnd.pcx","tfont.pcx"}){
  String path="glue/palcs/"+n;NativeBridge.overrides.put("4/"+path,Files.readAllBytes(imported.resolve(path)));
 }
 for(String bin:new String[]{"glucmpgn","gluexpcmpgn"}){
  NativeArt art=new NativeArt();NativeGlue glue=new NativeGlue(art,bin,"palcs",true);
  if(!glue.paletteName.equals("palcs")||!glue.recovery.isEmpty())throw new AssertionError(glue.recovery);
  if(glue.background.width!=640||glue.background.height!=480||glue.background.pixels[0]!=1)throw new AssertionError("Substitute background still selected");
  for(NativeArt.Font f:new NativeArt.Font[]{glue.tiny,glue.small,glue.large,glue.dialogue,glue.button})if(f.fallback)throw new AssertionError("System font still selected");
  if(!art.diagnostics().contains("imported interface"))throw new AssertionError("Missing source evidence");
  glue.close();
 }
 System.out.println("PASS partial import (font50 absent) -> sparse MPQ -> native decode -> both campaign menus: imported palette and all five menu fonts selected, no system font or palette recovery.");
}}''')
subprocess.run(['javac','-cp',str(menu/'classes'),'-d',str(menu/'classes'),str(handoff)],check=True)
handoff_result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(menu/'classes'),
    'org.openbw.androidtest.MenuRestored74Test',str(menu/'assets'),str(decoded)],capture_output=True,text=True,check=True)
print(handoff_result.stdout)
report['menuHandoff']=handoff_result.stdout.strip()
# Reproduce the tester's exact *asset availability*: palette present, no fonts.
# Synthetic PCXs verify handoff without pretending to be the tester's archive.
art_decoded = b/'art-decoded'
for name in ['glue/palcs/backgnd.pcx', 'glue/palcs/tfont.pcx']:
    target=art_decoded/name;target.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(menu/'extract-interface'),str(b/'art-cache/interface.mpq'),name,str(target)],check=True)
palette_handoff = b/'PaletteFallback75Test.java'
palette_handoff.write_text(r'''package org.openbw.androidtest;
import java.nio.file.*;
public class PaletteFallback75Test {public static void main(String[]args)throws Exception {
 NativeBridge.root=Paths.get(args[0]);Path imported=Paths.get(args[1]);
 for(int slot:new int[]{0,1,2,4})for(String prefix:new String[]{"files/font/","font/"})
  for(String size:new String[]{"8","10","12","14","16","16x","32","50"})
   NativeBridge.overrides.put(slot+"/"+prefix+"font"+size+".fnt",null);
 for(String name:new String[]{"glue/palcs/backgnd.pcx","glue/palcs/tfont.pcx"})
  NativeBridge.overrides.put("4/"+name,Files.readAllBytes(imported.resolve(name)));
 for(String bin:new String[]{"glucmpgn","gluexpcmpgn"}) {
  NativeArt art=new NativeArt();NativeGlue glue=new NativeGlue(art,bin,"palcs",true);
  if(!glue.paletteName.equals("palcs")||!glue.artworkRecovery.isEmpty())throw new AssertionError("Font-only fallback replaces/covers artwork");
  for(NativeArt.Font f:new NativeArt.Font[]{glue.tiny,glue.small,glue.dialogue,glue.large,glue.button})
   if(!f.fallback||f.glyph('A',2)==null)throw new AssertionError("Fontless import not rendered");
  if(!art.diagnostics().contains("STYLED SYSTEM FALLBACK"))throw new AssertionError("Fallback not disclosed");
  glue.close();
 }
 System.out.println("PASS palette-only normal import -> sparse MPQ -> native decoder -> both menus retain campaign palette, use styled system fonts and have no artwork repair warning.");
}}''')
subprocess.run(['javac','-cp',str(menu/'classes'),'-d',str(menu/'classes'),str(palette_handoff)],check=True)
palette_result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(menu/'classes'),
 'org.openbw.androidtest.PaletteFallback75Test',str(menu/'assets'),str(art_decoded)],capture_output=True,text=True,check=True)
print(palette_result.stdout)
report['paletteOnlyHandoff']=palette_result.stdout.strip()
if a.baseline_source:
    old = b/'baseline';old.mkdir(exist_ok=True)
    with zipfile.ZipFile(a.baseline_source) as archive_zip:
        for name in ['MissionBundle.java','CampaignCatalog.java','InterfaceData.java']:
            member=next(n for n in archive_zip.namelist() if n.endswith('/'+name))
            (old/name).write_bytes(archive_zip.read(member))
    baseline = old/'Baseline.java'
    baseline.write_text(r'''package org.openbw.androidtest;import java.io.*;import java.util.*;
public class Baseline{public static void main(String[]args)throws Exception{
 try{InterfaceData.validate(new File(args[0]));throw new AssertionError("Expected old validator to reject missing optional font");}
 catch(IOException expected){if(!expected.getMessage().contains("font set is incomplete"))throw expected;
  System.out.println("REPRODUCED 1.0.3: valid background and all menu fonts rejected because font50 is absent: "+expected.getMessage());}
}}''')
    subprocess.run(['javac','-cp',str(jar),'-d',str(old/'classes'),str(old/'MissionBundle.java'),str(old/'CampaignCatalog.java'),str(old/'InterfaceData.java'),str(baseline)],check=True)
    result = subprocess.run(['java','-cp',str(old/'classes')+':'+str(jar),'org.openbw.androidtest.Baseline',str(b/'installed/StarDroid-Interface.zip')],capture_output=True,text=True,check=True)
    print(result.stdout)
    report['baselineReproduction']=result.stdout.strip()
(r/'validation/menu-import-v1.0.7.json').write_text(json.dumps(report,indent=2)+'\n')

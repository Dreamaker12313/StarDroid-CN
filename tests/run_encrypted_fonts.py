#!/usr/bin/env python3
"""Exercise installed-font decoding with caller-owned classic MPQs.

Run run_menu_recovery.py and run_menu_import.py first. Requires --stardat,
--broodat, --patch, --starcraft. Optional --reference-fonts compares independently
decoded FONT bytes without bundling any game data or installation metadata.
"""
import argparse, hashlib, json, re, subprocess
from pathlib import Path

r = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
for name in ['stardat', 'broodat', 'patch', 'starcraft']:
    p.add_argument('--' + name, required=True, type=Path)
p.add_argument('--reference-fonts', type=Path)
p.add_argument('--baseline-source', type=Path)
a = p.parse_args()
b = r/'build-native/encrypted76'; b.mkdir(parents=True, exist_ok=True)
menu = r/'build-native/menu76'; imported = r/'build-native/import76'
extract = menu/'extract-interface'; assets = b/'assets'
src = r/'app/src/main/java/org/openbw/androidtest'
jar = r/'build-native/json-20240303.jar'

def run(command):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout

# Use the same base archive importer as Import game files, including interface
# installation and sparse reconstruction, rather than installing loose PCXs.
install = b/'RealImport76.java'
install.write_text('''package org.openbw.androidtest;
import java.io.*;import java.util.*;
class RealImport76 {public static void main(String[]a)throws Exception {
 File dir=new File(a[1]);dir.mkdirs();String result;
 try(FileInputStream input=new FileInputStream(a[0])) {
  result=GameContent.install(input.getChannel(),dir,false,
   id->Collections.singletonList(CampaignCatalog.prefix(id)+"staredit\\\\scenario.chk"),v->{});
 }
 if(!result.contains("31 maps imported")||result.contains("Interface:")||result.contains("Campaign artwork is unavailable"))
  throw new AssertionError(result);
 File bundle=new File(dir,InterfaceData.NAME);
 if(!InterfaceData.hasCampaignPalette(bundle))throw new AssertionError("Actual artwork omitted");
 if(InterfaceData.missingMenuFiles(bundle).size()!=5)throw new AssertionError("Expected no CD menu font copies");
 NativeData.prepare(bundle,new File(a[2]),"interface");
 System.out.println("PASS actual StarCraft.mpq normal import: 31 maps and campaign artwork; no font repair warning.");
}}''')
run(['javac', '-cp', str(imported/'classes')+':'+str(jar), '-d', b, install])
import_result = run(['java', '-Xmx128m', '-cp', str(b)+':'+str(imported/'classes')+':'+str(jar),
                    'org.openbw.androidtest.RealImport76', a.starcraft, b/'installed', b/'cache'])
names = {'rez/'+n+'.bin' for n in ['glumain', 'glucmpgn', 'gluexpcmpgn', 'glulogin']}
names |= {'glue/'+pal+'/'+file for pal in ['palmm','palnl','palcs']
          for file in ['backgnd.pcx','tfont.pcx','teffect.pcx','dlg.grp','tile.grp']}
names |= {prefix+'font'+size+'.fnt' for prefix in ['files/font/', 'font/']
          for size in ['8','10','12','14','16','16x','32','50']}
names.add('font/font.gid')
archives = [(0,a.stardat),(1,a.broodat),(2,a.patch),(4,b/'cache/interface.mpq')]

def extract_names(paths):
    extra = set()
    for slot, archive in archives:
        for name in sorted(paths):
            dest = assets/str(slot)/name; dest.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run([str(extract),str(archive),name,str(dest)], capture_output=True)
            if result.returncode: dest.unlink(missing_ok=True)
            elif name.endswith('.bin'):
                extra |= {v.decode('cp1252').replace('\\','/').lower()
                          for v in re.findall(rb'(?:glue|GLUE)[^\0]*?\.[pP][cC][xX]',dest.read_bytes())}
    return extra

try:
    extra = extract_names(names)
    extract_names(extra - names)
    classes = b/'classes'
    run(['javac','-cp',menu/'classes','-d',classes,r/'tests/EncryptedFontTest.java'])
    command = ['java','-Djava.awt.headless=true','-cp',str(classes)+':'+str(menu/'classes'),
               'org.openbw.androidtest.EncryptedFontTest',assets,b]
    if a.reference_fonts: command.append(a.reference_fonts)
    result = run(command)
    report = {'version':'1.0.7','versionCode':77,'passed':True,'physicalAndroid':False,
              'actualImport':import_result.strip(),'output':result.strip(),
              'independentDecodedFontComparison':bool(a.reference_fonts),
              'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()
                for f in [src/'ClassicFontCipher.java',src/'NativeArt.java',r/'tests/EncryptedFontTest.java',Path(__file__)]}}
    if a.baseline_source:
        import zipfile
        old = b/'baseline'; old.mkdir(exist_ok=True)
        with zipfile.ZipFile(a.baseline_source) as z:
            (old/'NativeArt.java').write_bytes(z.read(next(n for n in z.namelist() if n.endswith('/NativeArt.java'))))
        (old/'OldFontTest.java').write_text('''package org.openbw.androidtest;
import java.nio.file.*;class OldFontTest{public static void main(String[]a){NativeBridge.root=Paths.get(a[0]);
NativeArt art=new NativeArt();NativeArt.PCX tint=art.pcx("glue/palcs/tfont.pcx",false,-1),bg=art.pcx("glue/palcs/backgnd.pcx",false,-1);
for(String s:new String[]{"8","10","14","16","16x"})if(!art.font(s,tint,bg.palette,1).fallback)throw new AssertionError("Baseline unexpectedly read encrypted font");
System.out.println("REPRODUCED 1.0.5: all five menu fonts fall back on the same actual archives.");}}''')
        run(['javac','-cp',menu/'classes','-d',old,old/'NativeArt.java',old/'OldFontTest.java'])
        report['baseline'] = run(['java','-cp',str(old)+':'+str(menu/'classes'),
            'org.openbw.androidtest.OldFontTest',assets]).strip()
    (r/'validation/encrypted-fonts-v1.0.7.json').write_text(json.dumps(report,indent=2)+'\n')
    print(import_result + result + report.get('baseline',''))
finally:
    # Even the encrypted installation metadata is kept out of persistent reports.
    for slot, _ in archives: (assets/str(slot)/'font/font.gid').unlink(missing_ok=True)

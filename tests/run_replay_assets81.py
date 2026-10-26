#!/usr/bin/env python3
"""Verify imported original load-list UI and DELETE geometry without bundling assets."""
from pathlib import Path
import argparse, hashlib, json, struct, subprocess, tempfile

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(); p.add_argument('data_dir',type=Path); args = p.parse_args()
source = root/'app/src/main/java/org/openbw/androidtest'
names = ['MissionBundle.java','CampaignCatalog.java','InterfaceData.java','NativeData.java','NearbyProtocol.java']
jar = root/'build-native/json-20240303.jar'
extract = root/'build-native/reign79/extract'
test = root/'tests/ReplayAssets81Test.java'
compared = []
with tempfile.TemporaryDirectory(prefix='stardroid-replay-assets81-') as tmp:
    work = Path(tmp)
    subprocess.run(['javac','-encoding','UTF-8','-cp',str(jar),'-d',str(work/'classes'),*[str(source/n) for n in names],str(test)],check=True)
    run = subprocess.run(['java','-cp',str(work/'classes')+':'+str(jar),'org.openbw.androidtest.ReplayAssets81Test',str(args.data_dir.resolve()),str(work/'output')],capture_output=True,text=True)
    print(run.stdout+run.stderr,end='');run.check_returncode()
    for game in ['StarCraft','BroodWar']:
        archive=args.data_dir/(game+'.mpq');compact=work/'output'/game/'interface.mpq'
        for name in ['rez/gluload.bin','glue/load/plist.pcx','glue/load/pinfo.pcx']:
            original=work/'original.bin';rebuilt=work/'rebuilt.bin'
            for mpq,path in [(archive,original),(compact,rebuilt)]:
                subprocess.run([str(extract),str(mpq),name,str(path)],check=True,capture_output=True)
            raw=original.read_bytes();assert raw==rebuilt.read_bytes(),(game,name)
            compared.append({'game':game,'asset':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            if name.endswith('.bin'):
                u16=lambda offset:struct.unpack_from('<H',raw,offset)[0]
                u32=lambda offset:struct.unpack_from('<I',raw,offset)[0]
                pos=u32(66);widgets={}
                while pos:
                    widgets[u16(pos+32)]=[u16(pos+4),u16(pos+6),u16(pos+12),u16(pos+14)]
                    pos=u32(pos)
                assert widgets[6]==[64,92,286,218],widgets
                assert widgets[7]==[44,332,164,20],widgets
report={'passed':True,'physicalAndroid':False,'originalLoadListImported':True,'originalDeleteWidget':7,
        'legacyBundlesAccepted':True,'assetComparisons':compared,
        'sourceSha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [*[source/n for n in names],test,Path(__file__)]}}
(root/'validation/replay-assets-v81.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS 6 original replay-menu asset comparisons, both original DELETE widgets, and legacy bundle compatibility')

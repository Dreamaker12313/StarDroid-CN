#!/usr/bin/env python3
"""Protocol/transfer regression and a reproducible synthetic latency benchmark."""
import hashlib,json,pathlib,shutil,subprocess
r=pathlib.Path(__file__).resolve().parents[1];b=r/'build-native/nearby-efficiency54'
shutil.rmtree(b,ignore_errors=True);b.mkdir(parents=True)
src=r/'app/src/main/java/org/openbw/androidtest';names=['NearbyProtocol.java','NearbyMatch.java','MatchSetup.java','MatchSnapshot.java','NearbyMapCodec.java','NearbyMapCache.java','NativeData.java']
files=[src/n for n in names]+[r/'tests/NearbyEfficiencyTest.java',*sorted((r/'tests/fixtures/nearby50').glob('*.java'))]
jar=r/'build-native/json-20240303.jar'
subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn','-classpath',str(jar),'-d',str(b/'classes'),*map(str,files)],check=True)
run=subprocess.run(['java','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.NearbyEfficiencyTest',str(b/'output')],check=True,text=True,capture_output=True)
print(run.stdout)
report=json.loads((b/'output/efficiency.json').read_text());report['sourceSha256']={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files+[pathlib.Path(__file__)]}
(r/'validation/nearby-efficiency-v54.json').write_text(json.dumps(report,indent=2)+'\n')

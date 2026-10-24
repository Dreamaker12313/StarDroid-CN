#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build-native/match54';b.mkdir(parents=True,exist_ok=True);src=r/'app/src/main/java/org/openbw/androidtest'
files=[src/n for n in ['NearbyProtocol.java','NearbyMatch.java','NearbyMapCodec.java','MatchSetup.java','MatchSnapshot.java']]+[r/'tests/Match54Test.java'];jar=r/'build-native/json-20240303.jar'
subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn','-classpath',str(jar),'-d',str(b/'classes'),*map(str,files)],check=True)
p=subprocess.run(['java','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.Match54Test'],capture_output=True,text=True);print(p.stdout+p.stderr);p.check_returncode()
(r/'validation/match-v54.json').write_text(json.dumps({'passed':True,'physicalPhone':False,'output':p.stdout.strip(),'sources':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build-native/room55';b.mkdir(parents=True,exist_ok=True);src=r/'app/src/main/java/org/openbw/androidtest'
files=[src/n for n in ['RoomProtocol.java','RoomSnapshot.java','RoomMatch.java','MatchSetup.java','MatchSnapshot.java','NearbyProtocol.java','NearbyMatch.java','NearbyMapCodec.java']]+[r/'tests/RoomMatchTest.java']
jar=r/'build-native/json-20240303.jar'
p=subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn','-classpath',str(jar),'-d',str(b),*map(str,files)],capture_output=True,text=True);print(p.stdout+p.stderr,flush=True);p.check_returncode()
p=subprocess.run(['java','-cp',str(b)+':'+str(jar),'org.openbw.androidtest.RoomMatchTest'],capture_output=True,text=True);print(p.stdout+p.stderr,flush=True);p.check_returncode()
(r/'validation/room-v55.json').write_text(json.dumps({'passed':True,'physicalDevices':False,'output':p.stdout,'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files+[Path(__file__)]}},indent=2)+'\n')

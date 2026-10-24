#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];b=r/'build-native/socket55';b.mkdir(parents=True,exist_ok=True);src=r/'app/src/main/java/org/openbw/androidtest'
files=[src/n for n in ['RoomProtocol.java','RoomSnapshot.java','RoomMatch.java','MatchSetup.java','MatchSnapshot.java','NearbyProtocol.java','NearbyMatch.java','NearbyMapCodec.java','LocalTransport.java']]+[r/'tests'/n for n in ['RoomMatchTest.java','LocalTransportTest.java','RoomSocketTest.java']];jar=r/'build-native/json-20240303.jar'
p=subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn','-classpath',str(jar),'-d',str(b),*map(str,files)],capture_output=True,text=True);print(p.stdout+p.stderr,flush=True);p.check_returncode();output=[]
for cls in ['LocalTransportTest','RoomSocketTest']:
 p=subprocess.run(['java','-cp',str(b)+':'+str(jar),'org.openbw.androidtest.'+cls],capture_output=True,text=True,timeout=45);print(p.stdout+p.stderr,flush=True);p.check_returncode();output.append(p.stdout)
(r/'validation/room-sockets-v55.json').write_text(json.dumps({'passed':True,'realDesktopSockets':True,'physicalDevices':False,'output':output,'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files+[Path(__file__)]}},indent=2)+'\n')

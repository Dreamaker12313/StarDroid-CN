#!/usr/bin/env python3
"""Exercise production Google-free stream transport over real desktop sockets."""
import hashlib,json,pathlib,subprocess
r=pathlib.Path(__file__).resolve().parents[1];b=r/'build-native/local54';b.mkdir(parents=True,exist_ok=True)
src=r/'app/src/main/java/org/openbw/androidtest'
files=[src/n for n in ['NearbyProtocol.java','LocalTransport.java','NearbyMatch.java','MatchSetup.java','MatchSnapshot.java','NearbyMapCodec.java','NativeData.java','NearbyMapCache.java']]+[r/'tests'/n for n in ['LocalTransportTest.java','LocalMatchTest.java','NearbyProtocolTest.java']]
jar=r/'build-native/json-20240303.jar'
assert hashlib.sha256(jar.read_bytes()).hexdigest()=='3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed'
subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-classpath',str(jar),'-d',str(b),*map(str,files)],check=True)
result=subprocess.run(['java','-cp',str(b),'org.openbw.androidtest.LocalTransportTest'],check=False,capture_output=True,text=True,timeout=45)
print(result.stdout+result.stderr);result.check_returncode()
match=subprocess.run(['java','-cp',str(b)+':'+str(jar),'org.openbw.androidtest.LocalMatchTest'],check=False,capture_output=True,text=True,timeout=45)
print(match.stdout+match.stderr);match.check_returncode()
report={'version':'0.54','passed':True,'actualProductionClasses':['LocalTransport','NearbyProtocol'],'realDesktopSockets':True,'physicalAndroidRadioTested':False,'cases':['encrypted stream round trip','pairing code and capability negotiation','Wi-Fi session authentication','wrong key and tamper rejection','replay rejection','Bluetooth to Wi-Fi handover with in-flight packets','duplicate suppression and ordering','Wi-Fi stall and Bluetooth fallback','bounded queues','invalid acknowledgement rejection','all links lost','real TCP encrypted pipes','valid final messages precede EOF'],'output':result.stdout.strip(),'sourceSha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files+[pathlib.Path(__file__)]}}
report['integratedMatchOutput']=match.stdout.strip()
(r/'validation/local-transport-v54.json').write_text(json.dumps(report,indent=2)+'\n')

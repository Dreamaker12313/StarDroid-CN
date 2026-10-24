#!/usr/bin/env python3
"""Run the production Java protocol and build the real transferred-map fixture."""
import hashlib,json,os,pathlib,subprocess,urllib.request
r=pathlib.Path(__file__).resolve().parents[1];b=r/'build-native';b.mkdir(exist_ok=True)
jar=b/'json-20240303.jar'
if not jar.exists():urllib.request.urlretrieve('https://repo.maven.apache.org/maven2/org/json/json/20240303/json-20240303.jar',jar)
assert hashlib.sha256(jar.read_bytes()).hexdigest()=='3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed'
extract=os.environ.get('OPENBW_MAP_EXTRACTOR')
if not extract:
 cxx=os.environ.get('CXX',str(r/'.tools/android-ndk-r27d/toolchains/llvm/prebuilt/linux-x86_64/bin/clang++'))
 extract=str(b/'nearby-extract')
 subprocess.run([cxx,'-std=c++17','-O0','-I'+str(r/'native-engine'),str(r/'tests/extract_interface46.cpp'),'-o',extract],check=True)
subprocess.run([extract,str(r/'app/src/main/assets/native/weave.scx'),'staredit/scenario.chk',str(b/'nearby-weave.chk')],check=True)
src=r/'app/src/main/java/org/openbw/androidtest';names=['NearbyProtocol.java','NearbyMatch.java','MatchSetup.java','MatchSnapshot.java','NearbyMapCodec.java','NearbyMapCache.java','NativeData.java'];files=[src/n for n in names]+[r/'tests/NearbyProtocolTest.java']
subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-classpath',str(jar),'-d',str(b/'nearby-java'),*map(str,files)],check=True)
result=subprocess.run(['java','-cp',str(b/'nearby-java')+':'+str(jar),'org.openbw.androidtest.NearbyProtocolTest',str(b/'nearby-weave.chk'),str(b/'map54')],check=True,capture_output=True,text=True)
print(result.stdout)
report={'version':'0.54','passed':True,'physicalRadioTested':False,'actualProductionClasses':names,'cases':['bounded wire format','chunked map and SHA-256 verification','version mismatch','core data mismatch','initial state mismatch','delayed two-peer simulation','shared pause and resume','stale pause message','missing inputs freeze simulation','desync abort','explicit surrender','connection loss','results exit is not surrender','scenario MPQ construction'],'output':result.stdout.strip(),'sourceSha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}}
(r/'validation/nearby-protocol-v54.json').write_text(json.dumps(report,indent=2)+'\n')

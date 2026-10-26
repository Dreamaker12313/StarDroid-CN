#!/usr/bin/env python3
"""Reject incompatible replay and Nearby simulation rules before gameplay."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report-prefix',default='compat11')
args=parser.parse_args();prefix=args.report_prefix
if not re.fullmatch(r'[a-z0-9-]+',prefix):parser.error('Report prefix must contain lowercase letters, digits or hyphens')
r=Path(__file__).resolve().parents[1];out=r/'build-native'/(prefix+'-native');out.mkdir(parents=True,exist_ok=True)
stage=r/'native-engine'
subprocess.run(['gcc','-O2','-c',str(r/'vendor/libsmacker/smacker.c'),'-o',str(out/'smacker.o')],check=True)
cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER']
cmd+=['-I'+str(p)for p in (stage,stage/'ui',stage/'web')]
cmd+=[str(r/'tests/native_compat11.cpp'),str(r/'native/generated/wasm_backend.cpp'),str(out/'smacker.o'),'-o',str(out/'test')]
subprocess.run(cmd,check=True)
fixture=r/'build-native/replay-thumbnail-ui/assets/0/preview/scenario.chk'
result=subprocess.run([str(out/'test'),str(fixture)],check=True,capture_output=True,text=True);print(result.stdout,end='')
names=['tests/native_compat11.cpp','tests/native_replay81.cpp','tests/run_compat11.py','native/replay.h','native/runtime.cpp','app/src/main/java/org/openbw/androidtest/NativeBridge.java']
(r/'validation'/(prefix+'-native.json')).write_text(json.dumps({'passed':True,'scope':'Host native replay parse/open compatibility guards; current metadata accepted, old/future rules rejected before live state mutation','result':result.stdout.strip(),'embeddedChkBytes':fixture.stat().st_size,'sourceSha256':{n:hashlib.sha256((r/n).read_bytes()).hexdigest()for n in names}},indent=2)+'\n')

jar=r/'build-native/json-20240303.jar'
if not jar.exists():
 import urllib.request
 urllib.request.urlretrieve('https://repo.maven.apache.org/maven2/org/json/json/20240303/json-20240303.jar',jar)
assert hashlib.sha256(jar.read_bytes()).hexdigest()=='3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed'
src=r/'app/src/main/java/org/openbw/androidtest'
files=[src/n for n in ['NearbyProtocol.java','NearbyMatch.java','MatchSetup.java','MatchSnapshot.java','NearbyMapCodec.java','NearbyMapCache.java','NativeData.java']]
files += [r/'tests/NearbyProtocolTest.java',r/'tests/NearbyCompatibility11Test.java']
subprocess.run(['javac','-cp',str(jar),'-d',str(out/'java'),*map(str,files)],check=True)
result=subprocess.run(['java','-cp',str(out/'java')+':'+str(jar),'org.openbw.androidtest.NearbyCompatibility11Test'],check=True,capture_output=True,text=True);print(result.stdout,end='')
(r/'validation'/(prefix+'-nearby.json')).write_text(json.dumps({'passed':True,'physicalRadioTested':False,'result':result.stdout.strip(),'sourceSha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files+[Path(__file__)]}},indent=2)+'\n')

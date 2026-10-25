#!/usr/bin/env python3
"""Fingerprint completed build-78 regression logs; rejects missing/failed results.
Run Maps78Test, Language78Test with both data sets, run_presentation78.py,
NearbyProtocolTest, native-revision78 (normal + sweep), and native-saves first.
"""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[1];out=r/'build-native/revision78';j='app/src/main/java/org/openbw/androidtest/'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(path,required):
 s=path.read_text();assert 'FAIL ' not in s,(path,s)
 for word in required:assert word in s,(path,word)
 return s

def report(name,logs,files,**extra):
 value=dict(passed=True,version='1.0.8',physicalAndroid=False,output='\n'.join(logs),sourceSha256={n:sha(r/n)for n in files},**extra)
 (r/'validation'/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
report('maps-v78.json',[read(out/'maps.log',['PASS 5111','2501 distinct maps'])],
 [j+n+'.java'for n in ['NativeMaps','NativeMapCheck','MainActivity','NativeSurface','NativeBridge']]+['native/runtime.cpp','tests/Maps78Test.java'],testedMaps=2501,maxMaps=10000,maxExpandedBytes=8*1024**3,maxMapBytes=64*1024**2,heapLimitMiB=128)
report('languages-v78.json',[read(out/'languages-english.log',['PASS 488','Russian=false']),read(out/'languages-russian.log',['PASS 491','Russian=true'])],
 [j+n+'.java'for n in ['GameLanguage','PortText','NativeArt','NativeGlue','MenuLabels','MainActivity','NativeSurface']]+['app/src/main/assets/native/ui-languages.tsv','tests/Language78Test.java','tests/run_languages78.py'],languages=['en','ru','de','es','fr'],russianRequiresRussianData=False)
protocol=json.loads((r/'validation/protocol-v77.json').read_text())
report('protocol-v78.json',[read(r/'build-native/protocol78/result.txt',['PASS 1430'])],list(protocol['sourceSha256']),build=78)
report('saves-v78.json',[read(out/'saves.log',['PASS schema 1/2/3 compatibility','PASS damaged/truncated','PASS wrote persistent snapshot'])],
 ['native/save_state.h','native/multiplayer.h','tests/native_saves.cpp','tests/native_fixture.h'],schema=4,readSchemas=[1,2,3,4],freshProcessRead=True,binarySha256=sha(r/'build-native/host/native-saves'))
report('native-v78.json',[read(out/'native.log',['PASS one larva','PASS queued-input','PASS island builder','PASS all three transports','RESULT loaded=31 delivered=21 error=']),read(out/'sweep.log',['PASS 64 campaign maps / 144 computer owners'])],
 ['patches/native-polish78.patch','scripts/prepare_native.py','native/runtime.cpp','native/multiplayer.h','native/save_state.h','tests/native_revision78.cpp','tests/build_native_host.py'],
 binarySha256=sha(r/'build-native/host/native-revision78'),campaignLoadChecks=64,computerOwnerRestrictionChecks=144,
 transportCases=6,fullCampaignPlaythrough=False,originalZerg4Frames=18000,originalZerg4Loaded=31,originalZerg4Unloaded=21,
 preparedSourceSha256={n:sha(r/'native-engine'/n)for n in ['web/campaign_ai.h','web/sandbox.h']})
print('Collected maps, languages, protocol, saves and native reports for build 78.')

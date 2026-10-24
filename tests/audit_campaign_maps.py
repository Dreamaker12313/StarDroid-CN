#!/usr/bin/env python3
"""Audit original CHK references and mission routing, without claiming gameplay."""
import argparse,collections,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('maps',type=Path)
args=parser.parse_args()
catalog=json.loads((ROOT/'app/src/main/assets/native/missions.json').read_text())
bycode={m['code']:m for m in catalog}
byid={m['id']:m for m in catalog}
conditions={1,2,3,4,5,7,11,12,14,15,17,21,22,23}
# These presentation-only action types are currently skipped by the engine.
leaderboards={17,18,19,20,21,33,34,35,36,37}
actions={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,22,23,24,25,26,27,28,30,31,32,38,39,41,42,43,44,45,46,47,48,49,50,51,52,54,55,57}
location_actions={10,11,16,23,25,28,38,39,42,43,44,46,48,49,50,51,52}
text_actions={7,9,12,17,18,19,20,21,33,34,35,36,37,41,47}
results=[];issues=[];presentation=[]
for path in sorted(args.maps.glob('*.chk')):
    ident=path.stem;m=byid[ident];data=path.read_bytes();sections={};pos=0
    while pos<len(data):
        tag,n=struct.unpack_from('<4sI',data,pos);pos+=8
        if pos+n>len(data):raise ValueError(f'{ident}: truncated section')
        sections[tag]=sections.get(tag,b'')+data[pos:pos+n];pos+=n
    strings=sections[b'STR '];sn=struct.unpack_from('<H',strings)[0]
    def string(i):
        if not i:return ''
        assert 0<i<=sn,(ident,'string',i)
        offset=struct.unpack_from('<H',strings,2*i)[0]
        assert offset<len(strings),(ident,'string offset',i)
        return strings[offset:].split(b'\0')[0].decode('cp1252')
    owners=sections[b'OWNR'];forces=sections[b'FORC'];nloc=len(sections[b'MRGN'])//20
    assert owners[m['player']]==6,(ident,'campaign player is not playable')
    assert sections[b'SIDE'][m['player']]==m['race'],(ident,'campaign race mismatch')
    assert m.get('next',0) in bycode or m.get('next',0)==0,(ident,'missing next mission')
    triggers=sections[b'TRIG'];assert len(triggers)%2400==0
    cc=collections.Counter();ac=collections.Counter();scripts=collections.Counter();routes=[];wins=[];losses=[];goals=[];gaps=[]
    for offset in range(0,len(triggers),2400):
        index=offset//2400;enabled=triggers[offset+2372:offset+2400]
        human=bool(enabled[m['player']] or enabled[17] or enabled[18+forces[m['player']]])
        for ci in range(16):
            loc,group,count,unit,comparison,typ,extra,flags,unused=struct.unpack_from('<IIIHBBBBH',triggers,offset+20*ci)
            if not typ:break
            if flags&2:continue
            cc[typ]+=1
            if typ not in conditions:issues.append([ident,index,'unsupported condition',typ])
            if typ in (3,7,17):assert 1<=loc<=nloc,(ident,index,'condition location',loc)
            if typ in (2,3,5,7,15,17):assert unit<233,(ident,index,'condition unit',unit)
        for ai in range(64):
            loc,text,sound,time,group,other,unit,typ,modifier,flags,unused=struct.unpack_from('<6IH3BxH',triggers,offset+320+32*ai)
            if not typ:break
            if flags&2:continue
            ac[typ]+=1
            if typ in leaderboards:gaps.append(dict(trigger=index,action=typ,title=string(text)))
            elif typ not in actions:issues.append([ident,index,'unsupported action',typ])
            if typ in location_actions:assert 1<=loc<=nloc,(ident,index,'action location',typ,loc)
            if typ in (39,46):assert 1<=other<=nloc,(ident,index,'destination location',other)
            if typ in (11,44):assert unit<228,(ident,index,'creation unit',unit)
            if typ==11 and flags&8:assert 1<=other<=len(sections[b'UPRP'])//20,(ident,index,'unit properties',other)
            if typ in text_actions:string(text)
            if typ in (7,8):string(sound)
            if typ in (15,16):scripts[struct.pack('<I',other).decode('ascii')]+=1
            if typ==41:
                filename=string(text).lower().replace('\\','/').split('/')[-1]
                candidate=[n for n in catalog if n['game']==m['game'] and n['prefix'].rstrip('/').split('/')[-1]+'.scx'==filename]
                assert len(candidate)==1,(ident,index,'unresolved next scenario',filename)
                routes.append(dict(trigger=index,target=candidate[0]['id']))
            if human and typ==1:wins.append(index)
            if human and typ==2:losses.append(index)
            if human and typ==12:goals.append(dict(trigger=index,text=string(text)))
    assert wins,(ident,'no victory trigger for campaign player')
    results.append(dict(mission=ident,title=m['title'],sha256=hashlib.sha256(data).hexdigest(),triggers=len(triggers)//2400,
        conditionRecords=sum(cc.values()),actionRecords=sum(ac.values()),conditions=dict(cc),actions=dict(ac),
        victoryTriggers=wins,defeatTriggers=losses,objectives=goals,nextScenarioRoutes=routes,aiScripts=dict(scripts),
        validReferences=True,skippedLeaderboardActions=gaps))
    if gaps:presentation.append(dict(mission=ident,actions=gaps))
assert len(results)==len(catalog)==64
report=dict(version='0.38',passed=not issues,scope='Static original CHK references, trigger type coverage and mission catalog routing',
    originalMaps=True,originalCoreAssets=False,fullPlaythrough=False,mapCount=len(results),
    triggerCount=sum(x['triggers'] for x in results),conditionRecords=sum(x['conditionRecords'] for x in results),
    actionRecords=sum(x['actionRecords'] for x in results),issues=issues,knownPresentationGaps=presentation,
    limits=['This static audit does not simulate combat or pathfinding.',
            'This static audit inventories script names; real-data simulation is reported separately.',
            'Leaderboard actions are skipped; corresponding objective triggers still run.'],maps=results)
report['sourceSha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('tests/audit_campaign_maps.py','app/src/main/assets/native/missions.json')}
(ROOT/'validation/native-campaign-audit-v38.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('maps','sourceSha256','knownPresentationGaps')},indent=2))
print('Known leaderboard presentation gaps:',len(presentation))
if issues:raise SystemExit(1)

#!/usr/bin/env python3
"""Test multi-mission import with externally supplied original game data."""
import json,os,subprocess,tempfile,zipfile
from pathlib import Path
r=Path(__file__).resolve().parents[1]
tools=Path(os.environ['OPENBW_ANDROID_TOOLS']); archive=Path(os.environ['OPENBW_CAMPAIGN_MPQ'])
work=Path(tempfile.mkdtemp(prefix='openbw-campaign-import-'));classes=work/'classes';classes.mkdir()
def run(*cmd):return subprocess.run([str(c)for c in cmd],check=True,capture_output=True,text=True).stdout
run('java','-jar',tools/'ecj.jar','-source','1.8','-target','1.8','-proc:none','-cp',tools/'json.jar','-d',classes,r/'app/src/main/java/org/openbw/androidtest/MissionBundle.java',r/'app/src/main/java/org/openbw/androidtest/CampaignData.java',r/'tests/ExportHarness.java',r/'tests/CampaignDataHarness.java')
report={'checks':[],'archiveBytes':archive.stat().st_size}
for n in (1,2,3):
 src=work/f'terran0{n}.zip';dst=work/f'OpenBW-Terran0{n}.zip'
 run('java','-Xmx48m','-cp',classes,'ExportHarness',archive,src,r/f'app/src/main/assets/missions/terran0{n}-files.txt')
 with zipfile.ZipFile(src)as z:
  m=json.loads(z.read('manifest.json'));assert m['mission']==f'terran0{n}'
 report[f'mission{n}']={'entries':len(m['entries']),'bytes':src.stat().st_size,'missing':m['missing']}
 print(run('java','-cp',f'{classes}:{tools}/json.jar','org.openbw.androidtest.CampaignDataHarness',src,dst).strip())
 report['checks'].append(f'Mission {n} export under 48 MB heap; every imported/served entry matches original bundle')
print(run('java','-cp',f'{classes}:{tools}/json.jar','org.openbw.androidtest.CampaignDataHarness',work/'terran02.zip',work/'OpenBW-Terran01.zip','reject').strip())
report['checks'].append('Wrong mission rejected without replacing the installed Mission 1 bundle')
bad=work/'bad.zip'
with zipfile.ZipFile(work/'terran02.zip') as src,zipfile.ZipFile(bad,'w')as dst:
 for name in src.namelist():
  data=src.read(name)
  if name=='manifest.json':
   m=json.loads(data);m['entries'][0]['name']=m['entries'][0]['name'].replace('terran02','terran03');data=json.dumps(m).encode()
  dst.writestr(name,data)
print(run('java','-cp',f'{classes}:{tools}/json.jar','org.openbw.androidtest.CampaignDataHarness',bad,work/'OpenBW-Terran02.zip','reject').strip())
report['checks'].append('Mixed-mission manifest rejected without replacing the installed Mission 2 bundle')
(r/'validation/campaign-import.json').write_text(json.dumps(report,indent=2)+'\n')

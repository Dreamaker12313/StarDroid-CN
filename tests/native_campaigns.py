#!/usr/bin/env python3
"""Run a compiled desktop native engine against locally supplied campaign MPQs."""
import concurrent.futures,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
engine,fixtures=sys.argv[1:3]
missions=json.loads((root/'missions.json').read_text())
def check(m):
 p=subprocess.run([engine,fixtures,str(m['code']),'2400'],capture_output=True,text=True,timeout=90)
 lines=[l for l in p.stdout.splitlines() if l.startswith('NATIVE_RESULT ')]
 return dict(json.loads(lines[-1][14:]),passed=True) if p.returncode==0 and lines else dict(mission=m['code'],passed=False,error=(p.stdout+p.stderr)[-2500:])
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,missions))
report={'runtime':'native desktop C++ (same simulation sources as Android ARM64)','requestedFramesPerMission':2400,'notes':'Startup/AI smoke test, not full campaign playthroughs. Early triggered mission outcomes may stop the simulation.','passed':sum(r['passed'] for r in results),'total':len(results),'results':results}
(root/'validation/native-campaigns-v23.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if report['passed']!=report['total']:sys.exit(1)

#!/usr/bin/env python3
"""Original-data Dylarian bunker regression and bounded campaign/custom garrison tests.
Usage: python3 tests/run_bunker11.py CORE_DIR BROODWAR_MPQ --skip-prepare
No original game data is copied into the repository.
"""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('core',type=Path);p.add_argument('broodwar',type=Path);p.add_argument('--skip-prepare',action='store_true');p.add_argument('--skip-build',action='store_true');a=p.parse_args()
out=root/'build-native/bunker11';out.mkdir(parents=True,exist_ok=True)
if not a.skip_prepare:subprocess.run([sys.executable,str(root/'scripts/prepare_native.py')],cwd=root,check=True)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
names=['tests/native_bunker11.cpp','tests/native_abilities79.cpp','tests/run_bunker11.py','patches/native-bunker-ai11.patch','native/runtime.cpp','native/replay.h','native-engine/web/campaign_ai.h','native-engine/bwgame.h']
sources={name:sha(root/name) for name in names}
if not a.skip_build:
 subprocess.run(['gcc','-O2','-c','vendor/libsmacker/smacker.c','-o',str(out/'smacker.o')],cwd=root,check=True)
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER','-Inative-engine','-Inative-engine/ui','-Inative-engine/web','tests/native_bunker11.cpp','native/generated/wasm_backend.cpp',str(out/'smacker.o'),'-o',str(out/'test')],cwd=root,check=True)
r=subprocess.run([str(out/'test'),str(a.core.resolve()),str(a.broodwar.resolve())],cwd=root,capture_output=True,text=True)
(out/'regression.log').write_text(r.stdout+r.stderr);print(r.stdout,end='');print(r.stderr,end='',file=sys.stderr);r.check_returncode()
assert sources=={name:sha(root/name) for name in names},'Relevant sources changed while running; rerun after freeze.'
report=dict(passed=True,version='1.1',originalDylarianUnmodified=True,originalBunkers=12,originalGarrisonedTroops=45,originalBaselineOccupants=0,checks=[s[5:] for s in r.stdout.splitlines() if s.startswith('PASS ')],sourceSha256=sources,binarySha256=sha(out/'test'),originalArchiveSha256=sha(a.broodwar.resolve()),limitations=['Host engine regression, not physical Android testing.','Original Dylarian startup and controlled shared-AI cases, not complete mission playthroughs.','Automatic maintenance is restricted to active computer towns and idle local combat infantry; authored movement, attack waves, transports and human orders remain protected.'])
(root/'validation/bunker-ai11.json').write_text(json.dumps(report,indent=2)+'\n')

#!/usr/bin/env python3
"""Verify and capture original-data single/group/cargo wireframes with damage."""
from pathlib import Path
import hashlib,json,os,subprocess
from PIL import Image,ImageDraw
r=Path(__file__).resolve().parents[1];out=r/'build-native/wireframes11';out.mkdir(parents=True,exist_ok=True);(out/'after').mkdir(exist_ok=True)
subprocess.run(['gcc','-O2','-c',str(r/'vendor/libsmacker/smacker.c'),'-o',str(out/'smacker.o')],check=True)
cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O0','-g0','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread','-DOPENBW_ENABLE_UI','-DOPENBW_NO_SDL_IMAGE','-DOPENBW_NO_SDL_MIXER']
cmd+=['-I'+str(r/p)for p in ('native-engine','native-engine/ui','native-engine/web')]
cmd+=[str(r/'tests/native_wireframes11.cpp'),str(r/'native/generated/wasm_backend.cpp'),str(out/'smacker.o'),'-o',str(out/'test-after')]
subprocess.run(cmd,check=True)
core=r/'build-native/reign79/core'
result=subprocess.run([str(out/'test-after'),str(core),str(out/'after'),'fixed'],check=True,capture_output=True,text=True);print(result.stdout,end='')
# Before/after original pixels, enlarged with nearest-neighbor only.
names={0:'Marine',7:'SCV',12:'Battlecruiser',37:'Zergling',41:'Drone',38:'Hydralisk',65:'Zealot',66:'Dragoon',67:'High Templar',106:'Command Center',131:'Hatchery',154:'Nexus'}
canvas=Image.new('RGB',(1200,1700),'#14171d');d=ImageDraw.Draw(canvas)
d.text((20,12),'Original-data wireframes: HP 100%, 70%, 40%, 15%, 1% | before (left) / corrected (right)',fill='white')
for row,(unit,name) in enumerate(names.items()):
 y=40+row*105;d.text((10,y+6),name,fill='white')
 for col,hp in enumerate([100,70,40,15,1]):
  for side,state in enumerate(['before','after']):
   file=out/state/f'{unit}-0-{hp}.rgba'
   if file.exists():
    im=Image.frombytes('RGBA',(64,64),file.read_bytes());canvas.paste(im,(140+side*530+col*100,y),im)
  # Original 32x32 group tiles below each single-unit frame.
  for side,state in enumerate(['before','after']):
   file=out/state/f'{unit}-1-{hp}.rgba'
   if file.exists():
    im=Image.frombytes('RGBA',(32,32),file.read_bytes());canvas.paste(im,(156+side*530+col*100,y+65),im)
y=1330;d.text((20,y),'Protoss shields 100%, 70%, 40%, 15%, 1%, 0% (HP stays full)',fill='white')
for row,state in enumerate(['before','after']):
 d.text((20,y+30+row*80),state,fill='white')
 for col,sh in enumerate([100,70,40,15,1,0]):
  f=out/state/f'shield-{sh}.rgba'
  if f.exists():
   im=Image.frombytes('RGBA',(64,64),f.read_bytes());canvas.paste(im,(140+col*100,y+25+row*80),im)
y=1530;d.text((20,y),'Cargo silhouettes: corrected Marine / SCV / Zealot at 40% HP',fill='white')
for col,unit in enumerate([0,7,65]):
 f=out/'after'/f'{unit}-2-40.rgba'
 if f.exists():
  im=Image.frombytes('RGBA',(64,64),f.read_bytes()).resize((128,128),Image.Resampling.NEAREST);canvas.paste(im,(140+col*190,y+30),im)
canvas.save(out/'comparison.png')
source=['patches/native-wireframes11.patch','tests/native_wireframes11.cpp','tests/run_wireframes11.py']
report={'passed':True,'result':result.stdout.strip(),'scope':'Original MPQ GRPs: all single, group and transport frames; full/critical palette pixels, HP and shield transitions; live single/group/cargo selection entry points and redraw state; captured original frame pixels.','limitation':'Palette remaps use original assets and documented index tables. Exact classic damage thresholds and randomized part ordering remain approximated; no physical Android device tested.','references':['https://github.com/andreas-volz/stargus/wiki/Starcraft-Palettes'],'sourceSha256':{n:hashlib.sha256((r/n).read_bytes()).hexdigest()for n in source},'captureSha256':hashlib.sha256((out/'comparison.png').read_bytes()).hexdigest(),'originalDataSha256':{n:hashlib.sha256((core/n).read_bytes()).hexdigest()for n in ('STARDAT.MPQ','BROODAT.MPQ','patch_rt.mpq')}}
(r/'validation/wireframes11.json').write_text(json.dumps(report,indent=2)+'\n')

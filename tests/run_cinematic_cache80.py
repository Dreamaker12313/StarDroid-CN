#!/usr/bin/env python3
"""Check lazy cinematic staging and playback after closing/deleting its MPQ."""
import argparse, hashlib, json, subprocess, zipfile, tempfile
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--data-dir',required=True,type=Path);a=p.parse_args()
b=r/'build-native/cinematic-cache80';b.mkdir(parents=True,exist_ok=True)
src=r/'app/src/main/java/org/openbw/androidtest';jar=r/'build-native/json-20240303.jar';outputs=[]
def run(args):
 q=subprocess.run(list(map(str,args)),text=True,capture_output=True);print(q.stdout+'\n'.join(line for line in q.stderr.splitlines() if not line.startswith('CHECK_PHASE ')),end='',flush=True);q.check_returncode()
 if q.stdout.strip():outputs.append(q.stdout.strip())
 return q
surface=(src/'NativeSurface.java').read_text()
def method(signature):
 start=surface.index(signature);end=surface.index('\n  private ',start+1)
 return surface[start:end].replace('private ','',1)
(b/'MovieLifecycle80.java').write_text('''package org.openbw.androidtest;
import java.io.*;import java.util.*;import org.json.*;
class MovieLifecycle80 {
 final File files,cache;final Set<String> availableMovies=new HashSet<String>();Prefs prefs=new Prefs();
 Hud hud;boolean activeGame,failed;NativeArt.Movie cinematic;Runnable cinematicDone;long clock,cinematicStart;String page="",modal="";int logicalWidth;
 MovieLifecycle80(File f,File c){files=f;cache=c;}void closeGlue(){}void closeBriefMovies(){}void message(String s){}void error(Exception e){failed=true;}
'''+method('  private void loadArchives() throws Exception {')+method('  private boolean playCinematic(')+'''
}
class Hud {void close(){}}
class Prefs {Prefs edit(){return this;}Prefs putBoolean(String k,boolean v){return this;}void apply(){}}
class GameLanguage {static boolean russianData;static boolean isRussian(byte[] b){return false;}}
class NativeArt {static String normal(String s){return s.replace('\\\\','/').toLowerCase(Locale.ROOT);}static class Movie {Movie(int slot,String path)throws Exception {NativeBridge.lastMovieSlot=slot;if(NativeBridge.failMovie)throw new IOException("decode failure");if(NativeBridge.paths[slot].isEmpty()||!new File(NativeBridge.paths[slot]).isFile())throw new IOException("Missing temporary archive");}}}
class NativeBridge {static String[] paths=new String[11];static boolean failMovie;static int lastMovieSlot;static {Arrays.fill(paths,"");}
 static void open(int slot,String path){paths[slot]=path;}static byte[] asset(int slot,String path){return null;}static void endGame(){}static int sound(byte[] b,int c,boolean loop){return 0;}}
''')
production=['NativeData','NearbyProtocol','NativeCache','ProjectFiles','CampaignCatalog','CinematicCatalog','StoryData','InterfaceData','MissionBundle','MusicData']
run(['javac','-cp',jar,'-d',b/'classes',*[src/(n+'.java') for n in production],b/'MovieLifecycle80.java',r/'tests/CinematicCache80Test.java'])
run(['java','-Xmx128m','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.CinematicCache80Test',r/'build-native/storage80'])
runtime=(r/'native/runtime.cpp').read_text();start=runtime.index('struct Movie {');end=runtime.index('#ifdef __ANDROID__',start)
(b/'movie-runtime80.h').write_text('#include "data_loading.h"\n#include "'+str(r/'native/audio.h')+'"\n#include "'+str(r/'vendor/libsmacker/smacker.h')+'"\n'+runtime[start:end])
run(['gcc','-O2','-c',r/'vendor/libsmacker/smacker.c','-o',b/'smacker.o'])
run(['g++','-std=c++17','-O2','-pthread','-I'+str(r/'native-engine'),'-I'+str(b),r/'tests/native_cinematic_cache80.cpp',b/'smacker.o','-o',b/'native-cinematic-cache80'])
movies=[]
for game in ['StarCraft','BroodWar']:
 bundle=r/'build-native/storage80/real'/f'{game}-movies.zip'
 with zipfile.ZipFile(bundle) as z: entries=json.loads(z.read('manifest.json'))['entries']
 for entry in entries:
  path=entry['name']
  # Keep lifetime-sensitive inputs outside synchronized source trees: a workspace
  # sync must not recreate a deliberately deleted backing archive during playback.
  with tempfile.TemporaryDirectory(prefix='stardroid-cinematic-cache80-') as temporary_root:
   cache=Path(temporary_root)
   run(['java','-Xmx64m','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.CinematicCache80Test',bundle,cache,path])
   temporary=cache/'cinematic.mpq';size=temporary.stat().st_size
   result=run([b/'native-cinematic-cache80',a.data_dir/(game+'.mpq'),temporary,path])
   assert not temporary.exists();(cache/'cinematic.stamp').unlink(missing_ok=True)
   assert not list(cache.iterdir())
   phase=None;warnings={'baseline':[],'candidate':[]}
   for line in result.stderr.splitlines():
    if line.startswith('CHECK_PHASE '):phase=line.split()[-1]
    elif line.strip():warnings[phase].append(line)
   assert warnings['baseline']==warnings['candidate'], 'Decoder warnings changed after cache removal'
   movies.append(dict(game=game,path=path,temporaryBytes=size,baselineDecoderWarnings=warnings['baseline'],candidateDecoderWarnings=warnings['candidate']))
files=[src/'NativeData.java',src/'NativeCache.java',src/'NativeSurface.java',r/'native/runtime.cpp',r/'native/audio.h',r/'vendor/libsmacker/smacker.c',r/'tests/CinematicCache80Test.java',r/'tests/native_cinematic_cache80.cpp',Path(__file__)]
(r/'validation/cinematic-cache80.json').write_text(json.dumps(dict(passed=True,physicalAndroid=False,retainedMovieCacheBytes=0,movies=movies,checks=outputs,sourceSha256={str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}),indent=2)+'\n')

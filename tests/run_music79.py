#!/usr/bin/env python3
"""Check actual music selection and optionally private original archive playback.

Usage: python3 tests/run_music79.py [--data-dir /path/to/original/archives]
Requires javac/java and build-native/json-20240303.jar. The optional original
checks also require g++ and the prepared native engine. No Android SDK is needed.
"""
import argparse, hashlib, json, os, re, subprocess
from pathlib import Path

r = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--data-dir', type=Path)
p.add_argument('--report', type=Path, default=r/'validation/music-v79.json')
a = p.parse_args()
b = r/'build-native/music79'
b.mkdir(parents=True, exist_ok=True)
src = r/'app/src/main/java/org/openbw/androidtest'
jar = r/'build-native/json-20240303.jar'
surface = (src/'NativeSurface.java').read_text()
start = surface.index('  private void music(String phase) {')
end = surface.index('\n  private ', start + 1)
music = surface[start:end]
# Obsolete manual picks must not survive invisibly after removing their controls.
assert 'nextMusicTrack' not in surface and 'musicTrack' not in surface
assert '"Next track"' not in surface and '"Preview sound"' not in surface and '"tracks"' not in surface
assert '.remove("music-track")' in surface
# These are routing checks, not Android activity instrumentation.
def method(name):
    match=re.search(r'^  private void '+name+r'\(',surface,re.M);assert match,name
    start=surface.index('{',match.end())+1;end=start;depth=1
    while depth:
        if surface[end]=='{':depth+=1
        elif surface[end]=='}':depth-=1
        end+=1
    return surface[start:end-1]
routes={
 'campaign': 'expansion = mission.optString("game").equals("broodwar")' in method('loadMission') and 'music("game")' in method('startMission'),
 'custom': 'missionRace = race;' in method('startSkirmish') and 'NativeBridge.configuredInit(0,' in method('startSkirmish') and 'startMission();' in method('startSkirmish'),
 'nearby': 'missionRace=settings.races[slot];expansion=bw;' in surface and 'public void started(){closeChat();activeGame=true;startMission();}' in surface,
 'replay': 'expansion=replayExpansion;' in method('startReplay') and 'music("game")' in method('startReplay'),
 'savedGame': 'skirmishExpansion' in method('loadSlot') and 'music("game")' in method('loadSlot'),
 'automaticEndOfTrack': 'musicIndex++;\n        music("game");' in surface,
}
assert all(routes.values()),routes
assert 'Sound options retain mute' in (r/'docs/PLAYER-GUIDE.md').read_text()
outputs = []
java_home=Path(os.environ.get('JAVA_HOME',r/'.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64'))

def run(args):
    if args[0] in ('java','javac') and (java_home/'bin'/args[0]).exists(): args=[java_home/'bin'/args[0],*args[1:]]
    q = subprocess.run(list(map(str, args)), text=True, capture_output=True)
    print(q.stdout + q.stderr, end='')
    q.check_returncode()
    outputs.append(q.stdout.strip())

harness = b/'Music79Test.java'
harness.write_text('''package org.openbw.androidtest;
import java.util.*;import java.io.*;
public final class Music79Test {
 int musicIndex,missionRace;boolean expansion,currentMusicExpansion;String musicPhase="",currentMusicPath="",failure="";
 void saveSettings(){}
 void play(String phase){music(phase);}
''' + music + '''
 static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
 public static void main(String[] args)throws Exception{
  Music79Test h=new Music79Test();
  // The same production method serves campaigns, custom games and Nearby games.
  for(boolean bw:new boolean[]{false,true})for(int race=0;race<3;race++){
   h.expansion=bw;h.missionRace=race;h.musicPhase="title";h.musicIndex=99;
   String name=new String[]{"zerg","terran","protoss"}[race];
   for(int index=0;index<7;index++){
    NativeBridge.active=false;h.musicIndex=index;h.music("game");
    check(h.currentMusicPath.equals("music/"+name+(index%3+1)+".wav"),"Wrong loop ordering");
    check(NativeBridge.slot==(bw?6:5),"Wrong original/expansion source");
   }
  }
  h.expansion=true;h.missionRace=1;h.musicPhase="game";h.musicIndex=0;
  NativeBridge.active=false;NativeBridge.missingExpansion=true;h.music("game");
  check(NativeBridge.slot==5&&NativeBridge.active,"Missing expansion track failed original fallback");
  NativeBridge.missingExpansion=false;NativeBridge.missingAll=true;NativeBridge.active=false;h.music("game");
  check(!NativeBridge.active&&h.failure.isEmpty(),"Absent music should be silent, not an engine failure");
  NativeBridge.missingAll=false;NativeBridge.active=false;h.music("game");
  check(h.currentMusicPath.equals("music/terran1.wav")&&!NativeBridge.loop,"Automatic race track failed");
  h.expansion=false;h.music("game");check(NativeBridge.slot==5,"Same-name track retained Brood War audio in original game");
  h.expansion=true;h.music("game");check(NativeBridge.slot==6,"Same-name track retained original audio in Brood War game");
  h.music("briefing");check(h.currentMusicPath.equals("music/trdyroom.wav")&&NativeBridge.loop,"Briefing phase failed");
  h.music("victory");check(h.currentMusicPath.equals("music/tvict.wav")&&!NativeBridge.loop,"Victory phase failed");
  h.music("defeat");check(h.currentMusicPath.equals("music/tdefeat.wav")&&!NativeBridge.loop,"Defeat phase failed");
  MusicThemesTest.runSynthetic();
  System.out.println("PASS production music selection: all races, original/Brood War loops, source fallback, missing assets, expansion switching and phase isolation; manual picker/next/preview removed");
  if(args.length==2){
   File data=new File(args[0]),out=new File(args[1]);
   for(String name:new String[]{"StarCraft","BroodWar"}){
    File source=new File(data,name+".mpq"),temp=new File(out,name+".tmp"),bundle=new File(out,name+".zip");
    try(FileInputStream in=new FileInputStream(source);FileOutputStream stream=new FileOutputStream(temp)){
     MissionBundle.Result result=MissionBundle.exportMusic(in.getChannel(),MusicData.names(),stream,s->{});
     for(String race:new String[]{"terran","zerg","protoss"})for(int track=1;track<=3;track++)check(!result.missing.contains("music\\\\"+race+track+".wav"),"Race theme file missing");
    }
    MusicData.install(temp,bundle);NativeData.prepare(bundle,out,name);
    System.out.println("PASS "+name+" production import, validation and native archive preparation");
   }
  }
 }
}
final class NativeBridge {
 static boolean active,loop,missingExpansion,missingAll,failOriginal;static int slot,starts,seeks;static double position;
 static final HashMap<String,byte[]> fixtures=new HashMap<String,byte[]>();
 static boolean playing(int channel){return active;}
 static byte[] asset(int archive,String name){if(archive==5&&failOriginal)throw new IllegalStateException("Damaged reference archive");if(missingAll||(archive==6&&missingExpansion))return null;return fixtures.getOrDefault(archive+":"+name,new byte[]{(byte)archive});}
 static int sound(byte[] data,int channel,boolean repeat){active=data!=null;loop=repeat;position=0;starts++;if(data!=null&&data.length==1)slot=data[0];return 0;}
 static double soundPosition(int channel){return position;}
 static void seekSound(int channel,int ms){position=ms;seeks++;}
}
''')
production = ['MissionBundle','CampaignCatalog','MusicData','MusicThemes','NativeData','NearbyProtocol']
run(['javac','-cp',jar,'-d',b/'classes',*[src/(name+'.java') for name in production],harness,r/'tests/MusicThemesTest.java'])
run(['java','-Xmx64m','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.Music79Test',
     *([a.data_dir,b] if a.data_dir else [])])
if a.data_dir:
    run(['g++','-std=c++17','-O2','-pthread','-I'+str(r/'native-engine'),r/'tests/native_music79.cpp','-o',b/'native-music79'])
    run([b/'native-music79',a.data_dir/'StarCraft.mpq',a.data_dir/'BroodWar.mpq',b/'StarCraft.mpq',b/'BroodWar.mpq',b])
    run(['java','-Xmx128m','-cp',str(b/'classes'),'org.openbw.androidtest.MusicThemesTest',b])
sdk_compile=False
android_jar=r/'.tools/android-35/android.jar'
if android_jar.exists():
    target=b/'android';target.mkdir(parents=True,exist_ok=True)
    stub=target/'BuildConfig.java';stub.write_text('package org.openbw.androidtest; final class BuildConfig {static final String VERSION_NAME="1.1"; static final int VERSION_CODE=83;}')
    run(['javac','-source','8','-target','8','-encoding','UTF-8','-cp',android_jar,'-d',target,stub,*sorted(src.glob('*.java'))])
    sdk_compile=True
    outputs.append('PASS all production Android Java compiles against SDK35 / Java8')
files = [src/'NativeSurface.java',src/'MusicData.java',src/'MusicThemes.java',src/'MissionBundle.java',src/'NativeData.java',r/'native/audio.h',Path(__file__),r/'tests/native_music79.cpp',r/'tests/MusicThemesTest.java']
a.report.write_text(json.dumps({
    'passed': True, 'physicalAndroid': False, 'originalArchivesTested': bool(a.data_dir),
    'version':'1.1','androidSdk35JavaCompile':sdk_compile,'gameEntrySourceRoutingChecks':routes,'scope':'All three races: production Java music selection, campaign/custom/Nearby routing audit, original import bytes, full native WAV decode and EOF, embedded-original comparison. No physical Android audio test.',
    'availability':'Four themes per race require imported original Brood War soundtrack files; missing expansion files fall back to the original soundtrack.',
    'checks': [s for s in outputs if s],
    'sourceSha256': {str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
},indent=2)+'\n')

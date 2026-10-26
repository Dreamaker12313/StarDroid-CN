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
assert 'musicTrack' not in surface and 'musicEnabled' not in surface
assert '"Play original music"' not in surface
assert '"Next track"' in surface and '"Preview sound"' not in surface and '"tracks"' not in surface
assert '.remove("music-track")' in surface
# These are routing checks, not Android activity instrumentation.
def method(name):
    match=re.search(r'^  private (?:void|boolean) '+name+r'\(',surface,re.M);assert match,name
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
 'automaticEndOfTrack': 'advanceMusic();' in method('tick') and 'musicIndex++;' in method('advanceMusic'),
 'soundButton': 'drawSoundSettings(c, x, y);' in method('drawClassicMenu'),
 'audioMigration': 'loadAudioSettings();' in surface and '.remove("music-enabled")' in method('loadAudioSettings'),
}
assert all(routes.values()),routes
assert 'Sound options retain mute' in (r/'docs/PLAYER-GUIDE.md').read_text()
for name in ['advanceMusic','canNextMusicTrack','nextMusicTrack','drawSoundSettings','loadAudioSettings','saveSettings','syncAudio']:
    match=re.search(r'^  private (?:void|boolean) '+name+r'\(',surface,re.M);assert match,name
    begin=match.start();start=surface.index('{',match.end())+1;end=start;depth=1
    while depth:
        if surface[end]=='{':depth+=1
        elif surface[end]=='}':depth-=1
        end+=1
    music+='\n'+surface[begin:end]
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
 int musicIndex,missionRace,musicThemeBoundary;boolean expansion,currentMusicExpansion,muted;float music=1,effects=1;
 int fps=60,resourcePercent=100,commandPercent=100,descriptionPercent=100,touchPercent=100;double speed=42;
 boolean orderLines,nearbyDefenders,networkStats,wide,overCamera,zoomOut,foreground=true;float zoom=1,speechMusicGain=1;
 String modal="sound",page="game";FakeAudio audio;FakePreferences prefs=new FakePreferences();
 java.util.function.Consumer<Float> musicSlider,effectsSlider;Runnable muteAction;final List<String> toggles=new ArrayList<>(),sliders=new ArrayList<>();
 String musicPhase="",currentMusicPath="",failure="";final HashMap<String,Integer> musicThemeStarts=new HashMap<>();
 Runnable nextAction;boolean nextEnabled;String nextLabel;float nextX,nextY,nextWidth,nextHeight;
 void toggle(Canvas c,String name,boolean enabled,float x,float y,Runnable action){toggles.add(name);muteAction=action;}
 void slider(Canvas c,String name,float value,float x,float y,java.util.function.Consumer<Float> action){sliders.add(name);if(name.equals("Music"))musicSlider=action;else if(name.equals("Effects"))effectsSlider=action;}
 void menuActionButton(Canvas c,String label,float x,float y,float w,float h,Runnable action,boolean enabled){nextLabel=label;nextX=x;nextY=y;nextWidth=w;nextHeight=h;nextAction=action;nextEnabled=enabled;}
 void renderSettings(){toggles.clear();sliders.clear();drawSoundSettings(new Canvas(),136,32);check(toggles.equals(Arrays.asList("Mute all sound")),"Obsolete music switch remains");check(sliders.equals(Arrays.asList("Effects","Music")),"Volume sliders missing");}
 boolean nextButton(){renderSettings();check("Next track".equals(nextLabel),"Wrong settings button");check(nextX==162&&nextY==272&&nextWidth==320&&nextHeight==28,"Button geometry changed");if(nextEnabled)nextAction.run();return nextEnabled;}
 void volume(float value){renderSettings();musicSlider.accept(value);}
 void mute(){renderSettings();muteAction.run();}
 void load(FakePreferences p){prefs=p;loadAudioSettings();}
 void gain(){syncAudio();}
 void finish(){NativeBridge.active=false;advanceMusic();}
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
  AudioVolume11Test.run();
  MusicThemesTest.runSynthetic();
  System.out.println("PASS production music selection: all races, original/Brood War loops, source fallback, missing assets, expansion switching and phase isolation; manual picker/preview removed; tested Next track button retained");
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
final class Canvas {}
final class FakeAudio{boolean allowed=true;boolean canPlay(){return allowed;}}
final class FakePreferences {
 final Map<String,Object> values=new HashMap<>();int writes;
 boolean contains(String key){return values.containsKey(key);}
 boolean getBoolean(String key,boolean fallback){Object v=values.get(key);return v instanceof Boolean?(Boolean)v:fallback;}
 float getFloat(String key,float fallback){Object v=values.get(key);return v instanceof Float?(Float)v:fallback;}
 FakePreferences put(String key,Object value){values.put(key,value);return this;}
 Editor edit(){return new Editor();}
 final class Editor {
  final Map<String,Object> pending=new HashMap<>();final Set<String> removed=new HashSet<>();
  Editor putFloat(String key,float value){pending.put(key,value);return this;}
  Editor putInt(String key,int value){pending.put(key,value);return this;}
  Editor putBoolean(String key,boolean value){pending.put(key,value);return this;}
  Editor remove(String key){removed.add(key);return this;}
  void apply(){for(String key:removed)values.remove(key);values.putAll(pending);writes++;}
 }
}
final class NativeBridge {
 static boolean paused;static float effectsGain,musicGain;static void audio(boolean pause,float effects,float music){paused=pause;effectsGain=effects;musicGain=music;}
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
run(['javac','-cp',jar,'-d',b/'classes',*[src/(name+'.java') for name in production],harness,r/'tests/MusicThemesTest.java',r/'tests/AudioVolume11Test.java'])
run(['java','-Xmx64m','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.Music79Test',
     *([a.data_dir,b] if a.data_dir else [])])
if a.data_dir:
    runtime=(r/'native/runtime.cpp').read_text()
    seek_lines=[]
    for name in ['seekSound','soundPosition']:
        line=re.search(r'^JNI\('+name+r'\)[^\n]+',runtime,re.M);assert line,name
        seek_lines.append(line.group(0))
    (b/'music-seek-jni.h').write_text('#include <jni.h>\n#define JNI(name)\n'+'\n'.join(seek_lines)+'\n#undef JNI\n')
    run(['g++','-std=c++17','-O2','-pthread','-DSTARDROID_NEXT_TRACK_TEST','-I'+str(r/'native-engine'),'-I'+str(b),'-I'+str(java_home/'include'),'-I'+str(java_home/'include/linux'),r/'tests/native_music79.cpp','-o',b/'native-music79'])
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
files = [src/'NativeSurface.java',src/'MusicData.java',src/'MusicThemes.java',src/'MissionBundle.java',src/'NativeData.java',r/'native/audio.h',r/'native/runtime.cpp',Path(__file__),r/'tests/native_music79.cpp',r/'tests/MusicThemesTest.java',r/'tests/AudioVolume11Test.java']
a.report.write_text(json.dumps({
    'passed': True, 'physicalAndroid': False, 'originalArchivesTested': bool(a.data_dir),
    'version':'1.1','androidSdk35JavaCompile':sdk_compile,'gameEntrySourceRoutingChecks':routes,'scope':'All three races: production Java music selection, campaign/custom/Nearby routing audit, original import bytes, full native WAV decode and EOF, embedded-original comparison, production sound-settings button activation, individual-theme skipping, one-time old-toggle preference migration and volume/mute gain controls, exact native JNI seek entry points and sample-accurate PCM output after seeking. No physical Android audio test.',
    'availability':'Four themes per race require imported original Brood War soundtrack files; missing expansion files fall back to the original soundtrack.',
    'checks': [s for s in outputs if s],
    'sourceSha256': {str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
},indent=2)+'\n')

#!/usr/bin/env python3
"""Check actual music selection and optionally private original archive playback.

Usage: python3 tests/run_music79.py [--data-dir /path/to/original/archives]
Requires javac/java and build-native/json-20240303.jar. The optional original
checks also require g++ and the prepared native engine. No Android SDK is needed.
"""
import argparse, hashlib, json, re, subprocess
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
start = surface.index('  private void nextMusicTrack() {')
end = surface.index('\n  private ', start + 1)
next_track = surface[start:end]
outputs = []

def run(args):
    q = subprocess.run(list(map(str, args)), text=True, capture_output=True)
    print(q.stdout + q.stderr, end='')
    q.check_returncode()
    outputs.append(q.stdout.strip())

harness = b/'Music79Test.java'
harness.write_text('''package org.openbw.androidtest;
import java.util.*;import java.io.*;
public final class Music79Test {
 int musicIndex,missionRace,musicThemeBoundary;boolean expansion;String musicPhase="",musicTrack="auto",currentMusicPath="",failure="";
 final HashMap<String,Integer> musicThemeStarts=new HashMap<String,Integer>();
 void saveSettings(){}
 void play(String phase){music(phase);}
 void next(){nextMusicTrack();}
''' + music + next_track + '''
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
  NativeBridge.missingAll=false;h.musicTrack="protoss2";NativeBridge.active=false;h.music("game");
  check(h.currentMusicPath.equals("music/protoss2.wav")&&!NativeBridge.loop,"Manual battle track failed");
  h.music("briefing");check(h.currentMusicPath.equals("music/trdyroom.wav")&&NativeBridge.loop,"Manual track replaced briefing");
  h.music("victory");check(h.currentMusicPath.equals("music/tvict.wav")&&!NativeBridge.loop,"Manual track replaced victory");
  h.music("defeat");check(h.currentMusicPath.equals("music/tdefeat.wav")&&!NativeBridge.loop,"Manual track replaced defeat");
  MusicThemesTest.runSynthetic();
  System.out.println("PASS production music selection: all races, original/Brood War loops, source fallback, missing assets, manual track and phase isolation");
  if(args.length==2){
   File data=new File(args[0]),out=new File(args[1]);
   for(String name:new String[]{"StarCraft","BroodWar"}){
    File source=new File(data,name+".mpq"),temp=new File(out,name+".tmp"),bundle=new File(out,name+".zip");
    try(FileInputStream in=new FileInputStream(source);FileOutputStream stream=new FileOutputStream(temp)){
     MissionBundle.Result result=MissionBundle.exportMusic(in.getChannel(),MusicData.names(),stream,s->{});
     for(String race:new String[]{"terran","zerg","protoss"})check(!result.missing.contains("music\\\\"+race+"1.wav"),"Original race theme missing");
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
files = [src/'NativeSurface.java',src/'MusicData.java',src/'MusicThemes.java',src/'MissionBundle.java',src/'NativeData.java',r/'native/audio.h',Path(__file__),r/'tests/native_music79.cpp',r/'tests/MusicThemesTest.java']
a.report.write_text(json.dumps({
    'passed': True, 'physicalAndroid': False, 'originalArchivesTested': bool(a.data_dir),
    'checks': [s for s in outputs if s],
    'sourceSha256': {str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
},indent=2)+'\n')

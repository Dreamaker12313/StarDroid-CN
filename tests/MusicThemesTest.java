package org.openbw.androidtest;

import java.nio.file.*;
import java.util.*;

/** Exercises production Next Track with synthetic variants and private original music. */
public final class MusicThemesTest {
  static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
  static void put(byte[] b,int p,int value,int n) { for(int i=0;i<n;i++) b[p+i]=(byte)(value>>(8*i)); }
  static byte[] wave(int rate,int frames,int seed) {
    byte[] b=new byte[44+frames*2];
    for(int i=0;i<4;i++) { b[i]=(byte)"RIFF".charAt(i);b[8+i]=(byte)"WAVE".charAt(i);
      b[12+i]=(byte)"fmt ".charAt(i);b[36+i]=(byte)"data".charAt(i); }
    put(b,4,b.length-8,4);put(b,16,16,4);put(b,20,1,2);put(b,22,1,2);
    put(b,24,rate,4);put(b,28,rate*2,4);put(b,32,2,2);put(b,34,16,2);put(b,40,frames*2,4);
    Random random=new Random(seed); int amplitude=0;
    for(int i=0;i<frames;i++) {if(i%(rate/10)==0)amplitude=100+random.nextInt(20000);put(b,44+i*2,(i%2==0?1:-1)*amplitude,2);}
    return b;
  }
  static byte[] append(byte[] original,int rate,int prefixSeconds) {
    byte[] b=wave(rate,(original.length-44)/2+rate*prefixSeconds,123);
    System.arraycopy(original,44,b,44+rate*prefixSeconds*2,original.length-44);
    return b;
  }
  static Music79Test begin(int race,byte[] combined,byte[] original) {
    NativeBridge.fixtures.clear();NativeBridge.missingAll=false;NativeBridge.missingExpansion=false;NativeBridge.failOriginal=false;
    NativeBridge.active=false;NativeBridge.starts=0;NativeBridge.seeks=0;
    String name="music/"+new String[]{"zerg","terran","protoss"}[race]+"1.wav";
    NativeBridge.fixtures.put("6:"+name,combined);NativeBridge.fixtures.put("5:"+name,original);
    Music79Test h=new Music79Test();h.expansion=true;h.missionRace=race;h.play("game");return h;
  }
  static void cycle(int race,byte[] combined,byte[] original,int boundary) {
    Music79Test h=begin(race,combined,original);
    String prefix="music/"+new String[]{"zerg","terran","protoss"}[race];
    check(h.musicThemeBoundary==boundary,"Unverified/wrong boundary");
    check(NativeBridge.position==0&&NativeBridge.starts==1,"Natural playback must start the complete combined file");
    h.next();check(h.musicIndex==0&&NativeBridge.position==boundary&&NativeBridge.starts==1,"Next skipped embedded original theme");
    h.next();check(h.currentMusicPath.equals(prefix+"2.wav")&&NativeBridge.position==0,"Next failed second file");
    h.next();check(h.currentMusicPath.equals(prefix+"3.wav"),"Next failed third file");
    h.next();check(h.currentMusicPath.equals(prefix+"1.wav")&&NativeBridge.position==0,"Four-theme loop did not restart");
    check(NativeBridge.starts==4&&NativeBridge.seeks==1,"Four stops must use three files and one seek");
    NativeBridge.position=boundary+1000;h.next();
    check(h.currentMusicPath.equals(prefix+"2.wav"),"Next replayed already-playing original theme");
    h=begin(race,combined,original);NativeBridge.position=boundary+30000;
    NativeBridge.active=false;h.musicIndex++;h.play("game");
    check(h.currentMusicPath.equals(prefix+"2.wav")&&NativeBridge.seeks==0,"Natural loop duplicated original theme");
    h=begin(race,combined,original);h.musicTrack="terran1";h.next();
    check(h.musicIndex==1&&h.musicTrack.equals("auto")&&NativeBridge.seeks==0,"Manual selection no longer returns to automatic race loop");
  }
  static void runSynthetic() {
    int rate=4000;byte[] original=wave(rate,60*rate,42),combined=append(original,rate,37);
    check(MusicThemes.appendedThemeMs(combined,original)==37000,"Different length variant failed");
    for(int race=0;race<3;race++)cycle(race,combined,original,37000);
    check(MusicThemes.appendedThemeMs(wave(rate,97*rate,91),original)==0,"Same durations but unrelated music falsely matched");
    byte[] silence=original.clone();Arrays.fill(silence,44,silence.length,(byte)0);
    check(MusicThemes.appendedThemeMs(append(silence,rate,37),silence)==0,"Silence falsely matched");
    check(MusicThemes.appendedThemeMs(combined,null)==0,"Missing original accepted");
    check(MusicThemes.appendedThemeMs(original,combined)==0,"Short expansion accepted");
    byte[] bad=combined.clone();put(bad,20,17,2);
    check(MusicThemes.appendedThemeMs(bad,original)==0,"Unsupported WAV codec accepted");
    for(int length:new int[]{0,12,44,2000})check(MusicThemes.appendedThemeMs(Arrays.copyOf(combined,length),original)==0,"Truncated WAV accepted");
    for(byte[] variant:new byte[][]{null,wave(rate,97*rate,91),bad}) {
      Music79Test h=begin(1,variant,original);h.next();
      check(h.currentMusicPath.equals("music/terran2.wav")&&NativeBridge.seeks==0,"Unknown variant must retain safe full-file loop");
    }
    Music79Test h=begin(1,combined,original);NativeBridge.failOriginal=true;
    h.musicThemeStarts.clear();NativeBridge.active=false;h.play("game");
    check(NativeBridge.active&&h.musicThemeBoundary==0&&h.failure.isEmpty(),"Damaged optional original archive blocked valid expansion music");
    NativeBridge.failOriginal=false;
    NativeBridge.fixtures.clear();NativeBridge.active=false;
    System.out.println("PASS Next Track: four theme stops for every race; natural playback/manual selection preserved; unknown, missing, silent, malformed and unsupported variants never guessed");
  }
  public static void main(String[] args)throws Exception {
    if(args.length!=1)throw new IllegalArgumentException("Expected extracted private music directory");
    for(int race=0;race<3;race++) {
      String name=new String[]{"zerg","terran","protoss"}[race];
      byte[] combined=Files.readAllBytes(Paths.get(args[0],name+"-bw.wav")),original=Files.readAllBytes(Paths.get(args[0],name+"-sc.wav"));
      int boundary=MusicThemes.appendedThemeMs(combined,original);
      check(boundary>0,"Actual "+name+" original theme was not detected");
      cycle(race,combined,original,boundary);
      System.out.println("PASS actual "+name+" four Next Track stops; verified embedded theme starts at "+boundary+" ms");
      NativeBridge.fixtures.clear();
    }
  }
}

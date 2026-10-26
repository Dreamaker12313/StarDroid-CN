package org.openbw.androidtest;

import java.nio.file.*;
import java.util.*;

/** Audits all four themes using automatic playback and private original music. */
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
    check(MusicThemes.appendedThemeMs(combined,original)==boundary,"Unverified/wrong original theme boundary");
    check(NativeBridge.position==0&&NativeBridge.starts==1,"Natural playback must start the complete combined file");
    NativeBridge.position=boundary+30000;h.play("game");
    check(NativeBridge.starts==1&&NativeBridge.position==boundary+30000,"Original embedded theme restarted or skipped");
    h.finish();
    check(h.currentMusicPath.equals(prefix+"2.wav")&&NativeBridge.position==0,"Natural loop failed second file");
    h.finish();
    check(h.currentMusicPath.equals(prefix+"3.wav"),"Natural loop failed third file");
    h.finish();
    check(h.currentMusicPath.equals(prefix+"1.wav")&&NativeBridge.position==0,"Four-theme loop did not restart");
    check(NativeBridge.starts==4&&NativeBridge.seeks==0,"Automatic loop must retain three complete files without seeking");
  }
  static void nextCycle(int race,byte[] combined,byte[] original,int boundary) {
    Music79Test h=begin(race,combined,original);
    String prefix="music/"+new String[]{"zerg","terran","protoss"}[race];
    check(h.musicThemeBoundary==boundary,"Playback failed to retain the verified boundary");
    check(h.nextButton()&&NativeBridge.position==boundary&&NativeBridge.starts==1&&NativeBridge.seeks==1,
        "Next track button did not seek to the embedded original theme");
    check(h.nextButton()&&h.currentMusicPath.equals(prefix+"2.wav")&&NativeBridge.position==0,"Second press failed race2");
    check(h.nextButton()&&h.currentMusicPath.equals(prefix+"3.wav"),"Third press failed race3");
    check(h.nextButton()&&h.currentMusicPath.equals(prefix+"1.wav")&&NativeBridge.position==0,"Fourth press failed BW theme");
    check(h.nextButton()&&NativeBridge.position==boundary&&NativeBridge.seeks==2,"Rapid cycle failed embedded theme");
    h.finish();check(h.currentMusicPath.equals(prefix+"2.wav"),"Natural EOF after manual seek repeated/skipped race2");
    h.finish();check(h.currentMusicPath.equals(prefix+"3.wav"),"Natural EOF after manual seek skipped race3");
    h.finish();check(h.currentMusicPath.equals(prefix+"1.wav")&&NativeBridge.position==0,"Natural EOF failed to restore full loop");
    NativeBridge.position=boundary+1;
    check(h.nextButton()&&h.currentMusicPath.equals(prefix+"2.wav"),"Already-playing original theme was repeated");
    int starts=NativeBridge.starts,seeks=NativeBridge.seeks;
    h.muted=true;check(!h.nextButton(),"Muted Next track was enabled");h.nextAction.run();
    h.muted=false;h.music=0;check(!h.nextButton(),"Zero volume Next track was enabled");h.nextAction.run();
    check(NativeBridge.starts==starts&&NativeBridge.seeks==seeks,"Disabled settings button changed playback");
    h.music=1;
    for(String phase:new String[]{"title","briefing","victory","defeat"}) {
      h.play(phase);String path=h.currentMusicPath;starts=NativeBridge.starts;seeks=NativeBridge.seeks;
      check(!h.nextButton(),"Non-game phase allowed Next track");h.nextAction.run();
      check(h.musicPhase.equals(phase)&&h.currentMusicPath.equals(path)&&NativeBridge.starts==starts&&NativeBridge.seeks==seeks,
          "Next track replaced a menu/briefing/result track");
    }
    h.play("game");NativeBridge.active=false;
    check(!h.nextButton(),"Unavailable playback Next track was enabled");h.nextAction.run();
    h.finish();check(h.currentMusicPath.equals(prefix+"2.wav"),"EOF did not recover disabled Next track");
    System.out.println("PASS race "+race+" actual settings button: four-theme order, rapid presses, embedded seeking, automatic EOF, mute/disabled/zero-volume and phase guards");
  }
  static void runSynthetic() {
    int rate=4000;byte[] original=wave(rate,60*rate,42),combined=append(original,rate,37);
    check(MusicThemes.appendedThemeMs(combined,original)==37000,"Different length variant failed");
    for(int race=0;race<3;race++){cycle(race,combined,original,37000);nextCycle(race,combined,original,37000);}
    check(MusicThemes.appendedThemeMs(wave(rate,97*rate,91),original)==0,"Same durations but unrelated music falsely matched");
    byte[] silence=original.clone();Arrays.fill(silence,44,silence.length,(byte)0);
    check(MusicThemes.appendedThemeMs(append(silence,rate,37),silence)==0,"Silence falsely matched");
    check(MusicThemes.appendedThemeMs(combined,null)==0,"Missing original accepted");
    check(MusicThemes.appendedThemeMs(original,combined)==0,"Short expansion accepted");
    byte[] bad=combined.clone();put(bad,20,17,2);
    check(MusicThemes.appendedThemeMs(bad,original)==0,"Unsupported WAV codec accepted");
    for(int length:new int[]{0,12,44,2000})check(MusicThemes.appendedThemeMs(Arrays.copyOf(combined,length),original)==0,"Truncated WAV accepted");
    // The optional original archive must not be read to play valid BW music.
    Music79Test h=begin(1,combined,original);NativeBridge.failOriginal=true;
    NativeBridge.active=false;h.play("game");
    check(NativeBridge.active&&h.failure.isEmpty(),"Damaged optional original archive blocked valid expansion music");
    h.musicThemeStarts.clear();NativeBridge.active=false;h.play("game");
    check(h.musicThemeBoundary==0&&NativeBridge.active&&h.failure.isEmpty(),"Failed optional reference blocked music");
    check(h.nextButton()&&h.currentMusicPath.equals("music/terran2.wav"),"Missing reference broke Next track");
    NativeBridge.failOriginal=false;NativeBridge.missingExpansion=true;NativeBridge.active=false;h.musicIndex=0;h.play("game");
    check(h.musicThemeBoundary==0,"Expansion fallback used stale embedded boundary");
    int seeks=NativeBridge.seeks;check(h.nextButton()&&h.currentMusicPath.equals("music/terran2.wav")&&NativeBridge.seeks==seeks,"Original fallback must skip whole files");
    NativeBridge.missingExpansion=false;h.expansion=false;h.musicIndex=0;NativeBridge.active=false;h.play("game");
    check(h.musicThemeBoundary==0&&h.nextButton()&&h.currentMusicPath.equals("music/terran2.wav"),"StarCraft skip used BW boundary");
    h=begin(1,wave(rate,97*rate,91),original);check(h.musicThemeBoundary==0,"Unrelated variant gained a guessed boundary");
    check(h.nextButton()&&h.currentMusicPath.equals("music/terran2.wav"),"Unknown variant could not skip safely");
    NativeBridge.fixtures.clear();NativeBridge.active=false;
    System.out.println("PASS all races retain both themes in the combined file, then tracks2/3, then repeat; no seeks/skips; detection rejects unknown/silent/malformed variants");
  }
  public static void main(String[] args)throws Exception {
    if(args.length!=1)throw new IllegalArgumentException("Expected extracted private music directory");
    for(int race=0;race<3;race++) {
      String name=new String[]{"zerg","terran","protoss"}[race];
      byte[] combined=Files.readAllBytes(Paths.get(args[0],name+"-bw.wav")),original=Files.readAllBytes(Paths.get(args[0],name+"-sc.wav"));
      int boundary=MusicThemes.appendedThemeMs(combined,original);
      check(boundary>0,"Actual "+name+" original theme was not detected");
      cycle(race,combined,original,boundary);
      nextCycle(race,combined,original,boundary);
      System.out.println("PASS actual "+name+" four-theme automatic and Next track loops; verified original first theme starts at "+boundary+" ms");
      NativeBridge.fixtures.clear();
    }
  }
}

package org.openbw.androidtest;

/** Runs the production preference migration, sliders, mute and mixer-gain calls. */
final class AudioVolume11Test {
  static int checks;
  static void check(boolean value,String why){checks++;if(!value)throw new AssertionError(why);}
  static void near(float actual,float expected,String why){check(Math.abs(actual-expected)<.00001f,why);}

  static void run() {
    Music79Test fresh=new Music79Test();FakePreferences empty=new FakePreferences();fresh.load(empty);
    near(fresh.music,.65f,"Fresh music default changed");near(fresh.effects,1,"Fresh effects default changed");
    check(!fresh.muted&&empty.writes==0,"Fresh preferences were unnecessarily migrated");

    for(boolean oldEnabled:new boolean[]{false,true})for(boolean muted:new boolean[]{false,true}) {
      FakePreferences p=new FakePreferences().put("music-enabled",oldEnabled).put("music",.75f)
          .put("effects",.42f).put("muted",muted);
      Music79Test h=new Music79Test();h.load(p);
      float expected=oldEnabled?.75f:0;
      near(h.music,expected,"Migration changed the old audible state");near(h.effects,.42f,"Migration changed effects");
      check(h.muted==muted&&!p.contains("music-enabled")&&p.writes==1,"Old toggle was not removed in one transaction");
      near(p.getFloat("music",-1),expected,"Migrated volume was not persisted");
      Music79Test restarted=new Music79Test();restarted.load(p);
      near(restarted.music,expected,"Restart lost migrated volume");check(p.writes==1,"Migration repeated on restart");
      restarted.gain();near(NativeBridge.musicGain,muted?0:expected,"Migrated settings unexpectedly unmuted music");
      restarted.volume(.8f); // Actual sound-menu slider callback -> saveSettings -> syncAudio.
      near(NativeBridge.musicGain,muted?0:.8f,"Raising slider was overridden by removed toggle");
      near(p.getFloat("music",-1),.8f,"Slider value was not saved");check(!p.contains("music-enabled"),"Saving recreated old toggle");
      Music79Test secondRestart=new Music79Test();secondRestart.load(p);secondRestart.gain();
      near(secondRestart.music,.8f,"Restart reapplied old disabled state");
      near(NativeBridge.musicGain,muted?0:.8f,"Restart changed mute state");
      check(secondRestart.muted==muted,"Migration silently toggled Mute all sound");
    }
    for(boolean oldEnabled:new boolean[]{false,true}) {
      FakePreferences p=new FakePreferences().put("music-enabled",oldEnabled);
      Music79Test h=new Music79Test();h.load(p);near(h.music,oldEnabled?.65f:0,"Missing old volume migrated incorrectly");
    }
    FakePreferences zero=new FakePreferences().put("music-enabled",true).put("music",0f);
    Music79Test h=new Music79Test();h.load(zero);near(h.music,0,"Explicit old zero volume was overwritten");
    h.expansion=false;h.missionRace=1;h.effects=.4f;
    NativeBridge.missingAll=false;NativeBridge.missingExpansion=false;NativeBridge.failOriginal=false;NativeBridge.active=false;
    for(String phase:new String[]{"title","briefing","game","victory","defeat"}) {
      h.play(phase);h.volume(0);near(NativeBridge.musicGain,0,"Zero volume failed in "+phase);
      near(NativeBridge.effectsGain,.4f,"Zero music volume silenced effects in "+phase);
      h.volume(.6f);near(NativeBridge.musicGain,.6f,"Raising volume failed in "+phase);
      h.mute();near(NativeBridge.musicGain,0,"Mute did not mute music in "+phase);
      near(NativeBridge.effectsGain,0,"Mute did not mute effects in "+phase);
      h.mute();near(NativeBridge.musicGain,.6f,"Unmute did not restore music in "+phase);
    }
    h.play("game");h.volume(0);int starts=NativeBridge.starts,index=h.musicIndex;
    h.finish();check(NativeBridge.starts==starts&&h.musicIndex==index,"Zero volume loaded another silent track at EOF");
    check(!h.nextButton(),"Zero volume left Next track enabled");
    h.volume(.5f);h.finish();check(NativeBridge.starts==starts+1&&h.musicIndex==index+1,"Raising volume failed to resume after EOF");
    check(h.nextButton(),"Raising volume did not enable Next track");
    h.speechMusicGain=.35f;h.gain();near(NativeBridge.musicGain,.175f,"Dialogue ducking was lost");
    h.foreground=false;h.gain();check(NativeBridge.paused,"Background music did not pause");
    h.foreground=true;h.audio=new FakeAudio();h.audio.allowed=false;h.gain();check(NativeBridge.paused,"Audio-focus pause was lost");
    h.audio.allowed=true;h.modal="gamepad-controls";h.page="briefing";h.gain();check(NativeBridge.paused,"Gamepad settings pause was lost");
    h.page="game";h.gain();check(!NativeBridge.paused,"In-game music remained paused");
    System.out.println("PASS "+checks+" production audio preference/slider checks: one-time old off/on migration, persisted volume, restarts, no hidden toggle, mute/effects, all music phases, EOF recovery and focus/ducking");
  }
}

package org.openbw.androidtest;
import java.io.*;
import java.nio.charset.StandardCharsets;
import org.json.*;
public final class Presentation78Test {
 static int checks;
 static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static void le(ByteArrayOutputStream o,int n,int count){for(int i=0;i<count;i++)o.write(n>>(i*8));}
 static byte[] map()throws Exception {
  byte[][] strings={"First speech".getBytes("windows-1252"),"Second speech".getBytes("windows-1252")};
  ByteArrayOutputStream table=new ByteArrayOutputStream();le(table,2,2);int at=6;
  for(byte[] s:strings){le(table,at,2);at+=s.length+1;}for(byte[]s:strings){table.write(s);table.write(0);}
  ByteArrayOutputStream chk=new ByteArrayOutputStream();chk.write("STR ".getBytes(StandardCharsets.US_ASCII));le(chk,table.size(),4);chk.write(table.toByteArray());return chk.toByteArray();
 }
 public static void main(String[] a)throws Exception {
  NativeCampaign campaign=new NativeCampaign(map(),0);campaign.enterMission();
  NativeBridge.events="7\t1\t10\t2000\t0\n";campaign.poll();
  check(NativeBridge.voice==10&&NativeBridge.starts==1,"First dialogue did not start");
  NativeBridge.events="8\t0\t99\t0\t0\n7\t2\t11\t2000\t1\n";campaign.poll();
  check(NativeBridge.voice==10&&NativeBridge.starts==1&&NativeBridge.effects==1,"Effect or next transmission interrupted first line");
  check(campaign.pendingSpeech.size()==1,"Next transmission not queued");
  NativeBridge.frame=100000;campaign.poll();check(campaign.message.contains("First speech"),"Fast simulation hid active speech subtitle");
  JSONObject saved=campaign.save();NativeCampaign restored=new NativeCampaign(map(),0);restored.restore(saved);
  check(restored.pendingSpeech.size()==1&&NativeBridge.voice==10&&NativeBridge.position==350,"Save lost queued or playing transmission");
  NativeBridge.active=false;restored.poll();check(NativeBridge.voice==11&&restored.pendingSpeech.isEmpty(),"Queued dialogue not started after completion");
  restored.enterMission();check(!NativeBridge.active&&restored.pendingSpeech.isEmpty(),"Leaving briefing retained speech");
  // Legacy saves did not contain the queue or active subtitle id.
  saved.remove("pendingSpeech");saved.remove("voiceText");restored.restore(saved);check(restored.pendingSpeech.isEmpty(),"Legacy save not accepted");
  restored.enterMission();
  NativeCampaign.Action first=new NativeCampaign.Action();first.type=2;first.sound=20;
  NativeCampaign.Action second=new NativeCampaign.Action();second.type=8;second.sound=21;second.text=2;second.duration=1;
  restored.actions.add(first);restored.actions.add(second);restored.replay();restored.tick(1);
  check(NativeBridge.voice==20,"Briefing WAV immediately overwritten by transmission");
  restored.tick(99999);check(NativeBridge.voice==20,"Unfinished briefing WAV was cut off");
  NativeBridge.active=false;restored.tick(1);check(NativeBridge.voice==21,"Briefing did not continue after WAV");
  check(restored.transmissionDuration>=8000,"Briefing timer truncates actual audio duration");
  FakePrefs prefs=new FakePrefs();prefs.value="{\"version\":2,\"preset\":\"Custom\",\"holdMs\":350}";
  ControlSettings controls=new ControlSettings();controls.load(prefs);
  check(controls.originalLarvae&&!controls.singleLarvaMorph&&controls.holdMs==350,"Existing-user migration lost settings or default-on larvae");
  controls.originalLarvae=false;controls.singleLarvaMorph=true;controls.save(prefs);ControlSettings next=new ControlSettings();next.load(prefs);
  check(!next.originalLarvae&&next.singleLarvaMorph,"Larvae opt-out did not persist");
  for(String preset:new String[]{"Comfortable","Precise","Drag to select"}){next.preset(preset);check(next.originalLarvae&&!next.singleLarvaMorph,"Preset did not use original larvae default");}
  System.out.println("PASS "+checks+" presentation/preferences checks: dialogue/effects separation, queued speech and save restoration, fast-speed subtitle lifetime, briefing audio completion, larvae default/migration/persistence.");
 }
 static final class FakePrefs implements android.content.SharedPreferences {
  String value="{}";public String getString(String key,String fallback){return value;}
  public Editor edit(){return new Editor(){public Editor putString(String key,String text){value=text;return this;}public void apply(){}};}
 }
}

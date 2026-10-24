package org.openbw.androidtest;

import java.util.*;
import org.json.*;

/** The original CHK owns briefing text, portrait assignments, and voice timing. */
final class NativeCampaign {
  static final class Action {
    int type, text, sound, duration, slot, adjustment, unit, modifier;
  }

  final List<Action> actions = new ArrayList<Action>();
  final String[] strings;
  String objectives = "", message = "", next = "";
  int index = 0, talking = -1;
  int[] portraits = {-1, -1, -1, -1};
  double remaining = 0, messageUntil = 0;
  double transmissionPosition, transmissionDuration;
  double textRemaining, messageDuration;
  int messageRevision;
  int spokenLength;
  int missionVoice;
  boolean transmission;
  final ArrayList<String> messages = new ArrayList<String>();
  final ArrayList<Double> messageEnds = new ArrayList<Double>();

  NativeCampaign(byte[] chk, int player) {
    Map<String, byte[]> sections = new HashMap<String, byte[]>();
    for (int p = 0; p + 8 <= chk.length; ) {
      int n = NativeArt.u32(chk, p + 4);
      if (n < 0 || n > chk.length - p - 8)
        throw new IllegalArgumentException("Invalid map section");
      sections.put(new String(chk, p, 4, NativeArt.CP), Arrays.copyOfRange(chk, p + 8, p + 8 + n));
      p += 8 + n;
    }
    String[] table = NativeArt.tbl(sections.get("STR "));
    strings = new String[table.length + 1];
    strings[0] = "";
    System.arraycopy(table, 0, strings, 1, table.length);
    byte[] b = sections.get("MBRF"), forces = sections.get("FORC");
    if (b != null)
      for (int t = 0; t + 2400 <= b.length; t += 2400) {
        boolean any = false;
        for (int j = 0; j < 27; j++) any |= b[t + 2372 + j] != 0;
        int force = forces != null && player < forces.length ? forces[player] & 3 : 0;
        if (any
            && b[t + 2372 + player] == 0
            && b[t + 2372 + 17] == 0
            && b[t + 2372 + 18 + force] == 0) continue;
        for (int p = t + 320; p < t + 2368; p += 32) {
          int type = b[p + 26] & 255;
          if (type == 0) break;
          if ((b[p + 28] & 2) != 0) continue;
          Action a = new Action();
          a.type = type;
          a.text = NativeArt.u32(b, p + 4);
          a.sound = NativeArt.u32(b, p + 8);
          a.duration = NativeArt.u32(b, p + 12);
          a.slot = NativeArt.u32(b, p + 16);
          a.adjustment = NativeArt.u32(b, p + 20);
          a.unit = NativeArt.u16(b, p + 24);
          a.modifier = b[p + 27] & 255;
          actions.add(a);
          if (type == 4) objectives = text(a.text);
        }
      }
  }

  String text(int id) {
    return id > 0 && id < strings.length ? strings[id] : "";
  }

  private void showText(String value, double duration) {
    message = value;
    messageDuration = duration;
    messageRevision++;
  }

  void replay() {
    index = 0;
    remaining = 0;
    talking = -1;
    Arrays.fill(portraits, -1);
    showText("", 0);
    textRemaining = 0;
    transmission = false;
    transmissionPosition = transmissionDuration = 0;
    NativeBridge.sound(null, 62, false);
  }

  void enterMission() {
    // Briefing state must be cleared even when startup Tips pauses poll().
    index = actions.size();
    remaining = textRemaining = messageUntil = 0;
    transmission = false;
    transmissionPosition = transmissionDuration = 0;
    talking = -1;
    Arrays.fill(portraits, -1);
    missionVoice = 0;
    messages.clear();
    messageEnds.clear();
    showText("", 0);
    NativeBridge.sound(null, 62, false);
  }

  void tick(double dt) {
    if (textRemaining > 0) {
      textRemaining -= dt;
      if (textRemaining <= 0) showText("", 0);
    }
    if (transmission) {
      int position = NativeBridge.value(19, 62);
      transmissionPosition = position >= 0 ? position
          : Math.max(spokenLength, transmissionPosition + dt);
      remaining = transmissionDuration - transmissionPosition;
    } else remaining -= dt;
    if (remaining > 0) return;
    if (transmission) {
      NativeBridge.sound(null, 62, false);
      showText("", 0);
    }
    transmission = false;
    talking = -1;
    for (int guard = 0; guard < 256 && index < actions.size(); guard++) {
      Action a = actions.get(index++);
      int slot = Math.max(0, Math.min(3, a.slot));
      switch (a.type) {
        case 1:
          remaining = a.duration;
          return;
        case 2:
          NativeBridge.campaignSound(a.sound);
          break;
        case 3:
          showText(text(a.text), a.duration);
          textRemaining = a.duration;
          break;
        case 4:
          objectives = text(a.text);
          break;
        case 5:
          portraits[slot] = a.unit;
          break;
        case 6:
          portraits[slot] = -1;
          break;
        case 7:
          talking = slot;
          remaining = a.duration;
          return;
        case 8:
          talking = slot;
          textRemaining = 0;
          int duration = a.sound == 0 ? 0 : NativeBridge.campaignSound(a.sound);
          int base = duration > 0 ? duration : a.duration;
          remaining = base;
          if (a.modifier == 7) remaining = a.adjustment;
          else if (a.modifier == 8) remaining += a.adjustment;
          else if (a.modifier == 9) remaining -= a.adjustment;
          // A CHK timer may extend speech, but must never truncate its recording.
          remaining = Math.max(1, Math.max(base, remaining));
          showText(text(a.text), remaining);
          transmission = true;
          spokenLength = duration;
          transmissionDuration = remaining;
          transmissionPosition = 0;
          return;
      }
    }
  }

  JSONObject save() throws JSONException {
    JSONObject j=new JSONObject();j.put("objectives",objectives);j.put("message",message);j.put("next",next);
    j.put("talking",talking);j.put("messageUntil",messageUntil);j.put("portraits",new JSONArray(portraits));
    j.put("messages",new JSONArray(messages));j.put("messageEnds",new JSONArray(messageEnds));
    j.put("voice",missionVoice);j.put("voicePosition",NativeBridge.value(19,62));return j;
  }
  void restore(JSONObject j) throws JSONException {
    enterMission();objectives=j.getString("objectives");message=j.getString("message");next=j.getString("next");
    talking=j.getInt("talking");messageUntil=j.getDouble("messageUntil");
    JSONArray portraitsJson=j.getJSONArray("portraits"),lines=j.getJSONArray("messages"),ends=j.getJSONArray("messageEnds");
    if(portraitsJson.length()!=4||lines.length()>8||lines.length()!=ends.length())throw new JSONException("Invalid saved dialogue");
    for(int i=0;i<4;i++)portraits[i]=portraitsJson.getInt(i);
    for(int i=0;i<lines.length();i++){messages.add(lines.getString(i));messageEnds.add(ends.getDouble(i));}
    missionVoice=j.optInt("voice");int position=j.optInt("voicePosition",-1);
    if(missionVoice>0&&position>=0){NativeBridge.campaignSound(missionVoice);NativeBridge.seekSound(62,position);}
  }

  void poll() {
    int frame = NativeBridge.value(8, 0);
    for (String row : NativeBridge.text(5).split("\n")) {
      String[] a = row.split("\t");
      if (a.length < 5) continue;
      int type = Integer.parseInt(a[0]),
          id = Integer.parseInt(a[1]),
          wav = Integer.parseInt(a[2]),
          duration = Integer.parseInt(a[3]),
          unit = Integer.parseInt(a[4]);
      if (type == 41) next = NativeArt.normal(text(id));
      if (type == 7 || type == 8) {missionVoice = wav; NativeBridge.campaignSound(wav);}
      if (type == 7) {
        portraits[0] = unit;
        talking = 0;
      }
      if (type == 7 || type == 9) {
        String value = text(id);
        if (!value.isEmpty()) {
          messages.add(value);
          messageEnds.add(frame + Math.max(duration, 6500) / 42.);
          if (messages.size() > 8) {messages.remove(0); messageEnds.remove(0);}
        }
        if (type == 7) messageUntil = frame + Math.max(duration, 3000) / 42.;
      }
    }
    for (int i = messages.size() - 1; i >= 0; i--) if (frame > messageEnds.get(i)) {
      messages.remove(i); messageEnds.remove(i);
    }
    message = String.join("\n", messages);
    if (frame > messageUntil) {
      talking = -1;
    }
    String[] status = NativeBridge.text(6).split("\t");
    if (status.length > 0) {
      int i = Integer.parseInt(status[0]);
      if (i > 0) objectives = text(i);
    }
  }
}

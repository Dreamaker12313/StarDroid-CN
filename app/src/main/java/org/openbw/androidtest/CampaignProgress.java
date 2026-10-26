package org.openbw.androidtest;

import java.util.*;
import org.json.*;

/** Completed missions belong to a registered Player ID, never to the device. */
final class CampaignProgress {
  static final String KEY = "campaign-progress-v1";
  private final LinkedHashMap<String, Entry> players = new LinkedHashMap<String, Entry>();
  private final HashSet<String> retiredNames = new HashSet<String>();

  private static final class Entry {
    final String id;
    final LinkedHashSet<String> completed = new LinkedHashSet<String>();
    Entry(String value) { id = value; }
  }

  CampaignProgress(String json, List<String> registered) {
    try {
      JSONObject saved = new JSONObject(json);
      if (saved.optInt("version") == 1) {
        JSONArray list = saved.optJSONArray("players");
        HashSet<String> ids = new HashSet<String>();
        if (list != null) for (int i=0; i<Math.min(32,list.length()); i++) {
          JSONObject player = list.optJSONObject(i);
          if (player == null) continue;
          String name=player.optString("name"), id=player.optString("id");
          if (name.isEmpty() || !id.matches("[0-9a-f-]{36}") || !ids.add(id)) continue;
          Entry entry = new Entry(id);
          JSONArray complete=player.optJSONArray("completed");
          if (complete!=null) for (int n=0; n<complete.length(); n++) {
            String mission=complete.optString(n);
            if (CampaignCatalog.supported(mission)) entry.completed.add(mission);
          }
          players.put(name,entry);
        }
        JSONArray retired=saved.optJSONArray("retiredNames");
        if (retired!=null) for (int i=0;i<retired.length();i++) retiredNames.add(retired.optString(i));
      }
    } catch (Exception ignored) {
      // Old builds did not record completion. Never infer wins from unlocked maps.
    }
    synchronize(registered);
  }

  void synchronize(List<String> registered) {
    Iterator<Map.Entry<String,Entry>> iterator=players.entrySet().iterator();
    while(iterator.hasNext()) {
      Map.Entry<String,Entry> item=iterator.next();
      if(!registered.contains(item.getKey())) {
        retiredNames.add(item.getKey().toLowerCase(Locale.ROOT));
        iterator.remove();
      }
    }
    for(String name:registered) if(!name.isEmpty()&&!players.containsKey(name))
      players.put(name,new Entry(UUID.randomUUID().toString()));
  }

  String playerId(String name) {
    Entry entry=players.get(name);
    return entry==null?"":entry.id;
  }

  String playerName(String id) {
    for(Map.Entry<String,Entry> item:players.entrySet()) if(item.getValue().id.equals(id))return item.getKey();
    return "";
  }

  private Entry find(String id) {
    for(Entry entry:players.values()) if(entry.id.equals(id))return entry;
    return null;
  }

  /** New saves carry an immutable owner. Legacy saves carry only the old name. */
  String savedOwner(JSONObject save) {
    if(save.has("campaignProfile")) {
      String id=save.optString("campaignProfile");
      return find(id)==null?"":id;
    }
    String name=save.optString("profile");
    if(retiredNames.contains(name.toLowerCase(Locale.ROOT)))return "";
    for(String registered:players.keySet()) if(registered.equalsIgnoreCase(name))return playerId(registered);
    return "";
  }

  boolean completed(String name,String mission) {
    Entry entry=players.get(name);
    return entry!=null && entry.completed.contains(mission);
  }

  boolean record(String id,String mission,int outcome,boolean campaign,boolean replay,boolean multiplayer) {
    if(outcome!=1 || !campaign || replay || multiplayer || !CampaignCatalog.supported(mission))return false;
    Entry entry=find(id);
    return entry!=null && entry.completed.add(mission);
  }

  String serialize() {
    try {
      JSONArray list=new JSONArray();
      for(Map.Entry<String,Entry> item:players.entrySet()) {
        Entry entry=item.getValue();
        list.put(new JSONObject().put("name",item.getKey()).put("id",entry.id)
            .put("completed",new JSONArray(entry.completed)));
      }
      return new JSONObject().put("version",1).put("players",list)
          .put("retiredNames",new JSONArray(retiredNames)).toString();
    } catch(JSONException impossible) {throw new IllegalStateException(impossible);}
  }
}

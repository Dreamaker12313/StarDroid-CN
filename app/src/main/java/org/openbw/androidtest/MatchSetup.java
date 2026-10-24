package org.openbw.androidtest;

import java.io.IOException;
import java.util.Arrays;
import org.json.*;

/** Shared, validated setup for custom games and all network players. */
final class MatchSetup {
  static final String[] RACES={"Zerg","Terran","Protoss"};
  static final String[] SPEEDS={"Slowest","Slower","Slow","Normal","Fast","Faster","Fastest"};
  static final int[] FRAME_MS={167,111,83,67,56,48,42};
  final int[] controllers=new int[8],races=new int[8],teams=new int[8]; // closed, human, computer
  int speed=6,difficulty=2,starts=4;
  boolean freeForAll,teamGame,heroMode;
  MatchSetup(boolean multiplayer) {
    Arrays.fill(teams,2);teams[0]=1;Arrays.fill(races,1);controllers[0]=1;controllers[1]=multiplayer?1:2;
  }
  int frameMs(){return FRAME_MS[speed];}
  String mode(){return teamGame?"Teams":freeForAll?"Free for All":"Melee";}
  void cycleMode(){if(teamGame){teamGame=false;freeForAll=false;}else if(freeForAll){freeForAll=false;teamGame=true;}else freeForAll=true;}
  boolean hasOpponents(){int side=-1;for(int i=0;i<starts;i++)if(controllers[i]!=0){if(side<0)side=teams[i];else if(!teamGame||teams[i]!=side)return true;}return false;}
  void limit(int n){starts=Math.max(1,Math.min(8,n));for(int i=starts;i<8;i++)controllers[i]=0;}
  JSONObject json() throws JSONException {
    JSONObject j=new JSONObject();j.put("races",new JSONArray(races));j.put("controllers",new JSONArray(controllers));
    j.put("speed",speed);j.put("difficulty",difficulty);j.put("starts",starts);j.put("ffa",freeForAll);j.put("teams",new JSONArray(teams));j.put("teamGame",teamGame);j.put("heroMode",heroMode);return j;
  }
  static MatchSetup read(JSONObject j,boolean multiplayer) throws Exception {
    MatchSetup s=new MatchSetup(multiplayer);s.speed=j.getInt("speed");s.difficulty=j.getInt("difficulty");s.starts=j.getInt("starts");s.freeForAll=j.getBoolean("ffa");
    if(s.speed<0||s.speed>6||s.difficulty<0||s.difficulty>2||s.starts<(multiplayer?2:1)||s.starts>8)throw new IOException("Invalid game settings");
    s.teamGame=j.optBoolean("teamGame",false);s.heroMode=j.optBoolean("heroMode",false);
    if(s.teamGame&&s.freeForAll)throw new IOException("Choose Teams or Free for All");
    JSONArray team=j.optJSONArray("teams");if(team!=null){if(team.length()!=8)throw new IOException("Invalid teams");for(int i=0;i<8;i++){s.teams[i]=team.getInt(i);if(s.teams[i]<1||s.teams[i]>8)throw new IOException("Invalid team number");}}
    JSONArray r=j.getJSONArray("races"),c=j.getJSONArray("controllers");
    if(r.length()!=8||c.length()!=8)throw new IOException("Invalid player slots");
    for(int i=0;i<8;i++) {
      s.races[i]=r.getInt(i);s.controllers[i]=c.getInt(i);
      if(s.races[i]<0||s.races[i]>2||s.controllers[i]<0||s.controllers[i]>2||i>=s.starts&&s.controllers[i]!=0 ||
        !multiplayer&&(i==0?s.controllers[i]!=1:s.controllers[i]==1))throw new IOException("Invalid player slot");
    }
    boolean human=false;for(int c0:s.controllers)human|=c0==1;
    if(!human)throw new IOException("A game needs a human player");
    return s;
  }
  MatchSetup copy() throws Exception{MatchSetup s=new MatchSetup(false);System.arraycopy(controllers,0,s.controllers,0,8);System.arraycopy(races,0,s.races,0,8);s.speed=speed;s.difficulty=difficulty;s.starts=starts;s.freeForAll=freeForAll;s.teamGame=teamGame;s.heroMode=heroMode;System.arraycopy(teams,0,s.teams,0,8);return s;}
}

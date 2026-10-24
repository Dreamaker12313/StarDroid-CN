package org.openbw.androidtest;

import java.io.*;
import java.util.*;
import org.json.*;

/** All methods run on the existing simulation worker, never a radio callback thread. */
final class NearbyMatch50 {
  interface Engine {
    long[] prepare(byte[] map,int firstRace,int secondRace,int slot,boolean expansion) throws Exception;
    byte[] collect(); long hash(); void apply(byte[] first,byte[] second); void step();
    void started(); void stopped(String reason,boolean surrendered);
  }
  interface Link {void send(byte[] packet);void close();}
  private final Engine engine; private final Link link;
  final boolean host; final int race; final String name;
  String status="Connecting…",peerName="Opponent";
  boolean connected,ready,playing,closed,remotePaused,localPaused;
  private boolean localFinished,remoteFinished;private long finishingDisconnect;
  private boolean hello,configured,prepared,startReceived,turnSent;
  private byte[] map,localTurn;private int mapSize,offset,sentEnd,turn,remaining,pauseSequence,remotePauseSequence=-1;
  private String mapDigest;private int firstRace,secondRace;boolean expansion;
  String mapName="";private long initialHash,assetHash,turnHash,lastSeen=System.nanoTime()/1000000,lastPing;
  private long waitingSince;
  private double accumulator;private final NearbyProtocol50.Turns remote=new NearbyProtocol50.Turns();
  NearbyMatch50(boolean h,int r,String n,Engine e,Link l) {host=h;race=r;name=NearbyProtocol50.name(n);engine=e;link=l;}
  void hostMap(byte[] data,String title,boolean bw) throws Exception {
    if(!host || data==null || data.length<8 || data.length>NearbyProtocol50.MAX_MAP)throw new IOException("This map is too large for nearby play");
    map=data;mapSize=data.length;mapDigest=NearbyProtocol50.digest(data);mapName=NearbyProtocol50.name(title);expansion=bw;
  }
  private void send(int type,int n,long hash,byte[] data) throws Exception {link.send(NearbyProtocol50.pack(type,n,hash,data));}
  private void send(int type,int n,long hash) throws Exception {send(type,n,hash,NearbyProtocol50.EMPTY);}
  void connected() {
    if(closed)return;connected=true;lastSeen=System.nanoTime()/1000000;status="Checking game versions…";
    try {JSONObject j=new JSONObject();j.put("build",NearbyProtocol50.BUILD);j.put("race",race);j.put("name",name);send(NearbyProtocol50.HELLO,0,0,j.toString().getBytes("UTF-8"));}
    catch(Exception e){fail(e.getMessage());}
  }
  private void prepare() throws Exception {
    long[] info=engine.prepare(map,firstRace,secondRace,host?0:1,expansion);
    if(info==null || info.length!=2)throw new IOException("Could not initialize multiplayer");
    assetHash=info[0];initialHash=info[1];prepared=true;
  }
  void receive(byte[] packet) {
    if(closed)return;
    try {
      NearbyProtocol50.Message m=NearbyProtocol50.parse(packet);lastSeen=System.nanoTime()/1000000;
      switch(m.type) {
        case NearbyProtocol50.HELLO: {
          if(hello || !connected)throw new IOException("Unexpected connection handshake");
          JSONObject j=new JSONObject(new String(m.data,"UTF-8"));
          if(j.getInt("build")!=NearbyProtocol50.BUILD)throw new IOException("Install the same OpenBW version on both phones");
          int other=j.getInt("race");if(other<0 || other>2)throw new IOException("Invalid player race");
          peerName=NearbyProtocol50.name(j.getString("name"));hello=true;
          if(host) {
            if(map==null)throw new IOException("Choose a map before hosting");
            firstRace=race;secondRace=other;prepare();
            JSONObject c=new JSONObject();c.put("length",mapSize);c.put("digest",mapDigest);c.put("name",mapName);
            c.put("firstRace",firstRace);c.put("secondRace",secondRace);c.put("expansion",expansion);
            send(NearbyProtocol50.CONFIG,0,0,c.toString().getBytes("UTF-8"));configured=true;status="Sending map…";
          }
          break;
        }
        case NearbyProtocol50.CONFIG: {
          if(host || configured || !hello)throw new IOException("Unexpected map settings");
          JSONObject c=new JSONObject(new String(m.data,"UTF-8"));mapSize=c.getInt("length");
          if(mapSize<8 || mapSize>NearbyProtocol50.MAX_MAP)throw new IOException("Nearby map exceeds 8 MB");
          mapDigest=c.getString("digest");if(!mapDigest.matches("[0-9a-f]{64}"))throw new IOException("Invalid map checksum");
          firstRace=c.getInt("firstRace");secondRace=c.getInt("secondRace");
          if(firstRace<0 || firstRace>2 || secondRace!=race)throw new IOException("Invalid match races");
          expansion=c.getBoolean("expansion");mapName=NearbyProtocol50.name(c.getString("name"));map=new byte[mapSize];offset=0;configured=true;
          status="Receiving map…";send(NearbyProtocol50.ACK,0,0);break;
        }
        case NearbyProtocol50.ACK: {
          if(!host || !configured || prepared && ready || m.number!=sentEnd || m.number<0 || m.number>mapSize)throw new IOException("Unexpected map acknowledgement");
          offset=m.number;
          if(offset<mapSize) {sentEnd=Math.min(mapSize,offset+NearbyProtocol50.MAX_BODY);send(NearbyProtocol50.CHUNK,offset,0,Arrays.copyOfRange(map,offset,sentEnd));}
          status=offset==mapSize?"Checking game data…":"Sending map: "+(offset*100/mapSize)+"%";break;
        }
        case NearbyProtocol50.CHUNK: {
          if(host || !configured || prepared || m.number!=offset || m.data.length==0 || m.data.length>mapSize-offset)throw new IOException("Unexpected map data");
          System.arraycopy(m.data,0,map,offset,m.data.length);offset+=m.data.length;
          status="Receiving map: "+(offset*100/mapSize)+"%";send(NearbyProtocol50.ACK,offset,0);
          if(offset==mapSize) {
            if(!NearbyProtocol50.digest(map).equals(mapDigest))throw new IOException("Map transfer failed its checksum");
            prepare();send(NearbyProtocol50.READY,0,initialHash,longBytes(assetHash));ready=true;status="Ready — waiting for host";
          }
          break;
        }
        case NearbyProtocol50.READY:
          if(!host || !prepared || ready || m.data.length!=8 || m.hash!=initialHash || readLong(m.data)!=assetHash)throw new IOException("Game data differs. Import the same core files on both phones");
          ready=true;status="Both players ready";break;
        case NearbyProtocol50.START:
          if(host || !ready || startReceived || m.hash!=initialHash)throw new IOException("Unexpected match start");
          begin();break;
        case NearbyProtocol50.TURN:
          if(!prepared || !ready)throw new IOException("Turn arrived before the game was ready");
          remote.put(m,turn);break;
        case NearbyProtocol50.PAUSE:
          if(m.number<0 || m.hash<0 || m.hash>1)throw new IOException("Invalid pause state");
          if(m.number>remotePauseSequence){remotePauseSequence=m.number;remotePaused=m.hash==1;}break;
        case NearbyProtocol50.PING:break;
        case NearbyProtocol50.FINISH:
          if(!startReceived)throw new IOException("Match ended before it started");
          remoteFinished=true;break;
        case NearbyProtocol50.LEAVE:stop("Opponent left the match",playing);break;
        case NearbyProtocol50.ERROR:stop("Connection stopped: "+NearbyProtocol50.name(new String(m.data,"UTF-8")),false);break;
        default:throw new IOException("Unknown multiplayer message");
      }
    } catch(Exception e){fail(e.getMessage());}
  }
  static byte[] longBytes(long n) throws IOException {ByteArrayOutputStream b=new ByteArrayOutputStream();new DataOutputStream(b).writeLong(n);return b.toByteArray();}
  static long readLong(byte[] b) throws IOException {return new DataInputStream(new ByteArrayInputStream(b)).readLong();}
  void start() {
    if(!host || !ready || playing || closed)return;
    try {send(NearbyProtocol50.START,0,initialHash);begin();}catch(Exception e){fail(e.getMessage());}
  }
  private void begin() {startReceived=true;playing=true;status="Connected";map=null;engine.started();}
  void pulse(boolean paused) {
    if(!connected || closed)return;
    paused &= !localFinished;
    try {
      long now=System.nanoTime()/1000000;
      if(playing && localPaused!=paused) {localPaused=paused;send(NearbyProtocol50.PAUSE,++pauseSequence,paused?1:0);}
      if(now-lastPing>=2000){lastPing=now;send(NearbyProtocol50.PING,0,0);}
      if(now-lastSeen>60000)fail("Other phone stopped responding");
    }catch(Exception e){fail(e.getMessage());}
  }
  void tick(double milliseconds) {
    if(!playing || closed)return;
    if(finishingDisconnect!=0 && !localFinished && System.nanoTime()/1000000-finishingDisconnect>5000){fail("Connection closed before the final turn arrived");return;}
    if(localPaused || remotePaused){accumulator=0;waitingSince=0;status=remotePaused?"Paused on the other phone":"Paused";return;}
    try {
      if(remaining==0) {
        if(!turnSent) {localTurn=engine.collect();turnHash=engine.hash();send(NearbyProtocol50.TURN,turn,turnHash,localTurn);turnSent=true;}
        if(!remote.has(turn)){
          accumulator=0;long now=System.nanoTime()/1000000;if(waitingSince==0)waitingSince=now;
          status=now-waitingSince>=750?"Waiting for other phone…":"Connected";return;
        }
        waitingSince=0;
        NearbyProtocol50.Message other=remote.take(turn);
        if(other.hash!=turnHash)throw new IOException("Games went out of sync at frame "+(turn*4));
        engine.apply(host?localTurn:other.data,host?other.data:localTurn);remaining=4;status="Connected";
      }
      accumulator=Math.min(168,accumulator+Math.max(0,milliseconds));
      while(remaining>0 && accumulator>=42) {engine.step();remaining--;accumulator-=42;}
      if(remaining==0){turn++;turnSent=false;localTurn=null;}
    }catch(Exception e){fail(e.getMessage());}
  }
  void finish() {
    if(closed || localFinished)return;localFinished=true;
    try{send(NearbyProtocol50.FINISH,0,0);}catch(Exception e){fail(e.getMessage());}
  }
  void disconnected() {
    if(closed)return;
    if(remoteFinished){connected=false;remotePaused=false;finishingDisconnect=System.nanoTime()/1000000;return;}
    stop("Connection lost. The match has stopped",false);
  }
  void leave() {if(closed)return;try{if(connected && !localFinished)send(NearbyProtocol50.LEAVE,0,0);}catch(Exception ignored){}closed=true;playing=false;link.close();}
  void fail(String reason) {
    if(closed)return;String why=reason==null?"Nearby connection failed":reason;
    try{if(connected)send(NearbyProtocol50.ERROR,0,0,NearbyProtocol50.name(why).getBytes("UTF-8"));}catch(Exception ignored){}
    stop(why,false);
  }
  private void stop(String why,boolean surrender) {if(closed)return;closed=true;playing=false;status=why;link.close();engine.stopped(why,surrender);}
}

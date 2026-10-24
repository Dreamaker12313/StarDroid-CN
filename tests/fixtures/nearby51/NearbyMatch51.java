package org.openbw.androidtest;

import java.io.*;
import java.util.*;
import org.json.*;

/** Deterministic one-turn-ahead input; all methods run on the simulation worker. */
final class NearbyMatch51 {
  interface Engine {
    long[] prepare(byte[] map,int firstRace,int secondRace,int slot,boolean expansion) throws Exception;
    byte[] collect(); long hash(); void apply(byte[] first,byte[] second); void step();
    void started(); void stopped(String reason,boolean surrendered);
  }
  interface Link {void send(byte[] packet);void close();}
  interface Clock {long now();}
  interface MapCache {byte[] read(String digest,int size) throws Exception;void write(String digest,byte[] data) throws Exception;}
  private final Engine engine;private final Link link;private final Clock clock;private final MapCache cache;
  final boolean host;final int race;final String name;
  String status="Connecting…",peerName="Opponent",mapName="";
  boolean connected,ready,playing,closed,remotePaused,localPaused,expansion;
  private boolean localFinished,remoteFinished,hello,configured,prepared,startReceived,transferRequested,compressed,mapCached,blocked;
  private long finishingDisconnect=-1,waitingSince=-1;
  private byte[] map,transfer;
  private int mapSize,transferSize,offset,sentEnd,lastAck,turn,remaining,pauseSequence,remotePauseSequence=-1,firstRace,secondRace,pingSequence;
  private String mapDigest;
  private long initialHash,assetHash,lastSeen,lastPing,pingSentAt=-1,mapStartedAt,mapReadyMs;
  private double accumulator;
  private final NearbyProtocol51.Turns remote=new NearbyProtocol51.Turns();
  private final TreeMap<Integer,byte[]> local=new TreeMap<Integer,byte[]>();
  private final TreeMap<Integer,Long> hashes=new TreeMap<Integer,Long>();
  private long sentBytes,receivedBytes,mapSentBytes,framesDone,waitMs,engineNs,lastTick=-1,activeMs;
  private long sampleAt,sampleFrames,sampleWait,sampleEngine,sampleSent,sampleReceived,sampleActive;
  private double pingMs=-1,jitterMs,simulationFps,waitPercent,engineMsPerFrame,txKiB,rxKiB;
  private String summary="Measuring network…";

  NearbyMatch51(boolean h,int r,String n,Engine e,Link l){this(h,r,n,e,l,null,()->System.nanoTime()/1000000);}
  NearbyMatch51(boolean h,int r,String n,Engine e,Link l,MapCache c,Clock t){
    host=h;race=r;name=NearbyProtocol51.name(n);engine=e;link=l;cache=c;clock=t;lastSeen=sampleAt=clock.now();
  }
  void hostMap(byte[] data,String title,boolean bw) throws Exception {
    if(!host || data==null || data.length<8 || data.length>NearbyProtocol51.MAX_MAP)throw new IOException("This map is too large for nearby play");
    map=data;mapSize=data.length;mapDigest=NearbyProtocol51.digest(data);mapName=NearbyProtocol51.name(title);expansion=bw;
  }
  private void send(int type,int n,long hash,byte[] data) throws Exception {
    byte[] packet=NearbyProtocol51.pack(type,n,hash,data);sentBytes+=packet.length;link.send(packet);
  }
  private void send(int type,int n,long hash) throws Exception {send(type,n,hash,NearbyProtocol51.EMPTY);}
  void connected(){
    if(closed)return;connected=true;lastSeen=clock.now();status="Checking game versions…";
    try{JSONObject j=new JSONObject();j.put("build",NearbyProtocol51.BUILD);j.put("race",race);j.put("name",name);send(NearbyProtocol51.HELLO,0,0,j.toString().getBytes("UTF-8"));}
    catch(Exception e){fail(e.getMessage());}
  }
  private void prepare() throws Exception {
    long[] info=engine.prepare(map,firstRace,secondRace,host?0:1,expansion);
    if(info==null || info.length!=2)throw new IOException("Could not initialize multiplayer");
    assetHash=info[0];initialHash=info[1];prepared=true;
    if(cache!=null)try{cache.write(mapDigest,map);}catch(Exception ignored){} // Cache failure must not block a match.
  }
  private void receiveMapReady() throws Exception {
    prepare();mapReadyMs=Math.max(0,clock.now()-mapStartedAt);
    send(NearbyProtocol51.READY,mapCached?1:0,initialHash,longBytes(assetHash));ready=true;
    map=null;transfer=null;status=mapCached?"Map cached — ready for host":"Ready — waiting for host";
  }
  private void fillMapWindow() throws Exception {
    int limit=Math.min(transferSize,offset+NearbyProtocol51.MAP_WINDOW*NearbyProtocol51.MAX_BODY);
    while(sentEnd<limit){
      int end=Math.min(transferSize,sentEnd+NearbyProtocol51.MAX_BODY);
      send(NearbyProtocol51.CHUNK,sentEnd,0,Arrays.copyOfRange(transfer,sentEnd,end));mapSentBytes+=end-sentEnd;sentEnd=end;
    }
  }
  void receive(byte[] packet){
    if(closed)return;
    try{
      NearbyProtocol51.Message m=NearbyProtocol51.parse(packet);lastSeen=clock.now();receivedBytes+=packet.length;
      switch(m.type){
        case NearbyProtocol51.HELLO:{
          if(hello || !connected)throw new IOException("Unexpected connection handshake");
          JSONObject j=new JSONObject(new String(m.data,"UTF-8"));
          if(j.getInt("build")!=NearbyProtocol51.BUILD)throw new IOException("Install the same OpenBW version on both phones");
          int other=j.getInt("race");if(other<0 || other>2)throw new IOException("Invalid player race");
          peerName=NearbyProtocol51.name(j.getString("name"));hello=true;
          if(host){
            if(map==null)throw new IOException("Choose a map before hosting");
            firstRace=race;secondRace=other;prepare();transfer=NearbyMapCodec.encode(map);compressed=transfer!=map;transferSize=transfer.length;
            JSONObject c=new JSONObject();c.put("length",mapSize);c.put("wireLength",transferSize);c.put("encoding",compressed?"deflate":"raw");
            c.put("digest",mapDigest);c.put("name",mapName);c.put("firstRace",firstRace);c.put("secondRace",secondRace);c.put("expansion",expansion);
            configured=true;mapStartedAt=clock.now();send(NearbyProtocol51.CONFIG,0,0,c.toString().getBytes("UTF-8"));map=null;status="Sharing map…";
          }
          break;
        }
        case NearbyProtocol51.CONFIG:{
          if(host || configured || !hello)throw new IOException("Unexpected map settings");
          JSONObject c=new JSONObject(new String(m.data,"UTF-8"));mapSize=c.getInt("length");transferSize=c.getInt("wireLength");
          if(mapSize<8 || mapSize>NearbyProtocol51.MAX_MAP || transferSize<1 || transferSize>NearbyProtocol51.MAX_MAP)throw new IOException("Nearby map exceeds 8 MB");
          String encoding=c.getString("encoding");if(!encoding.equals("raw") && !encoding.equals("deflate"))throw new IOException("Unknown map encoding");
          compressed=encoding.equals("deflate");if(!compressed && transferSize!=mapSize)throw new IOException("Invalid map transfer length");
          mapDigest=c.getString("digest");if(!mapDigest.matches("[0-9a-f]{64}"))throw new IOException("Invalid map checksum");
          firstRace=c.getInt("firstRace");secondRace=c.getInt("secondRace");
          if(firstRace<0 || firstRace>2 || secondRace!=race)throw new IOException("Invalid match races");
          expansion=c.getBoolean("expansion");mapName=NearbyProtocol51.name(c.getString("name"));configured=true;mapStartedAt=clock.now();
          if(cache!=null)try{
            byte[] cached=cache.read(mapDigest,mapSize);
            if(cached!=null && cached.length==mapSize && NearbyProtocol51.digest(cached).equals(mapDigest)){map=cached;mapCached=true;}
          }catch(Exception ignored){}
          if(mapCached)receiveMapReady();
          else{transfer=new byte[transferSize];offset=0;status="Receiving map…";send(NearbyProtocol51.ACK,0,0);}
          break;
        }
        case NearbyProtocol51.ACK:{
          if(!host || !configured || ready || m.data.length!=0 || m.number<0 || m.number>sentEnd ||
             (m.number!=transferSize && m.number%NearbyProtocol51.MAX_BODY!=0))throw new IOException("Unexpected map acknowledgement");
          if(transferRequested && m.number<=offset)break; // Cumulative ACKs can repeat.
          if(!transferRequested && m.number!=0)throw new IOException("Missing initial map acknowledgement");
          transferRequested=true;offset=m.number;fillMapWindow();
          status=offset==transferSize?"Checking game data…":"Sending map: "+(offset*100/transferSize)+"%";break;
        }
        case NearbyProtocol51.CHUNK:{
          if(host || !configured || prepared || mapCached || m.number!=offset || m.data.length!=Math.min(NearbyProtocol51.MAX_BODY,transferSize-offset) || m.data.length==0)throw new IOException("Unexpected map data");
          System.arraycopy(m.data,0,transfer,offset,m.data.length);offset+=m.data.length;
          status="Receiving map: "+(offset*100/transferSize)+"%";
          if(offset==transferSize || offset-lastAck>=NearbyProtocol51.MAP_ACK_CHUNKS*NearbyProtocol51.MAX_BODY){lastAck=offset;send(NearbyProtocol51.ACK,offset,0);}
          if(offset==transferSize){
            map=NearbyMapCodec.decode(transfer,mapSize,compressed);
            if(!NearbyProtocol51.digest(map).equals(mapDigest))throw new IOException("Map transfer failed its checksum");
            receiveMapReady();
          }
          break;
        }
        case NearbyProtocol51.READY:
          if(!host || !prepared || ready || m.data.length!=8 || m.hash!=initialHash || readLong(m.data)!=assetHash ||
             (m.number!=0 && m.number!=1) || (transferRequested ? offset!=transferSize || m.number!=0 : m.number!=1))throw new IOException("Game data differs. Import the same core files on both phones");
          mapCached=m.number==1;mapReadyMs=Math.max(0,clock.now()-mapStartedAt);transfer=null;ready=true;status=mapCached?"Both ready — cached map":"Both players ready";break;
        case NearbyProtocol51.START:
          if(host || !ready || startReceived || m.hash!=initialHash)throw new IOException("Unexpected match start");begin();break;
        case NearbyProtocol51.TURN:
          if(!prepared || !ready || m.number<1)throw new IOException("Turn arrived before the game was ready");remote.put(m,turn);break;
        case NearbyProtocol51.PAUSE:
          if(m.number<0 || m.hash<0 || m.hash>1)throw new IOException("Invalid pause state");
          if(m.number>remotePauseSequence){remotePauseSequence=m.number;remotePaused=m.hash==1;lastTick=clock.now();resetSample(lastTick);}break;
        case NearbyProtocol51.PING:
          if(m.data.length!=0)throw new IOException("Invalid ping");send(NearbyProtocol51.PONG,m.number,m.hash);break;
        case NearbyProtocol51.PONG:
          if(m.data.length!=0)throw new IOException("Invalid pong");
          if(pingSentAt>=0 && m.number==pingSequence && m.hash==pingSentAt){
            double sample=Math.max(0,clock.now()-pingSentAt);jitterMs=pingMs<0?0:jitterMs*.75+Math.abs(sample-pingMs)*.25;
            pingMs=pingMs<0?sample:pingMs*.75+sample*.25;pingSentAt=-1;
          }break;
        case NearbyProtocol51.FINISH:
          if(!startReceived)throw new IOException("Match ended before it started");remoteFinished=true;break;
        case NearbyProtocol51.LEAVE:stop("Opponent left the match",playing);break;
        case NearbyProtocol51.ERROR:stop("Connection stopped: "+NearbyProtocol51.name(new String(m.data,"UTF-8")),false);break;
        default:throw new IOException("Unknown multiplayer message");
      }
    }catch(Exception e){fail(e.getMessage());}
  }
  static byte[] longBytes(long n) throws IOException {ByteArrayOutputStream b=new ByteArrayOutputStream();new DataOutputStream(b).writeLong(n);return b.toByteArray();}
  static long readLong(byte[] b) throws IOException {return new DataInputStream(new ByteArrayInputStream(b)).readLong();}
  void start(){if(!host || !ready || playing || closed)return;try{send(NearbyProtocol51.START,0,initialHash);begin();}catch(Exception e){fail(e.getMessage());}}
  private void begin() throws Exception {
    startReceived=true;playing=true;status="Connected";map=null;lastTick=sampleAt=clock.now();
    sampleSent=sentBytes;sampleReceived=receivedBytes;local.put(0,NearbyProtocol51.EMPTY);
    remote.put(new NearbyProtocol51.Message(NearbyProtocol51.TURN,0,initialHash,NearbyProtocol51.EMPTY),0);engine.started();
  }
  void pulse(boolean paused){
    if(!connected || closed)return;paused &= !localFinished;
    try{
      long now=clock.now();
      if(playing && localPaused!=paused){localPaused=paused;lastTick=now;resetSample(now);send(NearbyProtocol51.PAUSE,++pauseSequence,paused?1:0);}
      if(now-lastPing>=2000){lastPing=now;pingSentAt=now;send(NearbyProtocol51.PING,++pingSequence,now);}
      if(now-lastSeen>60000)fail("Other phone stopped responding");
    }catch(Exception e){fail(e.getMessage());}
  }
  void tick(double milliseconds){
    if(!playing || closed)return;
    long now=clock.now(),elapsed=lastTick<0?0:Math.max(0,now-lastTick);lastTick=now;
    if(finishingDisconnect>=0 && !localFinished && now-finishingDisconnect>5000){fail("Connection closed before the final turn arrived");return;}
    if(localPaused || remotePaused){accumulator=0;blocked=false;waitingSince=-1;status=remotePaused?"Paused on the other phone":"Paused";resetSample(now);return;}
    activeMs+=elapsed;if(blocked)waitMs+=elapsed;blocked=false;
    try{
      accumulator=Math.min(NearbyProtocol51.TURN_MS*2,accumulator+Math.max(0,milliseconds));
      int steps=0;
      while(steps<NearbyProtocol51.TURN_FRAMES*2){
        if(remaining==0){
          if(!remote.has(turn)){
            blocked=accumulator>=NearbyProtocol51.FRAME_MS;
            if(blocked && waitingSince<0)waitingSince=now;
            status=blocked && now-waitingSince>=750?"Waiting for other phone…":"Connected";break;
          }
          waitingSince=-1;
          NearbyProtocol51.Message other=remote.take(turn);byte[] own=local.remove(turn);
          if(own==null)throw new IOException("Missing local multiplayer input");
          if(turn>0){Long previous=hashes.remove(turn-1);if(previous==null || previous.longValue()!=other.hash)throw new IOException("Games went out of sync at frame "+((turn-1)*NearbyProtocol51.TURN_FRAMES));}
          long work=System.nanoTime();
          long checkpoint=turn==0?initialHash:engine.hash();hashes.put(turn,checkpoint);
          byte[] next=engine.collect();local.put(turn+1,next);
          // Hash belongs to the boundary BEFORE this turn. Input belongs to the
          // next turn, so network time overlaps simulation without prediction.
          engine.apply(host?own:other.data,host?other.data:own);remaining=NearbyProtocol51.TURN_FRAMES;status="Connected";
          engineNs+=System.nanoTime()-work;
          send(NearbyProtocol51.TURN,turn+1,checkpoint,next);
        }
        if(accumulator<NearbyProtocol51.FRAME_MS)break;
        long work=System.nanoTime();engine.step();engineNs+=System.nanoTime()-work;
        framesDone++;steps++;remaining--;accumulator-=NearbyProtocol51.FRAME_MS;
        if(remaining==0)turn++;
      }
      sample(now);
    }catch(Exception e){fail(e.getMessage());}
  }
  private void sample(long now){
    long wall=now-sampleAt;if(wall<1000)return;
    long active=activeMs-sampleActive,frames=framesDone-sampleFrames;
    simulationFps=active>0?frames*1000.0/active:0;waitPercent=active>0?Math.min(100,(waitMs-sampleWait)*100.0/active):0;
    engineMsPerFrame=frames>0?(engineNs-sampleEngine)/1e6/frames:0;
    txKiB=(sentBytes-sampleSent)*1000.0/(1024*wall);rxKiB=(receivedBytes-sampleReceived)*1000.0/(1024*wall);
    summary=String.format(Locale.ROOT,"Ping %s | Game %.0f%% | Wait %.0f%%",pingMs<0?"—":Math.round(pingMs)+" ms",simulationFps*NearbyProtocol51.FRAME_MS/10,waitPercent);
    resetSample(now);
  }
  private void resetSample(long now){sampleAt=now;sampleFrames=framesDone;sampleWait=waitMs;sampleEngine=engineNs;sampleSent=sentBytes;sampleReceived=receivedBytes;sampleActive=activeMs;}
  String summary(){return summary;}
  String diagnostics(){
    return String.format(Locale.ROOT,"Network: %s\nRTT jitter: %.1f ms\nSimulation: %.2f / %.2f frames/s; engine work %.2f ms/frame\nTraffic: %.2f KiB/s sent, %.2f KiB/s received\nInput buffer: 1 turn / %d ms; frames completed: %d\nMap: %s, %d bytes original, %d bytes wire, ready in %d ms\nTotal network wait: %d ms",summary,jitterMs,simulationFps,1000.0/NearbyProtocol51.FRAME_MS,engineMsPerFrame,txKiB,rxKiB,NearbyProtocol51.TURN_MS,framesDone,mapCached?"cache hit":compressed?"compressed":"raw",mapSize,mapCached?0:transferSize,mapReadyMs,waitMs);
  }
  long frames(){return framesDone;}
  long mapBytesSent(){return mapSentBytes;}
  void finish(){if(closed || localFinished)return;localFinished=true;try{send(NearbyProtocol51.FINISH,0,0);}catch(Exception e){fail(e.getMessage());}}
  void disconnected(){
    if(closed)return;
    if(remoteFinished){connected=false;remotePaused=false;finishingDisconnect=clock.now();return;}
    stop("Connection lost. The match has stopped",false);
  }
  void leave(){if(closed)return;try{if(connected && !localFinished)send(NearbyProtocol51.LEAVE,0,0);}catch(Exception ignored){}closed=true;playing=false;link.close();}
  void fail(String reason){
    if(closed)return;String why=reason==null?"Nearby connection failed":reason;
    try{if(connected)send(NearbyProtocol51.ERROR,0,0,NearbyProtocol51.name(why).getBytes("UTF-8"));}catch(Exception ignored){}
    stop(why,false);
  }
  private void stop(String why,boolean surrender){if(closed)return;closed=true;playing=false;status=why;link.close();engine.stopped(why,surrender);}
}

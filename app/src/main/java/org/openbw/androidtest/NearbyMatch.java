package org.openbw.androidtest;

import java.io.*;
import java.util.*;
import org.json.*;

/** Deterministic one-turn-ahead input; all methods run on the simulation worker. */
final class NearbyMatch {
  interface Engine {
    long[] prepare(byte[] map,int firstRace,int secondRace,int slot,boolean expansion) throws Exception;
    byte[] collect(); long hash(); void apply(byte[] first,byte[] second); void step();
    void started(); void stopped(String reason,boolean surrendered);
    default void configure(MatchSetup setup) throws Exception {}
    default byte[] snapshot() throws Exception {throw new IOException("Saving is unavailable");}
    default void restore(byte[] state) throws Exception {throw new IOException("Loading is unavailable");}
    default void countdown(int seconds) {}
    default void reloading() {}

  }
  interface Saved {void complete(byte[] snapshot) throws Exception;}
  interface Link {void send(byte[] packet);void close();}
  interface Clock {long now();}
  interface MapCache {byte[] read(String digest,int size) throws Exception;void write(String digest,byte[] data) throws Exception;}
  MatchSetup setup=new MatchSetup(true);
  int countdown;
  private int countdownSeconds;
  private long countdownEnd;
  private Saved savePending;
  private MatchSnapshot resume;
  private boolean resumeExpected,reloading,stateCompressed;
  private byte[] stateWire;
  private int stateSize,stateOffset,stateSent,stateAck;
  private String stateDigest;
  private final Engine engine;private final Link link;private final Clock clock;private final MapCache cache;
  final boolean host;final int race;final String name;
  String status="Connecting…",peerName="Opponent",mapName="";
  boolean connected,ready,playing,closed,remotePaused,localPaused,expansion;
  private boolean localFinished,remoteFinished,hello,configured,prepared,startReceived,transferRequested,compressed,mapCached,blocked;
  private long finishingDisconnect=-1,waitingSince=-1,waitAccountedAt=-1;
  private boolean resetElapsed;
  private byte[] map,transfer;
  private int mapSize,transferSize,offset,sentEnd,lastAck,turn,remaining,pauseSequence,remotePauseSequence=-1,firstRace,secondRace,pingSequence;
  private String mapDigest;
  private long initialHash,assetHash,lastSeen,lastPing,pingSentAt=-1,mapStartedAt,mapReadyMs;
  private double accumulator;
  private final NearbyProtocol.Turns remote=new NearbyProtocol.Turns();
  private final TreeMap<Integer,byte[]> local=new TreeMap<Integer,byte[]>();
  private final TreeMap<Integer,Long> hashes=new TreeMap<Integer,Long>();
  private long sentBytes,receivedBytes,mapSentBytes,framesDone,waitMs,engineNs,lastTick=-1,activeMs;
  private long pacingRecoveries,burstTicks,lastStepAt=-1,sampleBursts;
  private int sampleMaxSteps,sampleMaxGap,recentMaxSteps,recentMaxGap;
  private long recentBursts;
  private long sampleAt,sampleFrames,sampleWait,sampleEngine,sampleSent,sampleReceived,sampleActive;
  private double pingMs=-1,jitterMs,simulationFps,waitPercent,engineMsPerFrame,txKiB,rxKiB;
  private String summary="Measuring network…";

  NearbyMatch(boolean h,int r,String n,Engine e,Link l){this(h,r,n,e,l,null,()->System.nanoTime()/1000000);}
  NearbyMatch(boolean h,int r,String n,Engine e,Link l,MapCache c,Clock t){
    host=h;race=r;name=NearbyProtocol.name(n);engine=e;link=l;cache=c;clock=t;lastSeen=sampleAt=clock.now();
  }
  void hostMap(byte[] data,String title,boolean bw) throws Exception {
    if(!host || data==null || data.length<8 || data.length>NearbyProtocol.MAX_MAP)throw new IOException("This map is too large for nearby play");
    map=data;mapSize=data.length;mapDigest=NearbyProtocol.digest(data);mapName=NearbyProtocol.name(title);expansion=bw;
  }
  void hostSettings(MatchSetup value,byte[] saved) throws Exception {
    if(!host||playing)throw new IOException("Host settings cannot change during play");
    setup=MatchSetup.read(value.json(),true);countdownSeconds=5;
    resume=saved==null?null:MatchSnapshot.decode(saved);
  }
  private int frameMs(){return setup.frameMs();}
  void save(Saved callback) throws Exception {
    if(!host||!playing||closed||localFinished||savePending!=null)throw new IOException("Only the host can save an active match");
    savePending=callback;
  }
  private void clearRound() {
    playing=ready=configured=prepared=startReceived=transferRequested=mapCached=blocked=false;
    localFinished=remoteFinished=localPaused=remotePaused=false;countdown=0;countdownEnd=0;
    offset=sentEnd=lastAck=turn=remaining=pauseSequence=0;remotePauseSequence=-1;
    stateOffset=stateSent=stateAck=0;stateWire=null;transfer=null;savePending=null;
    finishingDisconnect=waitingSince=waitAccountedAt=-1;local.clear();hashes.clear();remote.clear();resetTiming(clock.now());
  }
  void reload(byte[] chk,String title,boolean bw,MatchSetup settings,byte[] saved) throws Exception {
    if(!host||closed||!connected||reloading)throw new IOException("The guest must be connected before loading");
    clearRound();hostMap(chk,title,bw);hostSettings(settings,saved);reloading=true;
    status="Loading game…";engine.reloading();send(NearbyProtocol.RELOAD,0,0);
  }
  private void configurePeer() throws Exception {
    firstRace=resume==null?race:setup.races[0];secondRace=resume==null?secondRace:setup.races[1];
    setup.races[0]=firstRace;setup.races[1]=secondRace;prepare();transfer=NearbyMapCodec.encode(map);compressed=transfer!=map;transferSize=transfer.length;
    JSONObject c=new JSONObject();c.put("length",mapSize);c.put("wireLength",transferSize);c.put("encoding",compressed?"deflate":"raw");
    c.put("digest",mapDigest);c.put("name",mapName);c.put("firstRace",firstRace);c.put("secondRace",secondRace);c.put("expansion",expansion);
    c.put("setup",setup.json());c.put("resume",resume!=null);
    configured=true;mapStartedAt=clock.now();send(NearbyProtocol.CONFIG,0,0,c.toString().getBytes("UTF-8"));map=null;status="Sharing map…";
  }
  private void sendState() throws Exception {
    byte[] raw=resume.encode();stateSize=raw.length;stateDigest=NearbyProtocol.digest(raw);stateWire=NearbyMapCodec.encode(raw);stateCompressed=stateWire!=raw;
    JSONObject j=new JSONObject();j.put("length",stateSize);j.put("wireLength",stateWire.length);j.put("digest",stateDigest);j.put("compressed",stateCompressed);
    send(NearbyProtocol.STATE_META,0,0,j.toString().getBytes("UTF-8"));status="Sharing saved game…";
  }
  private void fillStateWindow() throws Exception {
    int limit=Math.min(stateWire.length,stateOffset+NearbyProtocol.MAP_WINDOW*NearbyProtocol.MAX_BODY);
    while(stateSent<limit){int end=Math.min(stateWire.length,stateSent+NearbyProtocol.MAX_BODY);send(NearbyProtocol.STATE_CHUNK,stateSent,0,Arrays.copyOfRange(stateWire,stateSent,end));stateSent=end;}
  }
  private void send(int type,int n,long hash,byte[] data) throws Exception {
    byte[] packet=NearbyProtocol.pack(type,n,hash,data);sentBytes+=packet.length;link.send(packet);
  }
  private void send(int type,int n,long hash) throws Exception {send(type,n,hash,NearbyProtocol.EMPTY);}
  void connected(){
    if(closed)return;connected=true;lastSeen=clock.now();status="Checking game versions…";
    try{JSONObject j=new JSONObject();j.put("build",NearbyProtocol.BUILD);j.put("race",race);j.put("name",name);send(NearbyProtocol.HELLO,0,0,j.toString().getBytes("UTF-8"));}
    catch(Exception e){fail(e.getMessage());}
  }
  private void prepare() throws Exception {
    engine.configure(setup);
    long[] info=engine.prepare(map,firstRace,secondRace,host?0:1,expansion);
    if(info==null || info.length!=2)throw new IOException("Could not initialize multiplayer");
    assetHash=info[0];initialHash=info[1];
    if(host&&resume!=null){engine.restore(resume.state);initialHash=engine.hash();}
    prepared=true;
    if(cache!=null)try{cache.write(mapDigest,map);}catch(Exception ignored){} // Cache failure must not block a match.
  }
  private void receiveMapReady() throws Exception {
    prepare();mapReadyMs=Math.max(0,clock.now()-mapStartedAt);
    send(NearbyProtocol.READY,mapCached?1:0,initialHash,longBytes(assetHash));ready=!resumeExpected;
    map=null;transfer=null;status=mapCached?"Map cached — ready for host":"Ready — waiting for host";
  }
  private void fillMapWindow() throws Exception {
    int limit=Math.min(transferSize,offset+NearbyProtocol.MAP_WINDOW*NearbyProtocol.MAX_BODY);
    while(sentEnd<limit){
      int end=Math.min(transferSize,sentEnd+NearbyProtocol.MAX_BODY);
      send(NearbyProtocol.CHUNK,sentEnd,0,Arrays.copyOfRange(transfer,sentEnd,end));mapSentBytes+=end-sentEnd;sentEnd=end;
    }
  }
  void receive(byte[] packet){
    if(closed)return;
    try{
      NearbyProtocol.Message m=NearbyProtocol.parse(packet);lastSeen=clock.now();receivedBytes+=packet.length;
      switch(m.type){
        case NearbyProtocol.HELLO:{
          if(hello || !connected)throw new IOException("Unexpected connection handshake");
          JSONObject j=new JSONObject(new String(m.data,"UTF-8"));
          if(j.getInt("build")!=NearbyProtocol.BUILD)throw new IOException("Install the same StarDroid version on both devices");
          int other=j.getInt("race");if(other<0 || other>2)throw new IOException("Invalid player race");
          peerName=NearbyProtocol.name(j.getString("name"));hello=true;
          if(host){
            if(map==null)throw new IOException("Choose a map before hosting");
            secondRace=other;configurePeer();
          }
          break;
        }
        case NearbyProtocol.CONFIG:{
          if(host || configured || !hello)throw new IOException("Unexpected map settings");
          JSONObject c=new JSONObject(new String(m.data,"UTF-8"));mapSize=c.getInt("length");transferSize=c.getInt("wireLength");
          if(mapSize<8 || mapSize>NearbyProtocol.MAX_MAP || transferSize<1 || transferSize>NearbyProtocol.MAX_MAP)throw new IOException("Nearby map exceeds 8 MB");
          String encoding=c.getString("encoding");if(!encoding.equals("raw") && !encoding.equals("deflate"))throw new IOException("Unknown map encoding");
          compressed=encoding.equals("deflate");if(!compressed && transferSize!=mapSize)throw new IOException("Invalid map transfer length");
          mapDigest=c.getString("digest");if(!mapDigest.matches("[0-9a-f]{64}"))throw new IOException("Invalid map checksum");
          firstRace=c.getInt("firstRace");secondRace=c.getInt("secondRace");
          resumeExpected=c.optBoolean("resume",false);
          if(firstRace<0 || firstRace>2 || secondRace<0 || secondRace>2 || !resumeExpected&&secondRace!=race)throw new IOException("Invalid match races");
          setup=MatchSetup.read(c.getJSONObject("setup"),true);
          if(setup.races[0]!=firstRace||setup.races[1]!=secondRace)throw new IOException("Player races differ from setup");
          expansion=c.getBoolean("expansion");mapName=NearbyProtocol.name(c.getString("name"));configured=true;mapStartedAt=clock.now();
          if(cache!=null)try{
            byte[] cached=cache.read(mapDigest,mapSize);
            if(cached!=null && cached.length==mapSize && NearbyProtocol.digest(cached).equals(mapDigest)){map=cached;mapCached=true;}
          }catch(Exception ignored){}
          if(mapCached)receiveMapReady();
          else{transfer=new byte[transferSize];offset=0;status="Receiving map…";send(NearbyProtocol.ACK,0,0);}
          break;
        }
        case NearbyProtocol.ACK:{
          if(!host || !configured || ready || m.data.length!=0 || m.number<0 || m.number>sentEnd ||
             (m.number!=transferSize && m.number%NearbyProtocol.MAX_BODY!=0))throw new IOException("Unexpected map acknowledgement");
          if(transferRequested && m.number<=offset)break; // Cumulative ACKs can repeat.
          if(!transferRequested && m.number!=0)throw new IOException("Missing initial map acknowledgement");
          transferRequested=true;offset=m.number;fillMapWindow();
          status=offset==transferSize?"Checking game data…":"Sending map: "+(offset*100/transferSize)+"%";break;
        }
        case NearbyProtocol.CHUNK:{
          if(host || !configured || prepared || mapCached || m.number!=offset || m.data.length!=Math.min(NearbyProtocol.MAX_BODY,transferSize-offset) || m.data.length==0)throw new IOException("Unexpected map data");
          System.arraycopy(m.data,0,transfer,offset,m.data.length);offset+=m.data.length;
          status="Receiving map: "+(offset*100/transferSize)+"%";
          if(offset==transferSize || offset-lastAck>=NearbyProtocol.MAP_ACK_CHUNKS*NearbyProtocol.MAX_BODY){lastAck=offset;send(NearbyProtocol.ACK,offset,0);}
          if(offset==transferSize){
            map=NearbyMapCodec.decode(transfer,mapSize,compressed);
            if(!NearbyProtocol.digest(map).equals(mapDigest))throw new IOException("Map transfer failed its checksum");
            receiveMapReady();
          }
          break;
        }
        case NearbyProtocol.READY:
          if(!host || !prepared || ready || m.data.length!=8 || (resume==null&&m.hash!=initialHash) || readLong(m.data)!=assetHash ||
             (m.number!=0 && m.number!=1) || (transferRequested ? offset!=transferSize || m.number!=0 : m.number!=1))throw new IOException("Game data differs. Import the same core files on both devices");
          mapCached=m.number==1;mapReadyMs=Math.max(0,clock.now()-mapStartedAt);transfer=null;if(resume!=null){sendState();break;}ready=true;status=mapCached?"Both ready — cached map":"Both players ready";break;
        case NearbyProtocol.RELOAD:
          if(m.data.length!=0)throw new IOException("Invalid reload message");
          if(!host&&m.number==0){clearRound();resume=null;resumeExpected=false;engine.reloading();send(NearbyProtocol.RELOAD,1,0);}
          else if(host&&m.number==1&&reloading){reloading=false;configurePeer();}
          else throw new IOException("Unexpected reload");break;
        case NearbyProtocol.STATE_META:{
          if(host||!prepared||!resumeExpected||stateWire!=null||ready)throw new IOException("Unexpected saved game");
          JSONObject j=new JSONObject(new String(m.data,"UTF-8"));stateSize=j.getInt("length");int n=j.getInt("wireLength");stateDigest=j.getString("digest");stateCompressed=j.getBoolean("compressed");
          if(stateSize<56||stateSize>MatchSnapshot.LIMIT||n<1||n>MatchSnapshot.LIMIT||!stateDigest.matches("[0-9a-f]{64}"))throw new IOException("Invalid saved game transfer");
          stateWire=new byte[n];stateOffset=stateAck=0;send(NearbyProtocol.STATE_ACK,0,0);break;
        }
        case NearbyProtocol.STATE_ACK:
          if(!host||stateWire==null||ready||m.data.length!=0||m.number<stateOffset||m.number>stateSent||m.number!=stateWire.length&&m.number%NearbyProtocol.MAX_BODY!=0)throw new IOException("Unexpected saved game acknowledgement");
          if(m.number==stateOffset&&stateSent>0)break;
          stateOffset=m.number;fillStateWindow();break;
        case NearbyProtocol.STATE_CHUNK:
          if(host||stateWire==null||ready||m.number!=stateOffset||m.data.length==0||m.data.length!=Math.min(NearbyProtocol.MAX_BODY,stateWire.length-stateOffset))throw new IOException("Unexpected saved game data");
          System.arraycopy(m.data,0,stateWire,stateOffset,m.data.length);stateOffset+=m.data.length;status="Receiving saved game: "+(stateOffset*100L/stateWire.length)+"%";
          if(stateOffset==stateWire.length||stateOffset-stateAck>=NearbyProtocol.MAP_ACK_CHUNKS*NearbyProtocol.MAX_BODY){stateAck=stateOffset;send(NearbyProtocol.STATE_ACK,stateOffset,0);}
          if(stateOffset==stateWire.length){
            byte[] raw=NearbyMapCodec.decode(stateWire,stateSize,stateCompressed,MatchSnapshot.LIMIT);
            if(!NearbyProtocol.digest(raw).equals(stateDigest))throw new IOException("Saved game checksum differs");
            resume=MatchSnapshot.decode(raw);engine.restore(resume.state);initialHash=engine.hash();ready=true;stateWire=null;
            status="Saved game ready — waiting for host";send(NearbyProtocol.STATE_READY,0,initialHash);
          }break;
        case NearbyProtocol.STATE_READY:
          if(!host||resume==null||stateWire==null||stateOffset!=stateWire.length||ready||m.data.length!=0||m.hash!=initialHash)throw new IOException("Restored games differ");
          ready=true;stateWire=null;status="Saved game ready on both devices";break;
        case NearbyProtocol.COUNTDOWN:
          if(host||!ready||playing||m.number<0||m.number>5||m.hash!=initialHash||m.data.length!=0)throw new IOException("Unexpected countdown");
          if(m.number!=countdown){countdown=m.number;engine.countdown(countdown);}status=countdown>0?"Starting in "+countdown+"…":"Ready — waiting for host";break;
        case NearbyProtocol.START:
          if(host || !ready || startReceived || m.hash!=initialHash)throw new IOException("Unexpected match start");begin();break;
        case NearbyProtocol.TURN:
          if(reloading || !prepared || !ready)break; // Drain old-round packets before the reload handshake.
          if(m.number<1)throw new IOException("Turn arrived before the game was ready");
          remote.put(m,turn);if(blocked && m.number==turn)endWait(clock.now());break;
        case NearbyProtocol.PAUSE:
          if(!playing)break;
          if(m.number<0 || m.hash<0 || m.hash>1)throw new IOException("Invalid pause state");
          if(m.number>remotePauseSequence){remotePauseSequence=m.number;remotePaused=m.hash==1;resetTiming(clock.now());}break;
        case NearbyProtocol.PING:
          if(m.data.length!=0)throw new IOException("Invalid ping");send(NearbyProtocol.PONG,m.number,m.hash);break;
        case NearbyProtocol.PONG:
          if(m.data.length!=0)throw new IOException("Invalid pong");
          if(pingSentAt>=0 && m.number==pingSequence && m.hash==pingSentAt){
            double sample=Math.max(0,clock.now()-pingSentAt);jitterMs=pingMs<0?0:jitterMs*.75+Math.abs(sample-pingMs)*.25;
            pingMs=pingMs<0?sample:pingMs*.75+sample*.25;pingSentAt=-1;
          }break;
        case NearbyProtocol.FINISH:
          if(!startReceived)throw new IOException("Match ended before it started");remoteFinished=true;break;
        case NearbyProtocol.LEAVE:stop("Opponent left the match",playing);break;
        case NearbyProtocol.ERROR:stop("Connection stopped: "+NearbyProtocol.name(new String(m.data,"UTF-8")),false);break;
        default:throw new IOException("Unknown multiplayer message");
      }
    }catch(Exception e){fail(e.getMessage());}
  }
  static byte[] longBytes(long n) throws IOException {ByteArrayOutputStream b=new ByteArrayOutputStream();new DataOutputStream(b).writeLong(n);return b.toByteArray();}
  static long readLong(byte[] b) throws IOException {return new DataInputStream(new ByteArrayInputStream(b)).readLong();}
  void start(){if(!host || !ready || playing || closed || countdown>0)return;try{
    if(countdownSeconds>0){countdown=countdownSeconds;countdownEnd=clock.now()+countdown*1000;engine.countdown(countdown);send(NearbyProtocol.COUNTDOWN,countdown,initialHash);status="Starting in "+countdown+"…";}
    else {send(NearbyProtocol.START,0,initialHash);begin();}}catch(Exception e){fail(e.getMessage());}}
  private void begin() throws Exception {
    countdown=0;countdownEnd=0;startReceived=true;playing=true;status="Connected";map=null;resetTiming(clock.now());
    sampleSent=sentBytes;sampleReceived=receivedBytes;local.put(0,resume==null?NearbyProtocol.EMPTY:host?resume.first:resume.second);
    remote.put(new NearbyProtocol.Message(NearbyProtocol.TURN,0,initialHash,resume==null?NearbyProtocol.EMPTY:host?resume.second:resume.first),0);
    resume=null;engine.started();
  }
  void pulse(boolean paused){
    if(!connected || closed)return;paused &= !localFinished;
    try{
      long now=clock.now();
      if(host&&countdown>0) {
        int next=paused?0:(int)Math.max(0,(countdownEnd-now+999)/1000);
        if(next==0&&!paused){send(NearbyProtocol.START,0,initialHash);begin();}
        else if(next!=countdown){countdown=next;engine.countdown(next);send(NearbyProtocol.COUNTDOWN,next,initialHash);status=next>0?"Starting in "+next+"…":"Both players ready";}
      }
      if(playing && localPaused!=paused){localPaused=paused;resetTiming(now);send(NearbyProtocol.PAUSE,++pauseSequence,paused?1:0);}
      if(now-lastPing>=2000){lastPing=now;pingSentAt=now;send(NearbyProtocol.PING,++pingSequence,now);}
      if(now-lastSeen>60000)fail("Other device stopped responding");
    }catch(Exception e){fail(e.getMessage());}
  }
  void tick(double milliseconds){
    if(!playing || closed)return;
    long now=clock.now(),elapsed=lastTick<0?0:Math.max(0,now-lastTick);lastTick=now;
    if(finishingDisconnect>=0 && !localFinished && now-finishingDisconnect>5000){fail("Connection closed before the final turn arrived");return;}
    if((localPaused || remotePaused)&&savePending==null){resetTiming(now);status=remotePaused?"Paused on the other device":"Paused";return;}
    if(!resetElapsed)activeMs+=elapsed;
    try{
      accountWait(now);
      if(resetElapsed){accumulator=0;resetElapsed=false;}
      else if(blocked){
        // Network waiting is not simulation work owed. Keeping that debt makes
        // the earlier peer run whole turns on arrival, then wait again forever.
        // Keep one due frame and resume its normal cadence; never skip a step.
        accumulator=Math.min(accumulator,frameMs());
        if(remote.has(turn))pacingRecoveries++;
      }else accumulator=Math.min((frameMs()*NearbyProtocol.TURN_FRAMES)*2,accumulator+Math.max(0,milliseconds));
      if(savePending!=null)accumulator=Math.max(accumulator,frameMs()*NearbyProtocol.TURN_FRAMES);
      int steps=0;
      while(steps<NearbyProtocol.TURN_FRAMES*2){
        if(remaining==0){
          if(!remote.has(turn)){
            blocked=accumulator>=frameMs();
            if(blocked){
              accumulator=frameMs();
              if(waitingSince<0){waitingSince=now;waitAccountedAt=now;}
            }
            status=blocked && now-waitingSince>=750?"Waiting for other device…":"Connected";break;
          }
          if(savePending!=null) {
            NearbyProtocol.Message pending=remote.peek(turn);byte[] own=local.get(turn);
            if(own==null)throw new IOException("Missing saved input");
            if(turn>0 && !Objects.equals(hashes.get(turn-1),pending.hash))throw new IOException("Cannot save an out-of-sync match");
            byte[] saved=new MatchSnapshot(engine.snapshot(),host?own:pending.data,host?pending.data:own).encode();
            Saved callback=savePending;savePending=null;callback.complete(saved);resetTiming(now);return;
          }
          blocked=false;endWait(now);waitingSince=-1;
          NearbyProtocol.Message other=remote.take(turn);byte[] own=local.remove(turn);
          if(own==null)throw new IOException("Missing local multiplayer input");
          if(turn>0){Long previous=hashes.remove(turn-1);if(previous==null || previous.longValue()!=other.hash)throw new IOException("Games went out of sync at frame "+((turn-1)*NearbyProtocol.TURN_FRAMES));}
          long work=System.nanoTime();
          long checkpoint=turn==0?initialHash:engine.hash();hashes.put(turn,checkpoint);
          byte[] next=engine.collect();local.put(turn+1,next);
          // Hash belongs to the boundary BEFORE this turn. Input belongs to the
          // next turn, so network time overlaps simulation without prediction.
          engine.apply(host?own:other.data,host?other.data:own);remaining=NearbyProtocol.TURN_FRAMES;status="Connected";
          engineNs+=System.nanoTime()-work;
          send(NearbyProtocol.TURN,turn+1,checkpoint,next);
        }
        if(accumulator<frameMs())break;
        long work=System.nanoTime();engine.step();engineNs+=System.nanoTime()-work;
        if(lastStepAt>=0)sampleMaxGap=Math.max(sampleMaxGap,(int)Math.min(Integer.MAX_VALUE,Math.max(0,now-lastStepAt)));
        lastStepAt=now;
        framesDone++;steps++;remaining--;accumulator-=frameMs();
        if(remaining==0)turn++;
      }
      sampleMaxSteps=Math.max(sampleMaxSteps,steps);if(steps>1)burstTicks++;
      sample(now);
    }catch(Exception e){fail(e.getMessage());}
  }
  private void accountWait(long now){if(waitAccountedAt>=0){waitMs+=Math.max(0,now-waitAccountedAt);waitAccountedAt=now;}}
  private void endWait(long now){accountWait(now);waitAccountedAt=-1;}
  private void resetTiming(long now){
    endWait(now);accumulator=0;blocked=false;waitingSince=-1;lastTick=now;lastStepAt=-1;resetElapsed=true;resetSample(now);
  }
  private void sample(long now){
    long wall=now-sampleAt;if(wall<1000)return;
    long active=activeMs-sampleActive,frames=framesDone-sampleFrames;
    simulationFps=active>0?frames*1000.0/active:0;waitPercent=active>0?Math.min(100,(waitMs-sampleWait)*100.0/active):0;
    engineMsPerFrame=frames>0?(engineNs-sampleEngine)/1e6/frames:0;
    txKiB=(sentBytes-sampleSent)*1000.0/(1024*wall);rxKiB=(receivedBytes-sampleReceived)*1000.0/(1024*wall);
    recentMaxSteps=sampleMaxSteps;recentMaxGap=sampleMaxGap;recentBursts=burstTicks-sampleBursts;
    summary=String.format(Locale.ROOT,"Ping %s | Game %.0f%% | Wait %.0f%%",pingMs<0?"—":Math.round(pingMs)+" ms",simulationFps*frameMs()/10,waitPercent);
    resetSample(now);
  }
  private void resetSample(long now){sampleAt=now;sampleFrames=framesDone;sampleWait=waitMs;sampleEngine=engineNs;sampleSent=sentBytes;sampleReceived=receivedBytes;sampleActive=activeMs;sampleBursts=burstTicks;sampleMaxSteps=sampleMaxGap=0;}
  String summary(){return summary;}
  String diagnostics(){
    return String.format(Locale.ROOT,"Network: %s\nRTT jitter: %.1f ms\nSimulation: %.2f / %.2f frames/s; engine work %.2f ms/frame\nRecent pacing: max %d simulation steps/draw, %d multi-step draws, longest step gap %d ms\nPacing recoveries: %d\nTraffic: %.2f KiB/s sent, %.2f KiB/s received\nInput buffer: 1 turn / %d ms; frames completed: %d\nMap: %s, %d bytes original, %d bytes wire, ready in %d ms\nTotal network wait: %d ms",summary,jitterMs,simulationFps,1000.0/frameMs(),engineMsPerFrame,recentMaxSteps,recentBursts,recentMaxGap,pacingRecoveries,txKiB,rxKiB,(frameMs()*NearbyProtocol.TURN_FRAMES),framesDone,mapCached?"cache hit":compressed?"compressed":"raw",mapSize,mapCached?0:transferSize,mapReadyMs,waitMs);
  }
  long frames(){return framesDone;}
  long mapBytesSent(){return mapSentBytes;}
  void finish(){if(closed || localFinished)return;localFinished=true;try{send(NearbyProtocol.FINISH,0,0);}catch(Exception e){fail(e.getMessage());}}
  void disconnected(){
    if(closed)return;
    if(remoteFinished){
      boolean computers=false;for(int controller:setup.controllers)computers|=controller==2;
      if(computers&&!localFinished){stop("Opponent finished the match",true);return;}
      connected=false;remotePaused=false;finishingDisconnect=clock.now();return;
    }
    stop("Connection lost. The match has stopped",false);
  }
  void leave(){if(closed)return;try{if(connected && !localFinished)send(NearbyProtocol.LEAVE,0,0);}catch(Exception ignored){}closed=true;playing=false;link.close();}
  void fail(String reason){
    if(closed)return;String why=reason==null?"Nearby connection failed":reason;
    try{if(connected)send(NearbyProtocol.ERROR,0,0,NearbyProtocol.name(why).getBytes("UTF-8"));}catch(Exception ignored){}
    stop(why,false);
  }
  private void stop(String why,boolean surrender){if(closed)return;closed=true;playing=false;status=why;link.close();engine.stopped(why,surrender);}
}

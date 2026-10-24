package org.openbw.androidtest;

import java.io.*;
import java.util.*;
import org.json.*;

/** Host-relayed eight-player lockstep. The host assigns slots; every device verifies the same world. */
final class RoomMatch {
  interface Engine {
    long[] prepare(byte[] map,MatchSetup settings,int slot,boolean expansion)throws Exception;
    byte[] collect();long hash();void apply(byte[][] commands);void step();
    byte[] snapshot()throws Exception;void restore(byte[] state)throws Exception;
    void started();void stopped(String reason,boolean surrendered);void countdown(int seconds);void reloading();
  }
  interface Link {void send(int peer,byte[] packet);void drop(int peer);void close();}
  interface Saved {void complete(byte[] snapshot)throws Exception;}
  interface Clock {long now();}
  final boolean host;final String name;
  MatchSetup setup=new MatchSetup(true);
  final int[] occupants=new int[8];final String[] names=new String[8];
  final ArrayList<String> chat=new ArrayList<String>();
  int localSlot,countdown;boolean connected,ready,playing,closed,expansion,resuming;
  String status="Connecting…",mapName="",peerName="Host";
  private final Engine engine;private final Link link;private final Clock clock;private final NearbyMatch.MapCache cache;
  private final LinkedHashMap<Integer,Peer> peers=new LinkedHashMap<Integer,Peer>();
  private final TreeMap<Integer,Input[]> inputs=new TreeMap<Integer,Input[]>();
  private final TreeMap<Integer,Long> hashes=new TreeMap<Integer,Long>();
  private final int[] departed=new int[8];
  private int epoch,turn,remaining,barrier=-1,pauseSequence,remotePauseSequence=-1;
  private boolean prepared,hello,localPaused,remotePaused,finished,blocked,resetElapsed;
  private long initialHash,assetHash,countdownEnd,lastTick=-1,lastStep=-1,lastPing,sampleAt,framesDone,waitMs,waitingAt=-1;
  private long sampleFrames,sampleWait,activeMs,sampleActive,tx,rx,sampleTx,sampleRx,recoveries;
  private int maxSteps,recentMaxSteps,maxGap,recentMaxGap;
  private double accumulator,pingMs=-1;
  private String networkSummary="Measuring network…";
  private Blob mapBlob,stateBlob;private byte[] map;private RoomSnapshot resume;private Saved savePending;
  private Receiver mapReceiver,stateReceiver;
  private static final class Input {final long hash;final byte[] bytes;Input(long h,byte[] b){hash=h;bytes=b;}}
  private static final class Peer {
    final int id;String name="Player";boolean hello,ready,paused,finished;long seen,pingAt=-1;int highest=-1;
    int mapOffset,mapSent,stateOffset,stateSent;boolean mapAck,stateAck,mapVerified;
    Peer(int i,long now){id=i;seen=now;}
    void reset(){ready=false;highest=-1;mapOffset=mapSent=stateOffset=stateSent=0;mapAck=stateAck=mapVerified=false;}
  }
  private static final class Blob {
    final byte[] raw,wire;final String digest;final boolean compressed;
    Blob(byte[] b)throws Exception{raw=b;wire=NearbyMapCodec.encode(b);compressed=wire!=raw;digest=NearbyProtocol.digest(b);}
    JSONObject json()throws Exception{JSONObject j=new JSONObject();j.put("size",raw.length);j.put("wire",wire.length);j.put("digest",digest);j.put("zip",compressed);return j;}
  }
  private static final class Receiver {
    final int size;final String digest;final boolean compressed;final byte[] wire;int offset,ack;
    Receiver(JSONObject j,int limit)throws Exception{
      size=j.getInt("size");int n=j.getInt("wire");digest=j.getString("digest");compressed=j.getBoolean("zip");
      if(size<8||size>limit||n<1||n>limit||!digest.matches("[0-9a-f]{64}")||!compressed&&size!=n)throw new IOException("Invalid game transfer");wire=new byte[n];
    }
    boolean put(int at,byte[] data)throws Exception{
      if(at!=offset||data.length!=Math.min(RoomProtocol.MAX,wire.length-offset)||data.length==0)throw new IOException("Unexpected game transfer data");
      System.arraycopy(data,0,wire,offset,data.length);offset+=data.length;return offset==wire.length;
    }
    byte[] decode(int limit)throws Exception{byte[] b=NearbyMapCodec.decode(wire,size,compressed,limit);if(!digest.equals(NearbyProtocol.digest(b)))throw new IOException("Game transfer checksum differs");return b;}
  }
  RoomMatch(boolean h,int race,String n,Engine e,Link l,NearbyMatch.MapCache c,Clock t){
    host=h;name=NearbyProtocol.name(n);engine=e;link=l;cache=c;clock=t;Arrays.fill(occupants,-1);Arrays.fill(names,"");Arrays.fill(departed,Integer.MAX_VALUE);
    if(h){occupants[0]=0;names[0]=name;setup.races[0]=Math.max(0,Math.min(2,race));}sampleAt=t.now();
  }
  private byte[] utf(String s)throws Exception{return s.getBytes("UTF-8");}
  private String str(byte[] b)throws Exception{return new String(b,"UTF-8");}
  private void send(int peer,int type,int number,long hash,byte[] b)throws Exception{byte[] packet=RoomProtocol.pack(type,epoch,number,hash,b);tx+=packet.length;link.send(peer,packet);}
  private void send(int peer,int type,int number,long hash)throws Exception{send(peer,type,number,hash,RoomProtocol.EMPTY);}
  private void broadcast(int type,int number,long hash,byte[] b)throws Exception{for(Peer p:peers.values())if(p.hello)send(p.id,type,number,hash,b);}
  private void broadcast(int type,int number,long hash)throws Exception{broadcast(type,number,hash,RoomProtocol.EMPTY);}
  int slotOf(int id){for(int i=0;i<8;i++)if(occupants[i]==id)return i;return -1;}
  int humans(){int n=0;for(int c:setup.controllers)if(c==1)n++;return n;}
  int joined(){int n=0;for(int id:occupants)if(id>=0)n++;return n;}
  private void log(String text){chat.add(text);while(chat.size()>80)chat.remove(0);}
  void hostSettings(MatchSetup value,byte[] saved)throws Exception{
    if(!host||playing)throw new IOException("Cannot change a running game");setup=MatchSetup.read(value.json(),true);resume=saved==null?null:RoomSnapshot.decode(saved);resuming=resume!=null;
    Arrays.fill(occupants,-1);Arrays.fill(names,"");localSlot=resume==null?0:resume.hostSlot;
    if(setup.controllers[localSlot]!=1){localSlot=0;while(localSlot<8&&setup.controllers[localSlot]!=1)localSlot++;}
    occupants[localSlot]=0;names[localSlot]=name;
  }
  void hostMap(byte[] data,String title,boolean bw)throws Exception{
    if(!host||data==null||data.length<8||data.length>NearbyProtocol.MAX_MAP)throw new IOException("Invalid multiplayer map");
    map=data;mapBlob=new Blob(data);mapName=NearbyProtocol.name(title);expansion=bw;reconfigure();
  }
  void connected(int id,String peer){
    if(closed)return;
    if(peers.containsKey(id)||host&&peers.size()>=7||!host&&id!=0){link.drop(id);return;}
    Peer p=new Peer(id,clock.now());p.name=NearbyProtocol.name(peer);peers.put(id,p);connected=true;
    try{JSONObject j=new JSONObject();j.put("build",RoomProtocol.BUILD);j.put("name",name);send(id,RoomProtocol.HELLO,0,0,utf(j.toString()));}catch(Exception e){fail(e.getMessage());}
  }
  private void resetRound(){
    ready=playing=prepared=false;countdown=0;remaining=turn=0;barrier=-1;savePending=null;finished=false;localPaused=remotePaused=false;
    remotePauseSequence=-1;pauseSequence=0;inputs.clear();hashes.clear();Arrays.fill(departed,Integer.MAX_VALUE);mapReceiver=stateReceiver=null;
    for(Peer p:peers.values()){p.reset();p.paused=p.finished=false;}resetTiming();
  }
  private void prepare()throws Exception{
    long[] info=engine.prepare(map,setup.copy(),localSlot,expansion);if(info==null||info.length!=2)throw new IOException("Could not initialize multiplayer");
    assetHash=info[0];initialHash=info[1];if(resume!=null){engine.restore(resume.state);initialHash=engine.hash();}prepared=true;
  }
  private void reconfigure()throws Exception{
    if(!host||map==null||playing)return;if(++epoch<=0)throw new IOException("Lobby revision limit reached");
    resetRound();resuming=resume!=null;localSlot=slotOf(0);prepare();stateBlob=resume==null?null:new Blob(resume.encode());
    for(Peer p:peers.values())if(p.hello)config(p);updateReady();
  }
  private void config(Peer p)throws Exception{
    JSONObject j=new JSONObject();j.put("setup",setup.json());j.put("slot",slotOf(p.id));j.put("ids",new JSONArray(occupants));j.put("names",new JSONArray(names));
    j.put("map",mapBlob.json());j.put("name",mapName);j.put("bw",expansion);if(stateBlob!=null)j.put("state",stateBlob.json());
    send(p.id,RoomProtocol.CONFIG,0,0,utf(j.toString()));
  }
  private void updateReady(){
    if(!host)return;ready=prepared;int players=0;
    for(int i=0;i<setup.starts;i++){if(setup.controllers[i]!=0)players++;if(setup.controllers[i]==1&&occupants[i]<0)ready=false;}
    for(Peer p:peers.values())if(p.hello&&!p.ready)ready=false;
    ready&=players>=2&&setup.hasOpponents();
    status=!setup.hasOpponents()?"Choose at least two opposing sides":ready?"All players ready":joined()<humans()?"Waiting for players: "+joined()+" / "+humans():"Preparing game…";
  }
  void setSlot(int slot,int controller)throws Exception{
    if(!host||playing||resuming||countdown>0||slot<0||slot>=setup.starts||controller<0||controller>2||occupants[slot]>=0)return;
    setup.controllers[slot]=controller;reconfigure();
  }
  void move(int from,int to)throws Exception{
    if(!host||playing||countdown>0||from<0||to<0||from>=setup.starts||to>=setup.starts||from==to)return;
    if(resuming){if(setup.controllers[from]!=1||setup.controllers[to]!=1)return;}
    else{int c=setup.controllers[from];setup.controllers[from]=setup.controllers[to];setup.controllers[to]=c;int r=setup.races[from];setup.races[from]=setup.races[to];setup.races[to]=r;int team=setup.teams[from];setup.teams[from]=setup.teams[to];setup.teams[to]=team;}
    int id=occupants[from];occupants[from]=occupants[to];occupants[to]=id;String n=names[from];names[from]=names[to];names[to]=n;reconfigure();
  }
  void changeRace(int slot)throws Exception{
    if(playing||resuming||countdown>0||slot<0||slot>=setup.starts||setup.controllers[slot]==0)return;
    if(host){setup.races[slot]=(setup.races[slot]+1)%3;reconfigure();}
    else if(slot==localSlot)send(0,RoomProtocol.RACE,slot,(setup.races[slot]+1)%3);
  }
  void settingsChanged()throws Exception{if(host&&!playing&&!resuming&&countdown==0){setup=MatchSetup.read(setup.json(),true);reconfigure();}}
  void reload(byte[] chk,String title,boolean bw,MatchSetup value,byte[] saved)throws Exception{
    if(!host||closed)throw new IOException("Only the host can load a match");
    MatchSetup checked=MatchSetup.read(value.json(),true);RoomSnapshot.decode(saved);
    int capacity=0;for(int c:checked.controllers)if(c==1)capacity++;int devices=1;for(Peer p:peers.values())if(p.hello)devices++;
    if(capacity<devices)throw new IOException("The saved game has fewer player slots than connected devices");
    if(chk==null||chk.length<8||chk.length>NearbyProtocol.MAX_MAP)throw new IOException("Invalid multiplayer map");
    int[] old=occupants.clone();playing=false;hostSettings(checked,saved);
    // Keep connected devices in their old human positions where possible, then fill remaining saved positions.
    for(Peer p:peers.values())if(p.hello){int slot=-1;for(int i=0;i<8;i++)if(old[i]==p.id&&setup.controllers[i]==1&&occupants[i]<0)slot=i;
      if(slot<0)for(int i=0;i<8;i++)if(setup.controllers[i]==1&&occupants[i]<0){slot=i;break;}
      if(slot<0)throw new IOException("The saved game has fewer player slots than connected devices");occupants[slot]=p.id;names[slot]=p.name;
    }
    engine.reloading();hostMap(chk,title,bw);
  }
  void say(String text){text=RoomProtocol.chat(text);if(text.isEmpty()||closed)return;try{
    if(host){String line=name+": "+text;log(line);broadcast(RoomProtocol.CHAT,0,0,utf(line));}
    else send(0,RoomProtocol.CHAT,0,0,utf(text));
  }catch(Exception e){fail(e.getMessage());}}
  private void fill(Peer p,boolean state)throws Exception{
    Blob b=state?stateBlob:mapBlob;if(b==null)throw new IOException("Missing game transfer");
    int offset=state?p.stateOffset:p.mapOffset,sent=state?p.stateSent:p.mapSent,limit=Math.min(b.wire.length,offset+NearbyProtocol.MAP_WINDOW*RoomProtocol.MAX);
    while(sent<limit){int end=Math.min(limit,sent+RoomProtocol.MAX);send(p.id,state?RoomProtocol.STATE_CHUNK:RoomProtocol.MAP_CHUNK,sent,0,Arrays.copyOfRange(b.wire,sent,end));sent=end;}
    if(state)p.stateSent=sent;else p.mapSent=sent;
  }
  private void ack(Peer p,boolean state,int offset)throws Exception{
    Blob b=state?stateBlob:mapBlob;int sent=state?p.stateSent:p.mapSent,old=state?p.stateOffset:p.mapOffset;boolean begun=state?p.stateAck:p.mapAck;
    if(b==null||offset<0||offset>sent||offset!=b.wire.length&&offset%RoomProtocol.MAX!=0||!begun&&offset!=0)throw new IOException("Invalid game acknowledgement");
    if(begun&&offset<=old)return;
    if(state){p.stateAck=true;p.stateOffset=offset;}else{p.mapAck=true;p.mapOffset=offset;}fill(p,state);
  }
  private void mapReady()throws Exception{
    prepare();if(cache!=null)try{cache.write(mapReceiver.digest,map);}catch(Exception ignored){}
    ByteArrayOutputStream b=new ByteArrayOutputStream();DataOutputStream out=new DataOutputStream(b);out.writeLong(assetHash);out.writeLong(initialHash);
    send(0,RoomProtocol.MAP_READY,0,0,b.toByteArray());mapReceiver=null;
    if(stateReceiver!=null){send(0,RoomProtocol.STATE_ACK,0,0);status="Receiving saved game…";}
    else{ready=true;send(0,RoomProtocol.READY,0,initialHash);status="Ready — waiting for host";}
  }
  void receive(int id,byte[] packet){
    if(closed)return;Peer peer=peers.get(id);if(peer==null)return;
    try{
      RoomProtocol.Message m=RoomProtocol.read(packet);peer.seen=clock.now();rx+=packet.length;
      if(m.type==RoomProtocol.HELLO){
        if(peer.hello)throw new IOException("Repeated connection handshake");JSONObject j=new JSONObject(str(m.data));
        if(j.getInt("build")!=RoomProtocol.BUILD)throw new IOException("Install the same StarDroid version on all devices");
        peer.name=NearbyProtocol.name(j.getString("name"));peer.hello=true;hello=true;
        if(host){int slot=-1;if(!playing&&countdown==0)for(int i=0;i<setup.starts;i++)if(setup.controllers[i]==1&&occupants[i]<0){slot=i;break;}
          if(slot<0){send(id,RoomProtocol.ERROR,0,0,utf("No open player slot"));peers.remove(id);link.drop(id);return;}
          occupants[slot]=id;names[slot]=peer.name;log(peer.name+" joined.");reconfigure();
        }else peerName=peer.name;return;
      }
      if(!peer.hello)throw new IOException("Missing connection handshake");
      if(m.type==RoomProtocol.CONFIG){
        if(host||m.epoch<=epoch)return;JSONObject j=new JSONObject(str(m.data));epoch=m.epoch;resetRound();resume=null;
        setup=MatchSetup.read(j.getJSONObject("setup"),true);localSlot=j.getInt("slot");
        JSONArray ids=j.getJSONArray("ids"),ns=j.getJSONArray("names");if(localSlot<0||localSlot>=setup.starts||ids.length()!=8||ns.length()!=8||setup.controllers[localSlot]!=1)throw new IOException("Invalid player roster");
        HashSet<Integer> used=new HashSet<Integer>();boolean hasHost=false;
        for(int i=0;i<8;i++){occupants[i]=ids.getInt(i);names[i]=NearbyProtocol.name(ns.getString(i));if(occupants[i]<-1||occupants[i]>=0&&(setup.controllers[i]!=1||!used.add(occupants[i])))throw new IOException("Invalid player assignment");hasHost|=occupants[i]==0;}
        if(!hasHost||occupants[localSlot]<1)throw new IOException("Invalid local player assignment");
        mapName=NearbyProtocol.name(j.getString("name"));expansion=j.getBoolean("bw");mapReceiver=new Receiver(j.getJSONObject("map"),NearbyProtocol.MAX_MAP);
        stateReceiver=j.has("state")?new Receiver(j.getJSONObject("state"),RoomSnapshot.LIMIT):null;resuming=stateReceiver!=null;map=null;engine.reloading();
        if(cache!=null)try{byte[] cached=cache.read(mapReceiver.digest,mapReceiver.size);if(cached!=null&&cached.length==mapReceiver.size&&NearbyProtocol.digest(cached).equals(mapReceiver.digest))map=cached;}catch(Exception ignored){}
        if(map!=null)mapReady();else{status="Receiving map…";send(0,RoomProtocol.MAP_ACK,0,0);}return;
      }
      // Chat and keepalive are session messages. Every simulation/transfer message is revision-scoped.
      if(m.type!=RoomProtocol.CHAT&&m.type!=RoomProtocol.PING&&m.type!=RoomProtocol.PONG&&m.type!=RoomProtocol.ERROR&&m.type!=RoomProtocol.LEAVE&&m.epoch!=epoch)return;
      switch(m.type){
        case RoomProtocol.MAP_ACK:if(!host||playing)throw new IOException("Unexpected map acknowledgement");ack(peer,false,m.number);break;
        case RoomProtocol.STATE_ACK:if(!host||playing||!peer.mapVerified)throw new IOException("Unexpected save acknowledgement");ack(peer,true,m.number);break;
        case RoomProtocol.MAP_CHUNK:case RoomProtocol.STATE_CHUNK:{
          if(host||playing)throw new IOException("Unexpected game transfer");boolean state=m.type==RoomProtocol.STATE_CHUNK;Receiver r=state?stateReceiver:mapReceiver;if(r==null)throw new IOException("Unrequested game transfer");
          boolean done=r.put(m.number,m.data);status=(state?"Receiving saved game: ":"Receiving map: ")+(r.offset*100L/r.wire.length)+"%";
          if(done||r.offset-r.ack>=NearbyProtocol.MAP_ACK_CHUNKS*RoomProtocol.MAX){r.ack=r.offset;send(0,state?RoomProtocol.STATE_ACK:RoomProtocol.MAP_ACK,r.offset,0);}
          if(done){if(state){resume=RoomSnapshot.decode(r.decode(RoomSnapshot.LIMIT));engine.restore(resume.state);initialHash=engine.hash();stateReceiver=null;ready=true;send(0,RoomProtocol.READY,0,initialHash);status="Saved game ready — waiting for host";}
            else{map=r.decode(NearbyProtocol.MAX_MAP);mapReady();}}break;
        }
        case RoomProtocol.MAP_READY:{
          if(!host||!prepared||m.data.length!=16)throw new IOException("Unexpected map readiness");DataInputStream in=new DataInputStream(new ByteArrayInputStream(m.data));
          if(in.readLong()!=assetHash||resume==null&&in.readLong()!=initialHash)throw new IOException("Game data differs. Import the same core files on all devices");peer.mapVerified=true;break;
        }
        case RoomProtocol.READY:
          if(!host||!prepared||!peer.mapVerified||stateBlob!=null&&peer.stateOffset!=stateBlob.wire.length||m.hash!=initialHash||m.data.length!=0)throw new IOException("Prepared games differ");peer.ready=true;updateReady();break;
        case RoomProtocol.RACE:
          if(!host||playing||resuming||countdown>0||m.number!=slotOf(id)||m.hash<0||m.hash>2)throw new IOException("Invalid race change");setup.races[m.number]=(int)m.hash;reconfigure();break;
        case RoomProtocol.COUNTDOWN:
          if(host||!ready||playing||m.number<0||m.number>5||m.hash!=initialHash)throw new IOException("Unexpected countdown");countdown=m.number;engine.countdown(countdown);status=countdown>0?"Starting in "+countdown+"…":"Ready — waiting for host";break;
        case RoomProtocol.START:
          if(host||!ready||playing||m.hash!=initialHash)throw new IOException("Unexpected start");begin();break;
        case RoomProtocol.INPUT:{
          if(!playing)break;int slot=m.number&7,n=m.number>>>3;
          if(host&&slot!=slotOf(id)||setup.controllers[slot]!=1||n<1)throw new IOException("Invalid player input");
          store(n,slot,m.hash,m.data);if(host){peer.highest=Math.max(peer.highest,n);for(Peer other:peers.values())if(other.hello&&other.id!=id)send(other.id,RoomProtocol.INPUT,m.number,m.hash,m.data);}break;
        }
        case RoomProtocol.PAUSE:
          if(m.hash<0||m.hash>1||m.number<0)throw new IOException("Invalid pause state");
          if(host){peer.paused=m.hash==1&&!peer.finished;publishPause();}
          else if(m.number>remotePauseSequence){remotePauseSequence=m.number;remotePaused=m.hash==1;resetTiming();}break;
        case RoomProtocol.PING:send(id,RoomProtocol.PONG,m.number,m.hash);break;
        case RoomProtocol.PONG:if(peer.pingAt==m.hash){double sample=Math.max(0,clock.now()-m.hash);pingMs=pingMs<0?sample:.75*pingMs+.25*sample;peer.pingAt=-1;}break;
        case RoomProtocol.CHAT:{
          String text=host?RoomProtocol.chat(str(m.data)):RoomProtocol.chatLine(str(m.data));if(text.isEmpty())break;
          if(host){String line=peer.name+": "+text;log(line);broadcast(RoomProtocol.CHAT,0,0,utf(line));}else log(text);break;
        }
        case RoomProtocol.DEPART:
          if(host||!playing||m.hash<0||m.hash>7||m.number<turn||m.number>turn+3)throw new IOException("Invalid player departure");departed[(int)m.hash]=m.number;log(names[(int)m.hash]+" left.");break;
        case RoomProtocol.SAVE:
          if(host||!playing||m.number<-1||m.number>turn+3)throw new IOException("Invalid save boundary");barrier=m.number;resetTiming();break;
        case RoomProtocol.FINISH:if(!playing)break;peer.finished=true;peer.paused=false;if(host)publishPause();break;
        case RoomProtocol.LEAVE:disconnected(id);break;
        case RoomProtocol.ERROR:
          if(host){disconnected(id);break;}stop(RoomProtocol.chat(str(m.data)),false);break;
        default:throw new IOException("Unknown game message");
      }
    }catch(Exception e){if(host&&peers.size()>1){try{send(id,RoomProtocol.ERROR,0,0,utf(RoomProtocol.chat(e.getMessage())));}catch(Exception ignored){}disconnected(id);}else fail(e.getMessage());}
  }
  private void store(int n,int slot,long hash,byte[] bytes)throws Exception{
    if(n<turn||n>turn+2||bytes.length>RoomProtocol.MAX)throw new IOException("Unexpected multiplayer turn "+n+" at "+turn+" for slot "+slot);Input[] row=inputs.get(n);if(row==null){row=new Input[8];inputs.put(n,row);}Input old=row[slot];
    if(old!=null&&(old.hash!=hash||!Arrays.equals(old.bytes,bytes)))throw new IOException("Conflicting player input");row[slot]=new Input(hash,bytes);
    if(blocked&&complete(turn)){recoveries++;endWait();accumulator=Math.min(accumulator,setup.frameMs());}
  }
  private boolean complete(int n){Input[] row=inputs.get(n);for(int i=0;i<8;i++)if(setup.controllers[i]==1&&n<departed[i]&&(row==null||row[i]==null))return false;return true;}
  private byte[][] commands(int n,boolean verify)throws Exception{
    Input[] row=inputs.get(n);byte[][] all=new byte[8][];Long expected=n==0?initialHash:hashes.get(n-1);
    for(int i=0;i<8;i++){
      if(setup.controllers[i]!=1)all[i]=RoomProtocol.EMPTY;
      else if(n>=departed[i])all[i]=n==departed[i]?RoomProtocol.LEAVE_INPUT:RoomProtocol.EMPTY;
      else {if(row==null||row[i]==null)throw new IOException("Missing player input");if(verify&&n>0&&(expected==null||row[i].hash!=expected))throw new IOException("Games went out of sync at frame "+((n-1)*4));all[i]=row[i].bytes;}
    }return all;
  }
  void start(){if(!host||!ready||playing||closed||countdown>0)return;try{countdown=5;countdownEnd=clock.now()+5000;engine.countdown(5);broadcast(RoomProtocol.COUNTDOWN,5,initialHash);status="Starting in 5…";}catch(Exception e){fail(e.getMessage());}}
  private void begin()throws Exception{
    countdown=0;playing=true;remaining=turn=0;Input[] first=new Input[8];for(int i=0;i<8;i++)if(setup.controllers[i]==1)first[i]=new Input(initialHash,resume==null?RoomProtocol.EMPTY:resume.commands[i]);inputs.put(0,first);
    resume=null;stateBlob=null;resetTiming();status="Connected";engine.started();
  }
  private void publishPause()throws Exception{boolean paused=localPaused;for(Peer p:peers.values())paused|=p.paused;remotePaused=paused;broadcast(RoomProtocol.PAUSE,++pauseSequence,paused?1:0);resetTiming();}
  void pulse(boolean paused){
    if(closed)return;try{
      paused&=!finished;if(localPaused!=paused){localPaused=paused;if(host)publishPause();else if(hello)send(0,RoomProtocol.PAUSE,++pauseSequence,paused?1:0);resetTiming();}
      long now=clock.now();if(host&&countdown>0){int next=localPaused||remotePaused?0:(int)Math.max(0,(countdownEnd-now+999)/1000);
        if(next==0&&!localPaused&&!remotePaused){broadcast(RoomProtocol.START,0,initialHash);begin();}
        else if(next!=countdown){countdown=next;engine.countdown(next);broadcast(RoomProtocol.COUNTDOWN,next,initialHash);if(next==0)updateReady();else status="Starting in "+next+"…";}}
      if(now-lastPing>=2000){lastPing=now;for(Peer p:new ArrayList<Peer>(peers.values())){if(now-p.seen>60000){disconnected(p.id);continue;}p.pingAt=now;send(p.id,RoomProtocol.PING,0,now);}}
    }catch(Exception e){fail(e.getMessage());}
  }
  void save(Saved cb)throws Exception{
    if(!host||!playing||closed||finished||savePending!=null)throw new IOException("Only the host can save an active match");
    savePending=cb;barrier=saveBoundary();broadcast(RoomProtocol.SAVE,barrier,0);resetTiming();
  }
  private int saveBoundary(){int target=turn+(remaining>0?1:0);for(int at:departed)if(at!=Integer.MAX_VALUE)target=Math.max(target,at+1);return target;}
  MatchSetup savedSetup()throws Exception{MatchSetup value=setup.copy();for(int i=0;i<8;i++)if(departed[i]!=Integer.MAX_VALUE&&turn>departed[i])value.controllers[i]=0;return value;}
  boolean finished(){return finished;}
  void tick(double ms){
    if(!playing||closed)return;long now=clock.now(),elapsed=lastTick<0?0:Math.max(0,now-lastTick);lastTick=now;
    if((localPaused||remotePaused)&&barrier<0){resetTiming();status="Paused";return;}
    if(!resetElapsed)activeMs+=elapsed;
    try{
      if(resetElapsed){accumulator=0;resetElapsed=false;}else if(blocked)accumulator=Math.min(accumulator,setup.frameMs());else accumulator=Math.min(setup.frameMs()*8,accumulator+Math.max(0,ms));
      if(barrier>=0)accumulator=Math.max(accumulator,setup.frameMs()*4);
      int steps=0;while(steps<8){
        if(remaining==0){
          if(!complete(turn)){blocked=accumulator>=setup.frameMs();if(blocked){accumulator=setup.frameMs();if(waitingAt<0)waitingAt=now;}status=blocked&&now-waitingAt>=750?"Waiting for players…":"Connected";break;}
          byte[][] all=commands(turn,true);
          if(barrier>=0&&turn>=barrier){
            if(host&&savePending!=null){byte[] saved=new RoomSnapshot(engine.snapshot(),all,localSlot).encode();Saved cb=savePending;savePending=null;barrier=-1;broadcast(RoomProtocol.SAVE,-1,0);cb.complete(saved);}resetTiming();return;
          }
          endWait();blocked=false;long checkpoint=turn==0?initialHash:engine.hash();hashes.put(turn,checkpoint);
          byte[] next=finished?RoomProtocol.EMPTY:engine.collect();store(turn+1,localSlot,checkpoint,next);
          if(host)broadcast(RoomProtocol.INPUT,((turn+1)<<3)|localSlot,checkpoint,next);else send(0,RoomProtocol.INPUT,((turn+1)<<3)|localSlot,checkpoint,next);
          engine.apply(all);inputs.remove(turn);if(turn>0)hashes.remove(turn-1);remaining=4;status="Connected";
        }
        if(accumulator<setup.frameMs())break;engine.step();framesDone++;steps++;remaining--;accumulator-=setup.frameMs();
        if(lastStep>=0)maxGap=Math.max(maxGap,(int)Math.min(Integer.MAX_VALUE,now-lastStep));lastStep=now;if(remaining==0)turn++;
      }
      maxSteps=Math.max(maxSteps,steps);sample(now);
    }catch(Exception e){fail(e.getMessage());}
  }
  private void endWait(){if(waitingAt>=0){waitMs+=Math.max(0,clock.now()-waitingAt);waitingAt=-1;}}
  private void resetTiming(){endWait();blocked=false;accumulator=0;lastTick=clock.now();lastStep=-1;resetElapsed=true;}
  private void sample(long now){long wall=now-sampleAt;if(wall<1000)return;long active=activeMs-sampleActive,frames=framesDone-sampleFrames;double fps=active>0?frames*1000.0/active:0;
    networkSummary=String.format(Locale.ROOT,"Ping %s | Game %.0f%% | Wait %.0f%%",pingMs<0?"—":Math.round(pingMs)+" ms",fps*setup.frameMs()/10,active>0?Math.min(100,(waitMs-sampleWait)*100.0/active):0);
    sampleAt=now;sampleFrames=framesDone;sampleActive=activeMs;sampleWait=waitMs;sampleTx=tx;sampleRx=rx;recentMaxSteps=maxSteps;recentMaxGap=maxGap;maxSteps=maxGap=0;
  }
  String summary(){return networkSummary;}
  String diagnostics(){return "Network: "+networkSummary+"\nPlayers: "+joined()+" / "+humans()+"; local slot "+(localSlot+1)+"\nSimulation frames: "+framesDone+"; max steps/draw: "+recentMaxSteps+"; longest gap: "+recentMaxGap+" ms\nPacing recoveries: "+recoveries+"; network wait: "+waitMs+" ms\nTraffic: "+tx+" bytes sent, "+rx+" received";}
  long frames(){return framesDone;}
  void finish(){if(closed||finished)return;finished=true;try{if(host){localPaused=false;publishPause();}else send(0,RoomProtocol.FINISH,0,0);}catch(Exception e){fail(e.getMessage());}}
  void disconnected(int id){
    if(closed)return;Peer p=peers.remove(id);if(p==null)return;link.drop(id);connected=!peers.isEmpty();
    if(!host){stop("Host disconnected. The match has stopped",false);return;}
    int slot=slotOf(id);if(slot<0)return;try{
      log(p.name+" left.");if(playing){int at=Math.max(turn+(remaining>0?1:0),p.highest+1);departed[slot]=at;broadcast(RoomProtocol.DEPART,at,slot);if(savePending!=null){barrier=saveBoundary();broadcast(RoomProtocol.SAVE,barrier,0);}publishPause();}
      else{occupants[slot]=-1;names[slot]="";reconfigure();}
    }catch(Exception e){fail(e.getMessage());}
  }
  void leave(){if(closed)return;try{if(host)broadcast(RoomProtocol.LEAVE,0,0);else if(hello)send(0,RoomProtocol.LEAVE,0,0);}catch(Exception ignored){}closed=true;playing=false;link.close();}
  void fail(String reason){if(closed)return;String why=reason==null?"Multiplayer connection failed":reason;try{if(host)broadcast(RoomProtocol.ERROR,0,0,utf(RoomProtocol.chat(why)));else if(hello)send(0,RoomProtocol.ERROR,0,0,utf(RoomProtocol.chat(why)));}catch(Exception ignored){}stop(why,false);}
  private void stop(String why,boolean surrender){if(closed)return;closed=true;playing=false;status=why;link.close();engine.stopped(why,surrender);}
}

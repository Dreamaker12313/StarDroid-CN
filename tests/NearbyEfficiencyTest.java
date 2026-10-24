package org.openbw.androidtest;

import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;
import org.json.*;

/** Deterministic link model running actual old/new match schedulers, not phones. */
public final class NearbyEfficiencyTest {
  static int checks;
  static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
  interface Bad {void run() throws Exception;}
  static void rejects(Bad action,String message) throws Exception {boolean failed=false;try{action.run();}catch(Exception e){failed=true;}check(failed,message);}
  static final class Time implements NearbyMatch.Clock {long value=10000;public long now(){return value;}}
  static final class Engine implements NearbyMatch.Engine,NearbyMatch50.Engine {
    long state=1234;int frames,slot,sequence,starts,stops;String failure="";byte[] map;
    final int[] applied={0,0};final TreeMap<Integer,Long> checkpoints=new TreeMap<Integer,Long>();
    public long[] prepare(byte[] m,int first,int second,int s,boolean bw){map=m.clone();slot=s;return new long[]{9876,state};}
    public byte[] collect(){return ByteBuffer.allocate(8).putInt(slot).putInt(++sequence).array();}
    public long hash(){return state;}
    public void apply(byte[] first,byte[] second){
      for(byte[] b:new byte[][]{first,second}){
        if(b.length==0)continue;
        ByteBuffer in=ByteBuffer.wrap(b);int player=in.getInt(),command=in.getInt();
        check(command==++applied[player],"each player's commands apply exactly once, in order");
        state=state*31+player;state=state*31+command;
      }
    }
    public void step(){state=state*17+frames;frames++;if(frames%4==0)checkpoints.put(frames,state);}
    public void started(){starts++;}public void stopped(String why,boolean resigned){stops++;failure=why;}
  }
  static final class Delivery implements Comparable<Delivery> {
    long at,serial;int to;byte[] bytes;
    Delivery(long a,long s,int t,byte[] b){at=a;serial=s;to=t;bytes=b;}
    public int compareTo(Delivery d){int c=Long.compare(at,d.at);return c!=0?c:Long.compare(serial,d.serial);}
  }
  static final class Pair {
    final Time time=new Time();final Engine[] engine={new Engine(),new Engine()};
    final NearbyMatch[] current=new NearbyMatch[2];final NearbyMatch50[] old=new NearbyMatch50[2];
    final PriorityQueue<Delivery> wire=new PriorityQueue<Delivery>();final boolean improved;
    final Random random=new Random(51);final long[] lastDelivery={0,0};
    int delay,jitter;long serial,bytes,mapBytes,mapMs;byte[] original;
    Pair(boolean newer,int oneWay,int variance,byte[] map,NearbyMatch.MapCache guestCache) throws Exception {
      improved=newer;delay=oneWay;jitter=variance;original=map;
      for(int i=0;i<2;i++){
        final int from=i;
        if(newer)current[i]=new NearbyMatch(i==0,i==0?1:2,i==0?"Host":"Guest",engine[i],new NearbyMatch.Link(){public void send(byte[] p){queue(from,p);}public void close(){}},i==1?guestCache:null,time);
        else old[i]=new NearbyMatch50(i==0,i==0?1:2,i==0?"Host":"Guest",engine[i],new NearbyMatch50.Link(){public void send(byte[] p){queue(from,p);}public void close(){}});
      }
      if(newer)current[0].hostMap(map,"Model map",true);else old[0].hostMap(map,"Model map",true);
    }
    void queue(int from,byte[] p){
      long at=time.value+Math.max(0,delay+(jitter==0?0:random.nextInt(jitter*2+1)-jitter));
      at=Math.max(at,lastDelivery[from]);lastDelivery[from]=at;wire.add(new Delivery(at,serial++,1-from,p.clone()));
      bytes+=p.length;if((p[5]&255)==3)mapBytes+=p.length-22;
    }
    void deliver(){int guard=0;while(!wire.isEmpty() && wire.peek().at<=time.value){Delivery d=wire.remove();if(improved)current[d.to].receive(d.bytes);else old[d.to].receive(d.bytes);if(++guard>10000)throw new AssertionError("message loop");}}
    boolean ready(){return improved?current[0].ready&&current[1].ready:old[0].ready&&old[1].ready;}
    boolean closed(){return improved?current[0].closed||current[1].closed:old[0].closed||old[1].closed;}
    void connect(){
      long began=time.value;if(improved){current[0].connected();current[1].connected();}else{old[0].connected();old[1].connected();}
      for(int i=0;i<30000 && !ready() && !closed();i++){deliver();time.value++;}
      check(ready()&&!closed(),"map handshake: "+engine[0].failure+" / "+engine[1].failure);mapMs=time.value-began;
      check(Arrays.equals(engine[1].map,original),"decoded/transferred map matches original");
    }
    void start(){connect();if(improved)current[0].start();else old[0].start();}
    void run(int milliseconds,int hostStep,int guestStep){
      long end=time.value+milliseconds,nextA=time.value,nextB=time.value;
      while(time.value<end){
        deliver();
        if(time.value>=nextA){if(improved)current[0].tick(hostStep);else old[0].tick(hostStep);nextA+=hostStep;}
        if(time.value>=nextB){if(improved)current[1].tick(guestStep);else old[1].tick(guestStep);nextB+=guestStep;}
        deliver();time.value++;
        check(!closed(),"model remains connected: "+engine[0].failure+" / "+engine[1].failure);
      }
    }
    void consistent(){
      check(Math.abs(engine[0].frames-engine[1].frames)<=8,"bounded peer frame lead");
      for(Map.Entry<Integer,Long> e:engine[0].checkpoints.entrySet()){
        Long other=engine[1].checkpoints.get(e.getKey());if(other!=null)check(other.equals(e.getValue()),"equal state at frame "+e.getKey());
      }
    }
  }
  static byte[] noise(int size){byte[] b=new byte[size];new Random(9).nextBytes(b);return b;}
  static void codecs() throws Exception {
    for(int size:new int[]{8,256,16384,65537,1024*1024})for(boolean zeros:new boolean[]{true,false}){
      byte[] raw=zeros?new byte[size]:noise(size),wire=NearbyMapCodec.encode(raw);
      check(Arrays.equals(raw,NearbyMapCodec.decode(wire,size,wire!=raw)),"raw/compressed map round trip");
    }
    byte[] raw=new byte[100000],wire=NearbyMapCodec.encode(raw);
    check(wire.length<raw.length/10,"repetitive map compresses");
    rejects(()->NearbyMapCodec.decode(wire,8,true),"decompression cannot exceed declared map size");
    rejects(()->NearbyMapCodec.decode(Arrays.copyOf(wire,wire.length-1),raw.length,true),"truncated compression rejected");
    rejects(()->NearbyMapCodec.decode(Arrays.copyOf(wire,wire.length+1),raw.length,true),"trailing compression bytes rejected");
    rejects(()->NearbyMapCodec.decode(wire,NearbyProtocol.MAX_MAP+1,true),"oversized expanded map rejected");
    rejects(()->NearbyMapCodec.decode(new byte[8],10,false),"incorrect raw length rejected");
  }
  static void cache(Path temporary) throws Exception {
    NearbyMapCache cache=new NearbyMapCache(temporary.resolve("cache").toFile());byte[] map=noise(200001);String hash=NearbyProtocol.digest(map);
    Pair first=new Pair(true,25,0,map,cache);first.connect();check(first.mapBytes==map.length,"first visit transfers full random map");
    Pair repeat=new Pair(true,25,0,map,cache);repeat.connect();check(repeat.mapBytes==0,"verified cached map skips all chunks");
    check(repeat.mapMs<first.mapMs,"cached map handshake is faster");
    File disk=temporary.resolve("cache").resolve(hash+".chk").toFile();
    try(RandomAccessFile f=new RandomAccessFile(disk,"rw")){f.seek(0);f.write(7);}
    Pair corrupt=new Pair(true,25,0,map,cache);corrupt.connect();check(corrupt.mapBytes==map.length,"corrupt cache falls back to verified transfer");
    rejects(()->cache.read("../escape",20),"cache key cannot escape directory");
    rejects(()->cache.write(hash,new byte[10]),"cache rejects unchecked content");
    for(int i=0;i<6;i++){byte[] x=noise(300+i);cache.write(NearbyProtocol.digest(x),x);}
    check(temporary.resolve("cache").toFile().listFiles((d,n)->n.endsWith(".chk")).length==4,"cache evicts to four maps");
    NearbyMatch.MapCache broken=new NearbyMatch.MapCache(){public byte[] read(String h,int n)throws Exception{throw new IOException("disk unavailable");}public void write(String h,byte[] b)throws Exception{throw new IOException("disk full");}};
    Pair noDisk=new Pair(true,25,0,map,broken);noDisk.connect();check(noDisk.mapBytes==map.length,"cache I/O failure does not prevent play");
  }
  static void pauseAndPing() throws Exception {
    Pair p=new Pair(true,25,10,noise(1000),null);p.start();p.run(10000,16,33);p.consistent();
    p.current[0].pulse(true);p.current[1].pulse(false);p.run(500,16,33);int a=p.engine[0].frames,b=p.engine[1].frames;
    p.run(2000,16,33);check(p.engine[0].frames==a&&p.engine[1].frames==b,"pause freezes both buffered peers");
    p.current[0].pulse(false);p.run(5000,16,33);check(p.engine[0].frames>a,"resume progresses");p.consistent();
    p.current[0].pulse(false);p.current[1].pulse(false);p.run(500,16,33);
    check(!p.current[0].summary().contains("Ping —"),"round-trip ping measured with a single clock");
    check(p.current[0].diagnostics().contains("engine work")&&p.current[0].diagnostics().contains("Input buffer: 1 turn / 168 ms"),"timing diagnostics include simulation and buffering");
    // Stop deliveries entirely: buffered input may run out, but it may never be invented.
    p.wire.clear();int before=p.engine[0].frames;
    for(int i=0;i<500;i++){p.time.value+=16;p.current[0].tick(16);}
    check(p.engine[0].frames-before<=8,"missing peer input stops after bounded buffer");
  }
  static void invalidSettings() throws Exception {
    for(int kind=0;kind<4;kind++){
      Pair p=new Pair(true,25,0,noise(1000),null);NearbyMatch guest=p.current[1];guest.connected();
      guest.receive(NearbyProtocol.pack(NearbyProtocol.HELLO,0,0,new JSONObject().put("build",NearbyProtocol.BUILD).put("race",1).put("name","Host").toString().getBytes("UTF-8")));
      JSONObject c=new JSONObject().put("length",8).put("wireLength",8).put("encoding","raw").put("digest",NearbyProtocol.digest(new byte[8])).put("name","Invalid").put("firstRace",1).put("secondRace",2).put("expansion",true);
      if(kind==0)c.put("wireLength",NearbyProtocol.MAX_MAP+1);
      if(kind==1)c.put("encoding","unknown");
      if(kind==2)c.put("wireLength",9);
      if(kind==3)c.put("digest","../outside");
      guest.receive(NearbyProtocol.pack(NearbyProtocol.CONFIG,0,0,c.toString().getBytes("UTF-8")));
      check(guest.closed && p.engine[1].map==null,"invalid transfer metadata rejected before map preparation");
    }
  }
  public static void main(String[] args) throws Exception {
    Path out=Paths.get(args[0]);Files.createDirectories(out);codecs();cache(out);pauseAndPing();invalidSettings();
    JSONArray benchmarks=new JSONArray();byte[] map=noise(1024*1024);
    for(int delay:new int[]{0,10,25,50,100}){
      Pair baseline=new Pair(false,delay,0,map,null),candidate=new Pair(true,delay,0,map,null);
      baseline.start();candidate.start();baseline.run(60000,16,16);candidate.run(60000,16,16);baseline.consistent();candidate.consistent();
      int oldFrames=Math.min(baseline.engine[0].frames,baseline.engine[1].frames),newFrames=Math.min(candidate.engine[0].frames,candidate.engine[1].frames);
      check(newFrames>=oldFrames,"pipeline does not reduce throughput at one-way delay "+delay);
      check(newFrames>=1400,"pipeline maintains near Fastest at one-way delay "+delay);
      if(delay>=25)check(newFrames>oldFrames*1.1,"pipeline improves measured simulated waits");
      if(delay>0)check(candidate.mapMs<baseline.mapMs/2,"map window removes per-chunk round trips");
      benchmarks.put(new JSONObject().put("roundTripMs",2*delay).put("baselineFrames",oldFrames).put("candidateFrames",newFrames).put("baselineSpeedPercent",oldFrames*42.0/600).put("candidateSpeedPercent",newFrames*42.0/600).put("baselineMapMs",baseline.mapMs).put("candidateMapMs",candidate.mapMs));
    }
    Pair jitter=new Pair(true,60,50,map,null);jitter.start();jitter.run(60000,16,33);jitter.consistent();
    check(Math.min(jitter.engine[0].frames,jitter.engine[1].frames)>1380,"jitter and different display cadence retain game speed");
    Pair slow=new Pair(true,300,100,noise(10000),null);slow.start();slow.run(30000,16,33);slow.consistent();
    check(Math.min(slow.engine[0].frames,slow.engine[1].frames)>100,"latency beyond input buffer safely slows rather than inventing input");
    slow.delay=10;slow.jitter=0;int recover=slow.engine[0].frames;slow.run(10000,16,33);slow.consistent();
    check(slow.engine[0].frames-recover>200,"match recovers when the link improves");
    Pair compressed=new Pair(true,25,0,new byte[1024*1024],null);compressed.connect();
    check(compressed.mapBytes<8192,"compression reduces repetitive map traffic");
    JSONObject report=new JSONObject().put("version","0.54").put("passed",true).put("checks",checks).put("physicalPhones",false).put("model","Production 0.50 vs 0.54 match classes; ordered synthetic link; lightweight deterministic test engine; no radio/render workload").put("benchmarks",benchmarks).put("compressedMapBytes",compressed.mapBytes);
    Files.write(out.resolve("efficiency.json"),report.toString(2).getBytes("UTF-8"));
    System.out.println("PASS "+checks+" nearby efficiency assertions");System.out.println(benchmarks.toString(2));
  }
}

package org.openbw.androidtest;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Exercises production lobby, chunking and turn scheduler without replacing them. */
public final class NearbyProtocolTest {
  static int checks;
  static void check(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
  interface Bad {void run() throws Exception;}
  static void rejects(Bad f,String why) throws Exception {boolean rejected=false;try{f.run();}catch(IOException e){rejected=true;}check(rejected,why);}
  static final class Engine implements NearbyMatch.Engine {
    long state=1234,assets=9876;int frames,slot,starts,stops,collects;boolean surrendered;String failure="";byte[] map;
    public long[] prepare(byte[] m,int first,int second,int s,boolean expansion){map=m.clone();slot=s;return new long[]{assets,state};}
    public byte[] collect(){collects++;return new byte[]{(byte)slot,(byte)(frames&255)};}
    public long hash(){return state;}
    public void apply(byte[] a,byte[] b){for(byte[] batch:new byte[][]{a,b})for(byte n:batch)state=state*31+(n&255);}
    public void step(){state=state*17+frames;frames++;}
    public void started(){starts++;}
    public void stopped(String s,boolean resigned){stops++;failure=s;surrendered=resigned;}
  }
  static final class Peer {
    final Engine engine=new Engine();final ArrayDeque<byte[]> outgoing=new ArrayDeque<byte[]>();NearbyMatch match;boolean closed;
    Peer(boolean host){match=new NearbyMatch(host,host?1:2,host?"Host":"Guest",engine,new NearbyMatch.Link(){public void send(byte[] b){outgoing.add(b);}public void close(){closed=true;}});}
  }
  static final class Pair {
    Peer a=new Peer(true),b=new Peer(false);byte[] map=new byte[70001];
    Pair() throws Exception {new Random(7).nextBytes(map);a.match.hostMap(map,"Test",false);}
    void delivery(){if(!a.outgoing.isEmpty())b.match.receive(a.outgoing.remove());if(!b.outgoing.isEmpty())a.match.receive(b.outgoing.remove());}
    void drain(){for(int i=0;i<1000&&(!a.outgoing.isEmpty()||!b.outgoing.isEmpty());i++)delivery();}
    void connect(){a.match.connected();b.match.connected();drain();}
    void start(){connect();check(a.match.ready&&b.match.ready,"Both peers ready");a.match.start();drain();}
    void tick(int n){for(int i=0;i<n;i++){if(i%3==0)delivery();a.match.tick(30);b.match.tick(51);check(Math.abs(a.engine.frames-b.engine.frames)<=8,"Never more than two buffered turns apart");}}
  }
  public static void main(String[] args) throws Exception {
    byte[] p=NearbyProtocol.pack(NearbyProtocol.TURN,5,123,new byte[]{1,2});
    check(NearbyProtocol.parse(p).number==5,"packet round trip");
    for(int n=0;n<p.length;n++){final int length=n;rejects(()->NearbyProtocol.parse(Arrays.copyOf(p,length)),"truncated packet rejected");}
    rejects(()->NearbyProtocol.pack(7,0,0,new byte[16385]),"large packet rejected");
    byte[] bad=p.clone();bad[4]=9;rejects(()->NearbyProtocol.parse(bad),"wire version rejected");
    NearbyProtocol.Turns turns=new NearbyProtocol.Turns();turns.put(NearbyProtocol.parse(p),5);turns.put(NearbyProtocol.parse(p),5);
    rejects(()->turns.put(new NearbyProtocol.Message(7,5,124,new byte[]{1,2}),5),"conflicting duplicate rejected");
    rejects(()->turns.put(new NearbyProtocol.Message(7,8,124,new byte[0]),5),"unbounded lookahead rejected");
    Pair live=new Pair();live.start();check(Arrays.equals(live.a.engine.map,live.b.engine.map),"map transfer exact");
    check(live.b.engine.slot==1&&live.a.engine.slot==0,"distinct human slots");
    live.tick(1200);check(live.a.engine.frames>500&&!live.a.match.closed&&!live.b.match.closed,"delayed 2-peer play frames="+live.a.engine.frames+" / "+live.a.engine.failure+" / "+live.b.engine.failure);
    live.a.match.pulse(true);live.drain();int a=live.a.engine.frames,b=live.b.engine.frames;live.tick(40);
    check(a==live.a.engine.frames&&b==live.b.engine.frames,"pause freezes both phones");
    live.a.match.pulse(false);live.drain();live.tick(80);check(live.a.engine.frames>a,"resume continues");
    live.b.match.receive(NearbyProtocol.pack(NearbyProtocol.PAUSE,1,1,new byte[0]));check(!live.b.match.remotePaused,"stale pause ignored");
    for(int i=0;i<40;i++)live.a.match.tick(100);check(live.a.engine.frames-live.b.engine.frames<=8,"missing input stops advancement");
    live.a.engine.state++;live.drain();live.tick(60);live.drain();check(live.a.match.closed&&live.b.match.closed,"desync stops both games");
    Pair assets=new Pair();assets.b.engine.assets++;assets.connect();check(assets.a.match.closed&&!assets.a.match.playing,"different core data rejected");
    Pair initial=new Pair();initial.b.engine.state++;initial.connect();check(initial.a.match.closed,"different initial state rejected");
    Pair version=new Pair();version.a.match.connected();version.b.match.connected();version.a.match.receive(NearbyProtocol.pack(1,0,0,"{\"build\":49,\"race\":2,\"name\":\"Guest\"}".getBytes("UTF-8")));check(version.a.match.closed,"different app build rejected");
    Pair tamper=new Pair();tamper.a.match.connected();tamper.b.match.connected();boolean changed=false;
    for(int i=0;i<200;i++) {
      if(!tamper.a.outgoing.isEmpty()&&!changed){byte[] next=tamper.a.outgoing.peek();if(NearbyProtocol.parse(next).type==3){next[next.length-1]^=1;changed=true;}}
      tamper.delivery();
    }
    check(changed&&tamper.b.match.closed&&tamper.b.engine.starts==0,"corrupt map never starts");
    Pair resign=new Pair();resign.start();resign.a.match.leave();resign.drain();check(resign.b.engine.surrendered&&resign.b.engine.stops==1,"deliberate leave identified");
    Pair finished=new Pair();finished.start();finished.a.match.finish();finished.a.match.leave();finished.drain();finished.b.match.disconnected();
    check(!finished.b.engine.surrendered&&finished.b.engine.stops==0,"results exit cannot award false victory");finished.b.match.finish();finished.b.match.leave();
    Pair drop=new Pair();drop.start();drop.a.match.disconnected();check(!drop.a.engine.surrendered&&drop.a.engine.stops==1,"lost link does not fake victory");
    if(args.length>0){byte[] chk=Files.readAllBytes(Paths.get(args[0]));File map=NativeData.nearbyMap(chk,new File(args[1]));check(map.length()==chk.length+112+4*((chk.length+4095)/4096+1),"scenario MPQ has exact payload and tables");rejects(()->NativeData.nearbyMap(new byte[8],new File(args[1])),"malformed map rejected");}
    System.out.println("PASS "+checks+" nearby protocol assertions; version, map, ordering, delays, pauses, desync, leave and disconnect");
  }
}

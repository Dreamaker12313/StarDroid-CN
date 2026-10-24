package org.openbw.androidtest;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;

/** Production match + reliable handover + encrypted streams, using desktop TCP lanes. */
public final class LocalMatchTest {
  static final Queue<Runnable> callbacks=new ConcurrentLinkedQueue<Runnable>();
  static int checks;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
  static final class Peer {
    final NearbyProtocolTest.Engine engine=new NearbyProtocolTest.Engine();final boolean host;
    final LocalTransport.Pipe[] lanes=new LocalTransport.Pipe[2];final LocalTransport.Reliable reliable;
    final NearbyMatch match;boolean shutdown;long closeAt;
    Peer(boolean h){host=h;reliable=new LocalTransport.Reliable(this::received);
      match=new NearbyMatch(h,h?1:2,h?"Host":"Guest",engine,new NearbyMatch.Link(){
        public void send(byte[] b){try{reliable.send(b,System.nanoTime()/1000000);}catch(Exception e){throw new RuntimeException(e);}}
        public void close(){closeAt=System.nanoTime()+TimeUnit.MILLISECONDS.toNanos(350);}
      });
    }
    void received(byte[] b){match.receive(b);}
    void service(){if(closeAt!=0 && System.nanoTime()>=closeAt){shutdown=true;reliable.close();Arrays.fill(lanes,null);}}
    void attach(int lane,Socket socket,byte[] key)throws Exception{
      LocalTransport.Pipe p=new LocalTransport.Pipe(socket.getInputStream(),socket.getOutputStream(),socket,key,host,callbacks::add,new LocalTransport.StreamListener(){
        public void frame(LocalTransport.Frame f){if(!shutdown && lanes[lane]!=null)try{reliable.receive(lane,f,System.nanoTime()/1000000);}catch(Exception e){throw new RuntimeException(e);}}
        public void ended(){if(!shutdown && lanes[lane]!=null)drop(lane);}
      });lanes[lane]=p;reliable.attach(lane,p,System.nanoTime()/1000000);p.start();
    }
    void drop(int lane){try{lanes[lane]=null;reliable.detach(lane,System.nanoTime()/1000000);if(reliable.route()<0)match.disconnected();}catch(Exception e){throw new RuntimeException(e);}}
  }
  static void events(){Runnable r;int limit=10000;while((r=callbacks.poll())!=null){r.run();if(--limit==0)throw new AssertionError("Event flood");}}
  public static void main(String[] args)throws Exception{
    Peer host=new Peer(true),guest=new Peer(false);byte[] map=new byte[250123];new Random(48).nextBytes(map);host.match.hostMap(map,"Transfer during handover",true);
    Socket[] bt=LocalTransportTest.sockets();byte[] secret=LocalTransport.random(32);host.attach(0,bt[0],secret);guest.attach(0,bt[1],secret);
    host.match.connected();guest.match.connected();long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(15);
    boolean upgraded=false,started=false,dropped=false,paused=false,resumed=false;int pauseTicks=0,first=0,second=0;
    while(System.nanoTime()<deadline && Math.min(host.engine.frames,guest.engine.frames)<900){
      events();host.service();guest.service();
      if(!upgraded && host.engine.map!=null){
        // Switch while the scenario is still transferring, with Bluetooth packets in flight.
        Socket[] wifi=LocalTransportTest.sockets();byte[] wifiKey=LocalTransport.random(32);host.attach(1,wifi[0],wifiKey);guest.attach(1,wifi[1],wifiKey);upgraded=true;
      }
      if(!started && host.match.ready && guest.match.ready){check(Arrays.equals(map,guest.engine.map),"Transferred map exact across handover");host.match.start();started=true;}
      if(started){
        host.match.tick(42);guest.match.tick(42);
        // At a turn boundary one peer may have applied the next command batch but
        // not stepped it yet. Compare completed interior frames; the production
        // protocol separately compares both pre-apply boundary hashes.
        if(host.engine.frames==guest.engine.frames && host.engine.frames%NearbyProtocol.TURN_FRAMES!=0)check(host.engine.state==guest.engine.state,"State remains synchronized over real encrypted streams");
        if(!dropped && host.engine.frames>220){host.drop(1);guest.drop(1);dropped=true;}
        if(!paused && host.engine.frames>450){host.match.pulse(true);paused=true;}
        if(paused && !resumed && guest.match.remotePaused){
          if(pauseTicks++==0){first=host.engine.frames;second=guest.engine.frames;}
          else check(first==host.engine.frames && second==guest.engine.frames,"Shared pause survives fallback");
          if(pauseTicks==20){host.match.pulse(false);resumed=true;}
        }
      }
      check(!host.match.closed && !guest.match.closed,"Match did not stop: "+host.engine.failure+" / "+guest.engine.failure);
      Thread.sleep(1);
    }
    check(upgraded && dropped && paused && resumed && Math.min(host.engine.frames,guest.engine.frames)>=900,"Full transfer/play/fallback/pause scenario completed");
    // Deliberate leave must reach the peer before its connection ends.
    host.match.leave();deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);
    while(!guest.match.closed && System.nanoTime()<deadline){events();host.service();guest.service();Thread.sleep(1);}
    check(guest.match.closed && guest.engine.surrendered,"Deliberate leave arrives during the same 350ms drain used on Android");
    host.reliable.close();guest.reliable.close();System.out.println("PASS "+checks+" integrated match checks; exact map, encrypted stream handover, Bluetooth fallback, shared pause and 900+ simulation frames");
  }
}

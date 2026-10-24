package org.openbw.androidtest;
import java.net.*;import java.util.*;import java.util.concurrent.*;
/** Production room protocol and AES-GCM/reliable transport across fourteen actual TCP lanes. */
public final class RoomSocketTest {
 static final Queue<Runnable> callbacks=new ConcurrentLinkedQueue<>();static final RoomMatchTest.Clock clock=new RoomMatchTest.Clock();static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static class End {
  final boolean host;final int peer;final RoomMatch owner;final LocalTransport.Reliable reliable;final LocalTransport.Pipe[] pipes=new LocalTransport.Pipe[2];boolean closed;
  End(boolean h,int id,RoomMatch match){host=h;peer=id;owner=match;reliable=new LocalTransport.Reliable(b->owner.receive(peer,b));}
  void attach(int lane,Socket s,byte[] key)throws Exception{
   LocalTransport.Pipe p=new LocalTransport.Pipe(s.getInputStream(),s.getOutputStream(),s,key,host,callbacks::add,new LocalTransport.StreamListener(){
    public void frame(LocalTransport.Frame f){if(!closed&&pipes[lane]!=null)try{reliable.receive(lane,f,clock.now);}catch(Exception e){throw new RuntimeException(e);}}
    public void ended(){if(!closed&&pipes[lane]!=null)drop(lane);}
   });pipes[lane]=p;reliable.attach(lane,p,clock.now);p.start();
  }
  void drop(int lane){try{pipes[lane]=null;reliable.detach(lane,clock.now);if(reliable.route()<0&&!closed){closed=true;owner.disconnected(peer);}}catch(Exception e){throw new RuntimeException(e);}}
  void close(){closed=true;reliable.close();Arrays.fill(pipes,null);}
 }
 static void events(){Runnable r;int n=0;while((r=callbacks.poll())!=null){r.run();if(n++>100000)throw new AssertionError("Event flood");}}
 public static void main(String[]args)throws Exception{
  RoomMatch[] rooms=new RoomMatch[8];RoomMatchTest.Engine[] engines=new RoomMatchTest.Engine[8];End[] host=new End[8],guest=new End[8];boolean[] online=new boolean[8];Arrays.fill(online,true);
  for(int i=0;i<8;i++){final int id=i;engines[i]=new RoomMatchTest.Engine();rooms[i]=new RoomMatch(i==0,i%3,"Device "+i,engines[i],new RoomMatch.Link(){
    public void send(int peer,byte[] b){try{End e=id==0?host[peer]:guest[id];if(e!=null&&!e.closed)e.reliable.send(b,clock.now);}catch(Exception e){throw new RuntimeException(e);}}
    public void drop(int peer){End e=id==0?host[peer]:guest[id];if(e!=null)e.close();}public void close(){}
   },null,clock);
  }
  MatchSetup setup=new MatchSetup(true);setup.starts=8;Arrays.fill(setup.controllers,1);for(int i=0;i<8;i++)setup.races[i]=i%3;
  byte[] map=new byte[375123];new Random(55).nextBytes(map);rooms[0].hostSettings(setup,null);rooms[0].hostMap(map,"Eight socket devices",true);
  for(int i=1;i<8;i++){host[i]=new End(true,i,rooms[0]);guest[i]=new End(false,0,rooms[i]);Socket[] sockets=LocalTransportTest.sockets();byte[] key=LocalTransport.random(32);host[i].attach(0,sockets[0],key);guest[i].attach(0,sockets[1],key);rooms[0].connected(i,"Device "+i);rooms[i].connected(0,"Device 0");}
  boolean started=false,paused=false,resumed=false,departed=false;boolean[] upgraded=new boolean[8],fallback=new boolean[8];byte[][] saved={null};long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(30);int pauseAt=0;
  while(System.nanoTime()<deadline){events();clock.now+=16;
   if(!started&&rooms[0].ready){rooms[0].start();started=true;rooms[3].say("Eight players — chat relay");}
   for(int i=1;i<8;i++)if(!upgraded[i]&&engines[0].frame>40+i*8){Socket[] sockets=LocalTransportTest.sockets();byte[] key=LocalTransport.random(32);host[i].attach(1,sockets[0],key);guest[i].attach(1,sockets[1],key);upgraded[i]=true;}
   for(int i=1;i<8;i++)if(upgraded[i]&&!fallback[i]&&engines[0].frame>220+i*4){host[i].drop(1);guest[i].drop(1);fallback[i]=true;}
   if(!paused&&engines[0].frame>=350){paused=true;pauseAt=(int)clock.now;}
   if(paused&&!resumed&&clock.now-pauseAt>=1000&&saved[0]==null){rooms[0].save(b->saved[0]=b);resumed=true;}
   if(!departed&&engines[0].frame>=600&&saved[0]!=null){departed=true;online[7]=false;guest[7].close();rooms[0].disconnected(7);}
   for(int i=0;i<8;i++)if(online[i]){rooms[i].pulse(i==4&&paused&&!resumed);rooms[i].tick(16);check(!rooms[i].closed,"Device "+i+" stopped: "+engines[i].stopped);}
   int min=Integer.MAX_VALUE;for(int i=0;i<8;i++)if(online[i])min=Math.min(min,engines[i].frame);if(departed&&min>=740)break;
   Thread.sleep(1);
  }
  check(started&&resumed&&departed&&saved[0]!=null,"Scenario completed");
  for(int i=1;i<8;i++){check(upgraded[i]&&fallback[i],"Every lane upgraded and fell back");check(rooms[i].chat.toString().contains("Eight players"),"Chat reached all devices");for(int frame:engines[i].trace.keySet())if(engines[0].trace.containsKey(frame))check(engines[i].trace.get(frame).equals(engines[0].trace.get(frame)),"World differs device="+i+" frame="+frame);host[i].close();guest[i].close();}
  System.out.println("PASS "+checks+" real socket checks: eight devices, fourteen encrypted lanes, map/chat/countdown, seven handovers/fallbacks, paused save, guest departure, 740+ frames");
 }
}

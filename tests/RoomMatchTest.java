package org.openbw.androidtest;
import java.util.*;import java.io.*;
public class RoomMatchTest {
 static int checks;static void check(boolean b,String m){checks++;if(!b)throw new AssertionError(m);}
 static class Clock implements RoomMatch.Clock{long now;public long now(){return now;}}
 static class Engine implements RoomMatch.Engine{
  int frame,slot,collect,countdowns,starts;long state;byte[] saved;String stopped="";TreeMap<Integer,Long> trace=new TreeMap<>();
  public long[] prepare(byte[] map,MatchSetup s,int local,boolean bw)throws Exception{slot=local;frame=collect=0;state=17;trace.clear();for(int i=0;i<8;i++){state=state*31+s.controllers[i];state=state*31+s.races[i];}state=state*31+(s.freeForAll?1:0);state=state*31+(s.heroMode?1:0);state=state*31+(s.teamGame?1:0);for(int t:s.teams)state=state*31+t;return new long[]{12345,hash()};}
  public byte[] collect(){return new byte[]{(byte)slot,(byte)++collect};}
  public long hash(){return state*31+frame;}
  public void apply(byte[][] commands){for(int i=0;i<8;i++){state=state*31+i;for(byte b:commands[i])state=state*31+(b&255);}}
  public void step(){state=state*31+frame;frame++;trace.put(frame,hash());}
  public byte[] snapshot()throws Exception{ByteArrayOutputStream b=new ByteArrayOutputStream();DataOutputStream o=new DataOutputStream(b);o.writeInt(frame);o.writeLong(state);o.write(new byte[28]);return b.toByteArray();}
  public void restore(byte[] b)throws Exception{DataInputStream in=new DataInputStream(new ByteArrayInputStream(b));frame=in.readInt();state=in.readLong();trace.clear();}
  public void started(){starts++;}public void stopped(String r,boolean s){stopped=r;}public void countdown(int s){if(s>0)countdowns++;}public void reloading(){}
 }
 static class Packet{int from,to;byte[] data;long due,order;Packet(int f,int t,byte[] d,long time,long o){from=f;to=t;data=d;due=time;order=o;}}
 static class Network{
  Clock clock=new Clock();Random random=new Random(55);RoomMatch[] games;Engine[] engines;boolean[] pause,online;long order;boolean delay=true;int bytes;
  PriorityQueue<Packet> queue=new PriorityQueue<>((a,b)->a.due==b.due?Long.compare(a.order,b.order):Long.compare(a.due,b.due));Map<String,Long> routes=new HashMap<>();
  byte[] map=new byte[100000];MatchSetup setup;
  Network(int n,byte[] snapshot,MatchSetup old)throws Exception{
   games=new RoomMatch[n];engines=new Engine[n];pause=new boolean[n];online=new boolean[n];Arrays.fill(online,true);random.nextBytes(map);
   setup=old==null?new MatchSetup(true):old.copy();if(old==null){setup.starts=8;Arrays.fill(setup.controllers,0);for(int i=0;i<n;i++){setup.controllers[i]=1;setup.races[i]=i%3;}if(n<8)setup.controllers[7]=2;setup.heroMode=true;setup.teamGame=true;for(int i=0;i<8;i++)setup.teams[i]=i%2+1;}
   for(int i=0;i<n;i++){final int id=i;Engine e=new Engine();engines[i]=e;Map<String,byte[]> cache=new HashMap<>();
    games[i]=new RoomMatch(i==0,i%3,"Player "+i,e,new RoomMatch.Link(){public void send(int to,byte[] b){schedule(id,to,b);}public void drop(int peer){}public void close(){}},new NearbyMatch.MapCache(){public byte[] read(String d,int z){return cache.get(d);}public void write(String d,byte[] b){cache.put(d,b);}},clock);
   }
   games[0].hostSettings(setup,snapshot);games[0].hostMap(map,"Test map",true);
  }
  void schedule(int from,int to,byte[] data){bytes+=data.length;String k=from+":"+to;long due=Math.max(clock.now+(delay?4+random.nextInt(120):0),routes.getOrDefault(k,0L)+1);routes.put(k,due);queue.add(new Packet(from,to,data,due,order++));}
  void connect(int id){games[0].connected(id,"Player "+id);games[id].connected(0,"Player 0");}
  void step(){clock.now+=16;int count=0;while(!queue.isEmpty()&&queue.peek().due<=clock.now){Packet p=queue.remove();if(online[p.to]&&online[p.from])games[p.to].receive(p.from,p.data);if(++count>10000)throw new AssertionError("packet loop");}
   for(int i=0;i<games.length;i++)if(online[i]){games[i].pulse(pause[i]);games[i].tick(16);if(games[i].closed)throw new AssertionError("Device "+i+" stopped: "+engines[i].stopped+" at "+clock.now);}}
  void until(java.util.function.BooleanSupplier condition,int max,String what){for(int i=0;i<max&&!condition.getAsBoolean();i++)step();check(condition.getAsBoolean(),what+" timed out at "+clock.now+" host="+games[0].status);}
  void lobby()throws Exception{for(int i=1;i<games.length;i++)connect(i);until(()->games[0].ready,4000,"lobby");for(int i=1;i<games.length;i++){check(games[i].ready,"guest readiness");check(games[i].setup.json().toString().equals(games[0].setup.json().toString()),"setup broadcast");}}
  void start(){games[0].start();until(()->{for(int i=0;i<games.length;i++)if(online[i]&&!games[i].playing)return false;return true;},1500,"start");}
  void runFrames(int n){int target=engines[0].frame+n;until(()->{for(int i=0;i<games.length;i++)if(online[i]&&engines[i].frame<target)return false;return true;},20000,"frames");compare();}
  void compare(){for(int n:engines[0].trace.keySet())for(int i=1;i<engines.length;i++)if(online[i]&&engines[i].trace.containsKey(n))check(engines[0].trace.get(n).equals(engines[i].trace.get(n)),"world differs frame "+n+" peer "+i);}
 }
 public static void main(String[] args)throws Exception{
  Network mismatch=new Network(2,null,null);mismatch.games[0].connected(1,"Old version");
  String hello="{\"build\":"+(RoomProtocol.BUILD-1)+",\"name\":\"Old version\"}";
  mismatch.games[0].receive(1,RoomProtocol.pack(RoomProtocol.HELLO,0,0,0,hello.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
  check(mismatch.games[0].closed&&mismatch.games[0].status.contains("same StarDroid version"),"Older simulation build joined room");
  for(int n=2;n<=8;n++){
   Network net=new Network(n,null,null);net.lobby();check(net.games[0].joined()==n,"device count");
   check(net.games[n-1].setup.heroMode&&net.games[n-1].setup.teamGame,"Hero Mode and Teams reach every guest");int hostTeam=net.games[0].setup.teams[0];
   int destination=n<8?6:n-1;net.games[0].move(0,destination);net.until(()->net.games[0].ready&&net.engines[0].slot==destination,4000,"host move");
   check(net.games[0].occupants[destination]==0&&net.games[0].setup.teams[destination]==hostTeam,"host and team follow slot move");
   int guestSlot=net.games[1].localSlot;int before=net.games[1].setup.races[guestSlot];net.games[1].changeRace(guestSlot);net.until(()->net.games[0].ready&&net.games[1].setup.races[guestSlot]==(before+1)%3,4000,"guest race");
   net.games[n-1].say("こんにちは / Hello");net.until(()->net.games[0].chat.toString().contains("こんにちは"),500,"chat relay");
   net.games[0].start();for(int k=0;k<90;k++)net.step();net.pause[n-1]=true;net.until(()->net.games[0].countdown==0,500,"background cancels countdown");check(!net.games[0].playing,"cancelled start");net.pause[n-1]=false;for(int k=0;k<50;k++)net.step();
   int beeps=net.engines[0].countdowns;net.start();check(net.engines[0].countdowns-beeps==5,"five countdown beeps");int target=net.engines[0].frame+400;while(net.engines[0].frame<target){int[] prior=new int[n];for(int i=0;i<n;i++)prior[i]=net.engines[i].frame;net.step();for(int i=0;i<n;i++)check(net.engines[i].frame-prior[i]<=1,"Network waiting created a catch-up burst");}net.compare();
   net.pause[n-1]=true;for(int k=0;k<40;k++)net.step();int f=net.engines[0].frame;for(int k=0;k<40;k++)net.step();check(net.engines[0].frame==f,"guest pause");
   final byte[][] save={null};net.games[0].save(b->save[0]=b);net.until(()->save[0]!=null,3000,"paused save barrier");RoomSnapshot snapshot=RoomSnapshot.decode(save[0]);check(snapshot.hostSlot==destination,"saved host slot");check(snapshot.commands.length==8,"all accepted inputs saved");
   net.pause[n-1]=false;for(int k=0;k<40;k++)net.step();net.runFrames(80);
   MatchSetup settings=net.games[0].setup.copy();net.games[0].reload(net.map,"Saved test",true,settings,save[0]);net.until(()->net.games[0].ready,4000,"live saved reload");net.start();net.runFrames(100);
   Network fresh=new Network(n,save[0],settings);fresh.lobby();fresh.start();fresh.runFrames(100);
   if(n>=3){
    int gone=n-1,departedSlot=fresh.games[0].slotOf(gone);fresh.games[0].disconnected(gone);fresh.online[gone]=false;
    final byte[][] after={null};fresh.games[0].save(b->after[0]=b);fresh.until(()->after[0]!=null,3000,"save during departure");
    MatchSetup afterSetup=fresh.games[0].savedSetup();check(afterSetup.controllers[departedSlot]==0,"departed player closed in save");
    RoomSnapshot decoded=RoomSnapshot.decode(after[0]);check(decoded.commands[departedSlot].length==0,"departure already applied before save");
    fresh.runFrames(150);check(!fresh.games[0].closed,"remaining devices continue");
    Network fewer=new Network(n-1,after[0],afterSetup);fewer.lobby();fewer.start();fewer.runFrames(100);
    if(n>=4){MatchSetup tooSmall=afterSetup.copy();int removed=fewer.games[1].localSlot;tooSmall.controllers[removed]=0;int frame=fewer.engines[0].frame;
      try{fewer.games[0].reload(fewer.map,"Invalid load",true,tooSmall,after[0]);throw new AssertionError("Too-small save accepted");}catch(IOException expected){check(fewer.games[0].playing&&fewer.engines[0].frame==frame,"failed load leaves match running");}
      fewer.runFrames(32);
    }
   }
   System.out.println("PASS "+n+" devices: slots/races/chat/countdown/paused save/live reload/fresh restore/disconnect, "+checks+" checks");
  }
  for(byte[] b:new byte[][]{new byte[0],new byte[56],new byte[100]}){try{RoomSnapshot.decode(b);throw new AssertionError("bad snapshot accepted");}catch(IOException expected){checks++;}}
  System.out.println("PASS "+checks+" multi-device checks");
 }
}

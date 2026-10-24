package org.openbw.androidtest;
import java.io.*;import java.util.*;import java.nio.file.*;import org.json.*;

/** Production setup, transfer, scheduler and saved-turn restoration under delayed delivery. */
public final class Match54Test {
 static int checks;static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
 static class Engine implements NearbyMatch.Engine {
  long state;int frames,slot,started;boolean surrendered;String error="";MatchSetup setup;List<Integer> beeps=new ArrayList<>();Map<Integer,Long> trace=new TreeMap<>();
  public void configure(MatchSetup s)throws Exception{setup=s.copy();}
  public long[] prepare(byte[] map,int a,int b,int slot,boolean bw){this.slot=slot;frames=0;state=1234+setup.json().toString().hashCode();return new long[]{9876,state};}
  public byte[] collect(){return new byte[]{(byte)slot,(byte)frames};}
  public long hash(){return state;}
  public void apply(byte[] a,byte[] b){for(byte[] data:new byte[][]{a,b})for(byte v:data)state=state*31+(v&255);}
  public void step(){state=state*17+frames++;trace.put(frames,state);}
  public void started(){started++;}
  public void stopped(String s,boolean surrender){error=s;surrendered=surrender;}
  public void countdown(int n){if(n>0)beeps.add(n);}
  public byte[] snapshot()throws Exception {
   byte[] raw=new byte[260001];new Random(61).nextBytes(raw);ByteArrayOutputStream b=new ByteArrayOutputStream();DataOutputStream d=new DataOutputStream(b);d.writeLong(state);d.writeInt(frames);d.write(raw);return b.toByteArray();
  }
  public void restore(byte[] raw)throws Exception{DataInputStream d=new DataInputStream(new ByteArrayInputStream(raw));state=d.readLong();frames=d.readInt();}
 }
 static class Pair {
  long now;Engine a=new Engine(),b=new Engine();NearbyMatch host,guest;ArrayDeque<byte[]> toHost=new ArrayDeque<>(),toGuest=new ArrayDeque<>();byte[] map=new byte[120003];
  Pair(int guestRace)throws Exception {
   new Random(9).nextBytes(map);
   host=new NearbyMatch(true,1,"Host",a,new NearbyMatch.Link(){public void send(byte[] p){toGuest.add(p);}public void close(){}},null,()->now);
   guest=new NearbyMatch(false,guestRace,"Guest",b,new NearbyMatch.Link(){public void send(byte[] p){toHost.add(p);}public void close(){}},null,()->now);
  }
  void delivery(){if(!toGuest.isEmpty())guest.receive(toGuest.remove());if(!toHost.isEmpty())host.receive(toHost.remove());}
  void drain(){for(int i=0;i<10000&&(!toGuest.isEmpty()||!toHost.isEmpty());i++)delivery();}
  void healthy(){check(!host.closed&&!guest.closed,a.error+" / "+b.error);}
  void connect(MatchSetup s,byte[] state)throws Exception{host.hostSettings(s,state);host.hostMap(map,"Eight slots",true);host.connected();guest.connected();drain();healthy();check(host.ready&&guest.ready,"ready on both phones");}
  void countdown(){host.start();drain();check(!host.playing&&!guest.playing,"countdown does not start immediately");for(int i=0;i<4;i++){now+=1000;host.pulse(false);guest.pulse(false);drain();check(!host.playing,"five complete seconds required");}now+=1000;host.pulse(false);guest.pulse(false);drain();healthy();check(host.playing&&guest.playing,"starts after five seconds");}
  void tick(int n){for(int i=0;i<n;i++){now+=16;if(i%2==0)delivery();host.tick(16);guest.tick(16);if(i%60==0){host.pulse(false);guest.pulse(false);}healthy();}drain();}
 }
 public static void main(String[] args)throws Exception {
  MatchSetup s=new MatchSetup(true);s.starts=8;s.speed=4;s.freeForAll=true;for(int i=2;i<8;i++){s.controllers[i]=2;s.races[i]=i%3;}
  MatchSetup q=MatchSetup.read(s.json(),true);check(q.controllers[7]==2&&q.freeForAll&&q.frameMs()==56,"all setup settings round trip");
  JSONObject bad=s.json();bad.put("speed",7);boolean denied=false;try{MatchSetup.read(bad,true);}catch(Exception e){denied=true;}check(denied,"unbounded speed rejected");
  Pair p=new Pair(2);p.connect(s,null);check(p.b.setup.controllers[7]==2&&p.b.setup.freeForAll,"computer slots reach guest");p.countdown();check(p.a.beeps.equals(Arrays.asList(5,4,3,2,1))&&p.b.beeps.equals(p.a.beeps),"five original beep events on both peers");p.tick(401);
  p.host.pulse(true);p.drain();final byte[][] saved={null};p.host.save(bytes->saved[0]=bytes);
  for(int i=0;i<100&&saved[0]==null;i++){p.now+=16;p.delivery();p.host.tick(16);p.guest.tick(16);}
  p.healthy();check(saved[0]!=null,"save completes while menu is paused");int frame=p.a.frames;long hash=p.a.hash();check(frame%4==0,"save at complete native turn");
  MatchSnapshot snapshot=MatchSnapshot.decode(saved[0]);check(snapshot.first.length>0&&snapshot.second.length>0,"accepted commands saved for both players");
  p.host.pulse(false);p.drain();p.tick(601);Map<Integer,Long> expected=new TreeMap<>(p.a.trace);check(p.a.frames>frame+100,"continued original game");
  p.host.reload(p.map,"Resume",true,p.host.setup,saved[0]);p.drain();p.healthy();check(p.host.ready&&p.guest.ready&&p.a.frames==frame&&p.b.frames==frame&&p.a.hash()==hash&&p.b.hash()==hash,"in-session reload restores exact world on both peers");
  p.a.trace.clear();p.countdown();p.tick(601);for(Map.Entry<Integer,Long> e:p.a.trace.entrySet())if(expected.containsKey(e.getKey()))check(expected.get(e.getKey()).equals(e.getValue()),"continuation differs at "+e.getKey());
  Pair fresh=new Pair(0);fresh.connect(p.host.setup,saved[0]);check(fresh.b.setup.races[1]==2&&fresh.a.frames==frame&&fresh.b.frames==frame,"fresh lobby preserves saved guest race and frame");fresh.countdown();fresh.tick(200);
  fresh.host.finish();fresh.host.leave();fresh.drain();fresh.guest.disconnected();check(fresh.b.surrendered,"Eliminated human can leave while surviving human continues against computers");
  byte[] corrupt=saved[0].clone();corrupt[4]=127;denied=false;try{MatchSnapshot.decode(corrupt);}catch(IOException e){denied=true;}check(denied,"invalid snapshot allocation rejected");
  Pair cancel=new Pair(2);cancel.connect(s,null);cancel.host.start();cancel.drain();cancel.now+=1200;cancel.host.pulse(true);cancel.drain();check(cancel.host.countdown==0&&!cancel.host.playing&&cancel.guest.countdown==0,"background cancels countdown");
  System.out.println("PASS "+checks+" checks: shared AI/FFA/speed settings; countdown and cancellation; paused save; accepted commands; reload handshake; exact continuation; new-session restore; bounded snapshots");
 }
}

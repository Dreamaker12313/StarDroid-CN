package org.openbw.androidtest;

import java.nio.*;
import java.nio.file.*;
import java.util.*;
import org.json.*;

/** Frame spacing, not just aggregate throughput, on a reproducible ordered link. */
public final class NearbyPacingTest {
  static int checks;
  static void check(boolean ok,String message){checks++;if(!ok)throw new AssertionError(message);}
  static final class Time implements NearbyMatch.Clock,NearbyMatch51.Clock {
    long value=10000;public long now(){return value;}
  }
  static final class Engine implements NearbyMatch.Engine,NearbyMatch51.Engine {
    final Time time;int frames,slot,sequence;long state=1234,lastStep=-1;String failure="";
    final int[] applied={0,0};final TreeMap<Integer,Long> checkpoints=new TreeMap<Integer,Long>();
    Engine(Time t){time=t;}
    public long[] prepare(byte[] map,int a,int b,int s,boolean expansion){slot=s;return new long[]{9876,state};}
    public byte[] collect(){return ByteBuffer.allocate(8).putInt(slot).putInt(++sequence).array();}
    public long hash(){return state;}
    public void apply(byte[] a,byte[] b){
      for(byte[] data:new byte[][]{a,b})if(data.length>0){
        ByteBuffer in=ByteBuffer.wrap(data);int player=in.getInt(),command=in.getInt();
        check(command==++applied[player],"commands applied once and in order");
        state=state*31+player;state=state*31+command;
      }
    }
    public void step(){state=state*17+frames;frames++;lastStep=time.value;if(frames%4==0)checkpoints.put(frames,state);}
    public void started(){}public void stopped(String why,boolean surrender){failure=why;}
  }
  static final class Delivery implements Comparable<Delivery> {
    final long at,serial;final int peer;final byte[] packet;
    Delivery(long a,long s,int p,byte[] b){at=a;serial=s;peer=p;packet=b;}
    public int compareTo(Delivery d){int n=Long.compare(at,d.at);return n!=0?n:Long.compare(serial,d.serial);}
  }
  static final class Stats {
    int frames,draws,multi,maxSteps,maxGap;long last=-1;
    void draw(long now,int steps){
      draws++;frames+=steps;maxSteps=Math.max(maxSteps,steps);if(steps>1)multi++;
      if(steps>0){if(last>=0)maxGap=Math.max(maxGap,(int)(now-last));last=now;}
    }
    JSONObject json(int elapsed){return new JSONObject().put("gameSpeedPercent",frames*4200.0/elapsed)
        .put("multiStepDraws",multi).put("maxStepsPerDraw",maxSteps).put("longestStepGapMs",maxGap).put("draws",draws);}
  }
  static final class Pair {
    final boolean improved;final Time time=new Time();final Engine[] engines={new Engine(time),new Engine(time)};
    final NearbyMatch[] match=new NearbyMatch[2];final NearbyMatch51[] baseline=new NearbyMatch51[2];
    final PriorityQueue<Delivery> wire=new PriorityQueue<Delivery>();final Random random=new Random(52);
    final long[] deliveryAt={0,0},heldUntil={0,0},nextDraw={0,0},lastDraw={-1,-1};
    final boolean[] paused={false,false};int delay=30,jitter=20;long serial;
    Pair(boolean updated,int hostDelay,int guestDelay)throws Exception {
      improved=updated;
      for(int i=0;i<2;i++){
        final int from=i;
        if(updated)match[i]=new NearbyMatch(i==0,i,"Player",engines[i],new NearbyMatch.Link(){public void send(byte[] b){queue(from,b);}public void close(){}},null,time);
        else baseline[i]=new NearbyMatch51(i==0,i,"Player",engines[i],new NearbyMatch51.Link(){public void send(byte[] b){queue(from,b);}public void close(){}},null,time);
      }
      if(updated){match[0].hostMap(new byte[1000],"Pacing map",true);match[0].connected();match[1].connected();}
      else{baseline[0].hostMap(new byte[1000],"Pacing map",true);baseline[0].connected();baseline[1].connected();}
      for(int i=0;i<10000 && !ready();i++){deliver();time.value++;}
      check(ready(),"both map preparations finish");
      if(updated)match[0].start();else baseline[0].start();
      heldUntil[0]=time.value+hostDelay;heldUntil[1]=time.value+guestDelay;
      nextDraw[0]=nextDraw[1]=time.value;
    }
    boolean ready(){return improved?match[0].ready&&match[1].ready:baseline[0].ready&&baseline[1].ready;}
    boolean playing(int p){return improved?match[p].playing:baseline[p].playing;}
    void queue(int from,byte[] b){
      long arrival=time.value+Math.max(0,delay+(jitter==0?0:random.nextInt(2*jitter+1)-jitter));
      arrival=Math.max(arrival,deliveryAt[from]);deliveryAt[from]=arrival;
      wire.add(new Delivery(arrival,serial++,1-from,b.clone()));
    }
    void deliver(){while(!wire.isEmpty() && wire.peek().at<=time.value){Delivery d=wire.remove();if(improved)match[d.peer].receive(d.packet);else baseline[d.peer].receive(d.packet);}}
    Stats[] run(int duration,int hostCadence,int guestCadence){
      Stats[] stats={new Stats(),new Stats()};int[] cadence={hostCadence,guestCadence};long end=time.value+duration;
      while(time.value<end){
        deliver();
        for(int i=0;i<2;i++)if(time.value>=nextDraw[i]){
          nextDraw[i]+=cadence[i];
          if(time.value<heldUntil[i] || !playing(i))continue;
          int before=engines[i].frames;double elapsed=lastDraw[i]<0?0:Math.min(100,time.value-lastDraw[i]);lastDraw[i]=time.value;
          if(improved){match[i].pulse(paused[i]);match[i].tick(elapsed);}else{baseline[i].pulse(paused[i]);baseline[i].tick(elapsed);}
          stats[i].draw(time.value,engines[i].frames-before);
        }
        deliver();time.value++;
        check(engines[0].failure.isEmpty()&&engines[1].failure.isEmpty(),"no desync/disconnect: "+engines[0].failure+" / "+engines[1].failure);
        check(Math.abs(engines[0].frames-engines[1].frames)<=8,"peer lead stays bounded");
      }
      return stats;
    }
    void consistent(){
      for(Map.Entry<Integer,Long> entry:engines[0].checkpoints.entrySet()){
        Long peer=engines[1].checkpoints.get(entry.getKey());if(peer!=null)check(peer.equals(entry.getValue()),"equal states at frame "+entry.getKey());
      }
    }
  }
  static void smooth(Stats[] stats,int duration,int cadence,String scenario){
    for(int i=0;i<2;i++){
      check(stats[i].multi==0,scenario+" peer "+i+" must not keep bursting: "+stats[i].multi);
      check(stats[i].maxGap<=42+cadence,scenario+" peer "+i+" step gaps: "+stats[i].maxGap);
      check(stats[i].frames*4200.0/duration>=97,scenario+" peer "+i+" keeps Fastest speed");
    }
  }
  public static void main(String[] args)throws Exception {
    Path output=Paths.get(args[0]);Files.createDirectories(output);JSONArray scenarios=new JSONArray();
    Pair before=new Pair(false,0,600),after=new Pair(true,0,600);
    before.run(3000,16,16);after.run(3000,16,16);
    Stats[] old=before.run(15000,16,16),fixed=after.run(15000,16,16);before.consistent();after.consistent();
    check(old[0].multi>50 && old[1].multi==0,"0.51 reproduces host-only frame bursts after a late guest start");
    check(before.baseline[0].summary().contains("Wait 100%"),"0.51 reproduces the supplied 100% wait diagnosis");
    smooth(fixed,15000,16,"late guest start");check(after.match[0].summary().contains("Wait 0%"),"host wait ends after recovery");
    scenarios.put(new JSONObject().put("case","Guest starts 600 ms late; 60 ms RTT with +/-20 ms one-way jitter")
        .put("baselineHost",old[0].json(15000)).put("baselineGuest",old[1].json(15000))
        .put("fixedHost",fixed[0].json(15000)).put("fixedGuest",fixed[1].json(15000)));

    for(int[] scenario:new int[][]{{0,0,16,16},{0,300,16,16},{0,1000,16,33},{600,0,16,16},{0,600,33,16},{0,600,8,16}}){
      Pair p=new Pair(true,scenario[0],scenario[1]);p.run(4000,scenario[2],scenario[3]);
      Stats[] steady=p.run(10000,scenario[2],scenario[3]);smooth(steady,10000,Math.max(scenario[2],scenario[3]),Arrays.toString(scenario));p.consistent();
      scenarios.put(new JSONObject().put("case",Arrays.toString(scenario)).put("host",steady[0].json(10000)).put("guest",steady[1].json(10000)));
    }
    // A later loading stall must not leave either peer permanently bursty.
    after.heldUntil[1]=after.time.value+700;after.run(4000,16,16);smooth(after.run(10000,16,16),10000,16,"mid-match stall");after.consistent();
    // Backgrounded phones have no render ticks; pause/resume must still clear timing.
    after.match[0].pulse(true);after.paused[0]=true;after.heldUntil[0]=after.time.value+2000;
    after.run(1500,16,16);int a=after.engines[0].frames,b=after.engines[1].frames;
    after.run(400,16,16);check(after.engines[0].frames==a && after.engines[1].frames==b,"background pause freezes both peers");
    after.paused[0]=false;after.match[0].pulse(false);after.run(3000,16,16);smooth(after.run(10000,16,16),10000,16,"background resume");after.consistent();
    // The fix changes wall-time debt only; it never invents missing commands.
    after.wire.clear();int stoppedAt=after.engines[0].frames;
    for(int i=0;i<500;i++){after.time.value+=16;after.match[0].tick(16);}
    check(after.engines[0].frames-stoppedAt<=8,"absent inputs still stop simulation");
    check(after.match[0].diagnostics().contains("Recent pacing:") && after.match[0].diagnostics().contains("Pacing recoveries:"),"pacing diagnostics expose bursts and recovery");
    JSONObject result=new JSONObject().put("version","0.54").put("passed",true).put("checks",checks)
        .put("physicalPhones",false).put("model","Production 0.51 versus 0.54; deterministic engine, ordered delayed link, simulated startup and display cadence")
        .put("scenarios",scenarios);
    Files.write(output.resolve("pacing.json"),result.toString(2).getBytes("UTF-8"));
    System.out.println("PASS "+checks+" pacing assertions\n"+scenarios.getJSONObject(0).toString(2));
  }
}

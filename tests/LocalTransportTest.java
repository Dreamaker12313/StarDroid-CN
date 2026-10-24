package org.openbw.androidtest;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import java.nio.ByteBuffer;

public final class LocalTransportTest {
  static int checks;static final byte[] SECRET=LocalTransport.random(32);
  static void check(boolean ok,String what){checks++;if(!ok)throw new AssertionError(what);}
  interface Task{void run()throws Exception;}
  static void rejects(Task t,String what)throws Exception{boolean rejected=false;try{t.run();}catch(Exception e){rejected=true;}check(rejected,what);}
  static byte[] number(int n){return ByteBuffer.allocate(4).putInt(n).array();}
  static Socket[] sockets()throws Exception{
    try(ServerSocket server=new ServerSocket(0,1,InetAddress.getLoopbackAddress())){
      Socket client=new Socket(InetAddress.getLoopbackAddress(),server.getLocalPort()),host=server.accept();
      client.setSoTimeout(3000);host.setSoTimeout(3000);client.setTcpNoDelay(true);host.setTcpNoDelay(true);return new Socket[]{host,client};
    }
  }
  static void codec()throws Exception{
    LocalTransport.Codec enc=new LocalTransport.Codec(SECRET,"host"),dec=new LocalTransport.Codec(SECRET,"host");
    Random random=new Random(48);byte[] last=null;
    for(int i=0;i<150;i++){
      byte[] b=new byte[i%3==0?LocalTransport.MAX:random.nextInt(300)];random.nextBytes(b);
      last=enc.encode(new LocalTransport.Frame(LocalTransport.DATA,i,b));LocalTransport.Frame f=dec.decode(last);
      check(f.sequence==i && Arrays.equals(b,f.data),"Encrypted frame round trip");
    }
    final byte[] replay=last;rejects(()->dec.decode(replay),"Encrypted replay rejected");
    byte[] wire=new LocalTransport.Codec(SECRET,"host").encode(new LocalTransport.Frame(1,0,number(7)));
    rejects(()->new LocalTransport.Codec(SECRET,"guest").decode(wire),"Wrong direction rejected");
    rejects(()->new LocalTransport.Codec(LocalTransport.random(32),"host").decode(wire),"Wrong session rejected");
    wire[wire.length-1]^=1;rejects(()->new LocalTransport.Codec(SECRET,"host").decode(wire),"Tampering rejected");
    rejects(()->enc.encode(new LocalTransport.Frame(1,0,new byte[LocalTransport.MAX+1])),"Oversized payload rejected");
    rejects(()->dec.decode(new byte[LocalTransport.MAX+22]),"Oversized ciphertext rejected");
  }
  static void handshakes()throws Exception{
    ExecutorService work=Executors.newFixedThreadPool(2);
    try{
      Socket[] s=sockets();
      Future<LocalTransport.Pair> a=work.submit(()->LocalTransport.bluetooth(s[0].getInputStream(),s[0].getOutputStream(),true,"Host",true));
      Future<LocalTransport.Pair> b=work.submit(()->LocalTransport.bluetooth(s[1].getInputStream(),s[1].getOutputStream(),false,"Guest",false));
      LocalTransport.Pair x=a.get(5,TimeUnit.SECONDS),y=b.get(5,TimeUnit.SECONDS);
      check(Arrays.equals(x.secret,y.secret) && x.code().equals(y.code()),"Pairing secrets and codes agree");
      check(x.name.equals("Guest") && y.name.equals("Host") && !x.wifi && y.wifi,"Name and capability negotiation");
      s[0].close();s[1].close();
      byte[] previous=null;
      for(int i=0;i<2;i++){
        Socket[] w=sockets();
        Future<byte[]> h=work.submit(()->LocalTransport.wifi(w[0].getInputStream(),w[0].getOutputStream(),x.secret,true));
        Future<byte[]> g=work.submit(()->LocalTransport.wifi(w[1].getInputStream(),w[1].getOutputStream(),y.secret,false));
        byte[] hk=h.get(5,TimeUnit.SECONDS),gk=g.get(5,TimeUnit.SECONDS);
        check(Arrays.equals(hk,gk),"Authenticated Wi-Fi key agrees");
        check(!Arrays.equals(previous,hk),"Each Wi-Fi stream gets a distinct key");previous=hk;w[0].close();w[1].close();
      }
      Socket[] bad=sockets();
      Future<byte[]> h=work.submit(()->{try{return LocalTransport.wifi(bad[0].getInputStream(),bad[0].getOutputStream(),x.secret,true);}finally{bad[0].close();}});
      Future<byte[]> g=work.submit(()->{try{return LocalTransport.wifi(bad[1].getInputStream(),bad[1].getOutputStream(),LocalTransport.random(32),false);}finally{bad[1].close();}});
      rejects(()->h.get(5,TimeUnit.SECONDS),"Unpaired Wi-Fi client rejected");rejects(()->g.get(5,TimeUnit.SECONDS),"Wrong Wi-Fi session cannot connect");
    }finally{work.shutdownNow();}
  }
  static final class Message {final int to,lane;final LocalTransport.Frame frame;Message(int t,int l,LocalTransport.Frame f){to=t;lane=l;frame=f;}}
  static final class Model {
    final ArrayList<Message> queue=new ArrayList<Message>();final ArrayList<Integer>[] delivered=new ArrayList[]{new ArrayList<Integer>(),new ArrayList<Integer>()};
    final LocalTransport.Reliable[] peers=new LocalTransport.Reliable[2];long time=100;
    Model(){for(int i=0;i<2;i++){final int p=i;peers[i]=new LocalTransport.Reliable(b->delivered[p].add(ByteBuffer.wrap(b).getInt()));}}
    void attach(int lane)throws Exception{for(int i=0;i<2;i++){final int p=i;peers[i].attach(lane,new LocalTransport.Sender(){public void send(LocalTransport.Frame f){queue.add(new Message(1-p,lane,f));}public void close(){}},time);}}
    void drain(boolean reverse)throws Exception{
      int guard=10000;while(!queue.isEmpty()){check(--guard>0,"Acknowledgements terminate");Message m=queue.remove(reverse?queue.size()-1:0);peers[m.to].receive(m.lane,m.frame,++time);}
    }
  }
  static void handover()throws Exception{
    Model m=new Model();m.attach(0);
    for(int i=0;i<20;i++){m.peers[0].send(number(i),m.time);m.peers[1].send(number(1000+i),m.time);}
    // Wi-Fi activates while old Bluetooth packets are still in flight.
    m.attach(1);m.drain(true);
    for(int i=0;i<20;i++){check(m.delivered[1].get(i)==i,"Handover preserves order");check(m.delivered[0].get(i)==1000+i,"Reverse direction order");}
    check(m.delivered[1].size()==20 && m.peers[0].pending()==0,"Duplicates delivered once and acknowledged");
    for(int i=20;i<40;i++)m.peers[0].send(number(i),m.time);
    m.queue.clear();check(m.peers[0].wifiStalled(m.time+4001),"Silent Wi-Fi stall detected");
    m.peers[0].detach(1,m.time);m.peers[1].detach(1,m.time);m.drain(false);
    for(int i=0;i<40;i++)check(m.delivered[1].get(i)==i,"Lost Wi-Fi packets replay through Bluetooth");
    check(m.peers[0].route()==0 && m.peers[0].pending()==0,"Bluetooth fallback complete");
    rejects(()->m.peers[0].receive(0,new LocalTransport.Frame(2,9999,new byte[0]),m.time),"Future acknowledgement rejected");
    rejects(()->m.peers[1].receive(0,new LocalTransport.Frame(1,104,new byte[0]),m.time),"Far future input rejected");
    m.peers[0].detach(0,m.time);check(m.peers[0].route()==-1,"Both links lost");
    rejects(()->m.peers[0].send(number(40),m.time),"Cannot send after all links lost");
    Model full=new Model();full.attach(0);for(int i=0;i<64;i++)full.peers[0].send(number(i),0);
    rejects(()->full.peers[0].send(number(64),0),"Unacknowledged queue is bounded");
    Model conflict=new Model();conflict.attach(0);conflict.peers[1].receive(0,new LocalTransport.Frame(1,1,number(1)),0);
    rejects(()->conflict.peers[1].receive(0,new LocalTransport.Frame(1,1,number(2)),0),"Conflicting duplicate rejected");
    Model stale=new Model();stale.attach(0);stale.attach(1);stale.peers[0].send(number(0),100);
    stale.peers[0].receive(0,new LocalTransport.Frame(2,-1,new byte[0]),4000);check(stale.peers[0].wifiStalled(4200),"Stale ACK does not hide a stall");
  }
  static void writerFailure()throws Exception{
    Model m=new Model();m.attach(0);
    m.peers[0].attach(1,new LocalTransport.Sender(){
      public void send(LocalTransport.Frame f)throws IOException{throw new IOException("Wi-Fi writer already closed");}
      public void close(){}
    },m.time);
    m.peers[0].send(number(17),m.time);m.drain(false);
    check(m.peers[0].route()==0,"Writer failure switches to Bluetooth before ended callback");
    check(m.delivered[1].equals(Arrays.asList(17)),"Failed send delivered exactly once through standby");
    check(m.peers[0].pending()==0,"Fallback send acknowledged");
    m.peers[0].send(number(18),m.time);m.drain(false);
    check(m.delivered[1].equals(Arrays.asList(17,18)),"Later send uses next sequence without a gap");
  }
  static void pipes()throws Exception{
    Socket[] s=sockets();Queue<Runnable> callbacks=new ConcurrentLinkedQueue<Runnable>();
    ArrayList<Integer> received=new ArrayList<Integer>();boolean[] ended={false};
    LocalTransport.Pipe host=new LocalTransport.Pipe(s[0].getInputStream(),s[0].getOutputStream(),s[0],SECRET,true,callbacks::add,new LocalTransport.StreamListener(){public void frame(LocalTransport.Frame f){}public void ended(){}});
    LocalTransport.Pipe guest=new LocalTransport.Pipe(s[1].getInputStream(),s[1].getOutputStream(),s[1],SECRET,false,callbacks::add,new LocalTransport.StreamListener(){public void frame(LocalTransport.Frame f){received.add(f.sequence);}public void ended(){ended[0]=true;}});
    host.start();guest.start();for(int i=0;i<80;i++)host.send(new LocalTransport.Frame(1,i,new byte[i==79?LocalTransport.MAX:100]));
    long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(5);
    while(received.size()<80 && System.nanoTime()<deadline){Runnable r=callbacks.poll();if(r!=null)r.run();else Thread.sleep(1);}
    check(received.size()==80,"Real socket encrypted stream delivers all frames");for(int i=0;i<80;i++)check(received.get(i)==i,"Real socket order");
    host.close();deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);
    while(!ended[0] && System.nanoTime()<deadline){Runnable r=callbacks.poll();if(r!=null)r.run();else Thread.sleep(1);}
    check(ended[0],"Socket EOF reports disconnection");guest.close();
    // Deliberately postpone callbacks until after EOF: valid final messages must survive.
    Socket[] last=sockets();Queue<Runnable> pending=new ConcurrentLinkedQueue<Runnable>();ArrayList<Integer> events=new ArrayList<Integer>();
    LocalTransport.Pipe read=new LocalTransport.Pipe(last[1].getInputStream(),last[1].getOutputStream(),last[1],SECRET,false,pending::add,new LocalTransport.StreamListener(){public void frame(LocalTransport.Frame f){events.add(f.sequence);}public void ended(){events.add(-1);}});read.start();
    DataOutputStream out=new DataOutputStream(last[0].getOutputStream());LocalTransport.Codec c=new LocalTransport.Codec(SECRET,"host to guest");
    for(int i=0;i<3;i++){byte[] b=c.encode(new LocalTransport.Frame(1,i,number(i)));out.writeInt(b.length);out.write(b);}out.flush();last[0].close();
    deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);while(pending.size()<4 && System.nanoTime()<deadline)Thread.sleep(1);
    Runnable task;while((task=pending.poll())!=null)task.run();check(events.equals(Arrays.asList(0,1,2,-1)),"Final messages delivered before EOF callback");read.close();
  }
  public static void main(String[] args)throws Exception{codec();handshakes();handover();writerFailure();pipes();System.out.println("PASS "+checks+" local transport checks: encrypted sockets, pairing, Wi-Fi authentication, handover, fallback, ordering, bounds and EOF");}
}

package org.openbw.androidtest;

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.crypto.*;
import javax.crypto.spec.*;

/** Android-independent authenticated streams and ordered Bluetooth/Wi-Fi handover. */
final class LocalTransport {
  static final int MAGIC=0x4f42574c, VERSION=1, MAX=NearbyProtocol.MAX_BODY+26;
  static final int DATA=1, ACK=2, CONTROL=3, PING=4;
  static final SecureRandom RANDOM=new SecureRandom();
  static byte[] random(int n){byte[] b=new byte[n];RANDOM.nextBytes(b);return b;}
  static byte[] mac(byte[] key,byte[] data)throws GeneralSecurityException{
    Mac m=Mac.getInstance("HmacSHA256");m.init(new SecretKeySpec(key,"HmacSHA256"));return m.doFinal(data);
  }
  static byte[] key(byte[] secret,String label)throws GeneralSecurityException{return mac(secret,label.getBytes(StandardCharsets.UTF_8));}
  static void text(DataOutputStream out,String s)throws IOException{
    byte[] b=NearbyProtocol.name(s).getBytes(StandardCharsets.UTF_8);out.writeShort(b.length);out.write(b);
  }
  static String text(DataInputStream in)throws IOException{
    int n=in.readUnsignedShort();if(n>128)throw new IOException("Invalid device name");byte[] b=new byte[n];in.readFully(b);return NearbyProtocol.name(new String(b,StandardCharsets.UTF_8));
  }
  static final class Pair {
    final byte[] secret;final String name;final boolean wifi;
    Pair(byte[] s,String n,boolean w){secret=s;name=n;wifi=w;}
    String code()throws GeneralSecurityException{
      int n=ByteBuffer.wrap(key(secret,"OpenBW pairing code")).getInt()&0x7fffffff;
      return String.format(Locale.US,"%06d",n%1000000);
    }
  }
  // Only used on Android's secure, authenticated RFCOMM socket. Android owns bonding.
  static Pair bluetooth(InputStream input,OutputStream output,boolean host,String name,boolean wifi)throws IOException{
    DataInputStream in=new DataInputStream(input);DataOutputStream out=new DataOutputStream(output);
    out.writeInt(MAGIC);out.writeInt(VERSION);out.writeBoolean(host);out.writeBoolean(wifi);text(out,name);out.flush();
    if(in.readInt()!=MAGIC || in.readInt()!=VERSION || in.readBoolean()==host)throw new IOException("This device is not hosting a compatible StarDroid game");
    boolean peerWifi=in.readBoolean();String peer=text(in);byte[] secret;
    if(host){secret=random(32);out.write(secret);out.flush();}else{secret=new byte[32];in.readFully(secret);}
    return new Pair(secret,peer,peerWifi);
  }
  // A fresh challenge binds the Wi-Fi stream to the already confirmed Bluetooth session.
  static byte[] wifi(InputStream input,OutputStream output,byte[] secret,boolean host)throws Exception{
    DataInputStream in=new DataInputStream(input);DataOutputStream out=new DataOutputStream(output);
    byte[] nonce=new byte[32],proof=new byte[32];
    if(host){
      if(in.readInt()!=MAGIC || in.readInt()!=VERSION)throw new IOException("Invalid Wi-Fi handshake");
      in.readFully(nonce);in.readFully(proof);
      if(!MessageDigest.isEqual(proof,mac(key(secret,"Wi-Fi client"),nonce)))throw new IOException("Wi-Fi authentication failed");
      out.write(mac(key(secret,"Wi-Fi host"),nonce));out.flush();
    }else{
      RANDOM.nextBytes(nonce);out.writeInt(MAGIC);out.writeInt(VERSION);out.write(nonce);out.write(mac(key(secret,"Wi-Fi client"),nonce));out.flush();
      in.readFully(proof);if(!MessageDigest.isEqual(proof,mac(key(secret,"Wi-Fi host"),nonce)))throw new IOException("Wi-Fi authentication failed");
    }
    return mac(key(secret,"Wi-Fi stream"),nonce);
  }
  static final class Frame {
    final int type,sequence;final byte[] data;
    Frame(int t,int s,byte[] b){type=t;sequence=s;data=b.clone();}
  }
  static final class Codec {
    private final byte[] key;private long sequence;
    Codec(byte[] secret,String direction)throws Exception{key=LocalTransport.key(secret,direction);}
    private Cipher cipher(int mode)throws Exception{
      if(sequence==Long.MAX_VALUE)throw new IOException("Connection sequence exhausted");
      Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(mode,new SecretKeySpec(key,"AES"),new GCMParameterSpec(128,ByteBuffer.allocate(12).putInt(MAGIC).putLong(sequence).array()));return c;
    }
    byte[] encode(Frame f)throws Exception{
      if(f.data.length>MAX || f.type<DATA || f.type>PING)throw new IOException("Invalid local packet");
      byte[] plain=ByteBuffer.allocate(5+f.data.length).put((byte)f.type).putInt(f.sequence).put(f.data).array();
      byte[] b=cipher(Cipher.ENCRYPT_MODE).doFinal(plain);sequence++;return b;
    }
    Frame decode(byte[] b)throws Exception{
      if(b.length<21 || b.length>MAX+21)throw new IOException("Invalid encrypted packet size");
      byte[] plain=cipher(Cipher.DECRYPT_MODE).doFinal(b);sequence++;
      ByteBuffer p=ByteBuffer.wrap(plain);int type=p.get()&255,seq=p.getInt();byte[] data=new byte[p.remaining()];p.get(data);
      if(type<DATA || type>PING)throw new IOException("Invalid local packet type");return new Frame(type,seq,data);
    }
  }
  interface StreamListener {void frame(Frame f);void ended();}
  interface Sender {void send(Frame f)throws IOException;void close();}
  static final class Pipe implements Sender {
    private final DataInputStream in;private final DataOutputStream out;private final Closeable socket;
    private final Codec encoder,decoder;private final StreamListener listener;private final Executor callbacks;
    private final ArrayBlockingQueue<Frame> queue=new ArrayBlockingQueue<Frame>(128);
    private final AtomicBoolean closed=new AtomicBoolean(),cancelled=new AtomicBoolean();
    private final Semaphore callbacksPending=new Semaphore(128);private Thread reader,writer;
    Pipe(InputStream i,OutputStream o,Closeable s,byte[] secret,boolean host,Executor e,StreamListener l)throws Exception{
      in=new DataInputStream(i);out=new DataOutputStream(o);socket=s;callbacks=e;listener=l;
      encoder=new Codec(secret,host?"host to guest":"guest to host");decoder=new Codec(secret,host?"guest to host":"host to guest");
    }
    void start(){
      reader=new Thread(()->{try{while(!closed.get()){
        int n=in.readInt();if(n<21 || n>MAX+21)throw new IOException("Invalid local frame length");
        byte[] b=new byte[n];in.readFully(b);Frame f=decoder.decode(b);
        if(!callbacksPending.tryAcquire())throw new IOException("Local receiver cannot keep up");
        callbacks.execute(()->{try{if(!cancelled.get())listener.frame(f);}finally{callbacksPending.release();}});
      }}catch(Exception e){end();}},"StarDroid local reader");
      writer=new Thread(()->{try{while(!closed.get()){
        byte[] b=encoder.encode(queue.take());out.writeInt(b.length);out.write(b);out.flush();
      }}catch(Exception e){end();}},"StarDroid local writer");
      reader.setDaemon(true);writer.setDaemon(true);reader.start();writer.start();
    }
    public void send(Frame f)throws IOException{if(closed.get() || !queue.offer(f))throw new IOException("Local connection cannot keep up");}
    private void end(){if(closed.compareAndSet(false,true)){shutdown();callbacks.execute(listener::ended);}}
    public void close(){cancelled.set(true);if(closed.compareAndSet(false,true))shutdown();}
    private void shutdown(){try{socket.close();}catch(Exception ignored){}if(writer!=null)writer.interrupt();queue.clear();}
  }
  interface Delivery {void packet(byte[] b);}
  /** Called on one owner thread. Packets are acknowledged only after ordered delivery. */
  static final class Reliable {
    private final Sender[] lanes=new Sender[2];private final Delivery delivery;
    private final TreeMap<Integer,byte[]> unacked=new TreeMap<Integer,byte[]>(),waiting=new TreeMap<Integer,byte[]>();
    private int sent,received;private long oldest;
    Reliable(Delivery d){delivery=d;}
    boolean active(int lane){return lanes[lane]!=null;}
    int route(){return active(1)?1:active(0)?0:-1;}
    int pending(){return unacked.size();}
    void attach(int lane,Sender sender,long now)throws IOException{
      if(lanes[lane]!=null)throw new IOException("Duplicate local link");lanes[lane]=sender;replay(now);
    }
    void detach(int lane,long now)throws IOException{
      Sender old=lanes[lane];lanes[lane]=null;if(old!=null)old.close();if(route()>=0)replay(now);
    }
    private void replay(long now)throws IOException{
      if(route()<0)return;for(Map.Entry<Integer,byte[]> e:unacked.entrySet())lanes[route()].send(new Frame(DATA,e.getKey(),e.getValue()));oldest=now;
    }
    void send(byte[] data,long now)throws IOException{
      if(data.length>MAX || sent==Integer.MAX_VALUE || unacked.size()>=64 || route()<0)throw new IOException("Local connection cannot keep up");
      if(unacked.isEmpty())oldest=now;byte[] copy=data.clone();int seq=sent++;unacked.put(seq,copy);
      int lane=route();
      try{lanes[lane].send(new Frame(DATA,seq,copy));}
      catch(IOException e){
        // The Wi-Fi writer can stop before its ended callback runs. The packet
        // is already owned here: replay it through standby without allocating
        // another sequence or dropping the match.
        if(lane==1 && active(0))detach(1,now);else throw e;
      }
    }
    void receive(int lane,Frame f,long now)throws IOException{
      if(f.type==ACK){
        if(f.data.length!=0 || f.sequence< -1 || f.sequence>=sent)throw new IOException("Invalid local acknowledgement");
        int before=unacked.size();unacked.headMap(f.sequence,true).clear();if(before!=unacked.size())oldest=now;return;
      }
      if(f.type!=DATA || f.sequence<0 || f.sequence>(long)received+63 || f.data.length>MAX)throw new IOException("Invalid local packet order");
      if(f.sequence>=received){
        byte[] old=waiting.get(f.sequence);if(old!=null && !Arrays.equals(old,f.data))throw new IOException("Conflicting local packet");
        waiting.put(f.sequence,f.data);
        while(waiting.containsKey(received)){delivery.packet(waiting.remove(received));received++;}
      }
      // EOF can follow a valid final frame before its callback runs. Deliver all
      // queued frames first; the stream's ordered ended callback owns failover.
      if(lanes[lane]!=null)try{lanes[lane].send(new Frame(ACK,received-1,new byte[0]));}catch(IOException disconnected){}
    }
    boolean wifiStalled(long now){return active(1) && active(0) && !unacked.isEmpty() && now-oldest>4000;}
    void close(){for(Sender lane:lanes)if(lane!=null)lane.close();Arrays.fill(lanes,null);unacked.clear();waiting.clear();}
  }
}

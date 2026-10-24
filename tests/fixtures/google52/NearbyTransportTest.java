package org.openbw.androidtest;

import android.app.AlertDialog;
import android.os.*;
import com.google.android.gms.common.GoogleApiAvailability;
import com.google.android.gms.nearby.Nearby;
import com.google.android.gms.nearby.connection.*;
import java.nio.*;
import java.util.*;

/** Real NativeNearby sender/reordering logic with explicit fake GMS callbacks. */
public final class NearbyTransportTest {
  static int checks;
  static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
  static final class Events implements NativeNearby.Listener {
    final ArrayList<byte[]> received=new ArrayList<byte[]>();String failure="";int connections;
    public void status(String s){}public void failed(String s){failure=s;}public void found(String a,String b){}public void lost(String a){}
    public void connected(){connections++;}public void disconnected(){}public void received(byte[] b){received.add(b);}
  }
  static final class Fixture {
    final NativeNearby radio;final ConnectionsClient client;final Events events=new Events();
    Fixture(){
      Build.VERSION.SDK_INT=36;GoogleApiAvailability.result=0;Handler.delayed.clear();Nearby.client=client=new ConnectionsClient();
      MainActivity a=new MainActivity();a.granted.addAll(NearbyPermissionsTest.expected(36));radio=new NativeNearby(a,events);
      radio.start(false,"Guest");radio.join("peer");client.lifecycle.onConnectionInitiated("peer",new ConnectionInfo());
      AlertDialog.latest.confirm();client.lifecycle.onConnectionResult("peer",new ConnectionResolution());
      check(events.connections==1 && client.payloads!=null,"confirmed endpoint ready");
    }
    void send(int n)throws Exception{radio.send(NearbyProtocol.pack(NearbyProtocol.PING,n,0,NearbyProtocol.EMPTY));}
    void complete(int i){Payload p=client.sent.get(i);client.payloads.onPayloadTransferUpdate("peer",new PayloadTransferUpdate(p.getId(),PayloadTransferUpdate.Status.SUCCESS));}
    void receive(int sequence,int value){byte[] packet=ByteBuffer.allocate(8).putInt(sequence).putInt(value).array();client.payloads.onPayloadReceived("peer",Payload.fromBytes(packet));}
  }
  public static void main(String[] args)throws Exception{
    Fixture f=new Fixture();for(int i=0;i<9;i++)f.send(i);
    check(f.client.sent.size()==4,"four payloads in flight without waiting for first completion");
    f.complete(2);check(f.client.sent.size()==5,"out-of-order completion releases exactly one slot");
    f.complete(2);check(f.client.sent.size()==5,"duplicate completion cannot release a second slot");
    for(int i=0;i<9;i++)if(i!=2)f.complete(i);
    check(f.client.sent.size()==9,"all queued payloads sent");
    check(f.radio.diagnostics().contains("0 waiting, 0/4 sending"),"send window drains");
    for(int i=0;i<9;i++){
      byte[] wire=f.client.sent.get(i).asBytes();check(ByteBuffer.wrap(wire).getInt()==i,"monotonic send sequence");
      check(NearbyProtocol.parse(Arrays.copyOfRange(wire,4,wire.length)).number==i,"wire data preserved");
    }
    for(int n:new int[]{2,0,4,1,3,8,5,7,6})f.receive(n,n+100);
    check(f.events.received.size()==9,"reordered packets all delivered");
    for(int i=0;i<9;i++)check(ByteBuffer.wrap(f.events.received.get(i)).getInt()==i+100,"delivery remains ordered");
    f.receive(2,102);check(f.events.received.size()==9,"old duplicate suppressed");
    f.receive(10,1);f.receive(10,2);check(f.events.failure.contains("changed"),"conflicting pending duplicate rejected");

    Fixture bounded=new Fixture();for(int i=0;i<65;i++)bounded.send(i);
    check(bounded.client.sent.size()==4 && bounded.events.failure.contains("keep up"),"backlog bounded including in-flight payloads");
    Fixture gap=new Fixture();gap.receive(65,1);check(gap.events.failure.contains("sequence"),"receive lookahead bounded");
    Fixture failed=new Fixture();failed.send(0);
    failed.client.payloads.onPayloadTransferUpdate("peer",new PayloadTransferUpdate(failed.client.sent.get(0).getId(),PayloadTransferUpdate.Status.FAILURE));
    failed.send(1);check(failed.client.sent.size()==1 && failed.events.failure.contains("stopped"),"failed transfer stops the send pump");

    Fixture closing=new Fixture();for(int i=0;i<6;i++)closing.send(i);closing.radio.close();closing.send(6);
    check(closing.client.disconnects==0,"close permits queued final messages to drain");
    for(int i=0;i<6;i++)closing.complete(i);
    check(closing.client.sent.size()==6 && closing.client.disconnects==1,"drained close disconnects only its own endpoint");
    for(Runnable r:new ArrayList<Runnable>(Handler.delayed))r.run();
    check(closing.client.disconnects==1,"late close timeout is harmless");
    closing.receive(0,9);check(closing.events.received.isEmpty(),"late payload after close ignored");
    Fixture timeout=new Fixture();timeout.send(0);timeout.radio.close();for(Runnable r:new ArrayList<Runnable>(Handler.delayed))r.run();
    check(timeout.client.disconnects==1,"close timeout bounds waiting for transfer completion");
    System.out.println("PASS "+checks+" Nearby transport assertions; bounded send window, out-of-order completion/delivery, duplicates, failure and close draining");
  }
}

package org.openbw.androidtest;
public final class NearbyCompatibility11Test {
 public static void main(String[] args)throws Exception{
  NearbyProtocolTest.check(NearbyProtocol.BUILD==84,"Wrong simulation handshake build");
  for(int old:new int[]{78,80,81,83,85}){
   NearbyProtocolTest.Peer peer=new NearbyProtocolTest.Peer(false);peer.match.connected();
   peer.match.receive(NearbyProtocol.pack(NearbyProtocol.HELLO,0,0,("{\"build\":"+old+",\"race\":1,\"name\":\"Host\"}").getBytes("UTF-8")));
   NearbyProtocolTest.check(peer.match.closed&&!peer.match.playing&&peer.engine.starts==0,"Mixed rules must fail before starting");
  }
  NearbyProtocolTest.Pair pair=new NearbyProtocolTest.Pair();pair.start();pair.tick(150);
  NearbyProtocolTest.check(!pair.a.match.closed&&!pair.b.match.closed&&pair.a.engine.frames>0,"Matching updated peers failed");
  System.out.println("PASS "+NearbyProtocolTest.checks+" nearby compatibility checks: mixed simulation builds rejected before gameplay, matching peers advance");
 }
}

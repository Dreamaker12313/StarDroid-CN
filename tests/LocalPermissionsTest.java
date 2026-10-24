package org.openbw.androidtest;
import java.util.*;
import android.os.Build;

public final class LocalPermissionsTest {
 static int checks;
 static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static Set<String> expected(int api,boolean wifi){
  Set<String> p=new HashSet<String>();
  if(api>=31)p.addAll(Arrays.asList(LocalPermissions.SCAN,LocalPermissions.CONNECT,LocalPermissions.ADVERTISE));
  if(api<31 || wifi && api>=29 && api<33)p.addAll(Arrays.asList(LocalPermissions.COARSE,LocalPermissions.FINE));
  if(wifi && api>=33)p.add(LocalPermissions.WIFI);return p;
 }
 static class Events implements NativeNearby.Listener {
  String failure="";
  public void status(String s){}public void found(String i,String n){}public void lost(String i){}
  public void connected(int id,String name){}public void received(int id,byte[] b){}public void disconnected(int id){}public void failed(String s){failure=s;}
 }
 static class Fixture {
  final MainActivity a=new MainActivity();final Events e=new Events();final NativeNearby radio=new NativeNearby(a,e);
  final int api;final boolean host,wifi;
  Fixture(int p,boolean h,boolean w){api=p;host=h;wifi=w;Build.VERSION.SDK_INT=p;radio.useWifi(w);}
  void start(){radio.start(host,"Player");}
  void grant(){a.granted.addAll(expected(api,wifi));}
  int starts(){return a.bluetooth.adapter.scans+a.bluetooth.adapter.listens;}
  void started(){check(starts()==1,"start exactly once "+api);check(a.bluetooth.adapter.listens==(host?1:0),"host/join branch");check(e.failure.isEmpty(),"no failure: "+e.failure);}
 }
 public static void main(String[] args)throws Exception {
  for(int api:new int[]{26,28,29,30,31,32,33,34,35,36})for(boolean host:new boolean[]{true,false})for(boolean wifi:new boolean[]{true,false}){
   Fixture fresh=new Fixture(api,host,wifi);fresh.start();
   check(fresh.a.requests==1 && fresh.a.serviceCalls==0,"no radio before permissions");
   check(new HashSet<String>(Arrays.asList(fresh.a.requested)).equals(expected(api,wifi)),"correct API permission set "+api);
   fresh.start();check(fresh.a.requests==1,"duplicate start keeps permission owner");
   fresh.grant();fresh.radio.permissions();fresh.started();fresh.radio.permissions();fresh.start();fresh.started();fresh.radio.close();
   Fixture existing=new Fixture(api,host,wifi);existing.grant();existing.start();existing.started();check(existing.a.requests==0,"existing grants skip dialog");existing.radio.close();
   Fixture cancelled=new Fixture(api,host,wifi);cancelled.start();cancelled.radio.permissions();check(cancelled.starts()==0&&!cancelled.e.failure.isEmpty(),"denial/cancel stops before radio");
   Fixture late=new Fixture(api,host,wifi);late.start();late.radio.close();late.grant();late.radio.permissions();check(late.starts()==0,"late callback ignored after close");
   if(api>=31 && wifi){
    Fixture optional=new Fixture(api,host,wifi);optional.grant();String p=api>=33?LocalPermissions.WIFI:LocalPermissions.FINE;optional.a.granted.remove(p);optional.start();
    check(optional.starts()==0,"optional permission request is awaited");optional.radio.permissions();optional.started();
    check(!LocalPermissions.wifiAllowed(api,wifi,optional.a.granted::contains),"optional denial disables Wi-Fi only");
    if(api<33)check(Arrays.asList(optional.a.requested).contains(LocalPermissions.COARSE),"precise upgrade includes coarse");optional.radio.close();
   }
   if(api>=33)check(!expected(api,wifi).contains(LocalPermissions.FINE),"no location request on modern Android");
  }
  Fixture disabled=new Fixture(36,false,true);disabled.grant();disabled.a.bluetooth.adapter.enabled=false;disabled.start();disabled.radio.permissions();disabled.start();
  check(disabled.a.enableRequests==1&&disabled.starts()==0,"one Bluetooth enable prompt");disabled.a.bluetooth.adapter.enabled=true;disabled.radio.bluetoothResult(false,true);disabled.started();disabled.radio.close();
  Fixture denied=new Fixture(36,true,true);denied.grant();denied.start();denied.radio.bluetoothResult(true,false);check(denied.e.failure.contains("visible"),"discoverability denied explains retry");
  System.out.println("PASS "+checks+" local permission/lifecycle checks; API 26-36, Host/Join, grant/deny/cancel, optional Wi-Fi, duplicate and late callbacks, Bluetooth enable and visibility");
 }
}

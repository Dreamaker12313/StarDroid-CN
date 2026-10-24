package org.openbw.androidtest;

import android.Manifest.permission;
import android.os.Build;
import com.google.android.gms.common.GoogleApiAvailability;
import com.google.android.gms.common.api.ApiException;
import com.google.android.gms.nearby.Nearby;
import com.google.android.gms.nearby.connection.ConnectionsClient;
import java.util.*;

/** Runs the production NativeNearby entry points with fake Android/GMS boundaries. */
public final class NearbyPermissionsTest {
  static int checks;
  static void check(boolean value,String label){checks++;if(!value)throw new AssertionError(label);}
  static Set<String> expected(int api){
    Set<String> p=new HashSet<String>();
    p.add(permission.ACCESS_COARSE_LOCATION);
    if(api>=29)p.add(permission.ACCESS_FINE_LOCATION);
    if(api>=31)Collections.addAll(p,permission.BLUETOOTH_ADVERTISE,permission.BLUETOOTH_CONNECT,permission.BLUETOOTH_SCAN);
    if(api>=33)p.add(permission.NEARBY_WIFI_DEVICES);
    return p;
  }
  static final class Events implements NativeNearby.Listener {
    String failure="",status="";
    public void status(String s){status=s;} public void failed(String s){failure=s;}
    public void found(String id,String name){} public void lost(String id){}
    public void connected(){} public void received(byte[] b){} public void disconnected(){}
  }
  static final class Fixture {
    final int api;final boolean host;
    final MainActivity activity=new MainActivity();final Events events=new Events();
    final NativeNearby radio;final ConnectionsClient client;
    Fixture(int a,boolean h){
      api=a;host=h;Build.VERSION.SDK_INT=a;GoogleApiAvailability.result=0;
      Nearby.calls=0;Nearby.client=new ConnectionsClient();client=Nearby.client;
      radio=new NativeNearby(activity,events);
    }
    void start(){radio.start(host,"Player");}
    void grantAll(){activity.granted.addAll(expected(api));}
    int starts(){return client.advertising+client.discovery;}
    Set<String> requested(){return new HashSet<String>(Arrays.asList(activity.requested));}
    void started(){check(starts()==1,"one start API "+api);check(client.advertising==(host?1:0),"correct Host/Join branch");}
  }
  public static void main(String[] args){
    for(int api:new int[]{26,28,29,30,31,32,33,34,35,36})for(boolean host:new boolean[]{true,false}){
      Fixture fresh=new Fixture(api,host);fresh.start();
      check(fresh.activity.requests==1,"first use asks permission API "+api);
      check(fresh.starts()==0 && Nearby.calls==0,"no Google API before grant");
      check(fresh.requested().equals(expected(api)),"complete foreground permission request API "+api);
      fresh.start();check(fresh.activity.requests==1,"duplicate tap does not replace pending request");
      fresh.grantAll();fresh.radio.permissions();fresh.started();
      fresh.radio.permissions();fresh.start();check(fresh.starts()==1,"duplicate callback does not restart transport");

      Fixture already=new Fixture(api,host);already.grantAll();already.start();already.started();
      check(already.activity.requests==0,"existing permissions skip dialog");

      // Any one denied permission, including partial grants and a dismissed
      // dialog, must prevent both advertising and discovery.
      for(String denied:expected(api)){
        Fixture partial=new Fixture(api,host);partial.grantAll();partial.activity.granted.remove(denied);partial.start();
        check(partial.starts()==0 && Nearby.calls==0,"missing "+denied+" blocks start");
        partial.radio.permissions();check(partial.starts()==0,"denial/cancel blocks start");
        check(!partial.events.failure.isEmpty(),"denial gives actionable error");
        check(partial.activity.requests==1,"denial does not loop permission dialogs");
      }
      Fixture closed=new Fixture(api,host);closed.start();closed.radio.close();closed.grantAll();closed.radio.permissions();
      check(closed.starts()==0,"closing pending lobby ignores late permission callback");

      if(api>=31){
        Fixture approximate=new Fixture(api,host);approximate.grantAll();approximate.activity.granted.remove(permission.ACCESS_FINE_LOCATION);approximate.start();
        check(approximate.requested().equals(new HashSet<String>(Arrays.asList(permission.ACCESS_COARSE_LOCATION,permission.ACCESS_FINE_LOCATION))),"precise upgrade requests coarse and fine together");
        approximate.radio.permissions();check(approximate.events.failure.contains("Precise"),"approximate-only choice explains precise permission");
      }
      if(api>=33){
        // Reproduce a phone updated from 0.49: Nearby devices is already
        // granted, but location was not declared/requested on this Android.
        Fixture upgrade=new Fixture(api,host);upgrade.grantAll();
        upgrade.activity.granted.remove(permission.ACCESS_COARSE_LOCATION);upgrade.activity.granted.remove(permission.ACCESS_FINE_LOCATION);upgrade.start();
        check(upgrade.requested().contains(permission.ACCESS_COARSE_LOCATION),"0.49 upgrade requests missing coarse location");
        check(upgrade.starts()==0,"0.49 upgrade waits before contacting Google");
        upgrade.grantAll();upgrade.radio.permissions();upgrade.started();
      }
    }
    Fixture unavailable=new Fixture(36,true);GoogleApiAvailability.result=2;unavailable.start();
    check(unavailable.starts()==0 && unavailable.activity.requests==0,"unavailable Play services does not start/request permissions");
    check(unavailable.events.failure.contains("Google Play services"),"Play services error remains clear");
    for(int code:new int[]{8034,8036,8037,8038,8039}){
      Fixture serviceError=new Fixture(36,false);serviceError.grantAll();serviceError.client.failure=new ApiException(code);serviceError.start();
      check(serviceError.events.failure.contains("Location") || serviceError.events.failure.contains("Nearby devices"),"service permission errors name the setting");
      check(!serviceError.events.failure.contains("MISSING_PERMISSION"),"service errors do not expose raw permission constants");
    }
    System.out.println("PASS "+checks+" Nearby permission checks; API 26–36, Host/Join, update from 0.49, grant/deny/cancel, approximate upgrade, late callbacks and service errors");
  }
}

package org.openbw.androidtest;

import java.util.ArrayList;

/** Permission policy shared by the Android adapter and API-level regression tests. */
final class LocalPermissions {
  static final String COARSE="android.permission.ACCESS_COARSE_LOCATION", FINE="android.permission.ACCESS_FINE_LOCATION";
  static final String SCAN="android.permission.BLUETOOTH_SCAN", CONNECT="android.permission.BLUETOOTH_CONNECT", ADVERTISE="android.permission.BLUETOOTH_ADVERTISE";
  static final String WIFI="android.permission.NEARBY_WIFI_DEVICES";
  interface Grants {boolean has(String permission);}
  static boolean bluetoothAllowed(int api,Grants grants){
    return api>=31?grants.has(SCAN)&&grants.has(CONNECT)&&grants.has(ADVERTISE):grants.has(FINE);
  }
  static boolean wifiAllowed(int api,boolean wifi,Grants grants){return wifi && api>=29 && grants.has(api>=33?WIFI:FINE);}
  static String[] missing(int api,boolean wifi,Grants grants){
    ArrayList<String> required=new ArrayList<String>();
    if(api>=31){required.add(ADVERTISE);required.add(CONNECT);required.add(SCAN);}
    if(api<31 || wifi && api>=29 && api<33){required.add(COARSE);required.add(FINE);}
    if(wifi && api>=33)required.add(WIFI);
    required.removeIf(grants::has);
    // Android 12+ requires coarse and fine in the same precise-location request,
    // including an upgrade from a previously granted Approximate location.
    if(required.contains(FINE) && !required.contains(COARSE))required.add(0,COARSE);
    return required.toArray(new String[0]);
  }
}

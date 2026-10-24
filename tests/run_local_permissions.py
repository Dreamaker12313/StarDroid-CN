#!/usr/bin/env python3
"""Exercise production permission policy and NativeNearby with fake Android boundaries."""
import hashlib,json,pathlib,shutil,subprocess,xml.etree.ElementTree as ET
r=pathlib.Path(__file__).resolve().parents[1];b=r/'build-native/local-permissions55'
shutil.rmtree(b,ignore_errors=True);b.mkdir(parents=True)
stubs={
'android/content/pm/PackageManager.java': 'public class PackageManager {public static final int PERMISSION_GRANTED=0;public static final String FEATURE_WIFI_DIRECT="wifi.direct";public boolean hasSystemFeature(String s){return true;}}',
'android/content/Context.java': '''public class Context {
 public static final int RECEIVER_EXPORTED=2;
 public Context getApplicationContext(){return this;}
 public <T>T getSystemService(Class<T> c){return null;}
 public Intent registerReceiver(BroadcastReceiver r,IntentFilter f){return null;}
 public Intent registerReceiver(BroadcastReceiver r,IntentFilter f,int flags){return null;}
 public void unregisterReceiver(BroadcastReceiver r){}
}''',
'android/content/IntentFilter.java': 'public class IntentFilter {public void addAction(String s){}}',
'android/content/BroadcastReceiver.java': 'public abstract class BroadcastReceiver {public abstract void onReceive(Context c,Intent i);}',
'android/os/Build.java': 'public class Build {public static class VERSION {public static int SDK_INT;}}',
'android/os/Looper.java': 'public class Looper {public static Looper getMainLooper(){return new Looper();}}',
'android/os/SystemClock.java': 'public class SystemClock {public static long elapsedRealtime(){return System.nanoTime()/1000000;}}',
'android/os/Handler.java': '''public class Handler {
 public static final java.util.ArrayList<Runnable> delayed=new java.util.ArrayList<Runnable>();
 public Handler(Looper l){} public boolean post(Runnable r){r.run();return true;}
 public boolean postDelayed(Runnable r,long n){delayed.add(r);return true;}
}''',
'android/bluetooth/BluetoothManager.java': '''public class BluetoothManager {
 public final BluetoothAdapter adapter=new BluetoothAdapter();public BluetoothAdapter getAdapter(){return adapter;}
}''',
'android/bluetooth/BluetoothAdapter.java': '''public class BluetoothAdapter {
 public static final String ACTION_DISCOVERY_FINISHED="finished",ACTION_STATE_CHANGED="state",EXTRA_STATE="state";
 public static final int STATE_OFF=10;public boolean enabled=true,discovering;public int scans,listens;
 public boolean isEnabled(){return enabled;}public boolean isDiscovering(){return discovering;}
 public String getName(){return "Phone";}public java.util.Set<BluetoothDevice> getBondedDevices(){return java.util.Collections.emptySet();}
 public boolean startDiscovery(){scans++;discovering=true;return true;}public boolean cancelDiscovery(){discovering=false;return true;}
 public BluetoothServerSocket listenUsingRfcommWithServiceRecord(String s,java.util.UUID u){listens++;return new BluetoothServerSocket();}
}''',
'android/bluetooth/BluetoothServerSocket.java': '''public class BluetoothServerSocket implements java.io.Closeable {
 private final java.util.concurrent.CountDownLatch done=new java.util.concurrent.CountDownLatch(1);
 public BluetoothSocket accept()throws java.io.IOException {try{done.await();}catch(InterruptedException e){}throw new java.io.IOException("closed");}
 public void close(){done.countDown();}
}''',
'android/net/wifi/WifiManager.java': 'public class WifiManager {public boolean isWifiEnabled(){return true;}}',
'org/openbw/androidtest/MainActivity.java': '''public class MainActivity extends android.content.Context {
 final java.util.Set<String> granted=new java.util.HashSet<String>();String[] requested=new String[0];int requests,enableRequests,visibleRequests,serviceCalls;
 final android.bluetooth.BluetoothManager bluetooth=new android.bluetooth.BluetoothManager();
 public int checkSelfPermission(String p){return granted.contains(p)?0:-1;}
 public void requestNearbyPermissions(NativeNearby n,String[] p){requests++;requested=p;}
 public void requestNearbyBluetooth(NativeNearby n,boolean visible){if(visible)visibleRequests++;else enableRequests++;}
 public android.content.pm.PackageManager getPackageManager(){return new android.content.pm.PackageManager();}
 public <T>T getSystemService(Class<T> c){serviceCalls++;return c.cast(c==android.bluetooth.BluetoothManager.class?bluetooth:c==android.net.wifi.WifiManager.class?new android.net.wifi.WifiManager():null);}
}'''
}
for path,body in stubs.items():
 p=b/'src'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('package '+str(pathlib.PurePosixPath(path).parent).replace('/','.')+';\n'+body+'\n')
src=r/'app/src/main/java/org/openbw/androidtest';files=[src/n for n in ['NativeNearby.java','LocalPermissions.java','NearbyProtocol.java','LocalTransport.java']]+[r/'tests/LocalPermissionsTest.java']
android=r/'.tools/android-35/android.jar'
subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn','-classpath',str(android),'-d',str(b/'classes'),*map(str,files),*map(str,(b/'src').rglob('*.java'))],check=True)
run=subprocess.run(['java','-cp',str(b/'classes')+':'+str(android),'org.openbw.androidtest.LocalPermissionsTest'],capture_output=True,text=True,timeout=30)
print(run.stdout,run.stderr);run.check_returncode()
ns='{http://schemas.android.com/apk/res/android}';manifest=r/'app/src/main/AndroidManifest.xml'
declared={p.get(ns+'name'):p for p in ET.parse(manifest).getroot().findall('uses-permission')}
for p in ['ACCESS_COARSE_LOCATION','ACCESS_FINE_LOCATION']:assert declared['android.permission.'+p].get(ns+'maxSdkVersion')=='32'
for p in ['BLUETOOTH_SCAN','NEARBY_WIFI_DEVICES']:assert declared['android.permission.'+p].get(ns+'usesPermissionFlags')=='neverForLocation'
assert 'android.permission.ACCESS_BACKGROUND_LOCATION' not in declared
files += [manifest,src/'MainActivity.java',pathlib.Path(__file__)]
report={'version':'0.55','passed':True,'physicalAndroid':False,'productionClasses':['NativeNearby','LocalPermissions','LocalTransport'],'androidBoundary':'test doubles, no physical permission dialogs or radio','apiLevels':[26,28,29,30,31,32,33,34,35,36],'output':run.stdout.strip(),'sourceSha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(r/'validation/local-permissions-v55.json').write_text(json.dumps(report,indent=2)+'\n')

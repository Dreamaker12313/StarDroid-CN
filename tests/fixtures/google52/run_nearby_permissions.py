#!/usr/bin/env python3
"""Execute real NativeNearby permission/start flow; Android/GMS boundaries are fakes."""
import hashlib,json,pathlib,shutil,subprocess,xml.etree.ElementTree as ET

r=pathlib.Path(__file__).resolve().parents[1]
b=r/'build-native/nearby-permissions';shutil.rmtree(b,ignore_errors=True);b.mkdir(parents=True)
stubs={
 'android/content/pm/PackageManager.java': 'public class PackageManager {public static final int PERMISSION_GRANTED=0;}',
 'android/os/Build.java': 'public class Build {public static class VERSION {public static int SDK_INT;}}',
 'android/os/Looper.java': 'public class Looper {public static Looper getMainLooper(){return new Looper();}}',
 'android/os/Handler.java': 'public class Handler {public static final java.util.ArrayList<Runnable> delayed=new java.util.ArrayList<Runnable>();public Handler(Looper l){} public void post(Runnable r){r.run();}public void postDelayed(Runnable r,long n){delayed.add(r);}}',
 'android/app/AlertDialog.java': '''public class AlertDialog {
  public interface Click{void call(Object d,int w);}public interface Cancel{void call(Object d);}
  public static AlertDialog latest;public Click positive;public void show(){latest=this;}public void dismiss(){}public void confirm(){positive.call(this,0);}public static class Builder{
   private Click positive;
   public Builder(Object a){}public Builder setTitle(String s){return this;}public Builder setMessage(String s){return this;}
   public Builder setPositiveButton(String s,Click c){positive=c;return this;}public Builder setNegativeButton(String s,Click c){return this;}
   public Builder setOnCancelListener(Cancel c){return this;}public AlertDialog create(){AlertDialog d=new AlertDialog();d.positive=positive;return d;}}}''',
 'org/openbw/androidtest/MainActivity.java': '''public class MainActivity {
  final java.util.Set<String> granted=new java.util.HashSet<String>();String[] requested=new String[0];int requests;
  public int checkSelfPermission(String p){return granted.contains(p)?0:-1;}
  public void requestNearbyPermissions(NativeNearby n,String[] p){requests++;requested=p;}}''',
 'com/google/android/gms/common/GoogleApiAvailability.java': '''public class GoogleApiAvailability {
  public static int result;public static GoogleApiAvailability getInstance(){return new GoogleApiAvailability();}
  public int isGooglePlayServicesAvailable(Object a){return result;}}''',
 'com/google/android/gms/common/api/ApiException.java': '''public class ApiException extends Exception {
  private final int code;public ApiException(int c){super("MISSING_PERMISSION");code=c;}public int getStatusCode(){return code;}}''',
 'com/google/android/gms/nearby/Nearby.java': '''public class Nearby {
  public static int calls;public static com.google.android.gms.nearby.connection.ConnectionsClient client;
  public static com.google.android.gms.nearby.connection.ConnectionsClient getConnectionsClient(Object a){calls++;return client;}}''',
 'com/google/android/gms/nearby/connection/Task.java': '''public class Task {
  public interface Success{void call(Object v);}public interface Failure{void call(Exception e);}
  private final Exception error;public Task(Exception e){error=e;}
  public Task addOnSuccessListener(Success c){if(error==null)c.call(null);return this;}
  public Task addOnFailureListener(Failure c){if(error!=null)c.call(error);return this;}}''',
 'com/google/android/gms/nearby/connection/ConnectionsClient.java': '''public class ConnectionsClient {
  public int advertising,discovery,disconnects;public Exception failure;
  public ConnectionLifecycleCallback lifecycle;public PayloadCallback payloads;public final java.util.ArrayList<Payload> sent=new java.util.ArrayList<Payload>();
  public Task startAdvertising(String n,String s,ConnectionLifecycleCallback c,AdvertisingOptions o){advertising++;return new Task(failure);}
  public Task startDiscovery(String s,EndpointDiscoveryCallback c,DiscoveryOptions o){discovery++;return new Task(failure);}
  public Task requestConnection(String n,String id,ConnectionLifecycleCallback c){lifecycle=c;return new Task(null);}
  public Task acceptConnection(String id,PayloadCallback c){payloads=c;return new Task(null);}public void rejectConnection(String id){}
  public void stopAdvertising(){}public void stopDiscovery(){}public void disconnectFromEndpoint(String id){disconnects++;}
  public Task sendPayload(String id,Payload p){sent.add(p);return new Task(null);}}''',
 'com/google/android/gms/nearby/connection/Strategy.java': 'public class Strategy {public static final Strategy P2P_POINT_TO_POINT=new Strategy();}',
 'com/google/android/gms/nearby/connection/EndpointDiscoveryCallback.java': 'public abstract class EndpointDiscoveryCallback {public abstract void onEndpointFound(String id,DiscoveredEndpointInfo info);public abstract void onEndpointLost(String id);}',
 'com/google/android/gms/nearby/connection/DiscoveredEndpointInfo.java': 'public class DiscoveredEndpointInfo {public String getServiceId(){return "";}public String getEndpointName(){return "";}}',
 'com/google/android/gms/nearby/connection/ConnectionLifecycleCallback.java': 'public abstract class ConnectionLifecycleCallback {public abstract void onConnectionInitiated(String id,ConnectionInfo info);public abstract void onConnectionResult(String id,ConnectionResolution result);public abstract void onDisconnected(String id);}',
 'com/google/android/gms/nearby/connection/ConnectionInfo.java': 'public class ConnectionInfo {public String getAuthenticationDigits(){return "1234";}public String getEndpointName(){return "Peer";}}',
 'com/google/android/gms/nearby/connection/ConnectionResolution.java': 'public class ConnectionResolution {public static class Status {public boolean isSuccess(){return true;}}public Status getStatus(){return new Status();}}',
 'com/google/android/gms/nearby/connection/PayloadCallback.java': 'public abstract class PayloadCallback {public abstract void onPayloadReceived(String id,Payload payload);public abstract void onPayloadTransferUpdate(String id,PayloadTransferUpdate update);}',
 'com/google/android/gms/nearby/connection/Payload.java': 'public class Payload {private static long next;private long id;private byte[] data;public static class Type {public static final int BYTES=1;}public static Payload fromBytes(byte[] b){Payload p=new Payload();p.id=++next;p.data=b.clone();return p;}public long getId(){return id;}public int getType(){return Type.BYTES;}public byte[] asBytes(){return data;}}',
 'com/google/android/gms/nearby/connection/PayloadTransferUpdate.java': 'public class PayloadTransferUpdate {private long id;private int status;public PayloadTransferUpdate(long i,int s){id=i;status=s;}public static class Status {public static final int SUCCESS=1,FAILURE=2,CANCELED=3;}public long getPayloadId(){return id;}public int getStatus(){return status;}}',
 'com/google/android/gms/nearby/connection/ConnectionsStatusCodes.java': 'public class ConnectionsStatusCodes {public static final int MISSING_PERMISSION_ACCESS_COARSE_LOCATION=8034,MISSING_PERMISSION_ACCESS_FINE_LOCATION=8036,MISSING_PERMISSION_BLUETOOTH_ADVERTISE=8038,MISSING_PERMISSION_BLUETOOTH_CONNECT=8039,MISSING_PERMISSION_BLUETOOTH_SCAN=8037;}',
}
permissions=['ACCESS_COARSE_LOCATION','ACCESS_FINE_LOCATION','BLUETOOTH_ADVERTISE','BLUETOOTH_CONNECT','BLUETOOTH_SCAN','NEARBY_WIFI_DEVICES']
stubs['android/Manifest.java']='public class Manifest {public static class permission {'+''.join('public static final String '+p+'="android.permission.'+p+'";' for p in permissions)+'}}'
for name in ['AdvertisingOptions','DiscoveryOptions']:
 stubs['com/google/android/gms/nearby/connection/'+name+'.java']='public class '+name+' {public static class Builder {public Builder setStrategy(Strategy s){return this;}public '+name+' build(){return new '+name+'();}}}'
stubfiles=[]
for path,body in stubs.items():
 p=b/'src'/path;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text('package '+str(pathlib.PurePosixPath(path).parent).replace('/','.')+';\n'+body+'\n');stubfiles.append(p)
src=r/'app/src/main/java/org/openbw/androidtest'
files=[src/'NativeNearby.java',src/'NearbyProtocol.java',r/'tests/NearbyPermissionsTest.java',r/'tests/NearbyTransportTest.java']
subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn','-d',str(b/'classes'),*map(str,files+stubfiles)],check=True)
result=subprocess.run(['java','-cp',str(b/'classes'),'org.openbw.androidtest.NearbyPermissionsTest'],capture_output=True,text=True,check=True)
print(result.stdout.strip())
transport=subprocess.run(['java','-cp',str(b/'classes'),'org.openbw.androidtest.NearbyTransportTest'],capture_output=True,text=True,check=True)
print(transport.stdout.strip())
ns='{http://schemas.android.com/apk/res/android}'
manifest=r/'app/src/main/AndroidManifest.xml'
declared={p.get(ns+'name'):p for p in ET.parse(manifest).getroot().findall('uses-permission')}
for p in permissions:
 assert 'android.permission.'+p in declared,p
 if p.endswith('LOCATION'):assert declared['android.permission.'+p].get(ns+'maxSdkVersion') is None,p
assert 'android.permission.ACCESS_BACKGROUND_LOCATION' not in declared
activity=src/'MainActivity.java'
assert 'owner.permissions();' in activity.read_text()
sources=files+[manifest,activity,pathlib.Path(__file__)]
report={'version':'0.52','passed':True,'physicalAndroid':False,'actualProductionClasses':['NativeNearby.java','NearbyProtocol.java'],'androidAndGoogleServices':'test doubles; no real permission dialogs/radio','apiLevels':[26,28,29,30,31,32,33,34,35,36],'output':result.stdout.strip(),'transportOutput':transport.stdout.strip(),'manifestLocationNotCapped':True,'backgroundLocationRequested':False,'sourceSha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
(r/'validation/nearby-permissions-v52.json').write_text(json.dumps(report,indent=2)+'\n')

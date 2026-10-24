package org.openbw.androidtest;

import android.app.AlertDialog;
import android.bluetooth.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.net.wifi.WifiManager;
import android.net.wifi.p2p.*;
import android.os.*;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/** One secure host connection per device, with independent Bluetooth/Wi-Fi failover. */
@android.annotation.SuppressLint("MissingPermission")
final class NativeNearby {
  interface Listener {
    void status(String text);void found(String id,String name);void lost(String id);
    void connected(int id,String name);void received(int id,byte[] data);void disconnected(int id);void failed(String reason);
  }
  private static final UUID SERVICE=UUID.fromString("aa63bcf4-18b1-4de9-a091-91513648cd87");
  private static NativeNearby current;
  private final MainActivity activity;private final Listener listener;private final Handler main=new Handler(Looper.getMainLooper());
  private final java.util.concurrent.Semaphore wifiHandshakes=new java.util.concurrent.Semaphore(8);
  private final ConcurrentHashMap<Integer,Peer> peers=new ConcurrentHashMap<Integer,Peer>();
  private final ArrayList<Closeable> resources=new ArrayList<Closeable>(),wifiResources=new ArrayList<Closeable>();
  private final LinkedHashMap<String,BluetoothDevice> devices=new LinkedHashMap<String,BluetoothDevice>();
  private final ArrayDeque<Peer> confirmations=new ArrayDeque<Peer>();private final AtomicInteger nextId=new AtomicInteger(1);
  private volatile boolean closed,closing,wifiStopped;private boolean hosting,connecting,registered,started,waitingPermissions,waitingBluetooth,wantWifi=true,wifiAllowed,wifiConnecting;
  private volatile String diagnostic="Not started",lastRadioError="";
  private String player,ssid,password;private int port,scanRounds;private long lastPing,wifiDeadline;private AlertDialog pairing;private Peer confirming;
  private BluetoothAdapter bluetooth;private WifiP2pManager wifi;private WifiP2pManager.Channel channel;
  private final class Peer {
    final int id;final LocalTransport.Pipe[] pipes=new LocalTransport.Pipe[2];final LocalTransport.Reliable reliable;
    volatile LocalTransport.Pair pair;boolean confirmed,peerConfirmed,accepted,removed,wifiInvited;
    Peer(int n){id=n;reliable=new LocalTransport.Reliable(b->{if(accepted&&!removed&&live())listener.received(id,b);});}
  }
  NativeNearby(MainActivity a,Listener l){activity=a;listener=l;}
  void useWifi(boolean enabled){wantWifi=enabled;}
  String diagnostics(){int n=0,w=0,pending=0;for(Peer p:peers.values()){if(p.accepted)n++;if(p.pipes[1]!=null)w++;pending+=p.reliable.pending();}return "Local transport: "+diagnostic+"; "+n+" devices, "+w+" Wi-Fi links; "+pending+" packets awaiting acknowledgement"+(lastRadioError.isEmpty()?"":"; "+lastRadioError);}
  private long now(){return SystemClock.elapsedRealtime();}
  private boolean live(){return !closed&&!closing&&current==this;}
  private void status(String s){diagnostic=s;if(live())listener.status(s);}
  private boolean allowed(String p){return activity.checkSelfPermission(p)==PackageManager.PERMISSION_GRANTED;}
  void start(boolean host,String name){main.post(()->{
    if(closed||closing||waitingPermissions||waitingBluetooth||started)return;if(current!=null&&current!=this)current.dispose();current=this;hosting=host;player=NearbyProtocol.name(name);
    try{String[] missing=LocalPermissions.missing(Build.VERSION.SDK_INT,wantWifi,this::allowed);if(missing.length>0){waitingPermissions=true;activity.requestNearbyPermissions(this,missing);return;}permissions();}
    catch(Exception e){fail("Could not start local multiplayer",e);}
  });}
  void permissions(){
    if(!live()||started||waitingBluetooth)return;waitingPermissions=false;
    if(!LocalPermissions.bluetoothAllowed(Build.VERSION.SDK_INT,this::allowed)){fail(Build.VERSION.SDK_INT>=31?"Allow Nearby devices permission, then try again":"Allow precise Location permission for Android's Bluetooth discovery, then try again",null);return;}
    try{BluetoothManager manager=activity.getSystemService(BluetoothManager.class);bluetooth=manager==null?null:manager.getAdapter();if(bluetooth==null){fail("This device does not support Bluetooth",null);return;}
      if(!bluetooth.isEnabled()){waitingBluetooth=true;status("Turn on Bluetooth to connect");activity.requestNearbyBluetooth(this,false);return;}begin();
    }catch(Exception e){fail("Could not start Bluetooth",e);}
  }
  void bluetoothResult(boolean discoverable,boolean ok){
    if(!live())return;waitingBluetooth=false;if(!ok){fail(discoverable?"Allow the host device to be visible, then host again":"Bluetooth was not enabled",null);return;}
    try{if(discoverable)status("Hosting as "+NearbyProtocol.name(bluetooth.getName())+". Join from the other devices.");else permissions();}catch(SecurityException e){fail("Bluetooth permission was removed",e);}
  }
  private void begin(){
    if(!live()||started)return;started=true;
    try{WifiManager wm=activity.getApplicationContext().getSystemService(WifiManager.class);wifiAllowed=wantWifi&&Build.VERSION.SDK_INT>=29&&wm!=null&&wm.isWifiEnabled()&&activity.getPackageManager().hasSystemFeature(PackageManager.FEATURE_WIFI_DIRECT)&&LocalPermissions.wifiAllowed(Build.VERSION.SDK_INT,wantWifi,this::allowed);
      IntentFilter filter=new IntentFilter();filter.addAction(BluetoothDevice.ACTION_FOUND);filter.addAction(BluetoothAdapter.ACTION_DISCOVERY_FINISHED);filter.addAction(BluetoothAdapter.ACTION_STATE_CHANGED);filter.addAction(WifiP2pManager.WIFI_P2P_CONNECTION_CHANGED_ACTION);
      if(Build.VERSION.SDK_INT>=33)activity.registerReceiver(receiver,filter,Context.RECEIVER_EXPORTED);else activity.registerReceiver(receiver,filter);registered=true;
      if(hosting){final BluetoothServerSocket server=bluetooth.listenUsingRfcommWithServiceRecord("StarDroid Nearby",SERVICE);track(server,false);
        worker(()->{try{while(!closed&&!closing){BluetoothSocket socket=server.accept();if(!track(socket,false))return;
          if(peers.size()>=7){socket.close();continue;}Peer p=new Peer(nextId.getAndIncrement());peers.put(p.id,p);handshakeWorker(p,socket);
        }}catch(Exception e){main.post(()->{if(live())fail("Bluetooth hosting stopped",e);});}});activity.requestNearbyBluetooth(this,true);
      }else{for(BluetoothDevice d:bluetooth.getBondedDevices())found(d);scan();}main.postDelayed(this::pulse,1000);
    }catch(Exception e){fail("Could not start local discovery",e);}
  }
  private void scan(){if(!live()||hosting||connecting)return;try{if(bluetooth.isDiscovering())return;if(bluetooth.startDiscovery()){scanRounds++;status("Select the host device. Accept Android's pairing request on each device.");}else status("Cannot scan. Check Bluetooth and Location in Android settings, then retry.");}catch(Exception e){fail("Could not search for nearby devices",e);}}
  void refresh(){main.post(()->{if(!live())return;if(hosting){activity.requestNearbyBluetooth(this,true);}else if(!connecting){scanRounds=0;scan();}});}
  private void found(BluetoothDevice d){
    if(!live()||hosting||connecting||d==null)return;try{BluetoothClass type=d.getBluetoothClass();int major=type==null?0:type.getMajorDeviceClass();
      if(major!=0&&major!=BluetoothClass.Device.Major.UNCATEGORIZED&&major!=BluetoothClass.Device.Major.PHONE&&major!=BluetoothClass.Device.Major.COMPUTER)return;
      String name=d.getName();if(name==null||name.trim().isEmpty()||devices.size()>=64&&!devices.containsKey(d.getAddress()))return;devices.put(d.getAddress(),d);listener.found(d.getAddress(),NearbyProtocol.name(name));
    }catch(SecurityException e){fail("Bluetooth permission was removed",e);}
  }
  private final BroadcastReceiver receiver=new BroadcastReceiver(){@Override public void onReceive(Context c,Intent intent){
    if(!live())return;String action=intent.getAction();
    if(BluetoothDevice.ACTION_FOUND.equals(action))found(intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE));
    else if(BluetoothAdapter.ACTION_DISCOVERY_FINISHED.equals(action)&&scanRounds<8&&!connecting)main.postDelayed(NativeNearby.this::scan,1500);
    else if(WifiP2pManager.WIFI_P2P_CONNECTION_CHANGED_ACTION.equals(action))pollWifi();
    else if(BluetoothAdapter.ACTION_STATE_CHANGED.equals(action)&&intent.getIntExtra(BluetoothAdapter.EXTRA_STATE,0)==BluetoothAdapter.STATE_OFF){for(Peer p:peers.values())lost(p,0);if(peers.isEmpty())fail("Bluetooth was turned off",null);}
  }};
  void join(String id){main.post(()->{
    if(!live()||hosting||connecting)return;BluetoothDevice d=devices.get(id);if(d==null)return;
    try{connecting=true;bluetooth.cancelDiscovery();status("Connecting. Accept Android's Bluetooth pairing request on both devices.");BluetoothSocket socket=d.createRfcommSocketToServiceRecord(SERVICE);track(socket,false);Peer p=new Peer(0);peers.put(0,p);
      main.postDelayed(()->{if(live()&&!p.removed&&p.pair==null){try{socket.close();}catch(Exception ignored){}reject(p,"Connection timed out. Check that the host is running the same StarDroid version");}},45000);
      worker(()->{try{socket.connect();handshake(p,socket);}catch(Exception e){main.post(()->reject(p,"Could not connect to this host"));}});
    }catch(Exception e){fail("Could not open Bluetooth connection",e);}
  });}
  private void handshakeWorker(Peer p,BluetoothSocket socket){main.post(()->main.postDelayed(()->{if(live()&&!p.removed&&p.pair==null){try{socket.close();}catch(Exception ignored){}reject(p,"Pairing timed out");}},45000));
    worker(()->{try{handshake(p,socket);}catch(Exception e){try{socket.close();}catch(Exception ignored){}main.post(()->reject(p,"Could not pair this device"));}});
  }
  private void handshake(Peer p,BluetoothSocket socket)throws Exception{
    LocalTransport.Pair pair=LocalTransport.bluetooth(socket.getInputStream(),socket.getOutputStream(),hosting,player,wifiAllowed);
    LocalTransport.Pipe pipe=makePipe(p,0,socket.getInputStream(),socket.getOutputStream(),socket,pair.secret);
    main.post(()->{if(!live()||p.removed){pipe.close();return;}try{p.pair=pair;p.pipes[0]=pipe;p.reliable.attach(0,pipe,now());pipe.start();bluetooth.cancelDiscovery();confirmations.add(p);showConfirmation();
      main.postDelayed(()->{if(live()&&!p.removed&&!p.accepted)reject(p,"Pairing confirmation timed out");},120000);
    }catch(Exception e){reject(p,"Could not verify this connection");}});
  }
  private void showConfirmation(){
    if(!live()||pairing!=null)return;Peer p=confirmations.poll();if(p==null)return;if(p.removed){showConfirmation();return;}confirming=p;
    try{pairing=new AlertDialog.Builder(activity).setTitle("Connect to "+p.pair.name).setMessage("Check that the two devices show this code:\n\n"+p.pair.code())
      .setPositiveButton("Codes match",(d,w)->{p.confirmed=true;control(p,new byte[]{1});ready(p);})
      .setNegativeButton("Cancel",(d,w)->reject(p,"Connection cancelled")).setOnCancelListener(d->reject(p,"Connection cancelled")).create();
      pairing.setOnDismissListener(d->{pairing=null;confirming=null;showConfirmation();});pairing.show();
    }catch(Exception e){pairing=null;confirming=null;reject(p,"Could not verify this connection");showConfirmation();}
  }
  private LocalTransport.Pipe makePipe(Peer p,int lane,InputStream in,OutputStream out,Closeable socket,byte[] key)throws Exception{
    return new LocalTransport.Pipe(in,out,socket,key,hosting,r->main.post(r),new LocalTransport.StreamListener(){public void frame(LocalTransport.Frame f){receive(p,lane,f);}public void ended(){lost(p,lane);}});
  }
  private void ready(Peer p){
    if(!live()||p.removed||p.accepted||!p.confirmed||!p.peerConfirmed)return;p.accepted=true;status("Device connected");listener.connected(p.id,p.pair.name);
    if(hosting&&wifiAllowed&&p.pair.wifi&&Build.VERSION.SDK_INT>=29){if(channel==null&&!wifiStopped)startWifiHost();else invite(p);}
  }
  private void control(Peer p,byte[] b){if(!live()||p.removed||p.pipes[0]==null)return;try{p.pipes[0].send(new LocalTransport.Frame(LocalTransport.CONTROL,0,b));}catch(Exception e){lost(p,0);}}
  private void receive(Peer p,int lane,LocalTransport.Frame f){
    if(!live()||p.removed||p.pipes[lane]==null)return;try{
      if(f.type==LocalTransport.CONTROL){if(lane!=0||f.data.length==0||f.data.length>256)throw new IOException("Invalid connection control");
        if(f.data[0]==1&&f.data.length==1){p.peerConfirmed=true;ready(p);}
        else if(f.data[0]==2&&p.accepted&&!hosting){DataInputStream in=new DataInputStream(new ByteArrayInputStream(f.data));in.readByte();ssid=in.readUTF();password=in.readUTF();port=in.readInt();
          if(in.available()!=0||!ssid.matches("DIRECT-[A-Za-z0-9]{2}-(?:StarDroid|OpenBW)-[A-F0-9]{8}")||!password.matches("[A-F0-9]{32}")||port<1024||port>65535)throw new IOException("Invalid Wi-Fi invitation");
          if(Build.VERSION.SDK_INT>=29&&wifiAllowed&&!wifiStopped&&channel==null)startWifiGuest();
        }else throw new IOException("Unexpected connection control");
      }else if(f.type==LocalTransport.PING){if(f.data.length!=0)throw new IOException("Invalid keepalive");}
      else{if(!p.accepted)throw new IOException("Pairing is not confirmed");p.reliable.receive(lane,f,now());}
    }catch(Exception e){reject(p,"Local connection was interrupted");}
  }
  void send(int id,byte[] packet){main.post(()->{Peer p=peers.get(id);if(!live()||p==null||!p.accepted)return;try{p.reliable.send(packet,now());if(p.pipes[1]!=null&&!p.reliable.active(1))lost(p,1);}catch(Exception e){reject(p,"Could not send game data");}});}
  void drop(int id){main.post(()->{Peer p=peers.get(id);if(p!=null)remove(p,false);});}
  private void lost(Peer p,int lane){
    if(!live()||p.removed||p.pipes[lane]==null)return;p.pipes[lane]=null;try{p.reliable.detach(lane,now());}catch(Exception e){reject(p,"Could not switch connections");return;}
    if(p.reliable.route()<0)remove(p,true);else status(p.reliable.route()==1?"Wi-Fi Direct connected":"Bluetooth fallback — Wi-Fi Direct unavailable");
  }
  private void remove(Peer p,boolean notify){
    if(p.removed)return;p.removed=true;peers.remove(p.id,p);p.reliable.close();Arrays.fill(p.pipes,null);confirmations.remove(p);
    if(confirming==p&&pairing!=null)pairing.dismiss();if(notify&&p.accepted&&live())listener.disconnected(p.id);
    if(!hosting)connecting=false;
  }
  private void reject(Peer p,String why){if(!live()||p.removed)return;boolean accepted=p.accepted;remove(p,true);status(why);if(!hosting&&!accepted)listener.failed(why);}
  private void pulse(){
    if(!live())return;try{for(Peer p:peers.values()){if(p.reliable.wifiStalled(now()))lost(p,1);if(now()-lastPing>2000)for(int i=0;i<2;i++)if(p.pipes[i]!=null)try{p.pipes[i].send(new LocalTransport.Frame(LocalTransport.PING,0,new byte[0]));}catch(Exception e){lost(p,i);}}
      if(now()-lastPing>2000)lastPing=now();if(channel!=null&&!wifiStopped&&!wifiConnecting){if(now()>wifiDeadline)wifiFailed();else pollWifi();}
    }finally{if(live())main.postDelayed(this::pulse,1000);}
  }
  private boolean initWifi(){if(!live()||!wifiAllowed||wifiStopped)return false;try{wifi=activity.getSystemService(WifiP2pManager.class);if(wifi==null)return false;channel=wifi.initialize(activity,Looper.getMainLooper(),()->{if(live())wifiFailed();});wifiDeadline=now()+35000;status("Setting up Wi-Fi Direct…");return channel!=null;}catch(Exception e){wifiFailed();return false;}}
  private String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format(Locale.US,"%02X",v&255));return s.toString();}
  @android.annotation.TargetApi(29)
  private void startWifiHost(){if(!initWifi())return;try{wifi.requestGroupInfo(channel,group->{if(!live()||wifiStopped)return;if(group!=null){wifiFailed();return;}try{
    ssid="DIRECT-SD-StarDroid-"+hex(LocalTransport.random(4));password=hex(LocalTransport.random(16));WifiP2pConfig config=new WifiP2pConfig.Builder().setNetworkName(ssid).setPassphrase(password).build();
    wifi.createGroup(channel,config,new WifiP2pManager.ActionListener(){public void onSuccess(){pollWifi();}public void onFailure(int reason){lastRadioError="Wi-Fi Direct error "+reason;wifiFailed();}});
  }catch(Exception e){wifiFailed();}});}catch(Exception e){wifiFailed();}}
  @android.annotation.TargetApi(29)
  private void startWifiGuest(){if(!initWifi())return;try{wifi.requestGroupInfo(channel,group->{if(!live()||wifiStopped)return;if(group!=null){wifiFailed();return;}try{
    WifiP2pConfig config=new WifiP2pConfig.Builder().setNetworkName(ssid).setPassphrase(password).build();wifi.connect(channel,config,new WifiP2pManager.ActionListener(){public void onSuccess(){pollWifi();}public void onFailure(int reason){lastRadioError="Wi-Fi Direct error "+reason;wifiFailed();}});
  }catch(Exception e){wifiFailed();}});}catch(Exception e){wifiFailed();}}
  private void pollWifi(){if(!live()||wifiStopped||channel==null||wifiConnecting||ssid==null)return;try{wifi.requestGroupInfo(channel,group->{if(!live()||wifiStopped||wifiConnecting||group==null||!ssid.equals(group.getNetworkName()))return;try{wifi.requestConnectionInfo(channel,info->{
    if(!live()||wifiStopped||wifiConnecting||!info.groupFormed||info.groupOwnerAddress==null)return;if(info.isGroupOwner!=hosting){wifiFailed();return;}wifiConnecting=true;
    if(hosting)listenWifi(info.groupOwnerAddress);else connectWifi(info.groupOwnerAddress);
  });}catch(Exception e){wifiFailed();}});}catch(Exception e){wifiFailed();}}
  private void invite(Peer p){if(!live()||wifiStopped||port==0||!p.accepted||!p.pair.wifi||p.wifiInvited)return;try{ByteArrayOutputStream b=new ByteArrayOutputStream();DataOutputStream out=new DataOutputStream(b);out.writeByte(2);out.writeUTF(ssid);out.writeUTF(password);out.writeInt(port);p.wifiInvited=true;control(p,b.toByteArray());}catch(Exception e){lastRadioError="Wi-Fi invitation failed";}}
  private void listenWifi(InetAddress address){worker(()->{try{
    ServerSocket server=new ServerSocket();if(!track(server,true))return;server.bind(new InetSocketAddress(address,0),8);final int selected=server.getLocalPort();main.post(()->{port=selected;for(Peer p:peers.values())invite(p);});
    while(!closed&&!closing&&!wifiStopped){Socket socket=server.accept();if(!wifiHandshakes.tryAcquire()){socket.close();continue;}if(!track(socket,true)){wifiHandshakes.release();return;}worker(()->{try{
      socket.setSoTimeout(5000);byte[] identity=new byte[16];new DataInputStream(socket.getInputStream()).readFully(identity);Peer selectedPeer=null;
      for(Peer p:peers.values())if(p.accepted&&!p.removed&&p.pair!=null&&java.security.MessageDigest.isEqual(identity,Arrays.copyOf(LocalTransport.key(p.pair.secret,"Wi-Fi identity"),16))){selectedPeer=p;break;}
      if(selectedPeer==null)throw new IOException("Unknown device");byte[] key=LocalTransport.wifi(socket.getInputStream(),socket.getOutputStream(),selectedPeer.pair.secret,true);socket.setSoTimeout(12000);socket.setTcpNoDelay(true);attachWifi(selectedPeer,socket,key);
    }catch(Exception e){try{socket.close();}catch(Exception ignored){}}finally{wifiHandshakes.release();}});}
  }catch(Exception e){main.post(this::wifiFailed);}});}
  private void connectWifi(InetAddress address){worker(()->{try{
    Peer p=peers.get(0);if(p==null||!p.accepted)return;Socket socket=new Socket();if(!track(socket,true))return;socket.connect(new InetSocketAddress(address,port),10000);socket.setSoTimeout(5000);socket.setTcpNoDelay(true);
    socket.getOutputStream().write(Arrays.copyOf(LocalTransport.key(p.pair.secret,"Wi-Fi identity"),16));socket.getOutputStream().flush();byte[] key=LocalTransport.wifi(socket.getInputStream(),socket.getOutputStream(),p.pair.secret,false);socket.setSoTimeout(12000);attachWifi(p,socket,key);
  }catch(Exception e){main.post(this::wifiFailed);}});}
  private void attachWifi(Peer p,Socket socket,byte[] key)throws Exception{LocalTransport.Pipe pipe=makePipe(p,1,socket.getInputStream(),socket.getOutputStream(),socket,key);main.post(()->{
    if(!live()||wifiStopped||p.removed||p.pipes[1]!=null){pipe.close();return;}try{p.pipes[1]=pipe;p.reliable.attach(1,pipe,now());pipe.start();status("Wi-Fi Direct connected · Bluetooth standby");}catch(Exception e){lost(p,1);}
  });}
  private void wifiFailed(){if(!live()||wifiStopped)return;for(Peer p:peers.values())if(p.pipes[1]!=null)lost(p,1);stopWifi();status("Bluetooth connected — Wi-Fi Direct unavailable");}
  private void stopWifi(){if(wifiStopped)return;wifiStopped=true;synchronized(resources){for(Closeable c:wifiResources)try{c.close();}catch(Exception ignored){}wifiResources.clear();}
    if(wifi!=null&&channel!=null){final WifiP2pManager.Channel own=channel;channel=null;try{wifi.requestGroupInfo(own,group->{if((current==this||current==null)&&group!=null&&ssid!=null&&ssid.equals(group.getNetworkName()))wifi.removeGroup(own,new WifiP2pManager.ActionListener(){public void onSuccess(){closeChannel(own);}public void onFailure(int reason){closeChannel(own);}});else closeChannel(own);});}catch(Exception ignored){closeChannel(own);}}
  }
  private void closeChannel(WifiP2pManager.Channel c){if(Build.VERSION.SDK_INT>=27)c.close();}
  private boolean track(Closeable c,boolean isWifi){synchronized(resources){if(closed||closing||isWifi&&wifiStopped){try{c.close();}catch(Exception ignored){}return false;}resources.add(c);if(isWifi)wifiResources.add(c);return true;}}
  private void worker(Runnable r){Thread t=new Thread(r,"StarDroid local connection");t.setDaemon(true);t.start();}
  private void fail(String message,Exception e){if(!live())return;diagnostic=message;if(e!=null)lastRadioError=e.getClass().getSimpleName();listener.failed(message);dispose();}
  void close(){main.post(()->{if(closed||closing)return;closing=true;if(pairing!=null)pairing.dismiss();main.postDelayed(this::dispose,350);});}
  private void dispose(){if(closed)return;closed=closing=true;if(pairing!=null)pairing.dismiss();pairing=null;confirmations.clear();stopWifi();for(Peer p:peers.values())remove(p,false);peers.clear();
    synchronized(resources){for(Closeable c:resources)try{c.close();}catch(Exception ignored){}resources.clear();}if(registered){try{activity.unregisterReceiver(receiver);}catch(Exception ignored){}registered=false;}
    if(bluetooth!=null)try{bluetooth.cancelDiscovery();}catch(Exception ignored){}if(current==this)current=null;
  }
}

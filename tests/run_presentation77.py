#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess
r=Path(__file__).resolve().parents[1];out=r/'build-native/presentation77';out.mkdir(parents=True,exist_ok=True)
src=r/'app/src/main/java/org/openbw/androidtest';jar=r/'build-native/json-20240303.jar';menu=r/'build-native/menu76/classes'
bridge=out/'NativeBridge.java';bridge.write_text('''package org.openbw.androidtest;
final class NativeBridge {
 static String events="";static int frame,voice,starts,effects,position=350;static boolean active;
 static byte[] archiveText(String s){return null;}
 static int sound(byte[] data,int ch,boolean loop){if(ch==62)active=false;return 0;}
 static boolean playing(int ch){return ch==62&&active;}
 static int campaignSound(int id){voice=id;starts++;active=true;return 8000;}
 static void campaignEffect(int id){effects++;}
 static void seekSound(int ch,int ms){position=ms;}
 static int value(int id,int n){return id==8?frame:id==19?(active?position:-1):0;}
 static String text(int id){if(id==5){String s=events;events="";return s;}return "0";}
}''')
pref=out/'SharedPreferences.java';pref.write_text('''package android.content;
public interface SharedPreferences {String getString(String key,String fallback);Editor edit();interface Editor {Editor putString(String key,String value);void apply();}}''')
subprocess.run(['javac','-cp',str(menu)+':'+str(jar),'-d',str(out),str(bridge),str(pref),*[str(src/(n+'.java'))for n in ['GameLanguage','PortText','NativeCampaign','ControlSettings']],str(r/'tests/Presentation77Test.java')],check=True)
p=subprocess.run(['java','-cp',str(out)+':'+str(menu)+':'+str(jar),'org.openbw.androidtest.Presentation77Test'],capture_output=True,text=True);print(p.stdout+p.stderr);p.check_returncode()
files=[src/(n+'.java')for n in ['NativeCampaign','ControlSettings','NativeSurface','MainActivity']]+[r/'tests/Presentation77Test.java',Path(__file__)]
(r/'validation/presentation-v77.json').write_text(json.dumps({'passed':True,'physicalAndroid':False,'output':p.stdout.strip(),'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest()for f in files}},indent=2)+'\n')

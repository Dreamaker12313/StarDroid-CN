#!/usr/bin/env python3
"""Exercise bounded native tombstone parsing and persistent Android crash reports."""
from pathlib import Path
import hashlib, json, subprocess, re
r = Path(__file__).resolve().parents[1]
b = r/'build-native/crash67'
src = r/'app/src/main/java/org/openbw/androidtest'
stubs = {
'android/annotation/TargetApi.java': 'package android.annotation; public @interface TargetApi {int value();}',
'android/os/Build.java': 'package android.os; public class Build {public static class VERSION {public static int SDK_INT=30;}}',
'android/os/Debug.java': 'package android.os; public class Debug {public static long getNativeHeapAllocatedSize(){return 12345678;}}',
'android/os/Process.java': 'package android.os; public class Process {public static int myPid(){return 123;}public static void killProcess(int p){throw new AssertionError("Must delegate to Android handler");}}',
'android/content/Context.java': '''package android.content; import java.io.File;public class Context {
 public static final String ACTIVITY_SERVICE="activity"; public final File dir;
 public Context(File d){dir=d;dir.mkdirs();}public File getFilesDir(){return dir;}
 public Object getSystemService(String n){return android.app.ActivityManager.manager;}
 public String getPackageName(){return "org.openbw.androidtest";}}
''',
'android/util/AtomicFile.java': '''package android.util;import java.io.*;import java.nio.file.*;
 public class AtomicFile {private final File f; public AtomicFile(File f){this.f=f;}
 public File getBaseFile(){return f;}public byte[] readFully()throws IOException{return Files.readAllBytes(f.toPath());}
 public FileOutputStream startWrite()throws IOException{return new FileOutputStream(f);}
 public void finishWrite(FileOutputStream s)throws IOException{s.close();}public void failWrite(FileOutputStream s)throws IOException{s.close();}}
''',
'android/app/ApplicationExitInfo.java': '''package android.app;public class ApplicationExitInfo {
 public static final int REASON_CRASH_NATIVE=5;public byte[] trace;public boolean traceError;final int r,s;final String d;public ApplicationExitInfo(int r,int s,String d){this.r=r;this.s=s;this.d=d;}
 public java.io.InputStream getTraceInputStream()throws java.io.IOException{if(traceError)throw new java.io.IOException("test unavailable");return trace==null?null:new java.io.ByteArrayInputStream(trace);}public long getTimestamp(){return 1792857600000L;}public int getReason(){return r;}public int getStatus(){return s;}
 public int getImportance(){return 100;}public long getPss(){return 120000;}public long getRss(){return 200000;}public String getDescription(){return d;}}
''',
'android/app/ActivityManager.java': '''package android.app;import java.util.*;public class ActivityManager {
 public static ActivityManager manager=new ActivityManager();public boolean fail;
 public List<ApplicationExitInfo> history=new ArrayList<>();
 public List<ApplicationExitInfo> getHistoricalProcessExitReasons(String p,int pid,int max){
 if(!p.equals("org.openbw.androidtest")||pid!=0||max!=8)throw new AssertionError("Wrong exit query scope");
 if(fail)throw new SecurityException("Unavailable");return history;}
 public static class RunningAppProcessInfo{public static final int IMPORTANCE_FOREGROUND=100;}
 public static class MemoryInfo{public long availMem=1000000000L,totalMem=4000000000L;public boolean lowMemory;}
 public void getMemoryInfo(MemoryInfo i){}}
''',
'org/openbw/androidtest/BuildConfig.java': 'package org.openbw.androidtest; public class BuildConfig {public static final String VERSION_NAME="1.0";public static final int VERSION_CODE=67;}',
'org/openbw/androidtest/AppDiagnosticsTest.java': '''package org.openbw.androidtest;
import android.content.Context;import android.app.*;import android.os.Build;import java.io.File;
public class AppDiagnosticsTest {
 static int checks;static void check(boolean b,String message){checks++;if(!b)throw new AssertionError(message);}
 public static void main(String[]args){Context c=new Context(new File(args[1]));final int[] delegated={0};
 Thread.setDefaultUncaughtExceptionHandler((t,e)->delegated[0]++);
 AppDiagnostics.install(c);Thread.UncaughtExceptionHandler installed=Thread.getDefaultUncaughtExceptionHandler();
 AppDiagnostics.install(c);check(installed==Thread.getDefaultUncaughtExceptionHandler(),"Install only once");
 if(args[0].equals("read")){
  String s=AppDiagnostics.summary(c);check(s.contains("simulated allocation failure"),"Persist failure across process restart");
  check(s.contains("Page: game; multiplayer=guest"),"Persist last gameplay context");
  check(s.contains("libopenbw.so")&&s.contains("game_step"),"Persist Android native stack across restart");
 }else{
  Build.VERSION.SDK_INT=29;AppDiagnostics.loadPreviousExits(c);
  check(AppDiagnostics.summary(c).contains("requires Android 11"),"Old Android guard");
  Build.VERSION.SDK_INT=30;AppDiagnostics.loadPreviousExits(c);
  check(AppDiagnostics.summary(c).contains("does not rule out"),"No history is not no crash");
  ActivityManager.manager.history.add(new ApplicationExitInfo(3,0,"low memory"));
  ActivityManager.manager.history.add(new ApplicationExitInfo(2,9,""));
  ActivityManager.manager.history.add(new ApplicationExitInfo(16,0,null));
  AppDiagnostics.loadPreviousExits(c);String s=AppDiagnostics.summary(c);
  check(s.contains("Android low-memory kill"),"Read low memory record");
  check(s.contains("not confirmed"),"Unattributed SIGKILL");check(s.contains("App updated"),"Keep update separate");
  check(s.contains("(foreground)"),"Process importance");
  check(s.contains("not memory at the previous close"),"Do not confuse current and previous memory");
  ApplicationExitInfo nativeCrash=new ApplicationExitInfo(5,11,"crash");
  ActivityManager.manager.history.add(0,nativeCrash);
  AppDiagnostics.loadPreviousExits(c);check(AppDiagnostics.summary(c).contains("requires Android 12"),"Guard native traces on Android 11");
  Build.VERSION.SDK_INT=31;AppDiagnostics.loadPreviousExits(c);
  check(AppDiagnostics.summary(c).contains("no longer available"),"Missing Android trace is explicit");
  nativeCrash.traceError=true;AppDiagnostics.loadPreviousExits(c);
  check(AppDiagnostics.summary(c).contains("test unavailable"),"Unreadable trace preserves exit reason");nativeCrash.traceError=false;
  nativeCrash.trace=NativeCrashTraceTest.sample();AppDiagnostics.loadPreviousExits(c);
  check(AppDiagnostics.summary(c).contains("game_step"),"Decode faulting stack in real diagnostics integration");
  nativeCrash.trace=null;AppDiagnostics.loadPreviousExits(c);
  check(AppDiagnostics.summary(c).contains("game_step"),"Keep saved native trace when Android prunes its buffer");
  ActivityManager.manager.fail=true;AppDiagnostics.loadPreviousExits(c);
  check(AppDiagnostics.summary(c).contains("unavailable: SecurityException"),"OEM query failure does not crash app");
  AppDiagnostics.foreground(true);AppDiagnostics.memoryPressure(10);AppDiagnostics.session("Page: game; multiplayer=guest");
  installed.uncaughtException(Thread.currentThread(),new OutOfMemoryError("simulated allocation failure"));
  check(delegated[0]==1,"Original Android crash handler still called once");
  check(new File(c.getFilesDir(),"last-failure.txt").length()>0,"Failure persisted");
  check(AppDiagnostics.summary(c).contains("onTrimMemory level 10"),"Memory callback included");
 }
 System.out.println("PASS "+checks+" "+args[0]+" diagnostics checks");}}
'''
}
paths=[]
for name,content in stubs.items():
 p=b/'stubs'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content);paths.append(p)
production=[src/'AppDiagnostics.java',src/'ExitReport.java',src/'NativeCrashTrace.java']
subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-nowarn','-d',str(b/'classes'),*map(str,production+paths+[r/'tests/ExitReportTest.java',r/'tests/NativeCrashTraceTest.java'])],check=True)
outputs=[]
for name,args in [('ExitReportTest',[]),('NativeCrashTraceTest',[]),('AppDiagnosticsTest',['write',str(b/'private')]),('AppDiagnosticsTest',['read',str(b/'private')])]:
 p=subprocess.run(['java','-cp',str(b/'classes'),'org.openbw.androidtest.'+name,*args],capture_output=True,text=True,check=True)
 print(p.stdout.strip());outputs.append(p.stdout.strip())
files=production+[r/'tests/ExitReportTest.java',r/'tests/NativeCrashTraceTest.java',Path(__file__),src/'MainActivity.java',src/'NativeSurface.java']
report={'passed':True,'version':'1.0','versionCode':67,'physicalDeviceTested':False,'output':outputs,
 'limitations':'Host Android API fakes and AOSP-wire fixtures exercise SDK guards, scoped/empty/unavailable history, native trace retrieval, reason labels, original uncaught-handler delegation, persistent native/Java reports across separate JVMs, selected-thread decoding, unknown fields, privacy and malformed/oversized input bounds. Actual Android device traces remain pending.',
 'sourceSha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(r/'validation/native-crash-trace-v1.0.json').write_text(json.dumps(report,indent=2)+'\n')

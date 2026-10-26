#!/usr/bin/env python3
"""Exercise verified import-only relocation and failures without Android/storage mocks."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
r=Path(__file__).resolve().parents[1];src=r/'app/src/main/java/org/openbw/androidtest'
with tempfile.TemporaryDirectory(prefix='stardroid-storage-') as tmp:
 b=Path(tmp)
 h=b/'StorageTest.java';h.write_text(r'''package org.openbw.androidtest;
import java.io.*;import java.nio.file.*;import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
public class StorageTest{
 static int checks;static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static void put(File dir,String name,int size)throws Exception{File p=new File(dir,name);p.getParentFile().mkdirs();byte[] bytes=new byte[size];for(int i=0;i<size;i++)bytes[i]=(byte)(i*31);Files.write(p.toPath(),bytes);}
 static File folder(File base,String name){File f=new File(base,name);f.mkdirs();return f;}
 static void fail(Work w)throws Exception{boolean rejected=false;try{w.run();}catch(IOException e){rejected=true;}check(rejected,"Expected safe failure");}interface Work{void run()throws Exception;}
 public static void main(String[]args)throws Exception{
 File base=new File(args[0]);
 for(Object[] c:CampaignCatalog.ALL){String id=(String)c[1],name="StarDroid-"+Character.toUpperCase(id.charAt(0))+id.substring(1)+".zip";check(ImportedDataMove.imported(name),name);check(ImportedDataMove.imported(name.replace("StarDroid-","OpenBW-")),"legacy "+name);}
 for(String name:new String[]{"saves","multiplayer","replays","last-failure.txt","last-native-crash.txt","unknown.zip","StarDroid-source.zip"})check(!ImportedDataMove.imported(name),"Private/unknown data selected "+name);
 File a=folder(base,"internal"),b=folder(base,"card");put(a,"mpq/STARDAT.MPQ",180000);put(a,"melee-maps/abc.scx",50000);put(a,"melee-maps/abc.name",20);put(a,"StarDroid-Expzerg03.zip",300);put(a,"OpenBW-Terrantutorial.zip",100);put(a,"StarDroid-Cinematics-BroodWar.zip",123);put(a,"saves/slot-1.obwsave",70);put(a,"replays/match.rep",35);put(a,"last-failure.txt",20);
 int[] commits={0};ImportedDataMove.move(a,b,999999999L,()->{},()->commits[0]++,(d,t)->{});check(commits[0]==1,"Commit count");check(!new File(a,"mpq/STARDAT.MPQ").exists(),"Original retained after verified commit");check(new File(b,"mpq/STARDAT.MPQ").length()==180000,"Archive changed");check(new File(a,"saves/slot-1.obwsave").length()==70&&!new File(b,"saves").exists(),"Save moved");check(new File(a,"replays/match.rep").length()==35,"Replay moved");check(new File(b,"OpenBW-Terrantutorial.zip").length()==100,"Legacy tutorial missing");
 ImportedDataMove.move(b,a,999999999L,()->{},()->commits[0]++,(d,t)->{});check(new File(a,"mpq/STARDAT.MPQ").length()==180000&&!new File(b,"mpq/STARDAT.MPQ").exists(),"Move back");
 File low=folder(base,"low");fail(()->ImportedDataMove.move(a,low,ImportedDataMove.RESERVE,()->{},()->commits[0]++,(d,t)->{}));check(commits[0]==2&&new File(a,"mpq/STARDAT.MPQ").exists(),"Low space changed selection/source");
 File conflict=folder(base,"conflict");put(conflict,"mpq/STARDAT.MPQ",5);fail(()->ImportedDataMove.move(a,conflict,999999999L,()->{},()->commits[0]++,(d,t)->{}));check(new File(conflict,"mpq/STARDAT.MPQ").length()==5,"Overwrote conflicting file");
 File stale=folder(base,"stale");put(stale,"StarDroid-Interface.zip",7);fail(()->ImportedDataMove.move(a,stale,999999999L,()->{},()->commits[0]++,(d,t)->{}));check(commits[0]==2&&new File(stale,"StarDroid-Interface.zip").length()==7,"Destination-only data was mixed");
 fail(()->ImportedDataMove.move(a,new File(a,"nested"),999999999L,()->{},()->commits[0]++,(d,t)->{}));check(!new File(a,"nested").exists(),"Nested destination created");
 File interrupted=folder(base,"interrupted");int[] calls={0};fail(()->ImportedDataMove.move(a,interrupted,999999999L,()->{if(++calls[0]>6)throw new IOException("Removed card");},()->commits[0]++,(d,t)->{}));check(commits[0]==2&&new File(a,"mpq/STARDAT.MPQ").exists(),"Unplug changed selection/source");
 fail(()->ImportedDataMove.move(a,interrupted,999999999L,()->{},()->{throw new IOException("Cannot persist");},(d,t)->{}));check(new File(a,"mpq/STARDAT.MPQ").exists(),"Failed preference deleted source");
 ImportedDataMove.move(a,interrupted,999999999L,()->{},()->commits[0]++,(d,t)->{});check(commits[0]==3&&!new File(a,"mpq/STARDAT.MPQ").exists(),"Retry identical partial copies failed");
 File corrupt=folder(base,"corrupt");fail(()->ImportedDataMove.move(interrupted,corrupt,999999999L,()->{},()->commits[0]++,(d,t)->{if(d==t)try{put(corrupt,"mpq/STARDAT.MPQ",2);}catch(Exception e){throw new RuntimeException(e);}}));check(commits[0]==3&&new File(interrupted,"mpq/STARDAT.MPQ").exists(),"Verification failure deleted source");
 File syms=folder(base,"syms"),outside=folder(base,"outside");Files.createSymbolicLink(new File(syms,"mpq").toPath(),outside.toPath());fail(()->ImportedDataMove.move(syms,folder(base,"safe"),999999999L,()->{},()->commits[0]++,(d,t)->{}));
 File source=folder(base,"postcommit"),dest=folder(base,"gone");put(source,"mpq/test.mpq",100);boolean[] selected={false};ImportedDataMove.move(source,dest,999999999L,()->{if(selected[0])throw new IOException("Unmounted after commit");},()->selected[0]=true,(d,t)->{});check(selected[0]&&new File(source,"mpq/test.mpq").exists()&&new File(dest,"mpq/test.mpq").exists(),"Unplug during cleanup lost data");
 // A replacement Activity must observe the process lease through post-commit cleanup.
 File changing=folder(base,"lifecycle-source"),changed=folder(base,"lifecycle-destination");put(changing,"mpq/game.mpq",100000);
 GameDataOperation.Lease originalActivity=GameDataOperation.begin("Moving game data…");check(originalActivity!=null&&GameDataOperation.moving(),"Cannot acquire move ownership");
 CountDownLatch cleaning=new CountDownLatch(1),allowCleanup=new CountDownLatch(1);AtomicBoolean committed=new AtomicBoolean();AtomicReference<Throwable> fault=new AtomicReference<>();
 Thread oldActivityWorker=new Thread(()->{try{ImportedDataMove.move(changing,changed,999999999L,()->{if(committed.get()){cleaning.countDown();try{if(!allowCleanup.await(5,TimeUnit.SECONDS))throw new IOException("Timeout");}catch(InterruptedException e){throw new IOException(e);}}},()->committed.set(true),(d,t)->GameDataOperation.update(originalActivity,"Moving game data… "+d+" / "+t));}catch(Throwable t){fault.set(t);}finally{GameDataOperation.finish(originalActivity,"Game data moved.");}});
 oldActivityWorker.start();check(cleaning.await(5,TimeUnit.SECONDS),"Did not reach cleanup");check(GameDataOperation.busy(),"Recreated Activity sees idle during cleanup");
 check(GameDataOperation.begin("Importing selected files…")==null,"Replacement Activity imported during move");check(GameDataOperation.begin("Moving game data…")==null,"Opposite move overlapped cleanup");check(GameDataOperation.begin("Reading map pack…")==null,"Map import overlapped cleanup");
 allowCleanup.countDown();oldActivityWorker.join(5000);check(!oldActivityWorker.isAlive()&&fault.get()==null&&!GameDataOperation.busy(),"Operation not completed safely");check(new File(changed,"mpq/game.mpq").length()==100000&&!new File(changing,"mpq/game.mpq").exists(),"Lifecycle move did not retain selected data");
 GameDataOperation.Lease replacement=GameDataOperation.begin("Importing selected files…");check(replacement!=null,"Replacement cannot import after completion");GameDataOperation.finish(originalActivity,"stale callback");GameDataOperation.update(originalActivity,"stale progress");check(GameDataOperation.busy()&&GameDataOperation.message().equals("Importing selected files…"),"Stale Activity unlocked/overwrote newer operation");GameDataOperation.finish(replacement,"");
 CountDownLatch start=new CountDownLatch(1),claimed=new CountDownLatch(20),release=new CountDownLatch(1);AtomicInteger winners=new AtomicInteger();ArrayList<Thread> contenders=new ArrayList<>();
 for(int n=0;n<20;n++){Thread thread=new Thread(()->{try{start.await();GameDataOperation.Lease lease=GameDataOperation.begin("Importing selected files…");if(lease!=null)winners.incrementAndGet();claimed.countDown();release.await();if(lease!=null)GameDataOperation.finish(lease,"");}catch(InterruptedException e){throw new RuntimeException(e);}});contenders.add(thread);thread.start();}
 start.countDown();check(claimed.await(5,TimeUnit.SECONDS)&&winners.get()==1,"Concurrent Activities acquired overlapping mutations");release.countDown();for(Thread thread:contenders)thread.join(5000);check(!GameDataOperation.busy(),"Concurrent lease leaked");
 System.out.println("PASS "+checks+" storage checks: all campaign names; legacy imports; private-file isolation; bidirectional verified move; space/conflict/unplug/commit/corruption/symlink failures; safe retry and postcommit preservation");
 }
}''')
 java_home=Path(os.environ.get('JAVA_HOME',r/'.tools/jdk17/usr/lib/jvm/java-17-openjdk-amd64'))
 javac=str(java_home/'bin/javac') if (java_home/'bin/javac').exists() else 'javac'
 java=str(java_home/'bin/java') if (java_home/'bin/java').exists() else 'java'
 subprocess.run([javac,'-d',str(b),str(h),str(src/'ImportedDataMove.java'),str(src/'CampaignCatalog.java'),str(src/'GameDataOperation.java')],check=True)
 result=subprocess.run([java,'-cp',str(b),'org.openbw.androidtest.StorageTest',str(b/'fixtures')],text=True,capture_output=True,check=True);print(result.stdout,end='')
 activity=(src/'MainActivity.java').read_text()
 def method(signature):
  at=activity.index(signature);end=activity.index('{',at);depth=1;end+=1
  while depth:
   if activity[end]=='{':depth+=1
   elif activity[end]=='}':depth-=1
   end+=1
  return activity[at:end]
 ui=b/'StorageLifecycleTest.java';ui.write_text("""package org.openbw.androidtest;
public class StorageLifecycleTest {
 static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
 static class GameDataStorage {static boolean available(Host host){return host.card;}}
 static class FrameLayout {static class LayoutParams {LayoutParams(int a,int b){}}}
 static class Root {void removeAllViews(){} void addView(NativeSurface view,FrameLayout.LayoutParams params){}}
 static class NativeSurface {int titles,resumes,suspends,reopens;boolean failReopen;NativeSurface(Host h){}void reopenStorage(Runnable ready,java.util.function.Consumer<String> failed){reopens++;if(failReopen)failed.accept("Missing card");else ready.run();}void title(){titles++;}void resume(){resumes++;}void suspend(){suspends++;}void requestFocus(){}}
 static class Host {boolean optionsVisible=true,activityResumed=true,storageSuspendedGame,card=true,importing,mapImportRunning;String notice;NativeSurface game;Root root=new Root();
 boolean isDestroyed(){return false;}boolean ready(){return card;}void refreshDisplayArea(){}void showHome(){optionsVisible=true;if(game!=null)game.suspend();}
 """+method('private boolean busy()')+method('private void showStorageUnavailable()')+method('private void startTitle()')+"""
 }
 public static void main(String[] args){
 Host active=new Host();NativeSurface original=active.game=new NativeSurface(active);active.optionsVisible=false;active.card=false;active.showStorageUnavailable();check(active.storageSuspendedGame&&original.suspends==1,"Missing card did not suspend live game");active.startTitle();check(original.resumes==0&&original.titles==0,"Unavailable card resumed/reset game");active.card=true;active.startTitle();check(active.game==original&&original.resumes==1&&original.reopens==1&&original.titles==0&&!active.storageSuspendedGame,"Reinsert lost live match/replay");
 active.optionsVisible=false;active.showStorageUnavailable();original.failReopen=true;active.startTitle();check(active.game==original&&active.storageSuspendedGame&&original.resumes==1&&original.titles==0&&active.optionsVisible,"Failed reopen discarded or resumed live game");original.failReopen=false;active.startTitle();check(original.resumes==2&&!active.storageSuspendedGame,"Reopen retry failed");
 Host inactive=new Host();inactive.card=false;inactive.showStorageUnavailable();check(!inactive.storageSuspendedGame,"Missing card invented suspended game");inactive.card=true;inactive.startTitle();check(inactive.game!=null&&inactive.game.resumes==1,"Inactive reinsertion did not start game normally");
 Host regular=new Host();regular.game=new NativeSurface(regular);regular.startTitle();check(regular.game.titles==1,"Ordinary menu return changed");
 GameDataOperation.Lease lease=GameDataOperation.begin("Moving game data…");Host recreated=new Host();recreated.startTitle();check(recreated.game==null&&recreated.optionsVisible,"New Activity started native reader during move");GameDataOperation.finish(lease,"");recreated.startTitle();check(recreated.game!=null,"New Activity remained blocked after move");
 System.out.println("PASS production lifecycle methods: card removal/reinsertion preserves live match; inactive start; recreated-Activity native startup gate");
 }
} """)
 subprocess.run([javac,'-cp',str(b),'-d',str(b),str(ui)],check=True)
 lifecycle=subprocess.run([java,'-cp',str(b),'org.openbw.androidtest.StorageLifecycleTest'],text=True,capture_output=True,check=True);print(lifecycle.stdout,end='')
 assert 'if (ready() && !busy()) startTitle();' in activity
 assert 'if(busy())showHome();' in method('protected void onResume()')
 android_jar=r/'.tools/android-35/android.jar'
 stub=b/'BuildConfig.java';stub.write_text('package org.openbw.androidtest; final class BuildConfig {static final String VERSION_NAME="1.1"; static final int VERSION_CODE=83;}')
 android_compile=subprocess.run([javac,'-source','8','-target','8','-encoding','UTF-8','-cp',str(android_jar),'-d',str(b/'android'),str(stub),*map(str,sorted(src.glob('*.java')))],text=True,capture_output=True)
 if android_compile.returncode:print(android_compile.stdout+android_compile.stderr)
 android_compile.check_returncode()
 print('PASS Android SDK 35 compilation of all production Java classes (Java 8 target)')
 rows=[line.split('\t') for line in (r/'app/src/main/assets/native/ui-languages.tsv').read_text().splitlines() if line and not line.startswith('#')]
 assert all(len(row)==5 and all(row) for row in rows)
 for key in ['Game data storage','Internal storage','SD card','Change data storage','Move game data','Moving game data…','Game data moved.']:
  row=next(row for row in rows if row[0]==key);assert all(value!=key for value in row[1:]),key
 names=['app/src/main/java/org/openbw/androidtest/GameDataOperation.java','app/src/main/java/org/openbw/androidtest/ImportedDataMove.java','app/src/main/java/org/openbw/androidtest/GameDataStorage.java','app/src/main/java/org/openbw/androidtest/MainActivity.java','app/src/main/java/org/openbw/androidtest/NativeSurface.java','app/src/main/assets/native/ui-languages.tsv','tests/run_data_storage11.py']
 (r/'validation/data-storage11.json').write_text(json.dumps({'passed':True,'physicalSdCardTested':False,'androidSdk35JavaCompile':True,'storageTranslations':'en, ru, de, es, fr','scope':'Pure Java verified migration, real filesystem; Android integration checked separately by Android SDK Java compilation','result':result.stdout.strip(),'lifecycle':lifecycle.stdout.strip(),'sourceSha256':{n:hashlib.sha256((r/n).read_bytes()).hexdigest()for n in names}},indent=2)+'\n')

package org.openbw.androidtest;
import android.content.*;
import android.graphics.*;
import android.os.*;
import java.io.*;
import java.util.*;
/** Original ready-room artwork, moving panel separation and hover compositing. */
public final class NativeBriefingInstrumentation extends NativeInstrumentation {
  private Bundle args;
  @Override public void onCreate(Bundle b){args=b;super.onCreate(b);}
  void pass(String key)throws Exception{report.put(key,true);save();}
  Bitmap render(NativeGlue glue,double time,int hot,String name)throws Exception{
    glue.elapsed=time;glue.animationElapsed=time;glue.hot=hot;
    Bitmap bitmap=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(bitmap);glue.draw(canvas,0);
    for(int id:new int[]{13,14,20,65535})glue.label(canvas,id,null,true);
    try(FileOutputStream out=new FileOutputStream(new File(output,name+".png"))){bitmap.compress(Bitmap.CompressFormat.PNG,100,out);}return bitmap;
  }
  @Override public void onStart(){Bundle result=new Bundle();try{
    output=new File(getTargetContext().getExternalFilesDir(null),"native-briefing39");output.mkdirs();recordPackageHashes();
    report.put("version",getTargetContext().getPackageManager().getPackageInfo("org.openbw.androidtest",0).versionName);report.put("originalGameAssets",true);
    MainActivity activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));waitForIdleSync();
    runOnMainSync(()->{game=new NativeSurface(activity);game.shutdown();});((Thread)field(game,"worker")).join(15000);
    check(!((Thread)field(game,"worker")).isAlive(),"Background engine still running");
    String dir=args.getString("dataDir");String[] core={"StarDat.mpq","BrooDat.mpq","patch_rt.mpq"};
    for(int i=0;i<3;i++)NativeBridge.open(i,new File(dir,core[i]).getPath());
    NativeArt art=new NativeArt();set(game,"art",art);set(game,"modal","");set(game,"page","briefing");
    for(String race:new String[]{"t","z","p"}){
      NativeGlue glue=new NativeGlue(art,"glurdy"+race,"palr"+race,true);set(game,"glue",glue);
      if(race.equals("p")){check(!glue.fixedPanelDecorations.containsKey(5)&&!glue.movingPanels.containsKey(5),"Protoss replay base is still split");pass("protossReplayBaseSlidesWithButton");}else{
      Bitmap moving=glue.movingPanels.get(5),fixed=glue.fixedPanelDecorations.get(5);check(moving!=null&&fixed!=null,"Replay support was not separated");
      int supportPixels=0,buttonPixels=0;for(int y=0;y<moving.getHeight();y++)for(int x=0;x<moving.getWidth();x++){
        if(y>=Math.min(moving.getHeight(),glue.layout.get(20).y+glue.layout.get(20).h+8-glue.layout.get(5).y)){check((moving.getPixel(x,y)>>>24)==0,"Scenery still slides with Replay");if((fixed.getPixel(x,y)>>>24)!=0)supportPixels++;}
        else{check((fixed.getPixel(x,y)>>>24)==0,"Stationary decoration duplicates Replay frame");if((moving.getPixel(x,y)>>>24)!=0)buttonPixels++;}
      }
      check((race.equals("t")||supportPixels>200)&&buttonPixels>200,"Panel separation lost artwork");pass(race+"ReplaySupportStaysFixed");
      }
      render(glue,250,-1,race+"-sliding").recycle();
      for(NativeGlue.Layer l:glue.layers)check(glue.shift(l.widget)==0,"Background animation slides with controls");Bitmap idle=render(glue,1000,-1,race+"-idle");
      RectF start=glue.layout.get(13).hit();call(game,"updateHover",new Class<?>[]{float.class,float.class,boolean.class},start.centerX(),start.centerY(),false);
      check(glue.hot==13,"Start response region does not activate hover");
      Bitmap hot=render(glue,1000,13,race+"-hover");NativeGlue.Layer layer=null;
      for(NativeGlue.Layer l:glue.layers)if(l.spec.name.endsWith(!race.equals("p")?"/starton.smk":"/glow.smk"))layer=l;
      check(layer!=null,"Original hover movie unavailable");int matched=0,count=0,changed=0;
      int ox=layer.widget.x+layer.spec.x,oy=layer.widget.y+layer.spec.y;
      // Compare the visible crystal, outside the portrait/dialogue frames.
      for(int y=Math.max(0,275-oy);y<layer.movie.bitmap.getHeight()&&oy+y<355;y++)for(int x=Math.max(0,470-ox);x<layer.movie.bitmap.getWidth()&&ox+x<640;x++){
        int expected=layer.movie.bitmap.getPixel(x,y);if((expected>>>24)==255){count++;if(hot.getPixel(ox+x,oy+y)==expected)matched++;}
        if(hot.getPixel(ox+x,oy+y)!=idle.getPixel(ox+x,oy+y))changed++;
      }
      check(count>1000&&matched>count*.99,"Hover movie is overwritten or incorrectly blended: "+matched+"/"+count);
      check(changed>100,"Start hover does not visibly change");pass(race+"StartUsesOriginalHoverPixels");
      call(game,"updateHover",new Class<?>[]{float.class,float.class,boolean.class},0f,0f,true);check(glue.hot==-1,"Hover exit stuck");
      if(race.equals("t")) {
        check(layer.spec.x==-2&&layer.spec.y==7,"Terran hover movie is misaligned");
        int projector=0;for(int y=420;y<470;y++)for(int x=530;x<625;x++)if(idle.getPixel(x,y)==hot.getPixel(x,y))projector++;
        check(projector>4700,"Start hover changes projector hardware");
        layer.hotTime=800;Bitmap animated=render(glue,1000,13,"t-hover-animated");int movingPixels=0;
        for(int y=270;y<390;y++)for(int x=470;x<630;x++)if(animated.getPixel(x,y)!=hot.getPixel(x,y))movingPixels++;
        check(movingPixels>100,"Terran hover animation is frozen");animated.recycle();
        render(glue,2500,-1,"t-projector-loop").recycle();
        glue.exiting=true;render(glue,150,-1,"t-exiting").recycle();
        pass("terranProjectorBehindAnimatedPlanetDuringHoverAndExit");
      }
      hot.recycle();idle.recycle();glue.close();set(game,"glue",null);
    }
    NativeBridge.close();report.put("passed",true);save();result.putString("result","PASS briefing animation and hover");
  }catch(Throwable e){try{report.put("passed",false).put("error",android.util.Log.getStackTraceString(e));save();}catch(Exception ignored){}result.putString("error",e.toString());}
    finish(report.optBoolean("passed")?0:1,result);
  }
}

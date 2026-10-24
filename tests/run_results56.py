#!/usr/bin/env python3
"""Render actual Java result/glue classes on a small AWT Canvas shim (not a device test)."""
from pathlib import Path
import subprocess, json, hashlib, sys, os
r=Path(__file__).resolve().parents[1];b=r/'build-native/results56';b.mkdir(parents=True,exist_ok=True)
# Extract only UI fixtures from the caller's own archives; never bundle them.
assets=r/'build-native/assets56';assets.mkdir(exist_ok=True)
data=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else r/'build-native/game-data'
extract=b/'extract-interface'
subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-O0','-I'+str(r/'native-engine'),str(r/'tests/extract_interface46.cpp'),'-o',str(extract)],check=True,capture_output=True)
names=['rez/gluscore.bin','rez/glucustm.bin']
for key in ('tv','td','zv','zd','pv','pd'):
 names += ['glue/pal'+key+'/'+n+'.pcx'for n in ('backgnd','tfont','teffect')]
 names += ['glue/score'+key+'/iscore.grp']
 names += ['glue/score'+key+'/'+n+'.pcx'for n in ('pmain','pinset','scorebox','untab')]
names += ['glue/palnl/'+n+'.pcx'for n in ('backgnd','tfont','teffect','pcancel','pok')]
names += ['glue/create/'+n+'.pcx'for n in ('plistmap2','pinfo','pslots')]
names += [prefix+'font'+n+'.fnt'for prefix in ('font/','files/font/')for n in ('8','10','14','16','16x')]
for name in names:
 target=assets/name;target.parent.mkdir(parents=True,exist_ok=True)
 for archive in ('patch_rt.mpq','BROODAT.MPQ','STARDAT.MPQ'):
  if subprocess.run([str(extract),str(data/archive),name,str(target)],capture_output=True).returncode==0:break
# Ready-room fixture verifies that the entire Protoss Replay PCX moves.
raw=b''
for archive in ('patch_rt.mpq','BROODAT.MPQ','STARDAT.MPQ'):
 target=assets/'rez/glurdyp.bin'
 if subprocess.run([str(extract),str(data/archive),'rez/glurdyp.bin',str(target)],capture_output=True).returncode==0:raw=target.read_bytes();break
ready_names=['glue/palrp/'+n+'.pcx'for n in ('backgnd','tfont','teffect')]
pos=int.from_bytes(raw[66:70],'little')
while pos:
 offset=int.from_bytes(raw[pos+20:pos+24],'little');label=raw[offset:raw.index(b'\0',offset)].decode('cp1252') if offset else ''
 if label.lower().endswith('.pcx'):ready_names.append(label.replace('\\','/').lower())
 pos=int.from_bytes(raw[pos:pos+4],'little')
for name in ready_names:
 target=assets/name;target.parent.mkdir(parents=True,exist_ok=True)
 for archive in ('patch_rt.mpq','BROODAT.MPQ','STARDAT.MPQ'):
  if subprocess.run([str(extract),str(data/archive),name,str(target)],capture_output=True).returncode==0:break
sources={
'android/graphics/Bitmap.java':'''package android.graphics; import java.awt.image.*;public class Bitmap { public BufferedImage image; public enum Config{ARGB_8888} public Bitmap(int w,int h){image=new BufferedImage(w,h,BufferedImage.TYPE_INT_ARGB);} public static Bitmap createBitmap(int w,int h,Config c){return new Bitmap(w,h);}public static Bitmap createBitmap(int[]p,int w,int h,Config c){Bitmap b=new Bitmap(w,h);b.image.setRGB(0,0,w,h,p,0,w);return b;}public int getWidth(){return image.getWidth();}public int getHeight(){return image.getHeight();}public int getPixel(int x,int y){return image.getRGB(x,y);}public void getPixels(int[]p,int o,int stride,int x,int y,int w,int h){image.getRGB(x,y,w,h,p,o,stride);}public void recycle(){} }''',
'android/graphics/RectF.java':'''package android.graphics;public class RectF{public float left,top,right,bottom;public RectF(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}public float width(){return right-left;}public float height(){return bottom-top;}public void offset(float x,float y){left+=x;right+=x;top+=y;bottom+=y;}public boolean contains(float x,float y){return x>=left&&x<right&&y>=top&&y<bottom;}}''',
'android/graphics/Color.java':'''package android.graphics;public class Color{public static int WHITE=0xffffffff;public static int rgb(int r,int g,int b){return 0xff000000|r<<16|g<<8|b;}public static int red(int c){return c>>16&255;}public static int green(int c){return c>>8&255;}public static int blue(int c){return c&255;}}''',
'android/graphics/Typeface.java':'''package android.graphics;public class Typeface{public static Typeface MONOSPACE=new Typeface();}''',
'android/graphics/Paint.java':'''package android.graphics;public class Paint{public static int ANTI_ALIAS_FLAG=1; public int color=0xff000000,alpha=255;public float size=16;public Paint(){}public Paint(int f){}public void setColor(int c){color=c;}public void setTextSize(float v){size=v;}public void setTypeface(Typeface t){}public void setColorFilter(ColorMatrixColorFilter c){}public void setAlpha(int a){alpha=a;}public void setXfermode(PorterDuffXfermode x){}}''',
'android/graphics/Canvas.java':'''package android.graphics;import java.awt.*;import java.awt.geom.*;import java.util.*;public class Canvas{Graphics2D g;ArrayList<Graphics2D>stack=new ArrayList<>();public Canvas(Bitmap b){g=b.image.createGraphics();g.setRenderingHint(RenderingHints.KEY_INTERPOLATION,RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR);}public int save(){stack.add(g);g=(Graphics2D)g.create();return stack.size();}public void restore(){g.dispose();g=stack.remove(stack.size()-1);}public void translate(float x,float y){g.translate(x,y);}public void clipRect(float l,float t,float r,float b){g.clip(new Rectangle2D.Float(l,t,r-l,b-t));}public void drawRect(float l,float t,float r,float b,Paint p){g.setColor(new java.awt.Color(p.color,true));g.fill(new Rectangle2D.Float(l,t,r-l,b-t));}public void drawBitmap(Bitmap b,float x,float y,Paint p){g.drawImage(b.image,AffineTransform.getTranslateInstance(x,y),null);}public void drawBitmap(Bitmap b,Object src,RectF dst,Paint p){AffineTransform t=AffineTransform.getTranslateInstance(dst.left,dst.top);t.scale(dst.width()/b.getWidth(),dst.height()/b.getHeight());g.drawImage(b.image,t,null);}public void drawText(String t,float x,float y,Paint p){g.setFont(new Font("Monospaced",Font.PLAIN,Math.round(p.size)));g.setColor(new java.awt.Color(p.color,true));g.drawString(t,x,y);}}''',
'android/graphics/PorterDuff.java':'''package android.graphics;public class PorterDuff{public enum Mode{DST_IN}}''',
'android/graphics/PorterDuffXfermode.java':'''package android.graphics;public class PorterDuffXfermode{public PorterDuffXfermode(PorterDuff.Mode m){}}''',
'android/graphics/ColorMatrixColorFilter.java':'''package android.graphics;public class ColorMatrixColorFilter{public ColorMatrixColorFilter(float[]m){}}''',
'org/openbw/androidtest/NativeBridge.java':'''package org.openbw.androidtest;import android.graphics.*;import java.nio.file.*;final class NativeBridge{static Path root;static byte[] asset(int i,String name){try{return Files.readAllBytes(root.resolve(name));}catch(Exception e){return null;}}static int[] movieOpen(byte[]b,boolean a){throw new UnsupportedOperationException();}static int[] movieOpenAsset(int s,String p,boolean a){throw new UnsupportedOperationException();}static void movieFrame(int i,double t,boolean l,Bitmap b){}static void movieClose(int i){}}''',
'org/openbw/androidtest/NativeHud.java':'''package org.openbw.androidtest;final class NativeHud{static int number(String[]s,int i,int d){try{return Integer.parseInt(s[i]);}catch(Exception e){return d;}}}''',
'org/openbw/androidtest/Results46Harness.java':'''package org.openbw.androidtest;
import android.graphics.*;import javax.imageio.ImageIO;import java.nio.file.*;
public class Results46Harness {
 static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
 static boolean samePixel(int a,int b){for(int shift:new int[]{0,8,16,24})if(Math.abs((a>>>shift&255)-(b>>>shift&255))>1)return false;return true;}
 static Bitmap render(NativeResults r,double dt){Bitmap b=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);r.draw(new Canvas(b),dt);return b;}
 static void save(Bitmap b,Path p)throws Exception{ImageIO.write(b.image,"png",p.toFile());}
 public static void main(String[]args)throws Exception{
 NativeBridge.root=Paths.get(args[0]);Path output=Paths.get(args[1]);NativeArt art=new NativeArt();
 String raw="1\\t38016";for(int i=0;i<8;i++)raw+="\\n"+(i==0?1:0)+"\\t"+i%3+"\\t"+i+"\\t85\\t26\\t14500\\t8900\\t3200\\t43\\t12\\t11\\t3\\t8300\\t4900\\t7200\\t6500\\t"+i+"\\t1\\t2";
 for(int race=0;race<3;race++)for(boolean won:new boolean[]{false,true}){
 NativeResults result=new NativeResults(art,race,won,raw);result.playerName="A very long player name that must fit";result.canSave=true;
 Bitmap empty=render(result,0);check(result.progress==0,"Counters start during slide");check(!result.ready(),"Clickable before entry");
 for(int y=0;y<480;y++)for(int x=0;x<640;x++)check(empty.getPixel(x,y)==result.background.image.getPixel(x,y),"Background moved before slide-in");
 Bitmap entering=render(result,335);save(entering,output.resolve(race+"-"+won+"-enter.png"));check(!result.ready(),"Early label visibility");result.animationElapsed=670;java.awt.image.BufferedImage originalBackground=result.background.image.image;result.background.image.image=new java.awt.image.BufferedImage(640,480,java.awt.image.BufferedImage.TYPE_INT_ARGB);Bitmap ui=render(result,0);result.background.image.image=originalBackground;
 Bitmap expected=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas reference=new Canvas(expected);reference.drawBitmap(result.background.image,0,0,NativeArt.PIXELS);reference.drawBitmap(ui,-80,0,NativeArt.PIXELS);
 save(expected,output.resolve(race+"-"+won+"-expected.png"));for(int yy=0;yy<480;yy++)for(int xx=0;xx<640;xx++)check(samePixel(entering.getPixel(xx,yy),expected.getPixel(xx,yy)),"UI did not slide over fixed background at "+xx+","+yy);check(result.ready(),"Entry does not complete");
 for(int tab=0;tab<4;tab++){result.tab=tab;result.progress=0;result.counting=true;result.countElapsed=0;save(render(result,NativeResults.COUNT_MS),output.resolve(race+"-"+won+"-tab"+tab+".png"));}
 check(result.barParts[0][0]!=null&&result.barParts[7][5]!=null,"Original score bars absent");result.progress=0;result.countElapsed=0;result.counting=true;render(result,1100);check(Math.abs(result.progress-.5)<.0001,"Counter does not take 2200ms");render(result,1100);check(result.progress==1,"Counter fails to finish");
 check(result.large.measure(NativeResults.fit(result.large,result.playerName,144))<=144,"Name overlaps scores");
 result.exiting=true;result.animationElapsed=0;check(!result.ready(),"Exit remains clickable");save(render(result,180),output.resolve(race+"-"+won+"-exit.png"));
 empty=render(result,185);for(int y=0;y<480;y++)for(int x=0;x<640;x++)check(empty.getPixel(x,y)==result.background.image.getPixel(x,y),"Background moved after exit");
 }
 NativeGlue ready=new NativeGlue(art,"glurdyp","palrp",true);check(ready.panels.get(5)!=null,"Missing original Protoss Replay artwork");check(!ready.fixedPanelDecorations.containsKey(5)&&!ready.movingPanels.containsKey(5),"Protoss Replay base is split");ready.elapsed=335;check(ready.shift(ready.layout.get(5))!=0,"Whole Protoss Replay panel does not slide");
 NativeGlue glue=new NativeGlue(art,"glucustm","palnl",true);
 check(glue.shift(glue.layout.get(12))==glue.shift(glue.layout.get(4)),"Custom OK separated from panel");
 check(glue.shift(glue.layout.get(20))==glue.shift(glue.layout.get(19)),"Slots separated from panel");
 check(!glue.labelVisible(13),"Custom text visible before entry");glue.elapsed=670;check(glue.labelVisible(13),"Custom label never appears");glue.exiting=true;glue.elapsed=0;check(!glue.labelVisible(13),"Custom text visible on exit");
 // Original result tint uses 252,0,252 for transparent shades 5 and 6.
 byte[] font=new byte[19];font[0]='F';font[1]='O';font[2]='N';font[3]='T';font[4]=font[5]=65;font[6]=3;font[7]=1;font[8]=12;font[12]=3;font[13]=1;font[16]=1;font[17]=5;font[18]=6;
 NativeArt.PCX tint=art.pcx("glue/paltv/tfont.pcx",false,-1), bg=art.pcx("glue/paltv/backgnd.pcx",false,-1);
 NativeArt.Font original=new NativeArt.Font(font,tint,bg.palette,1,1);
 Bitmap shaded=original.withShadedColor(0xff30e050).glyph(65,2);check(shaded.getPixel(0,0)!=0&&shaded.getPixel(1,0)==0&&shaded.getPixel(2,0)==0,"Recoloring fills transparent glyph pixels");
 Bitmap glyph=original.glyph(65,2);check(glyph.getPixel(0,0)!=0&&glyph.getPixel(1,0)==0&&glyph.getPixel(2,0)==0,"Palette transparency leaks magenta into font");
 System.out.println("PASS: six race/outcome backgrounds, 24 result tab renders, stationary background and sliding UI, entry/exit/input timing, long names, original palette transparency and custom panel grouping. Host Canvas shim; physical Android testing pending.");
 }
}'''
}
for name,text in sources.items():
 p=b/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
real=[r/'app/src/main/java/org/openbw/androidtest'/f for f in ['NativeArt.java','NativeResults.java','NativeGlue.java']]
subprocess.run(['java','-jar',str(r/'.tools/ecj.jar'),'-source','1.8','-target','1.8','-proc:none','-d',str(b/'classes'),*[str(b/n)for n in sources],*map(str,real)],check=True,capture_output=True)
p=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes'),'org.openbw.androidtest.Results46Harness',str(r/'build-native/assets56'),str(b)],capture_output=True,text=True)
print(p.stdout+p.stderr);p.check_returncode()
paths=real+[Path(__file__),r/'app/src/main/java/org/openbw/androidtest/NativeSurface.java',r/'tests/extract_interface46.cpp']
report={'passed':True,'physicalAndroid':False,'canvas':'AWT compatibility shim; actual NativeArt/NativeGlue/NativeResults classes; alpha-composition rounding tolerance 1/255','fontFixture':'Supplied core FONT entries require fallback; synthetic glyph verifies original tint transparency', 'outcomeThemes':6,'tabRenders':24,'sourceSha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}}
(r/'validation/native-results-host-v56.json').write_text(json.dumps(report,indent=2)+'\n')

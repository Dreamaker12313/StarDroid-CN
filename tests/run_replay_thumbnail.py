#!/usr/bin/env python3
"""Exercise bounded embedded-CHK preview rendering with synthetic tileset assets."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
production=root/'app/src/main/java/org/openbw/androidtest/NativeMapPreview.java'
sources={
'android/graphics/Bitmap.java':'''package android.graphics;public class Bitmap {
 public enum Config{ARGB_8888}public final int[]pixels;public final int width,height;
 Bitmap(int[]p,int w,int h){pixels=p;width=w;height=h;}
 public static Bitmap createBitmap(int[]p,int w,int h,Config c){return new Bitmap(p,w,h);}
}''',
'org/openbw/androidtest/NativeArt.java':'''package org.openbw.androidtest;class NativeArt {
 static int u16(byte[]b,int p){return (b[p]&255)|(b[p+1]&255)<<8;}
 static int u32(byte[]b,int p){return u16(b,p)|u16(b,p+2)<<16;}
}''',
'org/openbw/androidtest/NativeBridge.java':'''package org.openbw.androidtest;class NativeBridge {
 static int reads;static boolean missing;
 static byte[]asset(int slot,String name){reads++;if(missing)return null;
  if(name.endsWith(".cv5"))return new byte[52];
  if(name.endsWith(".vx4"))return new byte[32];
  if(name.endsWith(".vr4")){byte[]b=new byte[64];b[55]=7;return b;}
  byte[]b=new byte[1024];b[28]=40;b[29]=90;b[30]=120;return b;
 }
}''',
'org/openbw/androidtest/ReplayThumbnailTest.java':'''package org.openbw.androidtest;
import android.graphics.Bitmap;import java.io.*;import java.util.*;
public class ReplayThumbnailTest {
 static int checks;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static void word(byte[]b,int p,int v){b[p]=(byte)v;b[p+1]=(byte)(v>>8);}
 static byte[]join(byte[]...parts)throws Exception{ByteArrayOutputStream o=new ByteArrayOutputStream();for(byte[]b:parts)o.write(b);return o.toByteArray();}
 static byte[]chunk(String tag,byte[]data)throws Exception{byte[]head=new byte[8];System.arraycopy(tag.getBytes("US-ASCII"),0,head,0,4);word(head,4,data.length);word(head,6,data.length>>16);return join(head,data);}
 static byte[]map(int w,int h,int era)throws Exception{byte[]dim=new byte[4],tiles=new byte[w*h*2];word(dim,0,w);word(dim,2,h);return join(chunk("DIM ",dim),chunk("ERA ",new byte[]{(byte)era,0}),chunk("MTXM",tiles));}
 static void bad(NativeMapPreview p,byte[]b)throws Exception{boolean failed=false;try{p.create(b);}catch(IOException e){failed=true;}check(failed,"Malformed CHK accepted");}
 public static void main(String[]a)throws Exception{
  NativeMapPreview p=new NativeMapPreview();
  for(int era=0;era<8;era++)for(int[]size:new int[][]{{64,64},{128,64},{64,256},{256,1},{1,256},{256,256}}){
   Bitmap b=p.create(map(size[0],size[1],era));int max=Math.max(size[0],size[1]);
   check(b.width==Math.max(1,128*size[0]/max)&&b.height==Math.max(1,128*size[1]/max),"Aspect ratio changed");
   for(int c:b.pixels)check(c==0xff285a78,"Wrong original terrain sample");
  }
  check(NativeBridge.reads==8*4,"Tileset tables read repeatedly");
  byte[]unit=new byte[36];word(unit,4,32*32);word(unit,6,16*32);word(unit,8,214);
  Bitmap starts=p.create(join(map(64,64,0),chunk("UNIT",unit)));
  check(starts.pixels[32*128+64]==0xffffff00,"Start location absent");
  word(unit,8,176);Bitmap mineral=p.create(join(map(64,64,0),chunk("UNIT",unit)));
  check(mineral.pixels[32*128+64]==0xff00d4d4,"Resource marker absent");
  word(unit,8,0);Bitmap marine=p.create(join(map(64,64,0),chunk("UNIT",unit)));
  check(marine.pixels[32*128+64]==0xff285a78,"Starting army revealed in terrain preview");
  bad(p,null);bad(p,new byte[16*1024*1024+1]);bad(p,new byte[7]);bad(p,new byte[8]);
  bad(p,chunk("DIM ",new byte[3]));bad(p,map(0,64,0));bad(p,map(257,64,0));
  bad(p,join(map(64,64,0),chunk("ERA ",new byte[0])));
  bad(p,join(map(64,64,0),chunk("MTXM",new byte[0])));
  byte[]truncated=map(64,64,0);bad(p,Arrays.copyOf(truncated,truncated.length-1));
  byte[]oversized=new byte[8];Arrays.fill(oversized,4,8,(byte)255);bad(p,oversized);
  Bitmap finalChunk=p.create(join(map(64,64,0),chunk("DIM ",new byte[]{32,0,32,0})));
  check(finalChunk.width==128&&finalChunk.height==128,"Last DIM chunk not honored");
  NativeBridge.missing=true;bad(new NativeMapPreview(),map(64,64,0));
  System.out.println("PASS "+checks+" embedded-map preview checks: eight tilesets, aspect ratios, bounded CHK, start/resource markers, cache and missing assets");
 }
}'''}
with tempfile.TemporaryDirectory(prefix='stardroid-thumbnail-') as work:
 work=Path(work)
 for name,text in sources.items():
  path=work/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
 subprocess.run(['javac','-d',str(work),str(production),*[str(work/n) for n in sources]],check=True)
 result=subprocess.run(['java','-cp',str(work),'org.openbw.androidtest.ReplayThumbnailTest'],capture_output=True,text=True,check=True)
 print(result.stdout,end='')
report={'passed':True,'scope':'Production CHK/terrain thumbnail renderer with synthetic original-format tileset tables; no Android device','result':result.stdout.strip(),'sourceSha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [production,Path(__file__)]}}
(root/'validation/replay-thumbnail.json').write_text(json.dumps(report,indent=2)+'\n')

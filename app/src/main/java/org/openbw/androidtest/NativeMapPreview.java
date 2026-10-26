package org.openbw.androidtest;
import android.graphics.Bitmap;
import java.io.IOException;
import java.util.*;

/** Original minimap terrain sample (CV5 -> VX4 -> VR4 pixel 55), without fog. */
final class NativeMapPreview {
  private static final String[] TILESETS={"badlands","platform","install","ashworld","jungle","desert","ice","twilight"};
  private final Map<Integer,int[]> colors=new HashMap<Integer,int[]>();
  Bitmap create(byte[] chk) throws IOException {
    if(chk==null||chk.length>16*1024*1024)throw new IOException("Preview scenario is unavailable");
    Map<String,byte[]> chunks=new HashMap<String,byte[]>();
    for(int p=0;p<chk.length;) {
      if(chk.length-p<8)throw new IOException("Truncated preview scenario");
      int size=NativeArt.u32(chk,p+4);String tag=new String(chk,p,4,java.nio.charset.StandardCharsets.US_ASCII);p+=8;
      if(size<0||size>chk.length-p)throw new IOException("Truncated preview scenario");
      if(tag.equals("DIM ")||tag.equals("ERA ")||tag.equals("MTXM")||tag.equals("UNIT"))chunks.put(tag,Arrays.copyOfRange(chk,p,p+size));
      p+=size;
    }
    byte[] dim=chunks.get("DIM ");
    if(dim==null||dim.length!=4)throw new IOException("Preview dimensions are missing");
    return create(chunks,NativeArt.u16(dim,0),NativeArt.u16(dim,2));
  }
  Bitmap create(Map<String,byte[]> chunks,int width,int height) throws IOException {
    if(width<1||height<1||width>256||height>256)throw new IOException("Unsupported preview dimensions");
    byte[] era=chunks.get("ERA "),mtxm=chunks.get("MTXM"),units=chunks.get("UNIT");
    if(mtxm==null||mtxm.length<width*height*2)throw new IOException("Map terrain is missing");
    if(era!=null&&era.length<2)throw new IOException("Preview tileset is missing");
    int tileset=era==null?0:era[0]&7;int[] palette=colors.get(tileset);
    if(palette==null) {
      String path="tileset/"+TILESETS[tileset];byte[] cv5=NativeBridge.asset(-1,path+".cv5"),vx4=NativeBridge.asset(-1,path+".vx4"),vr4=NativeBridge.asset(-1,path+".vr4"),wpe=NativeBridge.asset(-1,path+".wpe");
      if(cv5==null||vx4==null||vr4==null||wpe==null||wpe.length<1024)throw new IOException("Preview tileset is missing");
      palette=new int[cv5.length/52*16];
      for(int t=0;t<palette.length;t++) {
        int mega=NativeArt.u16(cv5,t/16*52+20+t%16*2),mini=mega*32+2<=vx4.length?NativeArt.u16(vx4,mega*32)/2:-1;
        int pixel=mini>=0&&mini*64+55<vr4.length?vr4[mini*64+55]&255:0;
        palette[t]=0xff000000|(wpe[pixel*4]&255)<<16|(wpe[pixel*4+1]&255)<<8|wpe[pixel*4+2]&255;
      }
      colors.put(tileset,palette);
    }
    int w=Math.max(1,128*width/Math.max(width,height)),h=Math.max(1,128*height/Math.max(width,height));int[] pixels=new int[w*h];
    for(int y=0;y<h;y++)for(int x=0;x<w;x++){int t=NativeArt.u16(mtxm,(y*height/h*width+x*width/w)*2);pixels[y*w+x]=t<palette.length?palette[t]:0xff000000;}
    if(units!=null)for(int p=0;p+36<=units.length;p+=36) {
      int type=NativeArt.u16(units,p+8);if(type!=214&&type!=188&&(type<176||type>178))continue;
      int x=NativeArt.u16(units,p+4)*w/(width*32),y=NativeArt.u16(units,p+6)*h/(height*32),radius=type==214?2:1,color=type==214?0xffffff00:0xff00d4d4;
      for(int yy=Math.max(0,y-radius);yy<=Math.min(h-1,y+radius);yy++)for(int xx=Math.max(0,x-radius);xx<=Math.min(w-1,x+radius);xx++)pixels[yy*w+xx]=color;
    }
    return Bitmap.createBitmap(pixels,w,h,Bitmap.Config.ARGB_8888);
  }
}

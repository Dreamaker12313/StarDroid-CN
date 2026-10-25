package org.openbw.androidtest;
import java.nio.file.*;
import java.util.*;
import android.graphics.*;
import javax.imageio.ImageIO;

/** Real imported fonts and palettes through the host Canvas shim. */
public final class Language77Test {
  static int checks;
  static void check(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
  public static void main(String[] a)throws Exception {
    NativeBridge.root=Paths.get(a[0]);Path output=Paths.get(a[1]);Files.createDirectories(output);
    GameLanguage.russianData=GameLanguage.isRussian(NativeBridge.asset(-1,"rez/stat_txt.tbl"));
    check(GameLanguage.russianData==Boolean.parseBoolean(a[3]),"Wrong archive language detected");
    PortText.load(Files.newInputStream(Paths.get(a[2])));
    check(Arrays.asList(PortText.availableLanguages(true)).contains("ru"),"Russian missing for detected data");
    check(!Arrays.asList(PortText.availableLanguages(false)).contains("ru"),"Russian shown without data");
    check(Arrays.asList(PortText.availableLanguages(false)).containsAll(Arrays.asList("en","de","es","fr")),"Western UI languages depend on data");
    if(GameLanguage.russianData) {
      String[] names=NativeArt.tbl(NativeBridge.asset(-1,"rez/stat_txt.tbl"));
      check(names[0].matches(".*[А-Яа-я].*"),"CP1251 unit names not decoded");
      check(GameLanguage.glyphCode('Я')==0xdf&&GameLanguage.glyphCode('я')==0xff,"Cyrillic glyph indices incorrect");
      check(GameLanguage.decode("Привет, мир!".getBytes("windows-1251")).equals("Привет, мир!"),"Raw JNI bytes decode incorrectly");
    }
    for(String lang:PortText.availableLanguages(GameLanguage.russianData)) {
      PortText.select(lang);
      if(!lang.equals("en"))check(!PortText.text("Original larvae selection").equals("Original larvae selection"),"Missing new option translation");
      check(!PortText.text("StarDat.mpq").equals(""),"Filename damaged");
      check(PortText.text("Widescreen").equals(PortText.text(PortText.text("Widescreen"))),"Translation not idempotent");
      NativeArt art=new NativeArt();
      NativeArt.PCX tint=art.pcx("glue/palcs/tfont.pcx",false,-1),palette=art.pcx("glue/palcs/backgnd.pcx",false,-1);
      NativeArt.Font small=art.font("10",tint,palette.palette,1),large=art.font("16",tint,palette.palette,1);
      check(!small.fallback&&!large.fallback,"Original fonts were not loaded");
      // A 3x3 letter with transparent-only runs must not gain a pixel per run.
      byte[] runs={70,79,78,84,65,65,3,3,12,0,0,0,3,3,0,0,8,1,8,1,8,1,8,1,8};
      NativeArt.Font runFont=new NativeArt.Font(runs,tint,palette.palette,0,3).withColor(0xffffffff);
      Bitmap runGlyph=runFont.glyph('A',2);
      for(int y=0;y<3;y++)for(int x=0;x<3;x++)
        check((runGlyph.getPixel(x,y)>>>24!=0)==(y==1?x!=1:x==1),"Transparent FONT run shifted pixels");
      for(String value:new String[]{"Original larvae selection","Show order & rally lines","Hold tap always selects","Double tap selects same type","Show control group buttons","Timing & accuracy"})
        check(small.measure(value)<=296,"Setting exceeds label width: "+lang+" "+PortText.text(value)+" width="+small.measure(value));
      check(small.measure("+ over camera area")<=156,"Camera radio label too wide: "+lang);
      for(String value:new String[]{"äöüßéèàçñíóú¿¡","Русский язык: личинки, ёж"}) for(char ch:value.toCharArray()) {
        if(ch==' ')continue;Bitmap g=large.glyph(ch,2);check(g!=null&&g.getHeight()==large.height,"Missing translated glyph: "+ch);
      }
      for(String menu:new String[]{"glumain","glucmpgn","gluexpcmpgn"}) {
        NativeGlue glue=new NativeGlue(art,menu,menu.equals("glumain")?"palmm":"palcs",false);
        glue.elapsed=700;Bitmap image=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(image);glue.draw(c,0);
        for(int id:menu.equals("glumain")?new int[]{3,4,5,8,9,2}:new int[]{5,6,7,8,9,10,11}) {
          NativeArt.Widget w=glue.layout.get(id);if(w==null)continue;
          String label=MenuLabels.forDialog(menu,id,"");
          NativeArt.Font f=(w.flags&0x4000)!=0?glue.button:(w.flags&0x800)!=0||w.type==14?glue.large:(w.flags&0x400)!=0?glue.small:glue.tiny;
          int width=Math.max(1,(w.rw>0?w.rw:w.w)-w.tx),height=Math.max(1,(w.rh>0?w.rh:w.h)-w.ty);
          int fitted=NativeGlue.labelWidth(f,label,width,height);
          check(width/(float)fitted>=.65f,"Translated label compressed too far: "+lang+" "+menu+" "+id);
          check(f.lines(label,fitted).size()*f.height<=height,"Translated menu label exceeds height: "+lang+" "+menu+" "+id+" "+PortText.text(label));
          glue.label(c,id,null,true);
        }
        ImageIO.write(image.image,"png",output.resolve(menu+"-"+lang+".png").toFile());glue.close();
      }
      Bitmap sample=Bitmap.createBitmap(640,360,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(sample);Paint bg=new Paint();bg.setColor(0xff081329);c.drawRect(0,0,640,360,bg);
      int y=12;for(String label:new String[]{"Interface language","Video Options","Widescreen","+ over camera area","Original larvae selection","Timing & accuracy","Save Game","äöüß éèàç ñíóú ¿¡"}) {large.draw(c,label,16,y,608,0,2,0);y+=34;}
      ImageIO.write(sample.image,"png",output.resolve("labels-"+lang+".png").toFile());
    }
    System.out.println("PASS "+checks+" language checks; Russian="+GameLanguage.russianData+"; archive encoding, original-font loading, Cyrillic/accent glyphs, locale gating, translated label bounds and menu captures.");
  }
}

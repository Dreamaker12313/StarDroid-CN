#!/usr/bin/env python3
"""Render production campaign entry with original SC/BW art and libsmacker frames.

Caller-owned archives and captures remain in ignored build-native/campaign-entry82.
The host Canvas verifies drawing and hit registration, not physical Android input.
"""
from pathlib import Path
import argparse, ast, ctypes, hashlib, json, re, shutil, subprocess
from PIL import Image

r = Path(__file__).resolve().parents[1]
src = r / 'app/src/main/java/org/openbw/androidtest'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--core', type=Path, default=r/'build-native/reign79/core')
p.add_argument('--data', type=Path, default=r.parent/'reign-data')
p.add_argument('--extract', type=Path, default=r/'build-native/reign79/extract')
a = p.parse_args()
b = r/'build-native/campaign-entry82'
b.mkdir(parents=True, exist_ok=True)
assets = b/'assets'
shutil.copytree(r/'build-native/campaign81/assets', assets, dirs_exist_ok=True)
archives = [(0,a.core/'STARDAT.MPQ'),(1,a.core/'BROODAT.MPQ'),(2,a.core/'patch_rt.mpq'),
            (4,a.data/'StarCraft.mpq'),(5,a.data/'BroodWar.mpq')]

def extract(name):
    found = []
    for slot, archive in archives:
        target = assets/str(slot)/name
        target.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([str(a.extract),str(archive),name,str(target)], capture_output=True)
        if result.returncode:
            target.unlink(missing_ok=True)
        else:
            found.append(target.read_bytes())
    return found

names = set()
for dialog in ['glucmpgn','gluexpcmpgn']:
    for raw in extract('rez/'+dialog+'.bin'):
        names |= {s.decode('cp1252').replace('\\','/').lower()
                  for s in re.findall(rb'(?:glue|GLUE)[^\x00]*?\.(?:[pP][cC][xX]|[sS][mM][kK])',raw)}
for name in sorted(names):
    extract(name)

# Decode the actual movie palette/index frames with the same library as Android.
# Zero is transparent, matching native/runtime.cpp movie_frame for menu movies.
library = b/'libsmacker-test.so'
subprocess.run(['gcc','-shared','-fPIC','-O2',str(r/'vendor/libsmacker/smacker.c'),'-o',str(library)],check=True)
smk = ctypes.CDLL(str(library))
ptr = ctypes.c_void_p
ul = ctypes.c_ulong
smk.smk_open_file.argtypes = [ctypes.c_char_p,ctypes.c_ubyte]
smk.smk_open_file.restype = ptr
smk.smk_info_video.argtypes = [ptr,ctypes.POINTER(ul),ctypes.POINTER(ul),ctypes.POINTER(ctypes.c_ubyte)]
smk.smk_info_all.argtypes = [ptr,ctypes.POINTER(ul),ctypes.POINTER(ul),ctypes.POINTER(ctypes.c_double)]
smk.smk_enable_all.argtypes = [ptr,ctypes.c_ubyte]
for name in ['smk_first','smk_next','smk_close']:
    getattr(smk,name).argtypes = [ptr]
for name in ['smk_get_palette','smk_get_video']:
    getattr(smk,name).argtypes = [ptr]
    getattr(smk,name).restype = ptr
decoded = {}
for movie in sorted(assets.rglob('*.smk')):
    digest = hashlib.sha256(movie.read_bytes()).hexdigest()
    if digest in decoded:
        continue
    handle = smk.smk_open_file(str(movie).encode(),1)
    assert handle, movie
    try:
        width,height,frames,us,scale = ul(),ul(),ul(),ctypes.c_double(),ctypes.c_ubyte()
        smk.smk_info_video(handle,ctypes.byref(width),ctypes.byref(height),ctypes.byref(scale))
        smk.smk_info_all(handle,None,ctypes.byref(frames),ctypes.byref(us))
        folder = b/'frames'/digest
        folder.mkdir(parents=True,exist_ok=True)
        interval = max(1,int(us.value/1000))
        (folder/'meta.txt').write_text(f'{width.value} {height.value} {frames.value} {interval}')
        smk.smk_enable_all(handle,128)
        assert smk.smk_first(handle) >= 0
        for frame in range(frames.value):
            image = Image.frombytes('P',(width.value,height.value),ctypes.string_at(smk.smk_get_video(handle),width.value*height.value))
            image.putpalette(ctypes.string_at(smk.smk_get_palette(handle),768))
            image.info['transparency'] = 0
            image.convert('RGBA').save(folder/f'{frame}.png')
            if frame+1 < frames.value:
                assert smk.smk_next(handle) >= 0
        decoded[digest] = dict(asset=str(movie.relative_to(assets)),frames=frames.value,width=width.value,height=height.value)
    finally:
        smk.smk_close(handle)

# Use the established artwork Canvas, retaining production NativeArt/NativeGlue.
old = ast.parse((r/'tests/run_menu_recovery.py').read_text())
active = False
for node in old.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tree' for t in node.targets):
        active = True
    if active:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.slice,ast.Constant)
                and t.slice.value=='org/openbw/androidtest/MenuRecoveryTest.java' for t in node.targets):
            break
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<original-art Canvas>','exec'))

# Honor the production movie fade/dimming when capturing the decoded artwork.
sources['android/graphics/ColorMatrixColorFilter.java'] = '''package android.graphics;
public class ColorMatrixColorFilter{public float[] matrix;public ColorMatrixColorFilter(float[] value){matrix=value;}}'''
sources['android/graphics/Paint.java'] = sources['android/graphics/Paint.java'].replace(
    'public void setColorFilter(ColorMatrixColorFilter c){}',
    'public ColorMatrixColorFilter filter;public void setColorFilter(ColorMatrixColorFilter c){filter=c;}')
sources['android/graphics/Canvas.java'] = sources['android/graphics/Canvas.java'].replace(
    'g.drawImage(b.image,t,null);', '''Graphics2D copy=(Graphics2D)g.create();
copy.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER,p==null?1:p.alpha/255f));
java.awt.image.BufferedImage image=b.image;
if(p!=null&&p.filter!=null){image=new java.awt.image.BufferedImage(b.getWidth(),b.getHeight(),2);
float[] m=p.filter.matrix;for(int yy=0;yy<b.getHeight();yy++)for(int xx=0;xx<b.getWidth();xx++){
int pixel=b.getPixel(xx,yy);image.setRGB(xx,yy,(pixel&0xff000000)|((int)((pixel>>16&255)*m[0])<<16)|((int)((pixel>>8&255)*m[6])<<8)|(int)((pixel&255)*m[12]));}}
copy.drawImage(image,t,null);copy.dispose();''')
bridge = sources['org/openbw/androidtest/NativeBridge.java']
bridge = bridge.replace('new int[]{2,1,0,4}','new int[]{2,1,0,4,5}')
start = bridge.index(' static int[] movieOpen(')
bridge = bridge[:start]+r'''
 static Path framesRoot;static int next;static Map<Integer,String> movies=new HashMap<>();static Map<Integer,int[]> info=new HashMap<>();
 static int[] movieOpen(byte[] bytes,boolean audio){try{
  StringBuilder hash=new StringBuilder();for(byte n:java.security.MessageDigest.getInstance("SHA-256").digest(bytes))hash.append(String.format("%02x",n));
  String key=hash.toString();String[] fields=Files.readString(framesRoot.resolve(key).resolve("meta.txt")).split(" ");
  int id=next++;int[] m={id,Integer.parseInt(fields[0]),Integer.parseInt(fields[1]),Integer.parseInt(fields[2]),Integer.parseInt(fields[3])};
  movies.put(id,key);info.put(id,m);return m;
 }catch(Exception e){throw new IllegalArgumentException(e);}}
 static int[] movieOpenAsset(int slot,String path,boolean audio){return movieOpen(asset(slot,path),audio);}
 static void movieFrame(int id,double t,boolean loop,Bitmap bitmap){try{
  int[] m=info.get(id);int frame=(int)Math.max(0,t)/m[4];frame=loop?frame%m[3]:Math.min(frame,m[3]-1);
  java.awt.image.BufferedImage image=javax.imageio.ImageIO.read(framesRoot.resolve(movies.get(id)).resolve(frame+".png").toFile());
  bitmap.image.setRGB(0,0,m[1],m[2],image.getRGB(0,0,m[1],m[2],null,0,m[1]),0,m[1]);
 }catch(Exception e){throw new IllegalStateException(e);}}
 static void movieClose(int id){movies.remove(id);info.remove(id);}
}'''
sources['org/openbw/androidtest/NativeBridge.java'] = bridge

surface = (src/'NativeSurface.java').read_text()
start = surface.index('  private void glueButton(')
button = surface[start:surface.index('\n  private void message(',start)]
start = surface.index('      if (page.equals("campaign")) {')
campaign = surface[start:surface.index('      if (page.equals("briefing"))',start)]
sources['org/openbw/androidtest/CampaignEntry82Test.java'] = r'''package org.openbw.androidtest;
import android.graphics.*;import java.nio.file.*;import java.util.*;import javax.imageio.ImageIO;
public class CampaignEntry82Test {
 static int checks;static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static class Button{RectF rect;Runnable run;boolean enabled;Button(RectF r,Runnable a,boolean e){rect=r;run=a;enabled=e;}}
 NativeGlue glue;Runnable pendingScreen;String page="campaign";boolean multiplayerSetup,multiplayerSaves;int selected=-1;
 List<Button> buttons=new ArrayList<>();
 void button(Canvas c,String label,float x,float y,float w,float h,Runnable action,boolean enabled){throw new AssertionError("Fallback used");}
 void add(RectF rect,Runnable action,boolean enabled){buttons.add(new Button(rect,action,enabled));}
 void missionList(int race){selected=race;}void navigate(Runnable action){action.run();}
 void showRegistry(){}void openSaves(boolean saving){}void showReplays(){}void showCustom(){}
''' + button + '\n void campaign(Canvas c){\n' + campaign + r'''}
 static class Recording extends Canvas{
  NativeGlue glue;int movieDraws;
  Recording(Bitmap b,NativeGlue value){super(b);glue=value;}
  public void drawBitmap(Bitmap b,Object source,RectF dst,Paint paint){
   for(NativeGlue.Layer layer:glue.layers)if(layer.movie.bitmap==b)movieDraws++;
   super.drawBitmap(b,source,dst,paint);
  }
 }
 Bitmap render(double dt,boolean ready){
  buttons.clear();Bitmap bitmap=Bitmap.createBitmap(640,480,Bitmap.Config.ARGB_8888);Recording c=new Recording(bitmap,glue);glue.draw(c,dt);campaign(c);
  check((c.movieDraws>0)==ready,"Character movie visibility at "+glue.elapsed+" exit="+glue.exiting);
  for(int id:new int[]{6,7,8}){
   check(glue.labelVisible(id)==ready,"Race/episode label visible at "+glue.elapsed);
   RectF hit=glue.layout.get(id).hit();Button match=null;
   for(Button target:buttons)if(target.rect.left==hit.left&&target.rect.top==hit.top&&target.rect.right==hit.right&&target.rect.bottom==hit.bottom)match=target;
   check((match!=null)==ready,"Hidden character retained a hit target at "+glue.elapsed);
   if(ready){check(match.enabled,"Shown character is disabled");match.run.run();check(selected==8-id,"Wrong race action");}
  }
  if(!ready)for(int y=0;y<352;y++)for(int x=0;x<640;x++)
   if(bitmap.getPixel(x,y)!=glue.background.image.getPixel(x,y))throw new AssertionError("Character/label pixels appeared during slide at "+glue.elapsed+": "+x+","+y);
  return bitmap;
 }
 static void save(Bitmap bitmap,Path file)throws Exception{ImageIO.write(bitmap.image,"png",file.toFile());}
 public static void main(String[] args)throws Exception{
  NativeBridge.root=Paths.get(args[0]);NativeBridge.framesRoot=Paths.get(args[1]);Path out=Paths.get(args[2]);
  CampaignEntry82Test h=new CampaignEntry82Test();
  for(int visit=0;visit<2;visit++)for(String name:new String[]{"glucmpgn","gluexpcmpgn"}){
   h.glue=new NativeGlue(new NativeArt(),name,"palcs",true);NativeGlue g=h.glue;
   check(g.layers.size()==9,"Missing original three character/disk/hover layers: "+name+" "+g.layers.size());
   check(g.paletteName.equals("palcs")&&!g.large.fallback,"Original campaign art/font unavailable");
   // Eager decoding must never flash a cached first frame before controls arrive.
   for(NativeGlue.Layer layer:g.layers){NativeBridge.movieFrame(layer.movie.id,0,true,layer.movie.bitmap);layer.movie.frame=0;}
   double previous=0;
   for(int time:new int[]{0,335,669,670,671,970,1270}){
    Bitmap bitmap=h.render(time-previous,time>=NativeGlue.ENTER_MS);previous=time;
    if(visit==0)save(bitmap,out.resolve(name+"-"+time+"ms.png"));
    if(time==669)check(g.shift(g.layout.get(1))!=0,"Boundary test lacks moving controls");
    if(time==670){check(g.shift(g.layout.get(1))==0&&g.shift(g.layout.get(3))==0,"Choices precede slide completion");
     for(NativeGlue.Layer layer:g.layers)if((layer.spec.flags&8)==0)check(layer.movie.frame==0,"Character animation ran before reveal");}
   }
   g.hot=6;h.render(100,true);check(g.layers.stream().anyMatch(layer->layer.wasHot),"Original hover movie was not activated");
   g.exiting=true;g.elapsed=0;save(h.render(0,false),out.resolve(name+"-exit.png"));h.render(NativeGlue.EXIT_MS,false);g.close();
  }
  h.glue=new NativeGlue(new NativeArt(),"glucmpgn","palcs",false);h.render(0,true);h.glue.close();
  h.glue=new NativeGlue(new NativeArt(),"gluexpcmpgn","palcs",true);h.render(900,true);h.glue.close();
  check(NativeBridge.movies.isEmpty(),"Campaign reentry leaked movie streams");
  System.out.println("PASS "+checks+" campaign entry checks: original SC/BW characters, episode labels and hit targets hidden at 0/335/669 ms; revealed at completed 670 ms slide; deferred movie fade/time; cached first-frame flash prevention; hover; exit; repeated SC/BW entry; no-slide/large-frame cases; no movie leaks");
 }
}'''
for name,value in sources.items():
    target=b/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(value)
real=[src/(name+'.java') for name in ['NativeArt','NativeGlue','MenuLabels','ClassicFontCipher','GameLanguage','PortText']]
subprocess.run(['javac','-d',str(b/'classes'),*[str(b/name) for name in sources],*map(str,real)],check=True)
result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes'),'org.openbw.androidtest.CampaignEntry82Test',str(assets),str(b/'frames'),str(b)],capture_output=True,text=True)
print(result.stdout+result.stderr,end='')
result.check_returncode()
files=real+[src/'NativeSurface.java',Path(__file__),r/'vendor/libsmacker/smacker.c']
(r/'validation/campaign-entry-v82.json').write_text(json.dumps(dict(passed=True,physicalAndroid=False,
    canvas='AWT shim with production NativeGlue, NativeArt, NativeSurface campaign/button methods and original libsmacker-decoded assets',
    result=result.stdout.strip(),decodedMovies=decoded,
    captures=[str(file.relative_to(r)) for file in sorted(b.glob('*.png'))],
    sourceSha256={str(file.relative_to(r)):hashlib.sha256(file.read_bytes()).hexdigest() for file in files}),indent=2)+'\n')

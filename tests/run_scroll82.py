#!/usr/bin/env python3
"""Exercise unchanged production map input and verify reference-style pixel scrollbars.

Reuses the established host AWT shim and caller-owned original artwork. No Android
hardware is simulated; pixel checks run on the production NativeGlue renderer.
"""
from pathlib import Path
import ast, hashlib, json, re, subprocess
r=Path(__file__).resolve().parents[1]
src=r/'app/src/main/java/org/openbw/androidtest'
b=r/'build-native/scroll82';b.mkdir(parents=True,exist_ok=True)
assets=r/'build-native/gamepad81/assets'
# Load only the existing production-method/input shim declarations, without
# asset extraction, Java execution, or writes to any historical v79 report.
old=ast.parse((r/'tests/run_map_scroll79.py').read_text());loading_shim=False
for node in old.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='old' for t in node.targets):loading_shim=True
 if loading_shim:
  if isinstance(node,ast.For) and isinstance(node.target,ast.Tuple):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<map input shim>','exec'))
harness=sources.pop('org/openbw/androidtest/MapScroll79Test.java').replace('MapScroll79Test','Scroll82Test')
start=harness.index(' for(float v:new float[]{0,.5f,1}){h.setup(2001);')
end=harness.index(' System.out.println(',start)
harness=harness[:start]+'''
 for(float v:new float[]{0,.5f,1}){h.setup(2001);h.mapOffset=h.mapMaxOffset()*v;Bitmap image=h.redraw();
  ImageIO.write(image.image,"png",out.resolve("map-list-"+(int)(v*100)+".png").toFile());}
 // Separate transparent captures prove that every nontransparent pixel belongs
 // to the red outline: no green bevel, center dot, fill or antialiased fringe.
 for(int height:new int[]{93,110,218})for(float v:new float[]{0,.25f,.5f,.75f,1}){
  Bitmap image=Bitmap.createBitmap(24,height+8,Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(image);glue.scrollbar(canvas,4,4,height,v);
  int center=Math.round(4+23+v*(height-46)),ink=0;
  for(int y=0;y<image.getHeight();y++)for(int x=0;x<image.getWidth();x++){
   int p=image.getPixel(x,y);if(p!=0){ink++;check(p==0xffff0033||p==0xffc00024,"Scrollbar has non-red or antialiased pixels");}
  }
  check(ink>height*2,"Outlined scrollbar is missing");
  check(image.getPixel(12,center)==0,"Thumb center must remain transparent");
  check(image.getPixel(12,center-6)==0xffff0033&&image.getPixel(12,center+6)==0xffff0033,"Hollow circle moved away from input center");
  check(image.getPixel(6,center)==0xffff0033&&image.getPixel(18,center)==0xffff0033,"Thumb side outline missing");
  check(image.getPixel(12,11)==0&&image.getPixel(12,height-4)==0,"Arrow has a filled interior");
  check(image.getPixel(5,22)==0xffc00024&&image.getPixel(18,22)==0xffc00024,"Thin rail missing");
  ImageIO.write(image.image,"png",out.resolve("scrollbar-"+height+"-"+(int)(v*100)+".png").toFile());
 }
 Bitmap detail=Bitmap.createBitmap(240,480,Bitmap.Config.ARGB_8888);Canvas dc=new Canvas(detail);Paint backdrop=new Paint();backdrop.setColor(0xff101016);dc.drawRect(0,0,240,480,backdrop);
 for(int i=0;i<3;i++){dc.save();dc.translate(20+i*75,20);dc.scale(4,4);glue.scrollbar(dc,0,0,110,i/2f);dc.restore();}
 ImageIO.write(detail.image,"png",out.resolve("pixel-scrollbar-detail.png").toFile());
''' + harness[end:]
harness=harness.replace('original bright arrows/circular thumb','red outlined pixel arrows/rail and hollow circle (15 geometry captures)')
sources['org/openbw/androidtest/Scroll82Test.java']=harness
for name,value in sources.items():
 target=b/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(value)
real=[src/n for n in ['NativeArt.java','NativeGlue.java','NativeResults.java','CommandHint.java','MenuLabels.java','ClassicFontCipher.java','GameLanguage.java','PortText.java']]
subprocess.run(['javac','-d',str(b/'classes'),*[str(b/n) for n in sources],*map(str,real)],check=True)
result=subprocess.run(['java','-Djava.awt.headless=true','-cp',str(b/'classes'),'org.openbw.androidtest.Scroll82Test',str(assets),str(b)],capture_output=True,text=True)
print(result.stdout+result.stderr,end='');result.check_returncode()
files=[src/'NativeGlue.java',src/'NativeSurface.java',Path(__file__)]
report={'passed':True,'physicalAndroid':False,'canvas':'AWT shim; production NativeGlue and extracted NativeSurface map input methods','result':result.stdout.strip(),'screenshots':[str(f.relative_to(r)) for f in sorted(b.glob('*.png'))],'sourceSha256':{str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
(r/'validation/scroll-v82.json').write_text(json.dumps(report,indent=2)+'\n')

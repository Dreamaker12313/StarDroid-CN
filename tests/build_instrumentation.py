import pathlib,subprocess,zipfile,shutil,os
r=pathlib.Path(__file__).resolve().parents[1];t=pathlib.Path(os.environ.get('OPENBW_ANDROID_TOOLS',r/'.tools'));b=r/'build-native/instrumentation';b.mkdir(exist_ok=True)
for folder in ('classes','dex'):
 shutil.rmtree(b/folder,ignore_errors=True)
 (b/folder).mkdir()
def run(*args):subprocess.run(list(map(str,args)),check=True)
run('java','-jar',t/'ecj.jar','-source','1.8','-target','1.8','-proc:none','-bootclasspath',t/'android-35/android.jar','-classpath',str(r/'build-native/apk/classes')+':'+str(t/'android-15/core-lambda-stubs.jar'),'-d',b/'classes',*sorted((r/'tests').glob('Native*Instrumentation.java')))
with zipfile.ZipFile(b/'classes.jar','w') as z:
 for p in (b/'classes').rglob('*.class'):z.write(p,p.relative_to(b/'classes'))
run('java','-cp',t/'android-15/lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--lib',t/'android-35/android.jar','--classpath',r/'build-native/apk/classes.jar','--output',b/'dex',b/'classes.jar')
run(t/'android-15/aapt2','link','-I',t/'android-35/android.jar','--manifest',r/'tests/AndroidManifest.xml','-o',b/'unsigned.apk')
with zipfile.ZipFile(b/'unsigned.apk','a') as z:z.write(b/'dex/classes.dex','classes.dex')
run('java','-jar',t/'android-15/lib/apksigner.jar','sign','--ks',r/'signing/test-key.p12','--ks-key-alias','openbw-test','--ks-pass','pass:android','--key-pass','pass:android','--out',b/'native-tests.apk',b/'unsigned.apk')

#!/usr/bin/env python3
"""Verify compact MPQ migration and normal in-game saves, without game data in source."""
import argparse, hashlib, json, struct, subprocess, zipfile
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path);p.add_argument('--reuse-real',action='store_true',help='Reuse local bundles, still rebuild/check current compact cache and compare native decoding');a=p.parse_args()
b=r/'build-native/storage80';b.mkdir(parents=True,exist_ok=True)
src=r/'app/src/main/java/org/openbw/androidtest';jar=r/'build-native/json-20240303.jar';outputs=[]
def run(args):
 q=subprocess.run(list(map(str,args)),capture_output=True,text=True);print(q.stdout+q.stderr,end='');q.check_returncode();outputs.append(q.stdout.strip())
crypt=[0]*1280;seed=0x100001
for i in range(256):
 for j in range(5):
  seed=(seed*125+3)%0x2aaaab;high=seed<<16;seed=(seed*125+3)%0x2aaaab;crypt[i+j*256]=(high|(seed&65535))&0xffffffff
def hashname(name,kind):
 a,bv=0x7fed7fed,0xeeeeeeee
 for c in name.replace('/','\\').upper().encode('latin1'):
  a=(crypt[kind*256+c]^(a+bv))&0xffffffff;bv=(c+a+bv+(bv<<5)+3)&0xffffffff
 return a
def cipher(data,key,encode=True):
 out=bytearray(data);seed=0xeeeeeeee
 for pos in range(0,len(data)//4*4,4):
  seed=(seed+crypt[1024+(key&255)])&0xffffffff
  word=struct.unpack_from('<I',data,pos)[0];result=word^((key+seed)&0xffffffff);plain=word if encode else result
  struct.pack_into('<I',out,pos,result);key=((((~key&0xffffffff)<<21)+0x11111111)|(key>>11))&0xffffffff;seed=(plain+seed+(seed<<5)+3)&0xffffffff
 return bytes(out)
def fixture(invalid=False):
 entries=[];blocks=[];payloads=[];hashes=bytearray(b'\xff'*(16*16));paths=[];offset=10*1024*1024
 flagses=[0x80000000,0x80010000,0x80030000,0x80030200,0x84030200,0x81030000]
 for index,flags in enumerate(flagses):
  name='test\\entry%d.bin'%index;plain=bytes((i*17+index)%251 for i in range(70003 if index==5 else 8195));size=len(plain)
  key=hashname(name.split('\\')[-1],3)
  if flags&0x20000:key=((key+offset)^size)&0xffffffff
  sectors=[plain[i:i+4096] for i in range(0,size,4096)]
  if flags&0x1000000:packed=cipher(plain,key)
  elif flags&0x300:
   checksums=bool(flags&0x4000000);tablelen=4*(len(sectors)+1+checksums);offsets=[tablelen];body=b''
   for sector,chunk in enumerate(sectors):
    body+=cipher(chunk,(key+sector)&0xffffffff);offsets.append(tablelen+len(body))
   if checksums:body+=b'\x12\x34\x56\x78'*len(sectors);offsets.append(tablelen+len(body))
   if invalid and index==3:offsets[1]=0xffffffff
   packed=cipher(struct.pack('<'+'I'*len(offsets),*offsets),(key-1)&0xffffffff)+body
  elif flags&0x10000:
   # The raw FIX_KEY fixture contains the valid installer word padding.
   if index==2:sectors[-1]+=b'\0'*(-len(sectors[-1])%4)
   packed=b''.join(cipher(chunk,(key+i)&0xffffffff) for i,chunk in enumerate(sectors))
  else:packed=plain
  slot=hashname(name,0)&15
  while struct.unpack_from('<I',hashes,slot*16+12)[0]!=0xffffffff:slot=(slot+1)&15
  struct.pack_into('<IIII',hashes,slot*16,hashname(name,1),hashname(name,2),0,index)
  entries.append(dict(name=name,block=index,offset=offset,packedSize=len(packed),size=size,flags=flags,hashSlots=[slot]))
  blocks.append(struct.pack('<IIII',offset,len(packed),size,flags));payloads.append(packed)
  if index!=5:paths.append(name)
  offset+=len(packed)+1024*1024
 archive_size=506995955;ht=archive_size-len(hashes)-16*len(blocks);bt=ht+len(hashes)
 header=struct.pack('<IIIHHIIII',0x1a51504d,32,archive_size,0,3,ht,bt,16,len(blocks))
 h=cipher(hashes,hashname('(hash table)',3));bl=cipher(b''.join(blocks),hashname('(block table)',3))
 with zipfile.ZipFile(b/('invalid.zip' if invalid else 'fixture.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in [('header.bin',header),('hash-table.bin',h),('block-table.bin',bl),('manifest.json',json.dumps(dict(entries=entries)).encode())]:z.writestr(name,data)
  for i,payload in enumerate(payloads):z.writestr('blocks/%d.bin'%i,payload)
 if not invalid:
  with (b/'original.mpq').open('wb') as f:
   f.truncate(archive_size);f.write(header)
   for entry,payload in zip(entries,payloads):f.seek(entry['offset']);f.write(payload)
   f.seek(ht);f.write(h);f.seek(bt);f.write(bl)
  (b/'paths.txt').write_text('\n'.join(paths)+'\n')
  (b/'single-expected.bin').write_bytes(bytes((i*17+5)%251 for i in range(70003)))
fixture();fixture(True)
stub=b/'android/util/AtomicFile.java';stub.parent.mkdir(parents=True,exist_ok=True)
stub.write_text('''package android.util;import java.io.*;import java.nio.file.*;
public class AtomicFile {
 private final File f,n; public AtomicFile(File file){f=file;n=new File(file+".new");}
 public File getBaseFile(){return f;} public FileInputStream openRead()throws IOException{return new FileInputStream(f);}
 public FileOutputStream startWrite()throws IOException{return new FileOutputStream(n);}
 public void finishWrite(FileOutputStream out)throws IOException{out.close();Files.move(n.toPath(),f.toPath(),StandardCopyOption.REPLACE_EXISTING);}
 public void failWrite(FileOutputStream out){try{out.close();}catch(Exception ignored){}n.delete();}
}''')
production=['NativeData','NativeSaves','NativeMapArchive','NativeCache','NearbyProtocol','CampaignCatalog']
run(['javac','-cp',jar,'-d',b/'classes',*[src/(name+'.java') for name in production],stub,r/'tests/CacheSaves80Test.java'])
run(['java','-Xmx128m','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.CacheSaves80Test',b])
run(['g++','-std=c++17','-O2','-I'+str(r/'native-engine'),r/'tests/native_cache80.cpp','-o',b/'native-cache80'])
run([b/'native-cache80',b/'original.mpq',b/'cache/fixture.mpq',b/'paths.txt'])
# Independently check a whole-file encrypted block crossing the 64 KiB stream buffer.
compact=(b/'cache/fixture.mpq').read_bytes();head=struct.unpack_from('<IIIHHIIII',compact)
blocks=cipher(compact[head[6]:head[6]+head[8]*16],hashname('(block table)',3),False)
offset,packed,size,flags=struct.unpack_from('<IIII',blocks,5*16)
key=((hashname('entry5.bin',3)+offset)^size)&0xffffffff
assert cipher(compact[offset:offset+packed],key,False)==(b/'single-expected.bin').read_bytes()
print('PASS single-unit FIX_KEY stream rekey across 64 KiB, including 3-byte cipher tail')
real=[]
if a.data_dir:
 harness=b/'RealCache80.java';harness.write_text('''package org.openbw.androidtest;
import java.io.*;import java.util.*;import java.util.zip.*;import org.json.*;
public class RealCache80 {public static void main(String[] a)throws Exception {
 File data=new File(a[0]),out=new File(a[1]);out.mkdirs();boolean reuse=a.length>2&&a[2].equals("reuse");
 for(String game:new String[]{"StarCraft","BroodWar","StarDat"}) {
  String[][] kinds={{"music"},{"story"},{"movies"},{"interface"},{"mission"}};
  for(String[] kind:kinds) {
   if(game.equals("StarDat")&&!kind[0].equals("interface"))continue;
   String stem=game+"-"+kind[0];File bundle=new File(out,stem+".zip");
   if(!reuse||!bundle.isFile())try(FileInputStream input=new FileInputStream(new File(data,game+".mpq"));FileOutputStream target=new FileOutputStream(bundle)) {
    try {if(kind[0].equals("music"))MissionBundle.exportMusic(input.getChannel(),MusicData.names(),target,s->{});
    else if(kind[0].equals("mission")) {
      String id=game.equals("StarCraft")?"terran01":"expzerg02";
      List<String> names=java.nio.file.Files.readAllLines(new File(a[3],id+"-files.txt").toPath(),java.nio.charset.StandardCharsets.UTF_8);
      names.removeIf(v->v.trim().isEmpty());MissionBundle.export(input.getChannel(),names,names.get(0),target,s->{});
    }
    else if(kind[0].equals("interface"))MissionBundle.exportInterface(input.getChannel(),InterfaceData.names(),target,s->{});
    else MissionBundle.exportStory(input.getChannel(),StoryData.names(kind[0].equals("movies")),target,s->{},kind[0].equals("movies"));}
    catch(IOException error){if(game.equals("BroodWar")&&kind[0].equals("interface"))continue;throw error;}
   }
   File compact=NativeData.prepare(bundle,out,stem);
   try(ZipFile zip=new ZipFile(bundle);PrintWriter paths=new PrintWriter(new File(out,stem+".paths"),"UTF-8")) {
    JSONObject m=new JSONObject(new String(NativeData.read(zip.getInputStream(zip.getEntry("manifest.json")),1048576),"UTF-8"));
    JSONArray entries=m.getJSONArray("entries");for(int i=0;i<entries.length();i++)paths.println(entries.getJSONObject(i).getString("name"));
    System.out.println(stem+": "+m.getLong("archiveSize")+" -> "+compact.length()+" bytes; "+entries.length()+" files");
   }
  }
 }
}}''')
 names=['MissionBundle','MusicData','StoryData','InterfaceData','ProjectFiles','CinematicCatalog']
 run(['javac','-cp',str(b/'classes')+':'+str(jar),'-d',b/'classes',*[src/(n+'.java') for n in names],harness])
 run(['java','-Xmx128m','-cp',str(b/'classes')+':'+str(jar),'org.openbw.androidtest.RealCache80',a.data_dir,b/'real','reuse' if a.reuse_real else 'fresh',r/'app/src/main/assets/missions'])
 for paths in sorted((b/'real').glob('*.paths')):
  stem=paths.stem;game=stem.split('-')[0]
  run([b/'native-cache80',a.data_dir/(game+'.mpq'),paths.with_suffix('.mpq'),paths])
  real.append(dict(bundle=stem,originalBytes=(a.data_dir/(game+'.mpq')).stat().st_size,compactBytes=paths.with_suffix('.mpq').stat().st_size,entries=len(paths.read_text().splitlines())))
files=[src/(n+'.java') for n in production]+[r/'tests/CacheSaves80Test.java',r/'tests/native_cache80.cpp',Path(__file__)]
(r/'validation/storage80.json').write_text(json.dumps(dict(passed=True,physicalAndroid=False,originalPcSavesSupported=False,saveFileTransferSupported=False,checks=outputs,realArchiveCaches=real,sourceSha256={str(f.relative_to(r)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}),indent=2)+'\n')

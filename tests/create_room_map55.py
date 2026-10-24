#!/usr/bin/env python3
"""An eight-start flat-terrain engine fixture; uses the bundled map's tileset."""
from pathlib import Path
import struct,sys,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from rebuild_mission_mpq import cipher,hash_name
r=Path(__file__).resolve().parents[1];src=r/'build-native/probe55/weave-source.chk'
if not src.exists():
 src.parent.mkdir(parents=True,exist_ok=True);extract=src.parent/'extract-fixture'
 subprocess.run(['g++','-std=c++17','-O0','-I'+str(r/'native-engine'),str(r/'tests/extract_interface46.cpp'),'-o',str(extract)],check=True,capture_output=True)
 subprocess.run([str(extract),str(r/'app/src/main/assets/native/weave.scx'),'staredit/scenario.chk',str(src)],check=True,capture_output=True)
b=src.read_bytes();chunks={};p=0
while p<len(b):tag,n=struct.unpack_from('<4sI',b,p);p+=8;chunks[tag]=b[p:p+n];p+=n
w,h=struct.unpack('<HH',chunks[b'DIM ']);units=chunks[b'UNIT'];start=next(units[p:p+36]for p in range(0,len(units),36)if struct.unpack_from('<H',units,p+8)[0]==214)
x,y=struct.unpack_from('<HH',start,4);tile=chunks[b'MTXM'][((y//32)*w+x//32)*2:((y//32)*w+x//32)*2+2]
chunks[b'DIM ']=struct.pack('<HH',128,128);chunks[b'MTXM']=tile*(128*128);chunks[b'MASK']=bytes(128*128);chunks.pop(b'ISOM',None)
units=bytearray();positions=[(512,512),(2048,512),(3584,512),(512,2048),(3584,2048),(512,3584),(2048,3584),(3584,3584)]
def unit(typ,owner,x,y,resources=0):
 b=bytearray(36);struct.pack_into('<IHHH',b,0,len(units)//36+1,x,y,typ);b[16]=owner;b[17]=b[18]=b[19]=100;struct.pack_into('<I',b,20,resources);units.extend(b)
for i,(x,y)in enumerate(positions):
 unit(214,i,x,y)
 for j in range(4):unit(176+j%3,11,x-96+j*64,y+176,1500)
 unit(188,11,x+192,y,5000)
chunks[b'UNIT']=bytes(units);chunks[b'OWNR']=bytes([6]*8+[0]*4);chunks[b'SIDE']=bytes([1]*8+[0]*4)
chk=b''.join(struct.pack('<4sI',tag,len(value))+value for tag,value in chunks.items())
name='staredit\\scenario.chk';ht=bytearray(b'\xff'*128);index=hash_name(name,0)%8;struct.pack_into('<IIHHI',ht,index*16,hash_name(name,1),hash_name(name,2),0,0,0)
parts=[chk[i:i+4096]for i in range(0,len(chk),4096)]
positions=[4*(len(parts)+1)]
for part in parts:positions.append(positions[-1]+len(part))
wire=struct.pack('<'+'I'*len(positions),*positions)+b''.join(parts)
offset=176;bt=struct.pack('<4I',offset,len(wire),len(chk),0x80000200);header=struct.pack('<4sIIHHIIII',b'MPQ\x1a',32,offset+len(wire),0,3,32,160,8,1)
out=r/'build-native/probe55/eight-starts.scx';out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(header+cipher(ht,hash_name('(hash table)',3),True)+cipher(bt,hash_name('(block table)',3),True)+wire);print(out)

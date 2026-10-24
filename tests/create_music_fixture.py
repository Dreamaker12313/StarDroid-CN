#!/usr/bin/env python3
"""Create three short original test tones in a classic MPQ (no Blizzard data).
Includes raw and sector-packed files, Storm encryption and FIX_KEY offsets.
Usage: python3 tests/create_music_fixture.py /tmp/music-test.mpq
"""
from pathlib import Path
import io,math,struct,sys,wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from rebuild_mission_mpq import hash_name,cipher
def crypt_tail(data,key):
    n=len(data)//4*4
    return cipher(data[:n],key&0xffffffff,True)+data[n:]
names=['music\\terran1.wav','music\\terran2.wav','music\\trdyroom.wav','music\\title.wav']
ht=bytearray(b'\xff'*128);bt=bytearray();offset=32+128+16*len(names);payload=bytearray()
for i,name in enumerate(names):
    buf=io.BytesIO()
    with wave.open(buf,'wb') as w:
        w.setparams((1,2,22050,0,'NONE','not compressed'))
        w.writeframes(b''.join(struct.pack('<h',int(2800*math.sin(2*math.pi*(220+i*110)*n/22050))) for n in range(22050*(int(sys.argv[2]) if len(sys.argv)>2 else 3)+1)))
    raw=buf.getvalue();key=((hash_name(name.split('\\')[-1],3)+offset)^len(raw))&0xffffffff
    pieces=[raw[p:p+4096] for p in range(0,len(raw),4096)]
    sectors=[crypt_tail(b,key+n) for n,b in enumerate(pieces)]
    if i==0: data=b''.join(sectors);flags=0x80030000
    else:
        positions=[(len(sectors)+1)*4]
        for b in sectors:positions.append(positions[-1]+len(b))
        data=crypt_tail(struct.pack('<'+'I'*len(positions),*positions),key-1)+b''.join(sectors);flags=0x80030200
    slot=hash_name(name,0)&7
    while struct.unpack_from('<I',ht,slot*16+12)[0]!=0xffffffff:slot=(slot+1)&7
    struct.pack_into('<IIHHI',ht,slot*16,hash_name(name,1),hash_name(name,2),0,0,i)
    bt+=struct.pack('<IIII',offset,len(data),len(raw),flags);offset+=len(data);payload+=data
header=struct.pack('<4sIIHHIIII',b'MPQ\x1a',32,offset,0,3,32,160,8,len(names))
Path(sys.argv[1]).write_bytes(header+cipher(ht,hash_name('(hash table)',3),True)+cipher(bt,hash_name('(block table)',3),True)+payload)
print('Created four generated test tones:',sys.argv[1])

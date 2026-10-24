"""Generated MPQ sectors: direct ADPCM, exact full/partial output; no game assets."""
import struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from rebuild_mission_mpq import hash_name,cipher
names=['testmono.raw','teststereo.raw','testfull.raw']
samples=[(1,6),(2,8),(1,4096)]
ht=bytearray(b'\xff'*128);bt=bytearray();payload=bytearray();offset=32+128+16*3
for name,(channels,size) in zip(names,samples):
    encoded=bytes([0,4])+struct.pack('<'+'h'*channels,*([1000]*channels))+bytes([0x80])*(size//2-channels)
    sector=bytes([0x40 if channels==1 else 0x80])+encoded
    packed=struct.pack('<II',8,8+len(sector))+sector
    slot=hash_name(name,0)&7
    while struct.unpack_from('<I',ht,slot*16+12)[0]!=0xffffffff:slot=(slot+1)&7
    struct.pack_into('<IIHHI',ht,slot*16,hash_name(name,1),hash_name(name,2),0,0,len(bt)//16)
    bt+=struct.pack('<IIII',offset,len(packed),size,0x80000200);payload+=packed;offset+=len(packed)
header=struct.pack('<4sIIHHIIII',b'MPQ\x1a',32,offset,0,3,32,160,8,3)
Path(sys.argv[1]).write_bytes(header+cipher(ht,hash_name('(hash table)',3),True)+cipher(bt,hash_name('(block table)',3),True)+payload)

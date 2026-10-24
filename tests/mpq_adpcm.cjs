const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..');global.fetch=async n=>{const b=fs.readFileSync(path.join(root,'app/src/main/assets/game',n));return{ok:true,arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)}};
require(root+'/web/mpq-decoder.js');
(async()=>{const decoder=await MPQDecoder.create(),archive=new Uint8Array(fs.readFileSync(process.argv[2]));
for(const [file,size] of [['testmono.raw',6],['teststereo.raw',8],['testfull.raw',4096]]){const b=decoder.read(archive,file);assert.equal(b.length,size);for(let i=0;i<size;i+=2)assert.equal(new DataView(b.buffer).getInt16(i,true),1000);console.log('PASS',file,size,'correct PCM bytes');}
})().catch(e=>{console.error(e);process.exitCode=1;});

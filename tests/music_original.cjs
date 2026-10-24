// Requires a private music bundle exported by ExportMusicHarness; no music is distributed.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),bundle=process.env.OPENBW_MUSIC_BUNDLE||'/tmp/openbw-music-real-v16';
global.window=global;
global.fetch=async n=>{const file=path.isAbsolute(n)?n:path.join(root,'app/src/main/assets/game',n),b=fs.readFileSync(file);return{ok:true,arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)}};
require(root+'/web/campaign.js');require(root+'/web/mpq-decoder.js');
(async()=>{const manifest=JSON.parse(fs.readFileSync(bundle+'/manifest.json')),report={tracks:[],errors:[]};
for(const e of manifest.entries){try{const archive=await OpenBWCampaign.load(bundle+'/','music',e.name),decoder=await MPQDecoder.create(),b=decoder.read(archive,e.name),v=new DataView(b.buffer);assert.equal(Buffer.from(b.subarray(0,4)).toString(),'RIFF');assert.equal(Buffer.from(b.subarray(8,12)).toString(),'WAVE');
 let format,data,rate,channels;for(let p=12;p+8<=b.length;){const n=v.getUint32(p+4,true),tag=Buffer.from(b.subarray(p,p+4)).toString();assert(p+8+n<=b.length);if(tag==='fmt '){format=v.getUint16(p+8,true);channels=v.getUint16(p+10,true);rate=v.getUint32(p+16,true);}if(tag==='data')data=n;p+=8+n+(n&1);}
 assert.equal(format,1);assert(data>0&&rate>0);assert(b.some(x=>x));report.tracks.push({name:e.name,bytes:b.length,channels,seconds:data/rate,sha256:crypto.createHash('sha256').update(b).digest('hex')});console.log('PASS',e.name,b.length);
 }catch(error){report.errors.push({name:e.name,error:error.message});}}
for(const race of ['terran','protoss','zerg'])for(let i=1;i<=3;i++)assert(report.tracks.some(t=>t.name===`music\\${race}${i}.wav`));
fs.writeFileSync(path.join(root,'validation/music-original-v16.json'),JSON.stringify(report,null,2));assert.deepEqual(report.errors,[]);
})().catch(e=>{console.error(e);process.exitCode=1});

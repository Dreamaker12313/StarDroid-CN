/* Only compressed movie data plus a few decoded frames are resident. */
self.window=self;importScripts('./mpq-decoder.js','./campaign.js');
let x,memory,index=0,meta=null,ended=false;
const files={intro:'smk\\starintr.smk',terran1:'smk\\terran1.smk'};
function batch(){const frames=[];for(let n=0;n<6&&!ended;n++){
 const rgba=new Uint8Array(memory.buffer,x.movie_rgba(),meta.width*meta.height*4).slice();
 const size=x.movie_audio_size(),audio=size?new Uint8Array(memory.buffer,x.movie_audio(),size).slice():new Uint8Array();
 frames.push({index,rgba,audio});index++;if(index>=meta.frames)ended=true;else if(x.movie_next()<0)throw Error('Movie frame could not be decoded.');
 }postMessage({frames,ended},frames.flatMap(f=>[f.rgba.buffer,f.audio.buffer]));}
onmessage=async({data})=>{try{
 if(data.type==='open'){
  const name=files[data.clip];if(!name)throw Error('Unknown movie.');
  let source=await OpenBWCampaign.load('./cinematics/','cinematic',name),decoder=await MPQDecoder.create(),bytes=decoder.read(source,name);source=null;decoder=null;
  if(!bytes)throw Error('Import cinematics from StarCraft.mpq in Game Files.');
  const wasi={fd_close:()=>0,fd_seek:()=>8,fd_read:()=>8,fd_prestat_get:()=>8,fd_prestat_dir_name:()=>8,fd_write:(fd,p,n,w)=>{const v=new DataView(memory.buffer);let count=0;for(let i=0;i<n;i++)count+=v.getUint32(p+i*8+4,true);v.setUint32(w,count,true);return 0;},proc_exit:()=>{throw Error('Movie decoder stopped.');}};
  const {instance}=await WebAssembly.instantiate(await(await fetch('./cinematic-decoder.wasm')).arrayBuffer(),{wasi_snapshot_preview1:wasi});x=instance.exports;memory=x.memory;x._initialize();
  const p=x.movie_input(bytes.length);if(!p)throw Error('Movie is too large.');new Uint8Array(memory.buffer,p,bytes.length).set(bytes);bytes=null;
  if(!x.movie_open())throw Error('Unsupported or damaged original movie.');
  meta={width:x.movie_width(),height:x.movie_height(),frames:x.movie_frames(),interval:x.movie_interval(),channels:x.movie_channels(),bits:x.movie_bits(),rate:x.movie_rate()};
  postMessage({meta});batch();
 }else if(data.type==='next'&&x)batch();
 }catch(e){postMessage({error:e.message});}};

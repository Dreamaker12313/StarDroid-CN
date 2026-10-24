/* Bounded original SMK decoding, shared by the title and briefing workers. */
globalThis.decodeMenuClips=async files=>{
 let memory;const wasi={fd_close:()=>0,fd_seek:()=>8,fd_read:()=>8,fd_prestat_get:()=>8,fd_prestat_dir_name:()=>8,fd_write:(fd,p,n,w)=>{const v=new DataView(memory.buffer);let count=0;for(let i=0;i<n;i++)count+=v.getUint32(p+i*8+4,true);v.setUint32(w,count,true);return 0;},proc_exit:()=>{throw Error('Interface decoder stopped');}};
 const {instance}=await WebAssembly.instantiate(await(await fetch('./menu-decoder.wasm')).arrayBuffer(),{wasi_snapshot_preview1:wasi});
 const x=instance.exports;memory=x.memory;x._initialize();const clips={};let total=0;
 for(const [name,bytes] of Object.entries(files)){
  try{const p=x.portrait_input(bytes.length);if(!p)throw Error('Animation too large: '+name);
   new Uint8Array(memory.buffer,p,bytes.length).set(bytes);if(!x.portrait_open())throw Error('Unsupported animation: '+name);
   const width=x.portrait_width(),height=x.portrait_height(),frames=x.portrait_frames(),interval=Math.max(10,x.portrait_interval()),size=width*height*4;
   total+=size*frames;if(total>160*1024*1024)throw Error('Interface animation cache too large');const rgba=new Uint8Array(size*frames);
   for(let i=0;i<frames;i++){rgba.set(new Uint8Array(memory.buffer,x.portrait_rgba(),size),i*size);if(i+1<frames&&x.portrait_next()<0)throw Error('Invalid animation');}
   clips[name]={width,height,frames,interval,rgba};
  }finally{x.portrait_close();}
 }
 return clips;
};

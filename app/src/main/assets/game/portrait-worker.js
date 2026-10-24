/* Decode small portrait clips off the simulation thread. Only the SMK is sent
   here, never another copy of the full game archives. */
let module;
async function decoder() {
  if (module) return module;
  let memory;
  const wasi={fd_close:()=>0,fd_seek:()=>8,fd_read:()=>8,fd_prestat_get:()=>8,fd_prestat_dir_name:()=>8,fd_write:(fd,p,n,w)=>{
    const v=new DataView(memory.buffer);let count=0;
    for(let i=0;i<n;i++)count+=v.getUint32(p+i*8+4,true);
    v.setUint32(w,count,true);return 0;
  },proc_exit:()=>{throw Error('Portrait decoder stopped');}};
  const r=await fetch('./portrait-decoder.wasm');if(!r.ok)throw Error('Portrait decoder missing');
  const {instance}=await WebAssembly.instantiate(await r.arrayBuffer(),{wasi_snapshot_preview1:wasi});
  module=instance.exports;memory=module.memory;module._initialize();return module;
}
let ready=decoder();
onmessage=async ({data:{id,bytes}})=>{
  try {
    const x=await ready,p=x.portrait_input(bytes.byteLength);if(!p)throw Error('Portrait too large');
    new Uint8Array(x.memory.buffer,p,bytes.byteLength).set(new Uint8Array(bytes));
    if(!x.portrait_open())throw Error('Unsupported portrait');
    const width=x.portrait_width(),height=x.portrait_height(),frames=x.portrait_frames();
    const interval=Math.max(16,Math.min(1000,x.portrait_interval()||67)),size=width*height*4;
    const rgba=new Uint8Array(size*frames);
    for(let i=0;i<frames;i++){
      rgba.set(new Uint8Array(x.memory.buffer,x.portrait_rgba(),size),i*size);
      if(i+1<frames && x.portrait_next()<0)throw Error('Damaged portrait frame');
    }
    x.portrait_close();postMessage({id,width,height,frames,interval,rgba:rgba.buffer},[rgba.buffer]);
  }catch(e){module?.portrait_close();postMessage({id,error:e.message});}
};

/* Original SMK portraits from the user's MPQs; no game imagery is bundled. */
window.OpenBWPortraits = function(x, read) {
  const $=id=>document.getElementById(id), cache=new Map(), pending=new Map(), names=new Map();
  let worker=null, serial=0, cacheBytes=0, error='', draws=0, paused=false, voice=false, closed=false;
  let briefing=[null,null,null,null], transmission=null, sequence=0, getVoice=null,lastTick=performance.now();
  const surfaces=[{canvas:$('unit-portrait'),fallback:$('unit-preview-image')},...['brief-portrait','brief-portrait-1','brief-portrait-2','brief-portrait-3'].map(id=>({canvas:$(id)}))];
  for(const [i,s] of surfaces.entries()){s.brief=i>0;s.ctx=s.canvas.getContext('2d');s.key='';s.clip=null;s.frame=-1;s.elapsed=0;}
  const dat=read('arr/portdata.dat'),tbl=read('arr/portdata.tbl');
  if(!dat || !tbl)throw Error('Missing portrait tables');
  const dv=new DataView(dat.buffer,dat.byteOffset,dat.byteLength),tv=new DataView(tbl.buffer,tbl.byteOffset,tbl.byteLength);
  const count=dat.length/12,strings=[''];
  for(let i=0;i<tv.getUint16(0,true);i++){
    const a=tv.getUint16(2+2*i,true);let b=a;while(b<tbl.length&&tbl[b])b++;
    strings.push(new TextDecoder().decode(tbl.subarray(a,b)));
  }
  function fileFor(unit,talking,variant) {
    const portrait=x.openbw_portrait_for_type(unit);
    if(portrait<0||portrait>=count)return null;
    const idx=dv.getUint32((talking?count*4:0)+portrait*4,true),base=strings[idx];
    if(!base)return null;
    const key=base+':'+variant;
    if(names.has(key))return names.get(key);
    // The table stores a prefix; classic files append the final variant digit.
    let name,bytes;
    // Original fallback walks down through the lower numbered variants.
    for(let i=variant;i>=0&&!bytes;i--){name='portrait/'+base+i+'.smk';bytes=read(name);}
    if(!bytes && talking)return fileFor(unit,false,variant);
    const found=bytes?{name,bytes}:null;names.set(key,found);return found;
  }
  function idleWeights(unit) {
    const id=x.openbw_portrait_for_type(unit);
    return id>=0&&id<count?[0,1,2,3].map(i=>dv.getUint8((8+i)*count+id)):[100,0,0,0];
  }
  function nextVariant(s) {
    if(s.variant<0)return 0;
    // These four DAT bytes are fid00..fid03 weights, not clip durations.
    // Most original portraits use 85/5/5/5; the SCV uses 87/5/5/3.
    if(!s.talking){const weights=idleWeights(s.unit),sum=weights.reduce((a,b)=>a+b,0);let roll=Math.random()*sum;
      for(let i=0;i<4;i++){roll-=weights[i];if(roll<0)return i;}return 0;
    }
    // Talking clips have their own three-variant selector; avoid an immediate repeat.
    const choices=[0,1,2].filter(i=>i!==s.variant);return choices[Math.floor(Math.random()*choices.length)];
  }
  function ensureWorker() {
    if(worker)return;
    worker=new Worker('./portrait-worker.js');
    worker.onmessage=({data})=>{
      const job=pending.get(data.id);if(!job)return;pending.delete(data.id);clearTimeout(job.timer);
      if(data.error)job.reject(Error(data.error));else job.resolve({...data,rgba:new Uint8ClampedArray(data.rgba)});
    };
    worker.onerror=e=>{
      error=e.message||'Portrait worker failed';
      for(const job of pending.values()){clearTimeout(job.timer);job.reject(Error(error));}
      pending.clear();worker.terminate();worker=null;
    };
  }
  async function load(file) {
    if(cache.has(file.name)){const c=cache.get(file.name);cache.delete(file.name);cache.set(file.name,c);return c;}
    ensureWorker();const id=++serial;
    const promise=new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>{pending.delete(id);reject(Error('Portrait decode timed out'));},15000);
      pending.set(id,{resolve,reject,timer});
      const bytes=file.bytes.slice().buffer;worker.postMessage({id,bytes},[bytes]);
    });
    cache.set(file.name,promise);
    try{
      const c=await promise;cacheBytes+=c.rgba.byteLength;
      while(cacheBytes>16*1024*1024 && cache.size>1){
        const [name,value]=cache.entries().next().value;cache.delete(name);
        // Settled promises retain their size without awaiting another decode.
        cacheBytes-=value.byteLength||0;
      }
      promise.byteLength=c.rgba.byteLength;return c;
    }catch(e){cache.delete(file.name);throw e;}
  }
  function setTarget(s,unit,talking) {
    const key=unit+':'+Number(talking);
    if(key===s.key)return;
    // Keep the last decoded frame while changing idle/talking variants. Hiding
    // the surface here caused a black flash at each transmission boundary.
    const retain=s.unit===unit&&unit>=0&&s.clip;
    s.key=key;s.unit=unit;s.talking=talking;s.variant=-1;s.loading=false;s.loops=[0,0,0,0];
    if(!retain){s.clip=null;s.name='';s.frame=-1;s.canvas.hidden=true;s.ctx.clearRect(0,0,s.canvas.width,s.canvas.height);if(s.fallback)s.fallback.hidden=true;}
    if(s.brief)s.canvas.style.filter=talking?'none':'brightness(.62)';
    s.canvas.setAttribute('aria-label',talking?'Talking portrait':'Unit portrait');
    if(unit>=0)startClip(s);
  }
  async function startClip(s) {
    if(closed||s.loading)return;
    s.loading=true;const key=s.key,request=++sequence;s.request=request;
    try{
      const variant=nextVariant(s),file=fileFor(s.unit,s.talking,variant);
      if(!file){s.loading=false;return;}
      const clip=await load(file);
      if(closed||s.key!==key||s.request!==request)return;
      s.variant=variant;s.loops[variant]++;s.clip=clip;s.name=file.name;s.frame=-1;s.elapsed=0;s.canvas.width=s.brief?128:clip.width;s.canvas.height=s.brief?118:clip.height;
      s.image=s.ctx.createImageData(s.canvas.width,s.canvas.height);s.canvas.hidden=false;if(s.fallback)s.fallback.hidden=true;
      s.loading=false;paint(s,0);error='';
    }catch(e){if(s.request===request){s.loading=false;error=e.message;}}
  }
  function paint(s,f){
    if(!s.clip||s.frame===f)return;s.frame=f;
    const n=s.clip.width*s.clip.height*4;
    const pixels=s.clip.rgba.subarray(f*n,(f+1)*n);
    if(s.brief){
      // The 60x56 portrait is doubled inside a 128x118 frame. Scanlines belong
      // to the enlarged communication monitor, not the small in-game portrait.
      const out=s.image.data,w=s.canvas.width,h=s.canvas.height;
      const ox=Math.floor((w-s.clip.width*2)/2),oy=Math.floor((h-s.clip.height*2)/2);
      for(let y=0;y<s.clip.height*2;y++)for(let x=0;x<s.clip.width*2;x++){
        if(x+ox<0||x+ox>=w||y+oy<0||y+oy>=h)continue;
        const src=((y>>1)*s.clip.width+(x>>1))*4,dst=((y+oy)*w+x+ox)*4,shade=y&1?.44:1;
        out[dst]=pixels[src]*shade;out[dst+1]=pixels[src+1]*shade;out[dst+2]=pixels[src+2]*shade;out[dst+3]=255;
      }
    }else s.image.data.set(pixels);
    s.ctx.putImageData(s.image,0,0);draws++;
  }
  function tick(now) {
    if(closed)return;
    const dt=Math.max(0,Math.min(100,now-lastTick));lastTick=now;
    if(!document.hidden){
      if(getVoice)voice=getVoice();
      const t=transmission && x.openbw_frame()<=transmission.until?transmission:null;
      setTarget(surfaces[0],t?t.unit:x.openbw_selected_type(),t?voice:!!x.openbw_portrait_talking());
      for(let i=0;i<4;i++){const b=briefing[i];setTarget(surfaces[i+1],b?b.unit:-1,!!b?.talking&&voice);}
      for(const s of surfaces){
        if(paused||s.unit<0||!s.clip)continue;
        s.elapsed+=dt;
        const f=Math.max(0,Math.floor(s.elapsed/s.clip.interval));
        if(f>=s.clip.frames){if(!s.loading)startClip(s);}else paint(s,f);
      }
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
  const api={
    voices:fn=>{getVoice=fn;},
    state:(hold,talk=voice)=>{if(paused!==hold)lastTick=performance.now();paused=hold;voice=talk;},
    briefing:(unit,talking=false,slot=0)=>{if(slot>=0&&slot<4)briefing[slot]=unit<0?null:{unit,talking};},
    clearBriefing:()=>{briefing=[null,null,null,null];},
    transmit:(unit,until)=>{transmission={unit,until};},
    close:()=>{closed=true;worker?.terminate();for(const job of pending.values()){clearTimeout(job.timer);job.reject(Error('Portraits closed'));}pending.clear();cache.clear();names.clear();},
    stats:()=>({draws,paused,cacheBytes,pending:pending.size,error,surfaces:surfaces.map(s=>({unit:s.unit,talking:s.talking,file:s.name||'',frame:s.frame,frames:s.clip?.frames||0,variant:s.variant,loops:s.loops,weights:s.unit>=0?idleWeights(s.unit):[],visible:!s.canvas.hidden,scanlines:s.brief,width:s.canvas.width,height:s.canvas.height}))}),
  };
  window.openbwPortraitStats=api.stats;return api;
};

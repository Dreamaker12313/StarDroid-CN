/* Original dialog geometry and bitmap lettering. All art comes from local MPQs. */
globalThis.OpenBWOriginal = (() => {
  const normalize=n=>n.toLowerCase().replaceAll('\\','/');
  const textAt=(data,p)=>{if(!p)return '';if(p>=data.length)throw Error('Invalid UI text offset');let e=p;while(e<data.length&&data[e])e++;return new TextDecoder('windows-1252').decode(data.subarray(p,e));};
  function dialog(data) {
    if(!data||data.length<86)throw Error('Original dialog is missing');
    const v=new DataView(data.buffer,data.byteOffset,data.byteLength),seen=new Set(),widgets=[];
    function record(p){if(p+86>data.length||seen.has(p))throw Error('Invalid dialog chain');seen.add(p);
      return{next:v.getUint32(p,true),x:v.getUint16(p+4,true),y:v.getUint16(p+6,true),width:v.getUint16(p+12,true),height:v.getUint16(p+14,true),text:textAt(data,v.getUint32(p+20,true)),flags:v.getUint32(p+24,true),id:v.getUint16(p+32,true),type:v.getUint32(p+34,true),smk:v.getUint32(p+66,true),tx:v.getUint16(p+70,true),ty:v.getUint16(p+72,true),rx:v.getUint16(p+54,true),ry:v.getUint16(p+56,true),rx2:v.getUint16(p+58,true),ry2:v.getUint16(p+60,true),rw:v.getUint16(p+74,true),rh:v.getUint16(p+76,true)};}
    const root=record(0);let p=root.smk;
    while(p){const w=record(p);widgets.push(w);p=w.next;if(widgets.length>512)throw Error('Dialog too large');}
    function animations(w){const result=[],offsets=new Set();let p=w.smk;
      while(p){if(p+30>data.length||offsets.has(p))throw Error('Invalid animation chain');offsets.add(p);
        result.push({name:normalize(textAt(data,v.getUint32(p+10,true))),flags:v.getUint16(p+4,true),x:v.getUint16(p+18,true),y:v.getUint16(p+20,true)});p=v.getUint32(p,true);}
      return result;
    }
    return{root,widgets,animations,get:id=>widgets.find(w=>w.id===id)};
  }
  function place(el,w){Object.assign(el.style,{position:'absolute',left:w.x+'px',top:w.y+'px',width:w.width+'px',height:w.height+'px'});}
  function response(w){return (w.flags&16)&&w.rx2>w.rx&&w.ry2>w.ry ? {x:w.x+w.rx,y:w.y+w.ry,width:w.rx2-w.rx+1,height:w.ry2-w.ry+1} : w;}
  function labelBox(el,w,origin=w){
    const width=Math.max(1,(w.rw||w.width)-w.tx),height=Math.max(1,(w.rh||w.height)-w.ty);
    Object.assign(el.style,{position:'absolute',left:(w.x-origin.x+w.tx)+'px',top:(w.y-origin.y+w.ty)+'px',width:width+'px',height:height+'px',bottom:'auto',display:'flex',justifyContent:w.flags&0x200000?'center':w.flags&0x400000?'flex-end':'flex-start',alignItems:w.flags&0x4000000?'flex-end':w.flags&0x2000000?'center':'flex-start'});
  }
  const fontSizes=['8','10','12','14','16','16x','32','50'];
  async function recoverFonts(sources,out={}) {
    const valid=b=>b?.length>=8&&String.fromCharCode(...b.subarray(0,4))==='FONT'&&b[5]>=b[4]&&b[7]>0&&b[7]<=64&&8+(b[5]-b[4]+1)*4<=b.length;
    // Fonts are optional. Never share their WASM decoder with gameplay or art,
    // and never reuse an instance after a trap (including between filenames).
    // A damaged font8 must not discard the readable font10/14/16 that follow it.
    let decoder=null;
    for(const source of sources.filter(Boolean))for(const n of fontSizes){
      if(out[n])continue;
      for(const prefix of ['files/font/','font/']){
        try{decoder||=await MPQDecoder.create();const b=decoder.read(source,prefix+'font'+n+'.fnt');if(valid(b)){out[n]=b;break;}}
        catch(e){decoder=null;console.info('Optional font '+n+':',e.message);}
      }
    }
    return out;
  }
  async function fonts(sources=[]) {
    const out={};
    try{await recoverFonts([await OpenBWCampaign.load('./interface/','interface')],out);}
    catch(e){console.info('Original font import:',e.message);}
    return recoverFonts(sources,out);
  }
  function text(el,value,draw,width=0,align='left',color=2) {
    el.setAttribute('aria-label',value.replace(/[\x00-\x1f]/g,' '));
    if(!draw){el.textContent=value.replace(/[\x01-\x09\x0b\x0c\x0e-\x1f]/g,'');return;}
    const c=draw(value,{width,align,color});c.className='original-text';c.setAttribute('aria-hidden','true');el.replaceChildren(c);
  }
  async function clips(files){
    if(!Object.keys(files).length)return{};
    return new Promise((resolve,reject)=>{const worker=new Worker('./menu-worker.js'),timer=setTimeout(()=>{worker.terminate();reject(Error('Interface animation timed out'));},30000);
      worker.onmessage=({data})=>{clearTimeout(timer);worker.terminate();data.error?reject(Error(data.error)):resolve(data.clips);};
      worker.onerror=e=>{clearTimeout(timer);worker.terminate();reject(Error(e.message));};
      const copy=Object.fromEntries(Object.entries(files).map(([n,b])=>[n,b.slice()]));worker.postMessage(copy,Object.values(copy).map(b=>b.buffer));
    });
  }
  function frame(canvas,clip,time,loop=true){if(!clip)return;time=Math.max(0,time);
    const f=loop?Math.floor(time/clip.interval)%clip.frames:Math.min(clip.frames-1,Math.floor(time/clip.interval));
    if(canvas._clip===clip&&canvas._frame===f)return;
    canvas._clip=clip;canvas._frame=f;canvas.width=clip.width;canvas.height=clip.height;
    const size=clip.width*clip.height*4;canvas.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(clip.rgba.buffer,clip.rgba.byteOffset+f*size,size),clip.width,clip.height),0,0);
  }
  // These movements are game code, not SMK movies. See REFERENCES.md for the
  // original recording and the measured/reconstructed timing boundaries.
  function tween(){let job=null;return{
    run(duration,draw){if(job)throw Error('Interface transition already running');return new Promise(resolve=>{job={duration,draw,resolve,time:0};draw(0);});},
    step(dt){if(!job)return;const j=job;j.time=Math.min(j.duration,j.time+dt);j.draw(j.time/j.duration);if(j.time===j.duration){job=null;j.resolve();}},
    get running(){return !!job;}
  };}
  function slide(el,w,amount){const off=w.x+w.width/2<320?-(w.x+w.width):640-w.x;el.style.transform='translateX('+Math.round(off*amount)+'px)';}
  const soundNames=['mousedown2','mouseover','swishin','swishlock','swishout'];
  function soundFiles(read){const result={};for(const n of [...soundNames,'button','youwin','youlose']){try{const b=read('sound/'+(['button','youwin','youlose'].includes(n)?'misc/':'glue/')+n+'.wav');if(b)result[n]=b;}catch(e){console.info('Optional menu sound:',e.message);}}return result;}
  function sounds(files){let ctx=null,paused=false,closed=false,played=0,lastPlayed='',error='';const buffers=new Map(),sources=new Set();
    const muted=()=>{try{return localStorage.getItem('openbw-muted')==='1';}catch{return false;}};
    async function play(name){if(closed||paused||document.hidden||muted()||!files[name])return;
      try{ctx||=new (window.AudioContext||window.webkitAudioContext)();await ctx.resume();
        if(!buffers.has(name))buffers.set(name,ctx.decodeAudioData(files[name].slice().buffer));
        const buffer=await buffers.get(name);if(closed||paused||document.hidden||muted())return;
        const source=ctx.createBufferSource();source.buffer=buffer;source.connect(ctx.destination);sources.add(source);source.onended=()=>sources.delete(source);source.start();played++;lastPlayed=name;
      }catch(e){error=e.message;}
    }
    function suspend(on){paused=on;if(ctx)(on?ctx.suspend():ctx.resume()).catch(()=>{});}
    function close(){closed=true;for(const s of sources)try{s.stop();}catch{}sources.clear();if(ctx)ctx.close().catch(()=>{});}
    document.addEventListener('visibilitychange',()=>suspend(document.hidden));addEventListener('pagehide',close,{once:true});
    return{play,suspend,close,stats:()=>({available:Object.keys(files),decoded:buffers.size,played,lastPlayed,paused,error})};
  }
  function buttonSounds(root,sound,game=false){if(!game)root.addEventListener('pointerover',e=>{const b=e.target.closest('button');if(e.pointerType==='mouse'&&b&&!b.disabled&&!b.contains(e.relatedTarget)&&!root.inert)sound.play('mouseover');});root.addEventListener('click',e=>{if(e.target.closest('button:not(:disabled)')&&!root.inert)sound.play(game?'button':'mousedown2');},true);}
  function buttonText(button,label,value,draw,normal=3,highlight=4){let hover=false,pressed=false,last=null;
    const hot=()=>hover||pressed||button.matches(':focus-visible');
    const update=()=>{const color=button.disabled?5:hot()?highlight:normal;if(color!==last){text(label,button.disabled?value.replace(/[\x01-\x08\x0b\x0c\x0e-\x1f]/g,''):value,draw,0,'left',color);last=color;}};
    button.addEventListener('pointerenter',e=>{hover=e.pointerType==='mouse';update();});
    button.addEventListener('pointerleave',()=>{hover=false;pressed=false;update();});
    button.addEventListener('pointerdown',()=>{pressed=true;update();});
    for(const event of ['pointerup','pointercancel','lostpointercapture'])button.addEventListener(event,()=>{pressed=false;update();});
    for(const event of ['focus','blur'])button.addEventListener(event,update);
    new MutationObserver(update).observe(button,{attributes:true,attributeFilter:['disabled']});
    update();return hot;
  }
  const slideProgress=p=>1-Math.pow(1-Math.max(0,Math.min(1,p)),3);
  return{slideProgress,dialog,place,response,labelBox,fonts,recoverFonts,text,clips,frame,normalize,tween,slide,soundNames,soundFiles,sounds,buttonSounds,buttonText};
})();

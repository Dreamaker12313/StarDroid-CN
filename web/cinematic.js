(() => {
 const $=id=>document.getElementById(id),canvas=$('movie-screen'),ctx=canvas.getContext('2d'),worker=new Worker('./cinematic-worker.js');
 const audio=new (window.AudioContext||window.webkitAudioContext)(),gain=audio.createGain();gain.connect(audio.destination);
 gain.gain.value=localStorage.getItem('openbw-muted')==='1'?0:1;
 let meta=null,queue=[],busy=true,ended=false,closed=false,suspended=document.hidden,origin=null,audioEnd=0,frame=-1,error='',scheduled=0,raf=0,wakeToken=0;
 const resize=()=>document.documentElement.style.setProperty('--movie-scale',Math.min(innerWidth/640,innerHeight/480));resize();addEventListener('resize',resize);
 const leave=()=>{if(closed)return;closed=true;worker.terminate();cancelAnimationFrame(raf);audio.close().catch(()=>{});location.replace('./title.html?menu');};
 $('movie-skip').onclick=leave;window.openbwBack=()=>{leave();return true;};
 addEventListener('keydown',e=>{if(['Escape','Enter',' '].includes(e.key)){e.preventDefault();leave();}});
 function wake(){const token=++wakeToken;const resume=()=>{if(!closed&&!suspended&&!document.hidden)audio.resume().catch(()=>{});};resume();for(const delay of [100,400,1000])setTimeout(()=>{if(token===wakeToken)resume();},delay);}
 window.openbwAndroidSuspend=()=>{suspended=true;++wakeToken;audio.suspend().catch(()=>{});};
 window.openbwAndroidResume=()=>{suspended=false;wake();};
 document.addEventListener('visibilitychange',()=>document.hidden?window.openbwAndroidSuspend():window.openbwAndroidResume());addEventListener('focus',wake);addEventListener('pageshow',wake);
 function schedule(bytes){if(!bytes.length||!meta.channels)return;
  const sampleBytes=meta.bits/8,n=bytes.length/(sampleBytes*meta.channels);if(!Number.isInteger(n)||n>meta.rate*10)throw Error('Invalid movie audio chunk.');
  const buffer=audio.createBuffer(meta.channels,n,meta.rate),view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  for(let channel=0;channel<meta.channels;channel++){const out=buffer.getChannelData(channel);for(let i=0;i<n;i++){const p=(i*meta.channels+channel)*sampleBytes;out[i]=meta.bits===16?view.getInt16(p,true)/32768:(bytes[p]-128)/128;}}
  const source=audio.createBufferSource();source.buffer=buffer;source.connect(gain);source.start(origin+audioEnd);audioEnd+=buffer.duration;scheduled++;
 }
 worker.onmessage=({data})=>{if(closed)return;
  try{if(data.error)throw Error(data.error);
   if(data.meta){meta=data.meta;canvas.width=meta.width;canvas.height=meta.height;canvas.style.height=meta.height+'px';return;}
   busy=false;ended=data.ended;if(origin===null){origin=audio.currentTime+.15;$('movie-status').hidden=true;setTimeout(()=>$('movie-hint').style.opacity=0,2200);wake();}
   for(const f of data.frames){schedule(f.audio);delete f.audio;queue.push(f);}
  }catch(e){error=e.message;$('movie-status').textContent=error+' Tap to return.';$('movie-status').hidden=false;worker.terminate();audio.suspend().catch(()=>{});}
 };
 worker.onerror=e=>{e.preventDefault();error=e.message;$('movie-status').textContent='Movie playback stopped. Tap to return.';$('movie-status').hidden=false;audio.suspend().catch(()=>{});};
 function draw(){if(!closed&&!error&&!suspended&&!document.hidden&&origin!==null&&audio.state==='running'){
  const elapsed=Math.max(0,(audio.currentTime-origin)*1000);let current=null;
  while(queue.length&&queue[0].index*meta.interval<=elapsed)current=queue.shift();
  if(current){ctx.putImageData(new ImageData(new Uint8ClampedArray(current.rgba.buffer),meta.width,meta.height),0,0);frame=current.index;}
  if(!busy&&!ended&&queue.length<7){busy=true;worker.postMessage({type:'next'});}
  if(ended&&!queue.length&&elapsed>=Math.max(meta.frames*meta.interval,audioEnd*1000)){leave();return;}
 }raf=requestAnimationFrame(draw);}
 window.openbwCinematicStats=()=>({meta,frame,queue:queue.length,ended,scheduled,audioEnd,position:origin===null?0:Math.max(0,audio.currentTime-origin),audioState:audio.state,suspended,error});
 addEventListener('pagehide',()=>{closed=true;worker.terminate();cancelAnimationFrame(raf);audio.close().catch(()=>{});},{once:true});
 if(suspended)audio.suspend().catch(()=>{});worker.postMessage({type:'open',clip:new URLSearchParams(location.search).get('clip')||'intro'});draw();
})();

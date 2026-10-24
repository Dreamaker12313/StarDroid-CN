/* Interpret original establishing-shot text files; no campaign prose/art bundled. */
window.OpenBWStory=(()=>{
 function parse(bytes){const pages=[];let state={duration:5000,fade:400,position:'left'},lines=[];
  for(const line of new TextDecoder('windows-1252').decode(bytes).replaceAll('\r','').split('\n')){
   const tag=line.match(/^<\/(\w+)(?:\s+(.*?))?>$/);if(!tag){lines.push(line);continue;}
   const [,key,arg='']=tag;
   if(key==='PAGE'){const text=lines.join('\n').trim();if(text)pages.push({...state,text});lines=[];}
   else if(key==='BACKGROUND')state.background=arg;
   else if(key==='FONTCOLOR')state.tint=arg;
   else if(key==='DISPLAYTIME')state.duration=Math.max(1000,Math.min(60000,+arg||5000));
   else if(key==='FADESPEED')state.fade=Math.max(100,Math.min(1000,(+arg||100)*4));
   else if(key.startsWith('SCREEN'))state.position=key==='SCREENLOWERLEFT'?'lowerleft':'left';
  }return pages;
 }
 let active=null,suspended=false;
 async function mission(id,fonts={}){
  const entry=OpenBWMissions.find(m=>m.id===id);if(!entry?.opening)return;
  let source,decoder,pages=[];
  try{source=await OpenBWCampaign.load(entry.game==='broodwar'?'./story-broodwar/':'./story/','story');decoder=await MPQDecoder.create();
   if(id==='terran01'){const data=decoder.read(source,'rez/estt0t.txt');if(data)pages.push(...parse(data).slice(0,1));}
   const data=decoder.read(source,entry.opening);if(data)pages.push(...parse(data));
   for(const page of pages){page.art=OpenBWArt.pcx(decoder.read(source,page.background),false);page.font=OpenBWArt.font(fonts['16'],OpenBWArt.pcx(decoder.read(source,page.tint)),page.art.palette,{lineHeight:22});}
  }catch(e){console.info('Optional mission opening:',e.message);return;}
  if(!pages.length)return;
  const screen=document.createElement('div');screen.id='story-screen';screen.setAttribute('role','button');screen.tabIndex=0;screen.setAttribute('aria-label','Mission opening. Tap to continue.');
  (document.getElementById('game-stage')||document.body).append(screen);
  let index=-1,elapsed=0,last=performance.now(),raf=0,closing=false;
  const previousBack=window.openbwBack;
  await new Promise(resolve=>{
   const done=()=>{cancelAnimationFrame(raf);removeEventListener('keydown',key,true);screen.remove();window.openbwBack=previousBack;active=null;resolve();};
   const next=()=>{if(closing)return;index++;elapsed=0;last=performance.now();if(index>=pages.length){closing=true;done();return;}
    const page=pages[index],img=new Image();img.src=page.art.canvas.toDataURL();img.alt='';const caption=document.createElement('div');caption.className='story-caption '+page.position;OpenBWOriginal.text(caption,page.text,page.font,576);const frame=document.createElement('div');frame.className='story-frame';frame.append(img,caption);screen.replaceChildren(frame);frame.style.opacity=0;
   };
   const key=e=>{if(['Escape','Enter',' '].includes(e.key)){e.preventDefault();e.stopImmediatePropagation();next();}};
   active={index:()=>index,pages:pages.length,elapsed:()=>elapsed};screen.onclick=next;window.openbwBack=()=>{next();return true;};addEventListener('keydown',key,true);
   function tick(now){const dt=Math.max(0,Math.min(100,now-last));last=now;if(!document.hidden&&!suspended){elapsed+=dt;const page=pages[index];screen.firstElementChild.style.opacity=Math.min(1,elapsed/page.fade,(page.duration+2*page.fade-elapsed)/page.fade);if(elapsed>=page.duration+2*page.fade)next();}if(!closing)raf=requestAnimationFrame(tick);}
   next();raf=requestAnimationFrame(tick);
  });
 }
 window.openbwStoryStats=()=>active?{active:true,page:active.index(),pages:active.pages,elapsed:active.elapsed()}:{active:false};
 return{parse,mission,suspend:on=>{suspended=on;}};
})();

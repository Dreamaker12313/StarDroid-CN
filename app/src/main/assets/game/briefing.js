/* Original race-specific room geometry/media; reconstructed glue-screen choreography. */
window.OpenBWBriefing = async function(read,fonts,sounds,race=1) {
 const $=id=>document.getElementById(id),room=$('brief-room'),letter=['z','t','p'][race]||'t',prefix='glue/ready'+letter+'/',layoutName='rez/glurdy'+letter+'.bin',layout=OpenBWOriginal.dialog(read(layoutName));
 room.setAttribute('aria-label',['Zerg','Terran','Protoss'][race]+' mission briefing');
 const background=OpenBWArt.pcx(read('glue/palr'+letter+'/backgnd.pcx'),false),tint=OpenBWArt.pcx(read('glue/palr'+letter+'/tfont.pcx'));
 const effect=read('glue/palr'+letter+'/teffect.pcx'),glass=effect?OpenBWArt.pcx(effect).indices[1]:138;
 const small=OpenBWArt.font(fonts['10'],tint,background.palette),large=OpenBWArt.font(fonts['16'],tint,background.palette),dialogue=OpenBWArt.font(fonts['14'],tint,background.palette,{lineHeight:19}),buttonFont=OpenBWArt.font(fonts['16x'],tint,background.palette)||large;
 $('brief-background').src=background.canvas.toDataURL();
 const panelArt=new Map(),moving=[],highlights=[],labels=[];
 function attach(el,w,parent=w){OpenBWOriginal.place(el,w);moving.push({el,w:parent});}
 for(const w of layout.widgets.filter(w=>w.type===5&&(w.flags&8))){
  const b=read(w.text);if(!b)continue;const img=new Image();img.className='brief-original-art';img.alt='';img.dataset.widget=w.id;
  const decoded=OpenBWArt.pcx(b,true,(w.flags&0x40000)?glass:-1);panelArt.set(w.id,{...decoded,widget:w});img.src=decoded.canvas.toDataURL();attach(img,w);
  // BIN boxes can include a one-pixel hit-test margin. Do not stretch the art.
  img.style.width=decoded.canvas.width+'px';img.style.height=decoded.canvas.height+'px';room.insertBefore(img,$('brief-text'));
 }
 for(let i=0;i<4;i++){
  const w=layout.get(15+i),c=$('brief-portrait'+(i?'-'+i:'')),art=panelArt.get(9+i);attach(c,w,layout.get(9+i));
  if(art){const mask=document.createElement('canvas');mask.width=w.width;mask.height=w.height;const ctx=mask.getContext('2d'),im=ctx.createImageData(w.width,w.height);
   for(let y=0;y<w.height;y++)for(let x=0;x<w.width;x++){const ax=w.x+x-art.widget.x,ay=w.y+y-art.widget.y;if(ax>=0&&ay>=0&&ax<art.canvas.width&&ay<art.canvas.height&&art.indices[ay*art.stride+ax]===glass)im.data.set([255,255,255,255],(y*w.width+x)*4);}
   ctx.putImageData(im,0,0);c.style.maskImage='url('+mask.toDataURL()+')';c.style.maskSize='100% 100%';
  }
  const border=read(prefix+letter+'frame'+(i+1)+'.pcx');if(border){const img=new Image();img.className='brief-speaker-frame brief-portrait-border';img.alt='';img.src=OpenBWArt.pcx(border).canvas.toDataURL();attach(img,w,layout.get(9+i));room.append(img);}
  const data=read(prefix+letter+'frameh'+(i+1)+'.pcx');if(data){const img=new Image();img.className='brief-speaker-frame brief-active-speaker';img.alt='';img.src=OpenBWArt.pcx(data).canvas.toDataURL();img.hidden=true;attach(img,w,layout.get(9+i));room.append(img);highlights[i]=img;}
 }
 let startHot=()=>false;
 const bindings=[['brief-text',65526,9],['brief-goals',65525,6],['brief-objectives-heading',65535,6],['brief-start',13,0],['brief-cancel',14,7],['brief-replay',20,5]];
 for(const [id,index,parent] of bindings){const w=layout.get(index),el=$(id);if(parent)attach(el,w,layout.get(parent));else OpenBWOriginal.place(el,OpenBWOriginal.response(w));
  if(w.type===14){const text=w.text.slice(1);el.setAttribute('aria-label',text.replace(/[\x00-\x1f]/g,''));const label=document.createElement('span');label.className='brief-button-label';el.append(label);
   const hot=OpenBWOriginal.buttonText(el,label,text,(w.flags&0x4000)?buttonFont:large);if(index===13)startHot=hot;
   OpenBWOriginal.labelBox(label,w,parent?w:OpenBWOriginal.response(w));
   if(parent)labels.push(label);
  }else if(w.text)OpenBWOriginal.text(el,w.text,large);
 }
 labels.push($('brief-objectives-heading'));
 if(sounds)OpenBWOriginal.buttonSounds(room,sounds);
 // Decode each widget's original SMK chain, including the Zerg room drip.
 // Terran Start has a separate selected globe in the archive; it is not in
 // glurdyt's projector chain and must be loaded explicitly.
 // proj/proloop are a separate projector sequence. They must not be restarted
 // or drawn over the globe as part of the idle/highlight button animation.
 const specs=layout.widgets.flatMap(w=>layout.animations(w).reverse().map(a=>({...a,w}))).filter(a=>letter!=='t'||!/(?:proj|proloop)\.smk$/.test(a.name));
 if(letter==='t'&&read(prefix+'starton.smk')){const base=specs.find(a=>a.name===prefix+'start.smk');specs.push({...base,name:prefix+'starton.smk',selected:true});}
 const motion={};for(const a of specs){const b=read(a.name);if(b)motion[a.name]=b;}
 let animations={};try{animations=await OpenBWOriginal.clips(motion);}catch(e){console.warn(e.message);}
 const layers=[];for(const a of specs){
  const clip=animations[a.name];if(!clip)continue;const c=document.createElement('canvas');c.className='brief-original-motion';c.dataset.clip=a.name;
  const base=animations[prefix+'start.smk'],dx=a.selected&&base?Math.floor((base.width-clip.width)/2):0,dy=a.selected&&base?base.height-clip.height:0;
  Object.assign(c.style,{left:(a.w.x+a.x+dx)+'px',top:(a.w.y+a.y+dy)+'px'});c.hidden=true;
  // The Protoss glow is an additive light layer; opaque dark pixels made a
  // rectangular black column and hid the original pedestal/background.
  if(letter==='p'&&a.name.endsWith('/glow.smk'))c.style.mixBlendMode='screen';
  room.insertBefore(c,room.querySelector('.brief-original-art')||$('brief-text'));layers.push({c,a,clip});
 }
 let selectedStart=false,selectPromise=null;
 const textWindow=$('brief-text');let textContent=null,textDrag=null,manualUntil=0,resumeStart=0,resumeOffset=0;
 const tween=OpenBWOriginal.tween();let elapsed=0,suspended=false,last=performance.now(),active=false,phase='closed',scrollStart=0,scrollDuration=0,speechPosition=null,manualScroll=null,scrollOffset=0,hoverTime=0,wasHot=false,slideAmount=1;
 const contentHeight=()=>textContent?Math.max(textContent.scrollHeight,textContent.querySelector('canvas')?.height||0):0;
 const scrollDistance=()=>contentHeight()>layout.get(65526).height?Math.max(0,contentHeight()-57):0;
 const slide=amount=>{slideAmount=amount;for(const {el,w} of moving)OpenBWOriginal.slide(el,w,amount);};
 const captionVisible=on=>labels.forEach(el=>el.style.visibility=on?'':'hidden');
 const speaker=slot=>highlights.forEach((img,i)=>img.hidden=i!==slot);
 function tick(now){const dt=Math.max(0,Math.min(100,now-last));last=now;
  if(active&&!suspended&&!document.hidden){elapsed+=dt;tween.step(dt);
   const hot=(phase==='ready'&&startHot())||selectedStart;if(hot&&!wasHot)hoverTime=0;if(hot)hoverTime+=dt;wasHot=hot;
   for(const {c,a,clip} of layers){let visible=phase!=='closed';
    const base=a.name===prefix+'start.smk',selected=a.name===prefix+'starton.smk';
    if(selected)visible&&=hot;else if(base&&animations[prefix+'starton.smk'])visible&&=!hot;else if(a.flags&8)visible&&=hot;OpenBWOriginal.frame(c,clip,(a.flags&8)?hoverTime:elapsed,!!(a.flags&4));
    c.hidden=!visible;
    c.style.filter=letter==='t'&&base?'brightness(.55)':a.flags&2&&!selected?(hot?'brightness(1)':'brightness(.25)'):'';
    if(a.flags&1)c.style.opacity=String(Math.min(1,elapsed/600));
   }
   if(textContent){
    // Native mission-three footage holds the opening lines for about four
    // seconds, then continues scrolling until roughly three lines remain.
    // The narration clock also freezes correctly when Android suspends audio.
    const distance=scrollDistance(),lead=Math.min(4000,scrollDuration*.2);
    const position=speechPosition??elapsed-scrollStart,progress=scrollDuration?Math.min(1,Math.max(0,(position-lead)/Math.max(1,scrollDuration-lead))):0;
    if(manualScroll!==null&&!textDrag&&elapsed>=manualUntil){manualScroll=null;resumeStart=elapsed;resumeOffset=scrollOffset;}
    const blend=resumeStart?Math.min(1,(elapsed-resumeStart)/650):1;
    const automatic=resumeOffset*(1-blend)+distance*progress*blend;
    scrollOffset=Math.min(distance,Math.max(0,manualScroll===null?automatic:manualScroll));textContent.style.transform='translateY(-'+Math.floor(scrollOffset)+'px)';
   }
  }
  requestAnimationFrame(tick);
 }
 requestAnimationFrame(tick);
 // The text window can also be read at the player's pace without dragging the room.
 textWindow.onpointerdown=e=>{if(e.button!==0)return;textWindow.setPointerCapture(e.pointerId);textDrag={id:e.pointerId,y:e.clientY,offset:scrollOffset,dragged:false};};
 textWindow.onpointermove=e=>{if(!textDrag||textDrag.id!==e.pointerId)return;const scale=room.getBoundingClientRect().width/640,dy=(textDrag.y-e.clientY)/scale;
  // Android emits small moves even for a tap. Only deliberate dragging takes
  // over; the speech clock resumes automatically after the reader lets go.
  if(!textDrag.dragged&&Math.abs(dy)<6)return;textDrag.dragged=true;manualScroll=Math.max(0,Math.min(scrollDistance(),textDrag.offset+dy));manualUntil=elapsed+2500;
 };
 textWindow.onpointerup=textWindow.onpointercancel=textWindow.onlostpointercapture=e=>{if(textDrag?.id===e.pointerId){textDrag=null;manualUntil=elapsed+2500;}};
 textWindow.addEventListener('wheel',e=>{e.preventDefault();manualScroll=Math.max(0,Math.min(scrollDistance(),scrollOffset+e.deltaY*(e.deltaMode===1?19:1)));manualUntil=elapsed+2500;},{passive:false});
 async function enter(){active=true;phase='entering';elapsed=0;last=performance.now();room.style.opacity='1';room.inert=true;captionVisible(false);slide(1);speaker(-1);sounds?.play('swishin');
  await tween.run(560,p=>slide(1-OpenBWOriginal.slideProgress(p)));phase='ready';room.inert=false;captionVisible(true);sounds?.play('swishlock');
 }
 async function leave(){if(phase!=='ready')return;phase='leaving';room.inert=true;captionVisible(false);speaker(-1);sounds?.play('swishout');
  await tween.run(320,p=>slide(OpenBWOriginal.slideProgress(p)));await tween.run(180,()=>{});await tween.run(200,p=>room.style.opacity=1-p);active=false;phase='closed';
 }
 slide(1);captionVisible(false);
 window.openbwBriefingArtStats=()=>({originalRoom:true,layout:layoutName,selectedStart,fonts:{small:!!small,large:!!large,button:!!buttonFont},dialogueFont:dialogue?'font14':'fallback',lineHeight:19,contentHeight:contentHeight(),scrollDistance:scrollDistance(),scrollOffset,scrollDuration,speechPosition,manualScroll:manualScroll!==null,animations:Object.keys(animations),active,suspended,phase,elapsed,slideAmount,glassIndex:glass,speakerFrames:highlights.length,sounds:sounds?.stats()});
 return{enter,leave,speaker,selectStart:()=>{
  if(selectPromise)return selectPromise;
  selectedStart=true;
  // One tap still starts. Retain the selected artwork for two SMK frames so a
  // touch release cannot erase it before Android paints the selection feedback.
  selectPromise=new Promise(resolve=>setTimeout(resolve,160));return selectPromise;
 },progress:(position,duration)=>{speechPosition=position;scrollDuration=duration;},active:on=>{active=on;last=performance.now();},suspend:(on,audio=true)=>{suspended=on;if(audio)sounds?.suspend(on);last=performance.now();},text:(value,duration=0)=>{
  textContent=document.createElement('div');textContent.className='brief-scroll-content';OpenBWOriginal.text(textContent,value,dialogue,layout.get(65526).width);textWindow.replaceChildren(textContent);textWindow.setAttribute('aria-label',textContent.getAttribute('aria-label'));
  scrollStart=elapsed;scrollDuration=duration;speechPosition=null;manualScroll=null;scrollOffset=0;textDrag=null;resumeStart=0;resumeOffset=0;
 },objectives:value=>OpenBWOriginal.text($('brief-goals'),value,small,layout.get(65525).width)};
};

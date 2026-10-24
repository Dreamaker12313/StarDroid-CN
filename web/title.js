(() => {
  const $=id=>document.getElementById(id),stage=$('title-stage'),music=OpenBWMusic(1),tween=OpenBWOriginal.tween();music.phase('title');
  let page='splash',loaded=false,drawText=null,clips={},layers=[],groups=[],animation=0,last=0,suspended=false,elapsed=0,transitioning=false,sounds=null,slideAmount=0,files={},fontBytes={},modal=null,available=new Set();
  let game=localStorage.getItem('openbw-campaign-game')||'starcraft';
  const palettes={},pages=['splash','main','registry','campaign','options-page','unavailable'];
  let profiles=[];try{profiles=JSON.parse(localStorage.getItem('openbw-profiles')||'[]').filter(n=>typeof n==='string'&&n.length&&n.length<=24).slice(0,32);}catch{}
  let selected=localStorage.getItem('openbw-profile')||profiles[0]||'';
  const persist=()=>{localStorage.setItem('openbw-profiles',JSON.stringify(profiles));localStorage.setItem('openbw-profile',selected);};
  const resize=()=>document.documentElement.style.setProperty('--title-scale',Math.min(innerWidth/640,innerHeight/480));resize();addEventListener('resize',resize);
  const select=next=>{page=next;for(const name of pages)$('title-'+name).hidden=next!==name;};
  const slide=amount=>{slideAmount=amount;for(const g of groups)if(g.page===page)OpenBWOriginal.slide(g.el,g.w,amount);};
  // The main screen's planets stay put when Single Player is selected. Only the
  // Registry/campaign glue panels use the in/out movement seen in the recording.
  async function depart(){if(page==='registry'||page==='campaign'){sounds?.play('swishout');await tween.run(320,p=>slide(OpenBWOriginal.slideProgress(p)));}}
  async function arrive(){
    $('title-'+page).style.opacity='1';slideAmount=0;
    if(page==='registry'||page==='campaign'){slide(1);sounds?.play('swishin');await tween.run(560,p=>slide(1-OpenBWOriginal.slideProgress(p)));sounds?.play('swishlock');}
  }
  async function show(next){
    if(!loaded||transitioning||next===page)return;closeModal();transitioning=true;stage.inert=true;music.unlock();
    await depart();select(next);await arrive();transitioning=false;stage.inert=false;
    if(next==='registry'&&!profiles.length)newID();
  }
  function animate(now){
    const dt=last?Math.max(0,Math.min(100,now-last)):0;last=now;
    if(!suspended&&!document.hidden){elapsed+=dt;tween.step(dt);
      if(loaded)for(const layer of layers){if(layer.page!==page)continue;const hot=layer.hot()&&!modal;if(hot&&!layer.wasHot)layer.time=0;if(hot)layer.time+=dt;layer.wasHot=hot;
        layer.canvas.hidden=!!(layer.flags&8)&&!hot;
        if(layer.flags&2)layer.canvas.style.filter=hot?'brightness(1)':'brightness(.25)';
        OpenBWOriginal.frame(layer.canvas,clips[layer.name],layer.flags&8?layer.time:elapsed,!!(layer.flags&4));}
    }
    animation=requestAnimationFrame(animate);
  }
  animation=requestAnimationFrame(animate);
  const native=async action=>{if(transitioning)return;
    if(action==='diagnostics'||(!loaded&&action==='data')){location.href='./native/'+action;return;}
    if(!loaded)return;transitioning=true;stage.inert=true;closeModal();await depart();location.href='./native/'+action;
  };
  function palette(name){if(palettes[name])return palettes[name];const prefix='glue/'+name+'/',fallback='glue/palnl/';
    const bg=OpenBWArt.pcx(files[prefix+'backgnd.pcx']||files[fallback+'backgnd.pcx'],false),tint=OpenBWArt.pcx(files[prefix+'tfont.pcx']||files[fallback+'tfont.pcx']);
    const fonts={};for(const n of ['8','10','16','16x'])fonts[n]=OpenBWArt.font(fontBytes[n],tint,bg.palette);
    const e=files[prefix+'teffect.pcx']||files[fallback+'teffect.pcx'];return palettes[name]={bg,fonts,glass:e?OpenBWArt.pcx(e).indices[1]:138,tiles:files[prefix+'tile.grp']||files[fallback+'tile.grp'],buttons:files[prefix+'dlg.grp']||files[fallback+'dlg.grp']};
  }
  const fontFor=(w,p)=>p.fonts[w.flags&0x4000?'16x':(w.flags&0x800)||w.type===14?'16':w.flags&0x400?'10':'8'];
  function panel(pageName,w,p){const b=files[OpenBWOriginal.normalize(w.text)];if(!b)return;const art=OpenBWArt.pcx(b,true,w.flags&0x40000?p.glass:-1),img=new Image();img.src=art.canvas.toDataURL();img.alt='';img.className='original-main-art';OpenBWOriginal.place(img,{...w,width:art.canvas.width,height:art.canvas.height});$('title-'+pageName).append(img);groups.push({el:img,w,page:pageName});}
  function glueButton(pageName,w,p,id,action,layout){
    const wrap=document.createElement('div');wrap.className='original-glue-widget';OpenBWOriginal.place(wrap,w);$('title-'+pageName).append(wrap);
    // The figures/disks stay fixed while the surrounding campaign panels move.
    const parentId=pageName==='campaign'?({5:1,11:1,10:3,9:3})[w.id]:pageName==='registry'?({4:3,5:2,6:1,7:1})[w.id]:null;
    if(pageName!=='campaign'||![6,7,8].includes(w.id))groups.push({el:wrap,w:parentId?layout.get(parentId):w,page:pageName});
    const hit=OpenBWOriginal.response(w),button=document.createElement('button');button.type='button';button.id=id;button.className='original-glue-button';OpenBWOriginal.place(button,{...hit,x:hit.x-w.x,y:hit.y-w.y});button.onclick=action;
    const label=document.createElement('span');label.className='original-main-label';const value=id==='title-options'?'App Options':w.text.slice(w.flags&0x200?1:0);button.setAttribute('aria-label',value.replace(/[\x00-\x1f]/g,' '));
    const hot=OpenBWOriginal.buttonText(button,label,value,fontFor(w,p));OpenBWOriginal.labelBox(label,w,{...w,x:0,y:0});
    // labelBox expects the parent origin; this label is relative to the full widget.
    label.style.left=w.tx+'px';label.style.top=w.ty+'px';
    for(const a of layout.animations(w).sort((a,b)=>(a.flags&8)-(b.flags&8))){if(!clips[a.name])continue;
      const canvas=document.createElement('canvas');canvas.className='original-main-motion';canvas.id=(pageName==='main'?'planet-':'race-')+a.name.split('/').pop().slice(0,-4);Object.assign(canvas.style,{left:a.x+'px',top:a.y+'px'});wrap.append(canvas);layers.push({canvas,hot,name:a.name,flags:a.flags,time:0,wasHot:false,page:pageName});}
    wrap.append(button,label);return button;
  }
  function setupPage(name,bin,pal,bindings){const p=palette(pal),layout=OpenBWOriginal.dialog(files['rez/'+bin+'.bin']),root=$('title-'+name);root.replaceChildren();
    const img=new Image();img.className='page-art';img.alt='';if(name!=='campaign'||files['glue/palcs/backgnd.pcx'])img.src=p.bg.canvas.toDataURL();else root.classList.add('missing-campaign-frame');root.append(img);
    for(const w of layout.widgets.filter(w=>w.type===5&&(w.flags&8)))panel(name,w,p);
    for(const [id,index,action] of bindings)glueButton(name,layout.get(index),p,id,action,layout);
    return{p,layout,root};
  }
  function registryList(){const list=$('registry-list');if(!list)return;list.replaceChildren();
    for(const name of profiles){const b=document.createElement('button');b.type='button';b.className='registry-id';b.setAttribute('role','option');b.setAttribute('aria-selected',name===selected);OpenBWOriginal.text(b,name,palette('palnl').fonts['16'],0,'left',name===selected?4:2);b.onclick=()=>{selected=name;persist();registryList();};b.ondblclick=()=>show('campaign');list.append(b);}
    $('registry-ok').disabled=!profiles.includes(selected);$('registry-delete').disabled=!profiles.includes(selected);
  }
  function closeModal(){modal=null;$('title-modal').hidden=true;$('title-modal-content').replaceChildren();for(const name of pages)$('title-'+name).inert=false;}
  function modalBox(width,height,name='palnl'){closeModal();modal={};for(const name of pages)$('title-'+name).inert=true;const box=$('title-modal-content'),p=palette(name);Object.assign(box.style,{width:width+'px',height:height+'px',left:Math.floor((640-width)/2)+'px',top:Math.floor((480-height)/2)+'px'});
    const art=OpenBWArt.dialogFrame(p.tiles,p.bg.palette,width,height);box.style.backgroundImage=art?'url('+art.toDataURL()+')':'';$('title-modal').hidden=false;return{box,p};
  }
  function modalLabel(box,p,text,x,y,w,font='16'){const el=document.createElement('div');OpenBWOriginal.place(el,{x,y,width:w,height:60});OpenBWOriginal.text(el,text,p.fonts[font],w);box.append(el);return el;}
  function modalButton(box,p,id,text,x,y,w,action){const b=document.createElement('button');b.id=id;b.type='button';b.className='original-modal-button';OpenBWOriginal.place(b,{x,y,width:w,height:29});b.onclick=action;
    // Original three-piece small dialog button, stretched only in its middle.
    for(const [state,start] of [['normal',103],['hot',106]]){const c=document.createElement('canvas');c.width=w;c.height=29;const ctx=c.getContext('2d'),parts=[0,1,2].map(i=>OpenBWArt.rawFrame(p.buttons,start+i,p.bg.palette));if(parts.every(Boolean)){for(let xx=8;xx<w-8;xx+=8)ctx.drawImage(parts[1],xx,0);ctx.drawImage(parts[0],0,0);ctx.drawImage(parts[2],w-8,0);b.style.setProperty('--'+state+'-button','url('+c.toDataURL()+')');}}
    const label=document.createElement('span');OpenBWOriginal.buttonText(b,label,text,p.fonts['16'],2,4);b.append(label);box.append(b);return b;
  }
  function message(text){const{box,p}=modalBox(360,200,page==='campaign'?'palcs':'palnl');modalLabel(box,p,text,16,22,328);modalButton(box,p,'title-message-ok','\x04O\x01k',103,159,158,closeModal);}
  function newID(){const{box,p}=modalBox(360,168),input=document.createElement('input');input.id='registry-name';input.type='text';input.maxLength=24;input.autocomplete='off';input.spellcheck=false;input.setAttribute('aria-label','Enter new character name');OpenBWOriginal.place(input,{x:24,y:63,width:312,height:26});
    modalLabel(box,p,'Enter new character name:',24,24,312);const visible=document.createElement('div');visible.id='registry-name-pixels';OpenBWOriginal.place(visible,{x:28,y:67,width:304,height:20});box.append(input,visible);
    const paint=()=>OpenBWOriginal.text(visible,input.value+(document.activeElement===input?'|':''),p.fonts['16']);for(const e of ['input','focus','blur'])input.addEventListener(e,paint);
    const save=()=>{const name=input.value.replace(/[\x00-\x1f]/g,'').trim();if(!name)return;const existing=profiles.find(s=>s.toLowerCase()===name.toLowerCase());if(!existing){if(profiles.length>=32)return;profiles.push(name);}selected=existing||name;persist();closeModal();registryList();};
    modalButton(box,p,'registry-create','\x04O\x01k',45,119,123,save);modalButton(box,p,'registry-create-cancel','\x04C\x01ancel',193,119,123,closeModal);input.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();save();}};input.focus();paint();
  }
  function deleteID(){const name=selected,{box,p}=modalBox(360,168);modalLabel(box,p,'Delete '+name+'?',24,24,312);modalButton(box,p,'registry-delete-yes','\x04O\x01k',45,119,123,()=>{profiles=profiles.filter(n=>n!==name);selected=profiles[0]||'';persist();closeModal();registryList();});modalButton(box,p,'registry-delete-no','\x04C\x01ancel',193,119,123,closeModal);}
  function setupCampaign(){
    groups=groups.filter(g=>g.page!=='campaign');layers=layers.filter(g=>g.page!=='campaign');
    setupPage('campaign',game==='broodwar'?'gluexpcmpgn':'glucmpgn','palcs',[
      ['campaign-terran',7,()=>missions(1)],['campaign-zerg',8,()=>missions(0)],['campaign-protoss',6,()=>missions(2)],
      ['campaign-load',5,()=>message('Saved games are not implemented yet.')],['campaign-replay',11,()=>message('Replay loading is not implemented yet.')],
      ['title-custom',10,()=>native('skirmish')],['campaign-cancel',9,()=>show('registry')]]);
  }
  function chooseGame(){
    const {box,p}=modalBox(360,196,'palmm'),layout=OpenBWOriginal.dialog(files['rez/glugamemode.bin']);
    if(files['glue/palmm/retail_ex.pcx'])box.style.backgroundImage='url('+OpenBWArt.pcx(files['glue/palmm/retail_ex.pcx'],false).canvas.toDataURL()+')';
    for(const [index,value,label] of [[6,'starcraft','StarCraft (Original)'],[7,'broodwar','Brood War (Expansion)']]){
      const w=layout.get(index),b=document.createElement('button');b.type='button';b.id='game-'+value;b.className='game-choice';b.setAttribute('aria-label',label);OpenBWOriginal.place(b,w);
      const caption=document.createElement('span');OpenBWOriginal.buttonText(b,caption,w.text.slice(1),p.fonts['16'],3,4);OpenBWOriginal.labelBox(caption,w);b.append(caption);
      b.onclick=()=>{game=value;localStorage.setItem('openbw-campaign-game',game);setupCampaign();closeModal();show('registry');};box.append(b);
    }
    const cancel=layout.get(3);modalButton(box,p,'game-cancel','Cancel',cancel.x,cancel.y,cancel.width,closeModal);
  }
  function missions(race=1){const{box,p}=modalBox(380,251,'palcs');box.style.backgroundImage='url('+OpenBWArt.pcx(files['glue/campaign/phist.pcx'],true,p.glass).canvas.toDataURL()+')';const layout=OpenBWOriginal.dialog(files['rez/gluhist.bin']);const entries=OpenBWMissions.filter(m=>m.game===game&&(m.campaignRace??m.race)===race&&!m.hidden);let chosen=entries.find(m=>available.has(m.code))?.code||0;
    const heading=layout.get(65535);modalLabel(box,p,heading.text,heading.x,heading.y,heading.width,'10');const list=document.createElement('div');list.id='mission-list';list.setAttribute('role','listbox');OpenBWOriginal.place(list,layout.get(6));box.append(list);
    const render=()=>{for(const b of list.children){b.setAttribute('aria-selected',+b.dataset.mission===chosen);OpenBWOriginal.text(b,b.dataset.title,p.fonts['16'],0,'left',b.disabled?5:+b.dataset.mission===chosen?4:2);}$('title-mission-go').disabled=!chosen;};
    entries.forEach(({title:name,code,number},i)=>{const b=document.createElement('button');b.id='title-mission'+code;b.className='registry-id';b.dataset.mission=code;b.dataset.title=(number===0?'':number+'. ')+name;b.setAttribute('role','option');b.disabled=!available.has(code);b.onclick=()=>{chosen=code;render();};list.append(b);});
    const ok=layout.get(1),cancel=layout.get(3);modalButton(box,p,'title-mission-go',ok.text.slice(1),ok.x,ok.y,ok.width,()=>chosen&&native('mission/'+chosen));modalButton(box,p,'title-mission-cancel',cancel.text.slice(1),cancel.x,cancel.y,cancel.width,closeModal);render();
    if(!entries.some(m=>available.has(m.code)))modalLabel(box,p,'Import '+(game==='broodwar'?'BroodWar.mpq':'StarCraft.mpq')+' in App Options.',18,172,344,'10');
  }
  $('title-enter').disabled=true;$('title-enter').onclick=()=>show('main');
  $('title-game-files').onclick=()=>native('data');$('title-diagnostics').onclick=()=>native('diagnostics');
  document.querySelectorAll('.title-back').forEach(b=>b.onclick=()=>show('main'));
  window.openbwBack=()=>{if(modal){closeModal();return true;}if(!loaded){select('options-page');stage.inert=false;}else if(page==='main')native('data');else show(page==='campaign'?'registry':'main');return true;};
  addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();window.openbwBack();}else if(!modal&&!transitioning){if(page==='splash'&&(e.key==='Enter'||e.key===' ')){e.preventDefault();show('main');}else if(page==='registry'&&e.key==='Enter'&&profiles.includes(selected))show('campaign');}});
  window.openbwAndroidSuspend=()=>{suspended=true;music.state(true,false,false);sounds?.suspend(true);};window.openbwAndroidResume=()=>{suspended=false;last=0;music.state(false,false,false);sounds?.suspend(false);music.wake();};
  document.addEventListener('visibilitychange',()=>document.hidden?window.openbwAndroidSuspend():window.openbwAndroidResume());
  const worker=new Worker('./title-worker.js');worker.onerror=e=>{e.preventDefault();$('title-status').textContent='Interface artwork unavailable. Use Android Back → Game Files.';worker.terminate();};
  worker.onmessage=async({data})=>{worker.terminate();if(data.error){$('title-status').textContent=data.error;return;}
    try{files=data.files;fontBytes=data.fonts;clips=data.clips||{};$('title-art').src=OpenBWArt.pcx(files['glue/title/title.pcx'],false).canvas.toDataURL();drawText=palette('palmm').fonts['16x'];
      setupPage('main','glumain','palmm',[
        ['title-single',3,chooseGame],['title-files',4,()=>message('Multiplayer is not implemented in this Android port.')],['title-options',5,()=>native('data')],['title-exit',2,()=>native('exit')],['title-intro',8,()=>native('cinematic/intro')],['title-credits',9,()=>native('diagnostics')]]);
      const registry=setupPage('registry','glulogin','palnl',[
        ['registry-ok',4,()=>profiles.includes(selected)&&show('campaign')],['registry-cancel',5,()=>show('main')],['registry-new',6,newID],['registry-delete',7,deleteID]]);
      const heading=document.createElement('div'),w=registry.layout.get(9);OpenBWOriginal.place(heading,w);OpenBWOriginal.text(heading,w.text,fontFor(w,registry.p));registry.root.append(heading);groups.push({el:heading,w:registry.layout.get(1),page:'registry'});
      const list=document.createElement('div');list.id='registry-list';list.setAttribute('role','listbox');list.setAttribute('aria-label','Player names');OpenBWOriginal.place(list,registry.layout.get(8));registry.root.append(list);groups.push({el:list,w:registry.layout.get(1),page:'registry'});registryList();
      setupCampaign();
      document.querySelectorAll('.sc-button').forEach(b=>OpenBWArt.label(b,palette('palmm').fonts['16']));
      sounds=OpenBWOriginal.sounds(data.sounds||{});OpenBWOriginal.buttonSounds(stage,sounds);loaded=true;$('title-enter').disabled=false;
      $('title-status').textContent=drawText&&files['glue/palcs/backgnd.pcx']?'':'Original interface: App Options → Import game files → StarCraft.mpq';
      if(page==='main'){await arrive();stage.inert=false;}
    }catch(e){$('title-status').textContent='Interface: '+e.message;console.error(e);}
  };
  worker.postMessage({});fetch('./availability.json').then(r=>r.json()).then(data=>{available=new Set(data.missions||[]);}).catch(()=>{});
  window.openbwTitleStats=()=>({page,game,loaded,animations:Object.keys(clips),originalFont:!!drawText,campaignPalette:!!files['glue/palcs/backgnd.pcx'],suspended,lastFrameTime:last,transitioning,slideAmount,profiles:profiles.length,modal:!!modal,sounds:sounds?.stats()});
  addEventListener('pagehide',()=>{worker.terminate();cancelAnimationFrame(animation);music.close();},{once:true});
  if(new URLSearchParams(location.search).has('menu')){select('main');stage.inert=true;}
})();

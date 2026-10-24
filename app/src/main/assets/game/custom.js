/* Original Play Custom geometry and artwork; file selection stays on-device. */
window.OpenBWCustom = async function(api) {
  const $=id=>document.getElementById(id),root=document.createElement('section');root.id='custom-game';root.setAttribute('aria-label','Create custom game');$('overlay').append(root);
  document.body.classList.add('custom-setup');
  const decoder=await MPQDecoder.create(),archives=[];
  for(const name of ['STARDAT.MPQ','BROODAT.MPQ','patch_rt.mpq']){const r=await fetch('./data/'+name);if(!r.ok)throw Error('Import '+name+' in Game Files first.');archives.push(new Uint8Array(await r.arrayBuffer()));}
  window.openbwSetupAssets=archives;
  let imported=null;try{imported=await OpenBWCampaign.load('./interface/','interface');}catch{}
  const read=n=>{for(const source of [archives[2],archives[1],archives[0],imported].filter(Boolean)){const b=decoder.read(source,n);if(b)return b;}return null;},pcx=OpenBWArt.pcx,place=OpenBWOriginal.place;
  const bg=pcx(read('glue/palnl/backgnd.pcx'),false),tint=pcx(read('glue/palnl/tfont.pcx')),glass=pcx(read('glue/palnl/teffect.pcx')).indices[1],bytes=await OpenBWOriginal.fonts([archives[2],archives[1],archives[0]]);
  const fonts={};for(const n of ['8','10','16','16x'])fonts[n]=OpenBWArt.font(bytes[n],tint,bg.palette);
  const layout=OpenBWOriginal.dialog(read('rez/glucustm.bin')),panels=[];
  const controls=read('glue/palnl/dlg.grp'),selectArt=new Map();
  function selectFrame(width,height,hot=false){const key=width+':'+height+':'+hot;if(selectArt.has(key))return selectArt.get(key);
    const c=document.createElement('canvas');c.width=width;c.height=height;const ctx=c.getContext('2d'),start=hot?56:53,parts=[0,1,2].map(i=>OpenBWArt.rawFrame(controls,start+i,bg.palette)),y=Math.floor((height-16)/2);
    for(let x=16;x<width-16;x+=16)ctx.drawImage(parts[1],x,y);ctx.drawImage(parts[0],0,y);ctx.drawImage(parts[2],width-16,y);
    ctx.drawImage(OpenBWArt.rawFrame(controls,hot?51:50,bg.palette),width-16,Math.floor((height-7)/2));const url='url('+c.toDataURL()+')';selectArt.set(key,url);return url;
  }
  root.style.backgroundImage='url('+bg.canvas.toDataURL()+')';
  let missingArt=false;
  for(const w of layout.widgets.filter(w=>w.type===5&&(w.flags&8))){const bytes=read(OpenBWOriginal.normalize(w.text));
    const canvas=bytes?pcx(bytes,true,glass).canvas:OpenBWArt.dialogFrame(read('glue/palnl/tile.grp'),bg.palette,w.width,w.height);if(!bytes)missingArt=true;
    const img=new Image();img.src=canvas.toDataURL();place(img,{...w,width:canvas.width,height:canvas.height});root.append(img);panels.push({el:img,w});}
  const sounds=OpenBWOriginal.sounds(OpenBWOriginal.soundFiles(read)),music=OpenBWMusic(1);music.phase('title');OpenBWOriginal.buttonSounds(root,sounds);
  let dropdown=null,closed=false,selected=api.current(),ready=false,importSerial=0;
  function label(id,text,w,font='10',color=2,align='left') {const el=document.createElement('div');el.id=id;place(el,w);OpenBWOriginal.text(el,text,fonts[font],w.width,align,color);root.append(el);return el;}
  function button(id,text,w,fn,font='16x'){const b=document.createElement('button');b.id=id;b.type='button';b.className='custom-button';place(b,w);const t=document.createElement('span');OpenBWOriginal.buttonText(b,t,text,fonts[font]);b.append(t);b.onclick=fn;root.append(b);return b;}
  const dynamic=document.createElement('div');root.append(dynamic);
  label('custom-heading','Create',layout.get(65535),'16x');label('custom-directory','Maps',layout.get(6),'16');
  label('custom-type-label','Game Type',layout.get(38));
  const list=document.createElement('div');list.id='custom-map-list';list.setAttribute('role','listbox');place(list,layout.get(5));root.append(list);
  const info={title:label('custom-map-title','',layout.get(7),'16',2,'center'),desc:label('custom-map-description','',layout.get(8)),size:label('custom-map-size','',layout.get(10),'8'),terrain:label('custom-map-terrain','',layout.get(11),'8')};
  const ok=button('custom-ok',layout.get(12).text.slice(1),layout.get(12),()=>{if(!ready)return;close();api.start();});
  button('custom-cancel',layout.get(13).text.slice(1),layout.get(13),()=>location.replace('./title.html?menu'));
  const status=label('custom-status','', {x:382,y:340,width:234,height:35},'8');
  const nativeFile=$('map-file');nativeFile.setAttribute('accept','.scm,.scx');
  function dismiss(){dropdown?.remove();dropdown=null;}
  function choose(b,choices,value,onchange,w){
    dismiss();const pop=document.createElement('div');pop.className='custom-choices';pop.setAttribute('role','listbox');
    const h=choices.length*21;place(pop,{x:w.x,y:Math.min(w.y+w.height,478-h),width:w.width,height:h});
    for(const [v,name,disabled] of choices){const option=document.createElement('button');option.type='button';option.disabled=!!disabled;option.setAttribute('role','option');option.setAttribute('aria-selected',String(v===value));OpenBWOriginal.text(option,name,fonts['10'],w.width-14,'left',disabled?5:v===value?4:2);option.onclick=()=>{dismiss();onchange(v);};pop.append(option);}
    root.append(pop);dropdown=pop;
  }
  function select(id,value,choices,w,onchange){const b=button(id,choices.find(c=>c[0]===value)?.[1]||'',w,()=>choose(b,choices,value,onchange,w),'10');b.classList.add('custom-select');b.style.setProperty('--select-normal',selectFrame(w.width,w.height));b.style.setProperty('--select-hot',selectFrame(w.width,w.height,true));b.setAttribute('aria-haspopup','listbox');dynamic.append(b);return b;}
  function slots(){dynamic.replaceChildren();dismiss();select('custom-type','melee',[['melee','Melee']],layout.get(17),()=>{});
    const ownerName=localStorage.getItem('openbw-profile')||'Player';
    for(let i=0;i<Math.min(8,selected.starts);i++){
      const a=layout.get(20+i),b=layout.get(28+i),you=i===0,source=you?api.slots._you:api.slots._opps[i-1];
      select('custom-player-'+i,you?'player':source.value,[...(you?[['player',ownerName]]:[['none','Closed'],['zzzk','Computer']])],a,value=>{source.value=value;source.onchange?.();slots();});
      const enabled=you||source.value!=='none';
      const race=select('custom-race-'+i,you?+source.value:0,you?[[1,'Terran'],[0,'Zerg'],[2,'Protoss'],[-1,'Random']]:[[0,'Zerg']],b,value=>{source.value=String(value);slots();});race.disabled=!enabled;
    }
  }
  function paint(){
    list.replaceChildren();
    for(const m of api.maps()){
      const b=document.createElement('button');b.type='button';b.className='custom-map';b.setAttribute('role','option');b.setAttribute('aria-selected',String(m.file===selected.file));
      OpenBWOriginal.text(b,m.displayName||m.name,fonts['10'],264,'left',m.file===selected.file?4:2);b.onclick=()=>{selected=m;api.select(m.file);paint();};list.append(b);
    }
    const browse=document.createElement('button');browse.id='custom-browse';browse.type='button';browse.className='custom-map';OpenBWOriginal.text(browse,'Browse…',fonts['10']);browse.onclick=()=>nativeFile.click();list.append(browse);
    OpenBWOriginal.text(info.title,selected.name,fonts['16'],190,'center');
    OpenBWOriginal.text(info.desc,selected.description||'',fonts['10'],190);
    OpenBWOriginal.text(info.size,'Size: '+selected.w+' × '+selected.h,fonts['8']);
    OpenBWOriginal.text(info.terrain,'Tileset: '+selected.tileset,fonts['8']);slots();ready=true;ok.disabled=false;
    OpenBWOriginal.text(status,missingArt?'Re-import Original Interface in Game Files for the custom-menu artwork.':'',fonts['8'],234);
  }
  async function importMap(file){
    const serial=++importSerial;ready=false;ok.disabled=true;OpenBWOriginal.text(status,'Reading map…',fonts['8'],234);
    try{
      if(file.size>64*1024*1024)throw Error('Map is too large.');
      const data=new Uint8Array(await file.arrayBuffer()),mapDecoder=await MPQDecoder.create();
      const chk=mapDecoder.read(data,'staredit/scenario.chk');if(!chk)throw Error('No scenario in this map.');
      const v=new DataView(chk.buffer,chk.byteOffset,chk.byteLength),chunks={};
      for(let p=0;p+8<=chk.length;){const size=v.getUint32(p+4,true);if(p+8+size>chk.length)throw Error('Truncated map.');chunks[String.fromCharCode(...chk.subarray(p,p+4))]=chk.slice(p+8,p+8+size);p+=8+size;}
      const dim=chunks['DIM '];if(!dim||dim.length!==4)throw Error('Missing map dimensions.');const d=new DataView(dim.buffer),w=d.getUint16(0,true),h=d.getUint16(2,true);if(!w||!h||w>256||h>256)throw Error('Unsupported map size.');
      const units=chunks.UNIT;let starts=0;if(units){const u=new DataView(units.buffer);for(let p=0;p+36<=units.length;p+=36)if(u.getUint16(p+8,true)===214)starts++;}
      if(starts<1||starts>8)throw Error('This map needs 1–8 start locations for Melee.');
      const info=OpenBWCampaign.parseChk(chk),prop=chunks.SPRP,p=prop?new DataView(prop.buffer):null;
      const clean=t=>(t||'').replace(/[\x00-\x1f]/g,' ').trim();
      const m={file:'custom:'+file.name,name:clean(p?info.strings[p.getUint16(0,true)]:null)||file.name,displayName:file.name,description:clean(p?info.strings[p.getUint16(2,true)]:null),w,h,starts,tileset:['Badlands','Space Platform','Installation','Ashworld','Jungle','Desert','Ice','Twilight'][(chunks['ERA ']?.[0]||0)&7]};
      if(closed||serial!==importSerial)return;api.addMap(m,data);selected=m;paint();
    }catch(e){if(serial!==importSerial)return;OpenBWOriginal.text(status,e.message,fonts['8'],234);ready=true;ok.disabled=false;}
    nativeFile.value='';
  }
  function close(){if(closed)return;closed=true;dismiss();music.close();sounds.close();root.hidden=true;document.body.classList.remove('custom-setup');}
  nativeFile.onchange=e=>{const f=e.target.files?.[0];if(f)importMap(f);};
  window.openbwBack=()=>{if(dropdown){dismiss();return true;}location.replace('./title.html?menu');return true;};
  window.openbwAndroidSuspend=()=>{music.state(true,false,false);sounds.suspend(true);};
  window.openbwAndroidResume=()=>{music.state(false,false,false);music.wake();sounds.suspend(false);};
  document.addEventListener('visibilitychange',()=>{if(!closed)(document.hidden?openbwAndroidSuspend:openbwAndroidResume)();});
  addEventListener('keydown',e=>{if(closed)return;if(e.key==='Escape'){e.preventDefault();openbwBack();}if(e.key==='Enter'&&!dropdown&&ready)ok.click();});
  addEventListener('pagehide',close,{once:true});
  window.openbwCustomStats=()=>({ready,closed,selected,layout:'rez/glucustm.bin',maps:api.maps().map(m=>m.name)});
  paint();sounds.play('swishin');
  // Labels, hit targets and artwork travel together in the entry animation.
  for(const el of [...root.children,...dynamic.children]){
    if(el===dynamic)continue;const left=parseFloat(el.style.left)||0,off=left<380?-640:640;
    el.animate([{transform:'translateX('+off+'px)'},{transform:'translateX(0)'}],{duration:500,easing:'ease-out'});
  }
  setTimeout(()=>{if(!closed)sounds.play('swishlock');},500);
  return{close,importMap};
};

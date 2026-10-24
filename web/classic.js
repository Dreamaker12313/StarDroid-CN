window.OpenBWClassic = async function(x, memory, assets, race, canvas, viewScale) {
  const $=id=>document.getElementById(id), esc=s=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const decoder=await MPQDecoder.create();
  const read=name=>{for(const i of [2,1,0]){const data=decoder.read(assets[i],name);if(data)return data;}return null;};
  const pcx=OpenBWArt.pcx,fonts=await OpenBWOriginal.fonts([assets[2],assets[1],assets[0]]);
  const portraits=OpenBWPortraits(x,read);
  const raceLetter=['z','t','p'][race]||'t';
  document.body.dataset.race=raceLetter;
  const soundDecoder=await MPQDecoder.create();
  const sounds=OpenBWOriginal.sounds(OpenBWOriginal.soundFiles(name=>{for(const i of [2,1,0]){const b=soundDecoder.read(assets[i],name);if(b)return b;}return null;}));
  window.openbwBuildClick=()=>sounds.play('button');
  OpenBWOriginal.buttonSounds($('card'),sounds,true);
  OpenBWOriginal.buttonSounds($('minimap-terrain'),sounds,true);
  let art={layouts:{},sounds,fontBytes:fonts};
  for(const [key,name] of Object.entries({main:'gamemenu',options:'options',end:'abrtmenu'}))art.layouts[key]=OpenBWOriginal.dialog(read('rez/'+name+'.bin'));
  try {
    const gamePalette=pcx(read('game/'+raceLetter+'console.pcx')).palette,tint=pcx(read('game/tfontgam.pcx'));
    // In-game art uses the map palette. PCX palettes contain reserved debug colors.
    let era=0;
    try{const n=x.openbw_campaign_chk_len?.()||0,chk=n?new Uint8Array(memory.buffer,x.openbw_campaign_chk(),n):decoder.read(assets[3],'staredit/scenario.chk');
      if(chk){const v=new DataView(chk.buffer,chk.byteOffset,chk.byteLength);for(let p=0;p+8<=chk.length;){const size=v.getUint32(p+4,true);if(p+8+size>chk.length)break;if(String.fromCharCode(...chk.subarray(p,p+4))==='ERA '&&size>=2){era=v.getUint16(p+8,true)&7;break;}p+=8+size;}}
    }catch(e){console.warn('Map palette:',e.message);}
    const wpe=read('tileset/'+['badlands','platform','install','ashworld','jungle','desert','ice','twilight'][era]+'.wpe');
    if(wpe?.length>=1024)for(let i=0;i<256;i++)gamePalette.set(wpe.subarray(i*4,i*4+3),i*3);
    art.palette=gamePalette;
    art.font=OpenBWArt.font(fonts['16'],tint,gamePalette);art.small=OpenBWArt.font(fonts['10'],tint,gamePalette);art.unitName=OpenBWArt.font(fonts['10'],tint,gamePalette,{spacing:0});art.health=OpenBWArt.font(fonts['8'],tint,gamePalette,{spacing:0});
    window.openbwTouchLabel=(el,value)=>{if(el.dataset.drawn===value)return;OpenBWOriginal.buttonText(el,el,value,art.font,3,4);el.dataset.drawn=value;};
    art.speech=OpenBWArt.font(fonts['10'],tint,gamePalette,{spacing:1,lineHeight:16});
    // Original 14px HUD glyphs, not carried-resource or supply-building sprites.
    const resources=read('game/icons.grp');art.resourceFrames=[0,1+race,4+race];
    art.resourceIcons=art.resourceFrames.map(id=>OpenBWArt.rawFrame(resources,id,gamePalette)?.toDataURL()||'');
    art.dialogFrame=(w,h)=>OpenBWArt.dialogFrame(read('dlgs/tile.grp'),gamePalette,w,h)?.toDataURL();
    const frame=OpenBWArt.dialogFrame(read('dlgs/tile.grp'),gamePalette,264,288);if(frame)document.documentElement.style.setProperty('--original-dialog-art','url('+frame.toDataURL()+')');
    const pal=gamePalette,grp=read('dlgs/'+({t:'terran',p:'protoss',z:'zerg'}[raceLetter])+'.grp');
    const commandFrames=read('unit/cmdbtns/'+raceLetter+'cmdbtns.grp');
    art.productionLayout=OpenBWOriginal.dialog(read('rez/statdata.bin'));
    art.commandFrames=Object.fromEntries([2,4,6,7,8,9,10,11,13,19,25,31].map(id=>[id,OpenBWArt.grpFrame(commandFrames,id,pal)]));
    art.groupFrames=Object.fromEntries([13,19,25,31].map(id=>[id,art.commandFrames[id].toDataURL()]));
    art.statFrame=OpenBWArt.grpFrame(commandFrames,12,pal);
    for(const [key,id] of [['--command-normal-art',0],['--command-pressed-art',1]]){const f=OpenBWArt.grpFrame(commandFrames,id,pal);if(f)document.documentElement.style.setProperty(key,'url('+f.toDataURL()+')');}
    for(const [key,id] of [['--menu-button-art',0],['--menu-hover-art',1],['--menu-pressed-art',2],['--terrain-off-art',3],['--terrain-on-art',4],['--terrain-pressed-art',5],['--unit-selection-art',12]]){
      const frame=OpenBWArt.rawFrame(grp,id,pal);if(frame)document.documentElement.style.setProperty(key,'url('+frame.toDataURL()+')');
    }
    OpenBWOriginal.buttonText($('settingsbtn'),$('settingsbtn'),'MENU',art.small,3,4);
    for(const [key,start] of [['--dialog-disabled-art',112],['--dialog-button-art',115],['--dialog-hover-art',118]]) {
      const c=document.createElement('canvas');c.width=224;c.height=28;const ctx=c.getContext('2d'),f=[0,1,2].map(i=>OpenBWArt.rawFrame(grp,start+i,pal));
      if(f.every(Boolean)){for(let x=8;x<216;x+=8)ctx.drawImage(f[1],x,0);ctx.drawImage(f[0],0,0);ctx.drawImage(f[2],216,0);document.documentElement.style.setProperty(key,'url('+c.toDataURL()+')');}
    }
  } catch(e){console.warn('Menu art fallback:',e.message);}
  const consoleImage=pcx(read('game/'+raceLetter+'console.pcx'));
  // The portrait opening is PCX index 138 (opaque black), not transparent index 0.
  // Cut only that opening; retain every original rim pixel in front of the movie.
  const cc=consoleImage.canvas.getContext('2d'),cut=cc.getImageData(413,410,60,56);
  for(let y=0;y<56;y++)for(let x=0;x<60;x++)if(consoleImage.indices[(410+y)*consoleImage.stride+413+x]===138)cut.data[(y*60+x)*4+3]=0;
  cc.putImageData(cut,413,410);
  for(const [id,left,width] of [['console-left',0,160],['console-center',160,247],['console-right',407,233]]){
    const c=document.createElement('canvas');c.width=width;c.height=180;c.getContext('2d').drawImage(consoleImage.canvas,left,300,width,180,0,0,width,180);$(id).src=c.toDataURL();
  }
  // Extend a quiet part of the original console between the minimap and status
  // panel. Mirrored pairs join on identical pixels; portrait and buttons stay
  // unscaled at the right edge. Rebuild only when the logical width changes.
  const wideImage=new Image();wideImage.id='console-wide';wideImage.alt='';$('classic-console').append(wideImage);
  const wideConsole=()=>{
    const width=OpenBWDisplay.width(),extra=width-640;if(!extra)return;
    const c=document.createElement('canvas');c.width=width;c.height=180;const ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;
    ctx.drawImage(consoleImage.canvas,0,300,216,180,0,0,216,180);
    for(let offset=0;offset<extra;){
      const pair=Math.min(128,extra-offset),half=pair/2;
      ctx.drawImage(consoleImage.canvas,216,300,64,180,216+offset,0,half,180);
      ctx.save();ctx.translate(216+offset+pair,0);ctx.scale(-1,1);ctx.drawImage(consoleImage.canvas,216,300,64,180,0,0,half,180);ctx.restore();
      offset+=pair;
    }
    ctx.drawImage(consoleImage.canvas,216,300,424,180,216+extra,0,424,180);
    wideImage.src=c.toDataURL();
  };
  addEventListener('openbwdisplaychange',wideConsole);wideConsole();
  const tbl=read('rez/stat_txt.tbl'),tv=new DataView(tbl.buffer,tbl.byteOffset,tbl.byteLength),strings=[];
  for(let id=0;id<tv.getUint16(0,true);id++){const start=tv.getUint16(2+id*2,true);let end=start;while(end<tbl.length&&tbl[end])end++;strings[id]=new TextDecoder('windows-1252').decode(tbl.subarray(start,end));}
  const unitNames=strings.slice(0,228);
  const grp=read('unit/cmdbtns/cmdicons.grp'), tint=pcx(read('unit/cmdbtns/ticon.pcx')), palette=tint.palette.slice(), icons=new Map();
  // ticon contains six 16-color ramps: command normal/disabled/active are 0/1/2.
  // Stat icons deliberately use the separate original gray ramp (5).
  // They are reserved magenta/debug colors in the unmodified game palette.
  for(let i=0;i<16;i++)palette.set(tint.palette.subarray(tint.indices[i]*3,tint.indices[i]*3+3),i*3);
  function icon(id,ramp=0,stat=false) {
    const key=id+':'+ramp+':'+stat;if(icons.has(key))return icons.get(key);
    const colors=palette.slice();for(let i=0;i<16;i++)colors.set(tint.palette.subarray(tint.indices[ramp*16+i]*3,tint.indices[ramp*16+i]*3+3),i*3);
    if(!grp || id<0)return '';
    const v=new DataView(grp.buffer);if(id>=v.getUint16(0,true))return '';
    const at=6+id*8,ox=grp[at],oy=grp[at+1],w=grp[at+2],h=grp[at+3],base=v.getUint32(at+4,true),cw=v.getUint16(2,true),ch=v.getUint16(4,true);
    if(cw>128||ch>128||ox+w>cw||oy+h>ch)return '';
    const c=document.createElement('canvas');c.width=cw;c.height=ch;const ctx=c.getContext('2d'),im=ctx.createImageData(cw,ch);
    for(let y=0;y<h;y++){let p=base+v.getUint16(base+y*2,true),a=0;
      while(a<w){if(p>=grp.length)throw Error('Truncated command icon');const b=grp[p++],n=b&128?b&127:b&64?b&63:b;
        if(!n||a+n>w)throw Error('Invalid command icon');
        if(b&128){a+=n;continue;}const repeat=b&64?grp[p++]:-1;
        for(let i=0;i<n;i++,a++){const color=repeat<0?grp[p++]:repeat,at=((Math.floor((ch-h)/2)+y)*cw+Math.floor((cw-w)/2)+a)*4;im.data.set(colors.subarray(color*3,color*3+3),at);im.data[at+3]=255;}
      }
    }
    ctx.putImageData(im,0,0);
    if(stat){
      const glyph=document.createElement('canvas');glyph.width=cw;glyph.height=ch;glyph.getContext('2d').drawImage(c,0,0);
      c.height=36;ctx.drawImage(glyph,0,1);if(art.statFrame)ctx.drawImage(art.statFrame,0,0);
    }
    const url=c.toDataURL();icons.set(key,url);return url;
  }
  const production=OpenBWProduction({x,memory,art,icon,strings});
  const orderIcons={Move:228,Stop:229,Attack:230,Gather:231,Repair:232,'Return Cargo':233,Build:[257,234,272][race],Advanced:[258,235,273][race],Cancel:236,Back:236,'Halt Construction':236,Patrol:254,Hold:255,'Hold Position':255,'Set Rally Point':286,'Lift Off':282,Land:283,Burrow:259,Unburrow:260,'Stim Pack':237,'Siege Mode':245,'Tank Mode':246};
  const resize=()=>{const s=1,root=document.documentElement.style;
    root.setProperty('--console-scale',s);root.setProperty('--console-height',180*s+'px');root.setProperty('--console-left',160*s+'px');root.setProperty('--console-right',233*s+'px');root.setProperty('--console-middle',(247*s)+'px');
  };resize();addEventListener('resize',resize);$('classic-console').hidden=false;
  const minimap=$('classic-minimap'),mctx=minimap.getContext('2d');mctx.imageSmoothingEnabled=false;
  const terrain=$('minimap-terrain');
  terrain.onclick=()=>{x.openbw_set_minimap_terrain(!x.openbw_minimap_terrain());draw();};
  const miniRect=()=>{const s=viewScale(),w=Math.round(x.openbw_map_w()/s),h=Math.round(x.openbw_map_h()/s);return{x:4,y:canvas.height-4-h,w,h};};
  let touch=null;
  function point(e){const r=minimap.getBoundingClientRect(),a=miniRect();return[Math.max(a.x,Math.min(a.x+a.w-1,a.x+(e.clientX-r.left)/r.width*a.w))|0,Math.max(a.y,Math.min(a.y+a.h-1,a.y+(e.clientY-r.top)/r.height*a.h))|0];}
  const move=(e,right=false)=>{const [a,b]=point(e);x.openbw_mouse_move(a,b);x.openbw_mouse_button(1,right?3:1,a,b,1);x.openbw_mouse_button(0,right?3:1,a,b,1);x.openbw_mouse_move(-100,-100);};
  minimap.onpointerdown=e=>{e.preventDefault();minimap.setPointerCapture(e.pointerId);touch={x:e.clientX,y:e.clientY,time:performance.now(),drag:false};};
  minimap.onpointermove=e=>{if(!touch)return;if(Math.hypot(e.clientX-touch.x,e.clientY-touch.y)>5){touch.drag=true;move(e);}};
  minimap.onpointerup=e=>{if(!touch)return;move(e,!touch.drag&&performance.now()-touch.time>380);touch=null;};
  minimap.onpointercancel=()=>{touch=null;};minimap.oncontextmenu=e=>e.preventDefault();
  let signature='',preview=-2,page=0,lastCommands='';
  $('card').addEventListener('click',e=>{if(e.target.closest('[data-page]')){e.stopImmediatePropagation();page++;signature='';}},true);
  const hint=$('command-hint');let hintTimer;
  $('card').addEventListener('pointerdown',e=>{const c=e.target.closest('.cmd');if(c){OpenBWOriginal.text(hint,c.dataset.hint,art.small,180);hint.hidden=false;clearTimeout(hintTimer);hintTimer=setTimeout(()=>hint.hidden=true,2400);}});
  const cstr=p=>{if(!p)return '';const a=new Uint8Array(memory.buffer);let e=p;while(e<a.length&&a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};
  let detailsKey='',detailRows=[],healthColor=7;
  const details=()=>{
    const raw=cstr(x.openbw_unit_details?.()),busy=!!cstr(x.openbw_status());
    const [header,...rows]=raw.split('\n'),[kills,shields,maxShields,energy,maxEnergy,building,detector,supplied,used,total,supplyRace,cargo]=header.split('\t').map(Number);
    const key=raw+'|'+busy;
    const extra=[];if(shields>=0){const hp=$('unit-life').getAttribute('aria-label')?.trim()||'';OpenBWOriginal.text($('unit-life'),'\x02'+shields+'/'+maxShields+' '+String.fromCharCode(healthColor)+hp,art.health,0,'center');}if(energy>=0)extra.push('\x10'+energy+'/'+maxEnergy);
    if(raw)OpenBWOriginal.text($('unit-extra'),extra.join('\n'),art.health,80,'center');
    if(key===detailsKey)return;detailsKey=key;detailRows=[];
    const box=$('unit-details');box.replaceChildren();$('unit-kills').replaceChildren();
    $('unit-detector').replaceChildren();$('unit-supply').replaceChildren();
    const supplyPanel=!!raw&&!busy&&supplied>0&&!cargo;
    $('unit-info').classList.toggle('supply-panel',supplyPanel);
    if(detector)OpenBWOriginal.text($('unit-detector'),strings[830]||'\x03Detector',art.unitName,144,'center');
    if(supplyPanel){
      for(const [label,value] of [[820+supplyRace,used],[814+supplyRace,supplied],[817+supplyRace,total],[823+supplyRace,200]]){
        const line=document.createElement('div');OpenBWOriginal.text(line,strings[label]+' '+value,art.health,111,'center');$('unit-supply').append(line);
      }
    }
    if(!raw||busy||building&&!rows.some(row=>row.startsWith('weapon\t')))return;
    if(!building&&!supplyPanel&&rows.some(row=>/^(weapon|ammo)\t/.test(row)))OpenBWOriginal.text($('unit-kills'),'Kills: '+kills,art.unitName,152,'center');
    const order={armor:0,shield:1,weapon:2,ammo:3};
    const ordered=rows.filter(row=>!building||!row.startsWith('armor\t')).sort((a,b)=>order[a.split('\t')[0]]-order[b.split('\t')[0]]);
    for(const row of ordered.slice(0,4)){
      const [kind,idx,level,base,bonus,hits,label]=row.split('\t'),name=kind==='ammo'?(+idx===85?'Scarabs':'Interceptors'):strings[+label-1]?.split('\0')[0]||({weapon:'Damage',armor:'Armor',shield:'Shields'}[kind]);
      const value=base+(+bonus?'+'+bonus:'')+(+hits>1?' (×'+hits+')':''),help=kind==='ammo'?name+': '+level+'\nDamage: '+value:name+'\n'+({weapon:'Damage',armor:'Armor',shield:'Armor'}[kind])+': '+value+'\nUpgrade level: '+level;
      const b=document.createElement('button');b.type='button';b.className='unit-stat';b.setAttribute('aria-label',help.replaceAll('\n',', '));b.dataset.level=level;b.dataset.kind=kind;b.dataset.icon=idx;
      const url=icon(+idx,5,true);if(url){const img=new Image();img.src=url;img.alt='';b.append(img);}const n=document.createElement('span');OpenBWOriginal.text(n,level,art.health);b.append(n);
      const show=()=>{OpenBWOriginal.text(hint,help,art.small,180);hint.hidden=false;clearTimeout(hintTimer);hintTimer=setTimeout(()=>hint.hidden=true,3600);};
      b.addEventListener('pointerenter',e=>{if(e.pointerType==='mouse')show();});b.onclick=show;box.append(b);detailRows.push({kind,icon:+idx,level:+level,base:+base,bonus:+bonus,hits:+hits});
    }
  };
  const draw=()=>{const a=miniRect();if(!a.w||!a.h||a.y<0)return;if(minimap.width!==a.w)minimap.width=a.w;if(minimap.height!==a.h)minimap.height=a.h;minimap.style.height='auto';
    // Fit every map into the original 128px well, preserving its aspect ratio.
    const mapScale=128/Math.max(1,x.openbw_map_w(),x.openbw_map_h());
    minimap.style.width=(x.openbw_map_w()*mapScale)+'px';minimap.style.height=(x.openbw_map_h()*mapScale)+'px';mctx.imageSmoothingEnabled=false;mctx.drawImage(canvas,a.x,a.y,a.w,a.h,0,0,a.w,a.h);
    terrain.setAttribute('aria-pressed',String(!!x.openbw_minimap_terrain()));
    terrain.title=x.openbw_minimap_terrain()?'Hide minimap terrain (Tab)':'Show minimap terrain (Tab)';
    $('wires').style.setProperty('--group-columns',Math.ceil($('wires').children.length/2));
    $('wires').classList.toggle('group',$('wires').children.length>1);
    document.body.classList.toggle('group-selection',$('wires').children.length>1);
  };
  const card=(text,fallbackIcon)=>{
    const lines=text.split('\n'),title=lines[0].split('\t'),count=$('wires').children.length;$('unit-name').textContent=count>1?count+' units selected':title[0]||'';$('unit-life').textContent=title[1]||'';$('unit-extra').textContent=title[2]||'';$('unit-effects').textContent=title[3]||'';
    const hp=(title[1]||'').match(/HP (\d+)\/(\d+)/),bar=$('unit-health');bar.hidden=!hp;if(hp){const percent=Math.min(100,Math.floor(+hp[1]/+hp[2]*100));bar.firstElementChild.style.width=percent+'%';bar.firstElementChild.style.background=percent>66?'#58b54e':percent>=33?'#dac148':'#d34938';healthColor=percent>66?7:percent>=33?3:6;$('unit-life').dataset.color=String(healthColor);}
    
    const id=x.openbw_selected_type?.() ?? -1;
    if(id>=0&&count===1&&unitNames[id])$('unit-name').textContent=unitNames[id];
    $('unit-life').textContent=(title[1]||'').replace(/^HP /,'');
    for(const key of ['unit-name','unit-life','unit-extra','unit-effects']){const el=$(key),value=el.textContent,draw=key==='unit-life'||key==='unit-extra'?art.health:art.unitName;if(value)OpenBWOriginal.text(el,(key==='unit-life'?String.fromCharCode(healthColor):'')+value,draw,0,'center');}
    // The card header is rebuilt every frame, including the shields/energy text.
    // Keep details in sync even when commands themselves have not changed.
    details();

    if(id!==preview){preview=id;$('unit-preview-image').hidden=true;$('unit-preview-image').removeAttribute('src');}
    const commands=title[0]+'|'+lines.slice(1).join('\n')+'|'+x.openbw_cursor();
    if(commands!==lastCommands){page=0;lastCommands=commands;}
    const sig=commands+'|'+page;if(sig===signature)return;signature=sig;
    let buttons=lines.slice(1).map(s=>s.split('\t')).filter(a=>a.length>=2);
    const worker=[7,41,64].includes(id);
    if(worker)buttons=buttons.filter(f=>!['Patrol','Hold','Hold Position'].includes(f[1]));
    const buildMenu=title[0]==='Build' || title[0]==='Advanced Build';
    if((buildMenu || x.openbw_cursor()) && !buttons.some(f=>f[0].charCodeAt(0)===27))buttons.push(['\x1b','Cancel','1','-1']);
    const standard=buttons.some(f=>f[1]==='Move'),slots={Move:0,Stop:1,Attack:2,Patrol:3,Hold:4,'Hold Position':4,Gather:4,'Return Cargo':4,Repair:3,Build:6,Advanced:7,
      'Stim Pack':6,'Spider Mines':6,'Siege Mode':6,'Tank Mode':6,
      Burrow:8,Unburrow:8,'Lift Off':8,Land:8,'Set Rally Point':5,'Select Larva':0,
      'Build Interceptor':6,'Build Scarab':6,'Merge Archon':8,'Dark Archon':8,
      'Yamato Gun':6,'Lockdown':6,'Nuclear Strike':8,'Defensive Matrix':6,'EMP Shockwave':7,Irradiate:8,
      'Psionic Storm':6,Hallucination:7,Recall:6,'Stasis Field':7,'Disruption Web':6,
      Feedback:6,'Mind Control':7,Maelstrom:8,Parasite:6,'Spawn Broodlings':7,Ensnare:8,'Infest CC':5,
      'Dark Swarm':6,Plague:7,Consume:8,Restoration:6,'Optical Flare':7,Heal:3,
      Cloak:id===1?7:6,Decloak:id===1?7:6,Unload:8,'Scanner Sweep':0};
    if(id===46){slots.Burrow=5;slots.Unburrow=5;}
    if([72,82,83,81].includes(id))slots['Build Scarab']=slots['Build Interceptor']=6;

    // Original worker menu order, independent of the engine's numeric unit order.
    const buildSlots={106:0,109:1,110:2,111:3,122:4,124:5,112:6,125:7,113:0,114:1,116:2,123:3,
      154:0,156:1,157:2,160:3,166:4,162:5,172:6,159:7,155:0,167:1,163:2,165:3,169:4,164:5,171:6,170:7,
      131:0,143:1,149:2,142:3,139:4,135:5,141:0,138:1,134:2,140:3,136:4};
    const trainingSlots={
      106:{7:0,107:6,108:7},111:{0:0,32:1,1:2,34:3},
      113:{2:0,5:1,3:2,120:6},114:{8:0,11:1,9:2,12:3,58:4,115:6},
      154:{64:0},160:{65:0,66:1,67:2,61:3},155:{69:0,83:1,84:2},167:{70:0,72:1,71:2,60:3},
      131:{132:6},132:{133:6},
      35:{41:0,37:1,42:2,38:3,43:4,47:5,45:6,39:7,46:8},
      38:{103:6},43:{44:6,62:7},143:{144:0,146:1},141:{137:6}
    };
    // Fixed original research slots, indexed by DAT ID. An option disappearing
    // must leave its cell empty; the remaining upgrades never slide into it.
    const upgradeSlots={0:1,1:3,2:4,3:2,4:1,5:1,6:1,7:0,8:0,9:1,10:0,11:1,12:0,13:0,14:0,15:2,
      16:0,17:0,19:2,20:3,21:4,22:1,23:1,24:3,25:4,26:5,27:0,28:1,29:0,30:1,31:2,32:2,
      33:2,34:0,35:0,36:1,37:2,38:1,39:0,40:2,41:0,42:1,43:2,44:2,47:4,49:5,51:5,52:1,53:0,54:3};
    const researchSlots={0:1,1:0,2:1,3:1,5:2,7:0,8:0,9:0,10:1,11:2,13:0,15:0,16:1,17:1,19:0,20:1,21:0,22:1,24:3,25:3,27:3,30:4,31:4,32:2};
    const pages=buttons.length>9?Math.ceil(buttons.length/8):1;
    if(pages>1)buttons=buttons.slice((page%pages)*8,(page%pages)*8+8);
    const used=new Set(pages>1?[8]:[]),positions=buttons.map(f=>{
      const label=f[1],isEsc=f[0].charCodeAt(0)===27;
      let slot=pages>1?undefined:buildMenu?buildSlots[+f[3]]:(+f[11]>=0?upgradeSlots[+f[11]]:+f[12]>=0?researchSlots[+f[12]]:slots[label]??trainingSlots[id]?.[+f[3]]);
      if(isEsc && pages===1)slot=8;
      if(slot!==undefined && used.has(slot))slot=undefined;
      if(slot!==undefined)used.add(slot);return slot;
    });
    positions.forEach((slot,i)=>{if(slot!==undefined)return;const free=Array.from({length:9},(_,a)=>a).find(a=>!used.has(a));positions[i]=free;used.add(free);});
    let html='',buttonIndex=0;
    for(const f of buttons){const label=f[1],isEsc=f[0].charCodeAt(0)===27,unit=+f[3],idx=f[10]!==undefined&&+f[10]>=0?+f[10]:unit>=0?unit:orderIcons[label],url=idx!==undefined?icon(idx,f[2]==='0'?1:f[9]==='1'?2:0):'',cost=(+f[4]||+f[5])?' · '+f[4]+' minerals'+(+f[5]?' / '+f[5]+' gas':''):'';
      const slot=positions[buttonIndex++];
      const off=f[2]==='0',poor=f[6]==='0',active=f[9]==='1',detail=off&&f[7]?' · Requires '+f[7]:cost;
      html+=`<button type="button" data-slot="${slot}" class="cmd${off?' off':''}${poor?' poor':''}${active?' active':''}" data-key="${isEsc?'&#27;':esc(f[0])}" data-hint="${esc(label+detail+(f[8]?' · '+f[8]:''))}" aria-label="${esc(label+detail)}" aria-disabled="${off}" ${slot!==undefined?`style="grid-column:${slot%3+1};grid-row:${Math.floor(slot/3)+1}"`:''}>${url?`<img class="ico" src="${url}" alt="">`:''}<span class="lbl${url?'':' fallback-label'}">${esc(label)}</span></button>`;
    }
    if(pages>1)html+=`<button type="button" class="cmd" data-page="next" style="grid-column:3;grid-row:3" aria-label="More commands" data-hint="More commands"><span class="lbl fallback-label">More<br>${page%pages+1}/${pages}</span></button>`;
    $('card').innerHTML=html;
    for(const el of $('card').querySelectorAll('.fallback-label'))OpenBWOriginal.text(el,el.textContent,art.unitName,34,'center');
  };
  window.openbwClassicStats=()=>({race,sounds:sounds.stats(),originalConsole:true,originalFonts:Object.keys(fonts),speechFont:art.speech?'font10':'fallback',timerFont:art.font?'font16':'fallback',resourceFrames:art.resourceFrames,commandIcons:icons.size,minimap:miniRect(),minimapTerrain:!!x.openbw_minimap_terrain(),dialogArt:'dlgs/'+({t:'terran',p:'protoss',z:'zerg'}[raceLetter])+'.grp',selectedType:preview,details:detailRows,commandSlots:[...$('card').querySelectorAll('.cmd')].map(b=>({label:b.getAttribute('aria-label'),slot:+b.dataset.slot})),submenu:/^(Build|Advanced Build)\|/.test(lastCommands)});
  return{card,draw,portraits,art,read,fonts,sounds,icon,unitNames,production};
};

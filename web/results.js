/* Classic 1.16 score screens, decoded from the player's original archives. */
window.OpenBWResults = function({x,memory,classic,race,music,saveReplay,exit}) {
  const root=document.createElement('section');root.id='classic-results';root.hidden=true;root.setAttribute('role','dialog');
  document.getElementById('game-stage').append(root);
  const str=p=>{if(!p)return '';const a=new Uint8Array(memory.buffer);let e=p;while(e<a.length&&a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};
  const read=classic.read,place=OpenBWOriginal.place,pcx=OpenBWArt.pcx;
  let phase='closed',tab=0,won=false,rows=[],elapsed=0,timer=0,started=0,fonts=null,layout=null,art=null,scoreSounds=null;
  const colors=['#f40404','#0c48cc','#2cb494','#88409c','#f88c14','#703014','#cce0d0','#fcfc38'];
  function label(parent,text,box,font,color=2,align='center'){
    const el=document.createElement('div');place(el,box);OpenBWOriginal.text(el,text,font,box.width,align,color);parent.append(el);return el;
  }
  function button(parent,id,text,box,font,action,game=false){
    const b=document.createElement('button');b.id=id;b.type='button';b.setAttribute('aria-label',text.replace(/[\x00-\x1f]/g,''));b.className=game?'result-message-button':'result-glue-button';place(b,box);
    const t=document.createElement('span');OpenBWOriginal.buttonText(b,t,text,font,game?3:3,4);b.append(t);b.onclick=action;parent.append(b);return b;
  }
  function show(outcome){
    if(phase!=='closed')return;won=!!outcome;classic.sounds.play(won?'youwin':'youlose');phase='message';root.hidden=false;root.replaceChildren();root.setAttribute('aria-label',won?'Victory':'Defeat');
    window.openbwCancelTouch?.();document.getElementById('game-menu').hidden=true;document.body.classList.remove('menu-open');
    const dialog=document.createElement('div');dialog.className='result-message';place(dialog,{x:176,y:144,width:288,height:128});root.append(dialog);
    const frame=OpenBWArt.dialogFrame(read('dlgs/tile.grp'),classic.art.palette,288,128);
    if(frame){const img=new Image();img.src=frame.toDataURL();img.className='result-dialog-art';dialog.append(img);}
    label(dialog,won?'Congratulations!\nYou are victorious!':'You have been defeated.',{x:12,y:8,width:264,height:45},classic.art.font);
    button(dialog,'result-continue',won?'Victory':'Defeat',{x:32,y:58,width:224,height:28},classic.art.font,scores,true);
    OpenBWOriginal.buttonSounds(dialog,classic.sounds,true);
    window.openbwBack=()=>{scores();return true;};
  }
  function scores(){
    if(phase==='scores')return;phase='scores';root.replaceChildren();root.classList.add('scores');
    music.phase(won?'victory':'defeat');
    const key=(['z','t','p'][race]||'t')+(won?'v':'d'),prefix='glue/score'+key+'/',pal='glue/pal'+key+'/';
    const bg=pcx(read(pal+'backgnd.pcx'),false),tint=pcx(read(pal+'tfont.pcx')),glass=pcx(read(pal+'teffect.pcx')).indices[1];
    art={};for(const n of ['pmain','pinset','scorebox','untab'])art[n]=pcx(read(prefix+n+'.pcx'),true,glass).canvas.toDataURL();
    fonts={};for(const n of ['8','10','16','16x'])fonts[n]=OpenBWArt.font(classic.fonts[n],tint,bg.palette);
    root.style.backgroundImage='url('+bg.canvas.toDataURL()+')';layout=OpenBWOriginal.dialog(read('rez/gluscore.bin'));
    const raw=str(x.openbw_stats()).split('\n'),header=raw.shift().split('\t');elapsed=Math.floor(+header[1]/24);
    rows=raw.filter(Boolean).map(line=>{const a=line.split('\t').map(Number);return {me:!!a[0],race:a[1],color:a[2],units:a[3],buildings:a[4],minerals:a[5],gas:a[6],kills:a[8]||0,lost:a[9]||0,razed:a[10]||0,buildingsLost:a[11]||0,unitScore:a[12]||0,buildingScore:a[13]||0,spent:(a[14]||0)+(a[15]||0),slot:a[16]||0};});
    const sounds={};for(const n of ['scorefill','scorefillend','mousedown2','mouseover']){const b=read('sound/glue/'+n+'.wav');if(b)sounds[n]=b;}
    scoreSounds=OpenBWOriginal.sounds(sounds);OpenBWOriginal.buttonSounds(root,scoreSounds);window.openbwBack=()=>{exit();return true;};render(0);
  }
  function render(which){
    tab=which;cancelAnimationFrame(timer);root.replaceChildren();const main=new Image();main.src=art.pmain;main.className='result-main';root.append(main);
    label(root,won?'Victory!':'Defeat',layout.get(2),fonts['16x'],won?4:2,'center');
    for(const [i,name] of ['O\x04v\x01erview','\x04U\x01nits','S\x04t\x01ructures','\x04R\x01esources'].entries()){
      const w=layout.get(i+3),b=button(root,'result-tab-'+i,name,w,fonts['10'],()=>render(i));b.setAttribute('aria-selected',String(i===tab));
      if(i===tab){const cap=new Image();cap.src=art.untab;Object.assign(cap.style,{position:'absolute',left:'0',top:'0',width:'93px',height:'4px'});b.prepend(cap);}
    }
    const headings=[['Units','Structures','Resources'],['Produced','Killed','Lost'],['Constructed','Razed','Lost'],['Minerals','Vespene Gas','Spent']][tab];
    headings.forEach((s,i)=>label(root,s,layout.get(10+i),fonts['10']));label(root,'Total Score',layout.get(8),fonts['16x']);
    const values=[],bars=[];
    const categories=r=>tab===0?[r.unitScore,r.buildingScore,r.minerals+r.gas]:tab===1?[r.units,r.kills,r.lost]:tab===2?[r.buildings,r.razed,r.buildingsLost]:[r.minerals,r.gas,r.spent];
    const max=Math.max(1,...rows.flatMap(categories));
    rows.forEach((r,i)=>{
      const base=13+i*6,back=new Image();back.src=art.pinset;place(back,layout.get(base));root.append(back);
      let name=r.me?(localStorage.getItem('openbw-profile')||'Player'): 'Computer';
      label(root,name,{...layout.get(base+1),width:148,height:18},fonts['16'],r.me?4:2,'left');
      label(root,['Zerg','Terran','Protoss'][r.race]||'Player',{x:36,y:97+i*40,width:140,height:12},fonts['8'],2,'left');
      categories(r).forEach((v,j)=>{const w=layout.get(base+2+j),el=label(root,'0',w,fonts['10']);values.push({el,value:v,font:fonts['10'],width:w.width});
        const bar=document.createElement('div');bar.className='result-bar';place(bar,{x:w.x,y:w.y+21,width:0,height:6});bar.style.backgroundColor=colors[r.color]||'#ccc';root.append(bar);bars.push({el:bar,width:Math.round(96*v/max)});
      });
      const w=layout.get(base+5),box=new Image();box.src=art.scorebox;place(box,w);root.append(box);
      const total=r.unitScore+r.buildingScore+r.minerals+r.gas,el=label(root,'0',{...w,y:w.y+4},fonts['16']);values.push({el,value:total,font:fonts['16'],width:w.width});
    });
    const seconds=String(elapsed%60).padStart(2,'0');label(root,'Elapsed Time: '+Math.floor(elapsed/60)+':'+seconds,{...layout.get(9),width:230},fonts['16'],2,'left');
    button(root,'result-ok',layout.get(7).text.slice(1),layout.get(7),fonts['16x'],exit);
    const replay=button(root,'result-replay',layout.get(61).text.slice(1),layout.get(61),fonts['16x'],()=>saveReplay());
    replay.disabled=!!window.openbwTestingStats?.().used;
    started=performance.now();scoreSounds.play('scorefill');
    function animate(now){const p=Math.min(1,(now-started)/1000);for(const v of values)OpenBWOriginal.text(v.el,String(Math.floor(v.value*p)),v.font,v.width,'center');for(const b of bars)b.el.style.width=Math.round(b.width*p)+'px';
      if(p<1)timer=requestAnimationFrame(animate);else scoreSounds.play('scorefillend');}
    timer=requestAnimationFrame(animate);
  }
  addEventListener('keydown',e=>{if(phase==='closed')return;e.stopImmediatePropagation();if(e.key==='Enter'||e.key==='Escape'){e.preventDefault();phase==='message'?scores():exit();}},true);
  window.openbwResultStats=()=>({phase,won,tab,race,players:rows,titleBox:layout?.get(2),fonts:{title:'font16x',total:'font16x',elapsed:'font16',tabs:'font10'},art:phase==='scores'?'glue/score'+(['z','t','p'][race]||'t')+(won?'v':'d'):'rez/ok.bin'});
  return{show};
};

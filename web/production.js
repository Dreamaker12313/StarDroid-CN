/* Classic statdata.bin production controls and cmdbtns.grp queue artwork. */
globalThis.OpenBWProduction = ({x,memory,art,icon,strings}) => {
  const root=document.getElementById('status'),layout=art.productionLayout;
  const str=p=>{if(!p)return '';const b=new Uint8Array(memory.buffer);let e=p;while(e<b.length&&b[e])e++;return new TextDecoder().decode(b.subarray(p,e));};
  const frame=id=>art.commandFrames[id]?.toDataURL();
  const urls=Object.fromEntries([2,4,6,7,8,9,10,11].map(id=>[id,frame(id)]));
  OpenBWOriginal.buttonSounds(root,art.sounds,true);
  let key='',bar=null,lastPercent=-1;
  const place=(el,id)=>{const w=layout.get(id);OpenBWOriginal.place(el,w);return w;};
  const image=(url,cls)=>{const img=new Image();img.src=url;img.alt='';img.className=cls;return img;};
  root.addEventListener('pointerdown',e=>{
    const q=e.target.closest('[data-slot]');if(!q||!q.dataset.slot||window.openbwAndroidStats?.().paused)return;
    e.preventDefault();x.openbw_cancel(+q.dataset.slot-1);
  });
  return ()=>{
    const text=str(x.openbw_status()),parts=text?text.split('\t'):[],kind=x.openbw_production_kind?.()||0;
    const race=x.openbw_selected_race?.()??1,type=x.openbw_selected_type?.(),ids=Array.from({length:5},(_,i)=>x.openbw_production_queue_type?.(i)??-1);
    const nextKey=[kind,race,type,...parts.slice(1),...ids].join('|');
    if(nextKey!==key){
      key=nextKey;root.replaceChildren();bar=null;lastPercent=-1;
      root.hidden=!text;root.dataset.kind=String(kind);
      if(!text)return;
      const label=document.createElement('span');label.className='production-label';
      // Incomplete units (including Eggs) have their own label/bar, no queue boxes.
      const morph=kind===4,hasTarget=morph&&ids[0]>=0,labelId=morph&&!hasTarget?65506:65521,barId=morph&&!hasTarget?13:kind===2?14:kind===3?16:7;
      const rect=place(label,labelId),tblId=morph?799+race:kind===2?0:kind===3?0:([160,167].includes(type)?771:774)+race;
      const title=tblId?strings[tblId-1]:kind===2?'Researching':'Upgrading';
      OpenBWOriginal.text(label,title||'Building',art.unitName,rect.width,'center');root.append(label);
      bar=document.createElement('canvas');bar.className='production-bar';const br=place(bar,barId);bar.width=br.width;bar.height=br.height;root.append(bar);
      // Eggs retain their target icon even though they have no production queue.
      // Use the normal current-unit rectangle, with the separate morph bar.
      if(morph && ids[0]>=0){
        const q=document.createElement('button');q.type='button';q.className='production-slot';
        q.dataset.slot='1';q.setAttribute('aria-label','Cancel '+parts[1]);place(q,2);
        q.append(image(urls[2],'production-frame'));
        const url=icon(ids[0]);if(url)q.append(image(url,'production-icon'));
        root.append(q);
      }
      if(!morph){
        const count=kind===1?5:1;
        for(let slot=0;slot<count;slot++){
          const name=parts[slot+1]||'',q=document.createElement('button');q.type='button';q.className='production-slot';q.disabled=!name;
          q.dataset.slot=String(slot+1);q.setAttribute('aria-label',name?'Cancel '+name:'Queue slot '+(slot+1));place(q,slot+2);
          q.append(image(urls[slot===0||slot===4?2:4],'production-frame'));
          if(name){
            const id=slot===0?x.openbw_production_icon():ids[slot],url=icon(id);
            if(url)q.append(image(url,'production-icon'));
            if(kind===1){const n=document.createElement('span');n.className='production-number';OpenBWOriginal.text(n,String(slot+1),art.health,0,'left',slot===0?3:2);q.append(n);}
          }else q.append(image(urls[slot+6],'production-empty-number'));
          root.append(q);
        }
        if(kind===1){const connector=image(urls[11],'production-connector');place(connector,8);root.append(connector);}
      }
    }
    if(!bar)return;
    const percent=Math.max(0,Math.min(100,+parts[0]||0));if(percent===lastPercent)return;lastPercent=percent;
    const p=x.openbw_progress_bar(percent,bar.width-2),w=x.openbw_progress_bar_w(),h=x.openbw_progress_bar_h();if(!p||!w||!h)return;
    const ctx=bar.getContext('2d');ctx.fillStyle='#080c08';ctx.fillRect(0,0,bar.width,bar.height);ctx.strokeStyle='#4c5840';ctx.strokeRect(.5,.5,bar.width-1,bar.height-1);
    const im=ctx.createImageData(w,h);im.data.set(new Uint8Array(memory.buffer,p,w*h*4));ctx.putImageData(im,Math.floor((bar.width-w)/2),Math.floor((bar.height-h)/2));
    root.dataset.progress=String(percent);
  };
};

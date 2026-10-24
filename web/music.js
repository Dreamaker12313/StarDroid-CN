window.OpenBWMusic = function(race) {
  const $ = id => document.getElementById(id), audio = new Audio();
  audio.preload = 'auto';
  const mission=globalThis.OpenBWMissions?.find(m=>m.id===new URLSearchParams(location.search).get('campaign'));
  const expansion=mission?.game==='broodwar',sources=new Map();
  const raceName = ['zerg','terran','protoss'][race] || 'terran', prefix = raceName[0];
  let entries=[], phase='game', selected='auto', index=0, url='', worker=null, generation=0;
  let enabled=true, volume=.3, muted=false, paused=false, ducked=false, current='', loading=false, packedBytes=0, closed=false;
  let playPending=false, retryTimer=0, wakeGeneration=0, playError='';
  try { enabled=localStorage.getItem('openbw-music')!=='0';volume=Math.max(0,Math.min(1,Number(localStorage.getItem('openbw-music-volume') ?? .3))); } catch {}
  if(!Number.isFinite(volume)) volume=.3;
  const label = name => name.replace(/^music[\\/]/i,'').replace(/\.wav$/i,'').replace(/(terran|protoss|zerg)([123])/i,'$1 $2');
  const status = message => {$('music-status').textContent=message;};
  const volumeSync = () => {audio.muted=muted || !enabled;audio.volume=volume*(ducked ? .3 : 1);};
  const wanted=()=>!closed && enabled && !muted && !paused && !document.hidden && current && !loading;
  const resume = () => {
    if(!wanted()){audio.pause();return;}
    if(playPending)return;
    playPending=true;
    Promise.resolve(audio.play()).then(()=>{playError='';if(!wanted())audio.pause();},e=>{
      playError=e.name||e.message;
      if(wanted())status('Music is waiting for audio playback to resume.');
    }).finally(()=>{playPending=false;});
  };
  // Native focus can return before WebView becomes visible. Audio focus can
  // also pause media a second time. Retry both events without seeking or
  // clearing the user's pause/mute settings.
  const wake=()=>{
    clearTimeout(retryTimer);const token=++wakeGeneration;resume();
    const delays=[100,250,650,1500];let next=0;
    const retry=()=>{if(token!==wakeGeneration||closed)return;resume();if(next<delays.length)retryTimer=setTimeout(retry,delays[next++]);};
    if(!document.hidden&&!closed)retryTimer=setTimeout(retry,0);
  };
  const visibility=()=>{if(document.hidden){clearTimeout(retryTimer);++wakeGeneration;audio.pause();}else wake();};
  document.addEventListener('visibilitychange',visibility);
  addEventListener('focus',wake);addEventListener('pageshow',wake);
  audio.addEventListener('pause',()=>{if(wanted()&&!audio.ended)wake();});
  const playlist = () => entries.filter(n=>new RegExp('^music\\\\'+raceName+'[123]\\.wav$','i').test(n));
  const desired = () => {
    if(selected !== 'auto') return selected;
    const extra = phase==='title' ? 'title' : phase==='briefing' ? prefix+'rdyroom' : phase==='victory' ? prefix+'vict' : phase==='defeat' ? prefix+'defeat' : '';
    const special=entries.find(n=>n.toLowerCase()==='music\\'+extra+'.wav');
    if(special) return special;
    const list=playlist(); return list.length ? list[index % list.length] : '';
  };
  const load = () => {
    if(closed)return;
    const name=desired();
    if(!name) {audio.pause();status(entries.length ? 'No '+raceName+' music in this archive. Choose a track below.' : 'Import music from StarCraft.mpq on the app home screen.');return;}
    if(name===current) {volumeSync();resume();return;}
    const token=++generation;loading=true;worker?.terminate();audio.pause();audio.removeAttribute('src');audio.load();
    if(url) {URL.revokeObjectURL(url);url='';}
    current=name;loading=true;status('Loading '+label(name)+'…');
    worker=new Worker('./music-worker.js');
    const fail=message=>{if(token!==generation)return;worker?.terminate();worker=null;loading=false;current='';status('Music: '+message);};
    worker.onerror=e=>{e.preventDefault();fail(e.message || 'could not decode track');};
    worker.onmessage=({data})=>{
      if(token!==generation)return;
      worker.terminate();worker=null;
      if(data.error) {fail(data.error);return;}
      packedBytes=data.allocatedBytes;url=URL.createObjectURL(new Blob([data.bytes],{type:'audio/wav'}));
      audio.src=url;loading=false;status(label(name));volumeSync();wake();
    };
    worker.postMessage({name,base:sources.get(name)||'./music/'});
  };
  audio.onended=()=>{if(selected==='auto' && phase==='game') {index++;const next=desired();if(next!==current)load();else {audio.currentTime=0;resume();}}else if(phase!=='victory' && phase!=='defeat'){audio.currentTime=0;resume();}};
  audio.onerror=()=>{if(current)status('This music file could not be played. Try another track.');};
  $('opt-music').checked=enabled;$('music-volume').value=Math.round(volume*100);
  $('opt-music').onchange=()=>{enabled=$('opt-music').checked;try{localStorage.setItem('openbw-music',enabled?'1':'0');}catch{}volumeSync();if(enabled)load();else audio.pause();};
  $('music-volume').oninput=()=>{volume=+$('music-volume').value/100;try{localStorage.setItem('openbw-music-volume',volume);}catch{}volumeSync();};
  $('music-track').onchange=()=>{selected=$('music-track').value;index=0;if(enabled)load();};
  $('music-next').onclick=()=>{selected='auto';$('music-track').value='auto';phase='game';index++;if(enabled)load();};
  Promise.all((expansion?['./music-broodwar/','./music/']:['./music/']).map(async base=>{try{const r=await fetch(base+'manifest.json');return{base,m:r.ok?await r.json():{entries:[]}};}catch{return{base,m:{entries:[]}};}})).then(parts=>{
    const m={format:'openbw-music-bundle-v1',entries:[]};
    for(const part of parts)for(const e of part.m.entries||[])if(!sources.has(e.name)){sources.set(e.name,part.base);m.entries.push(e);}
    if(m.format && m.format!=='openbw-music-bundle-v1')throw Error('Unsupported music import');
    entries=(m.entries||[]).map(e=>e.name).filter(n=>typeof n==='string' && /^music\\(?:terran[123]|protoss[123]|zerg[123]|[tpz](?:rdyroom|vict|defeat)|title)\.wav$/i.test(n));
    for(const n of entries){const option=document.createElement('option');option.value=n;option.textContent=label(n);$('music-track').appendChild(option);}
    if(enabled)load();else status(entries.length?'Music off':'Import music on the app home screen.');
  }).catch(e=>status('Music unavailable: '+e.message));
  const api={
    duck(value){ducked=value;volumeSync();},
    state(p,m,d){const changed=paused!==p || muted!==m;paused=p;muted=m;ducked=d;volumeSync();if(changed)wake();},
    phase(value){if(value===phase)return;phase=value;index=0;if(enabled)load();},
    unlock:wake,wake,
    close(){closed=true;generation++;++wakeGeneration;clearTimeout(retryTimer);document.removeEventListener('visibilitychange',visibility);removeEventListener('focus',wake);removeEventListener('pageshow',wake);worker?.terminate();audio.pause();audio.removeAttribute('src');audio.load();if(url)URL.revokeObjectURL(url);},
    stats:()=>({enabled,volume,muted,paused,ducked,phase,track:current,playing:!audio.paused,time:audio.currentTime,loading,tracks:entries.length,packedBytes,error:audio.error?.message||playError||null}),
  };
  window.openbwMusicStats=api.stats;
  addEventListener('pagehide',e=>{if(e.persisted)audio.pause();else api.close();});
  return api;
};

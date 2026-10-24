/* Local campaign bundle support. Packed MPQ segments stay at their original
   virtual offsets, preserving FIX_KEY encryption without allocating 600 MB. */
window.OpenBWCampaign = (() => {
  const $ = id => document.getElementById(id);
  const check = (ok, why) => { if (!ok) throw new Error('Mission bundle: ' + why); };
  const table = new Uint32Array(1280);
  let seed = 0x100001;
  for (let i = 0; i < 256; i++) for (let j = 0; j < 5; j++) {
    seed = (seed * 125 + 3) % 0x2aaaab; const hi = (seed & 65535) << 16;
    seed = (seed * 125 + 3) % 0x2aaaab; table[i + j * 256] = hi | (seed & 65535);
  }
  function hash(name, type) {
    let a = 0x7fed7fed, b = 0xeeeeeeee;
    for (const ch of name.toUpperCase().replaceAll('/', '\\')) {
      const c = ch.charCodeAt(0); a = (table[(type << 8) + c] ^ (a + b)) >>> 0;
      b = (c + a + b + (b << 5) + 3) >>> 0;
    }
    return a;
  }
  function crypt(bytes, key, encrypt = false) {
    const data = bytes.slice(), view = new DataView(data.buffer); let b = 0xeeeeeeee;
    for (let i = 0; i < data.length; i += 4) {
      b = (b + table[1024 + (key & 255)]) >>> 0;
      let value = view.getUint32(i, true), coded = (value ^ (key + b)) >>> 0;
      view.setUint32(i, coded, true);
      if (!encrypt) value = coded;
      key = (((~key << 21) + 0x11111111) | (key >>> 11)) >>> 0;
      b = (value + b + (b << 5) + 3) >>> 0;
    }
    return data;
  }
  async function load(base = './mission/', profile = 'mission', onlyName = null) {
    const get = async name => {
      const r = await fetch(base + name); check(r.ok, 'import this mission on the app home screen.');
      return new Uint8Array(await r.arrayBuffer());
    };
    const m = JSON.parse(new TextDecoder().decode(await get('manifest.json')));
    const music = profile === 'music', ui = profile === 'interface', story = profile === 'story', cinematic = profile === 'cinematic', extra=ui||music||story||cinematic;
    const expected = profile === 'mission' ? 'terran01' : profile;
    const entry=globalThis.OpenBWMissions?.find(v=>v.id===expected),prefix=entry?.prefix.replaceAll('/','\\')+'staredit\\';
    check(extra ? m.format === 'openbw-'+profile+'-bundle-v1' : m.format === 'openbw-mission-bundle-v1' && !!entry && m.mission === expected, 'wrong bundle format');
    check(Array.isArray(m.entries) && m.entries.length > 0 && m.entries.length <= 256, 'invalid entry count');
    const header = await get('header.bin'), h = new DataView(header.buffer);
    check(header.length === 32 && h.getUint32(0, true) === 0x1a51504d && h.getUint16(12, true) === 0, 'invalid MPQ header');
    const size = h.getUint32(8, true), htpos = h.getUint32(16, true), btpos = h.getUint32(20, true);
    const htn = h.getUint32(24, true), btn = h.getUint32(28, true);
    check(htn > 0 && htn <= 524288 && (htn & (htn - 1)) === 0 && btn <= 524288 && size === m.archiveSize, 'invalid table sizes');
    let ht = await get('hash-table.bin'), bt = await get('block-table.bin');
    check(ht.length === htn * 16 && bt.length === btn * 16, 'table length mismatch');
    ht = crypt(ht, hash('(hash table)', 3)); bt = crypt(bt, hash('(block table)', 3));
    const hv = new DataView(ht.buffer), bv = new DataView(bt.buffer), selected = new Set(), pieces = [];
    let total = 0, scenario = false;
    for (const e of m.entries) {
      if (onlyName && e.name.toLowerCase() !== onlyName.toLowerCase()) continue;
      check(Number.isInteger(e.block) && e.block >= 0 && e.block < btn && !selected.has(e.block), 'invalid block');
      check(typeof e.name === 'string' && (story ? /^(?:rez\\est[tzp](?:0t|[0-9]{2}[ab]?)[x]?\.txt|glue\\pal[tzp][abc]x?\\[a-z]+\.pcx)$/i.test(e.name) : cinematic ? /^smk\\(?:starintr|terran1)\.smk$/i.test(e.name) : ui ? /^(?:(?:files\\)?font\\font(?:8|10|12|14|16|16x|32|50)\.fnt|glue\\palcs\\(?:backgnd\.pcx|tfont\.pcx|teffect\.pcx|dlg\.grp|tile\.grp)|glue\\create\\(?:plistmap2|pinfo|pslots)\.pcx)$/i.test(e.name) : music ? /^music\\(?:terran[123]|protoss[123]|zerg[123]|[tpz](?:rdyroom|vict|defeat)|title)\.wav$/i.test(e.name) : e.name.toLowerCase().startsWith(prefix) && /^(?:scenario\.chk|wav\\[a-z0-9 _'-]{1,80}\.wav)$/i.test(e.name.slice(prefix.length))), 'unexpected entry name');
      check(extra || e.name.toLowerCase().startsWith(prefix), 'entry belongs to another mission');
      scenario ||= /scenario\.chk$/i.test(e.name);
      const at = e.block * 16;
      check(bv.getUint32(at, true) === e.offset && bv.getUint32(at+4, true) === e.packedSize && bv.getUint32(at+8, true) === e.size && bv.getUint32(at+12, true) === e.flags, 'block metadata mismatch');
      check(e.packedSize > 0 && e.packedSize <= 64*1024*1024 && e.size <= 64*1024*1024 && e.offset >= 32 && e.offset + e.packedSize <= size, 'block too large or out of range');
      const start = hash(e.name, 0) & (htn - 1); let found = false;
      for (let n = 0; n < htn; n++) {
        const at = ((start+n)&(htn-1))*16, block = hv.getUint32(at+12,true);
        if (block === 0xffffffff) break;
        if (block === e.block && hv.getUint32(at,true) === hash(e.name,1) && hv.getUint32(at+4,true) === hash(e.name,2)) { found = true; break; }
      }
      check(found, 'entry hash mismatch');
      total += e.packedSize; check(total <= 128*1024*1024, 'bundle too large');
      const bytes = await get('blocks/' + e.block + '.bin'); check(bytes.length === e.packedSize, 'missing or damaged entry');
      pieces.push({ offset: e.offset, bytes }); selected.add(e.block);
    }
    check(extra ? selected.size > 0 : scenario, ui ? 'Original fonts are missing' : music ? 'Music track is missing' : 'Mission map is missing');
    // Hide entries that were not exported, while retaining hash probe chains.
    for (let i=0;i<htn;i++) { const at=i*16+12, block=hv.getUint32(at,true); if (block!==0xffffffff && block!==0xfffffffe && !selected.has(block)) hv.setUint32(at,0xfffffffe,true); }
    for (let i=0;i<btn;i++) if (!selected.has(i)) bt.fill(0,i*16,i*16+16);
    pieces.push({offset:0,bytes:header},{offset:htpos,bytes:crypt(ht,hash('(hash table)',3),true)},{offset:btpos,bytes:crypt(bt,hash('(block table)',3),true)});
    pieces.sort((a,b)=>a.offset-b.offset);
    for (let i=0;i<pieces.length;i++) check(pieces[i].offset+pieces[i].bytes.length<=size && (!i || pieces[i-1].offset+pieces[i-1].bytes.length<=pieces[i].offset),'overlapping data');
    return { length:size, allocatedBytes:pieces.reduce((n,p)=>n+p.bytes.length,0), subarray(start,end) {
      check(start>=0 && end<=size && end>=start && end-start<=64*1024*1024,'invalid read');
      const out=new Uint8Array(end-start);
      for (const p of pieces) { const a=Math.max(start,p.offset),b=Math.min(end,p.offset+p.bytes.length); if (b>a) out.set(p.bytes.subarray(a-p.offset,b-p.offset),a-start); }
      return out;
    }};
  }
  function parseChk(data,player=null) {
    const view = new DataView(data.buffer, data.byteOffset, data.byteLength), chunks = {};
    for (let p=0;p+8<=data.length;) {
      const tag = String.fromCharCode(...data.subarray(p,p+4)), n=view.getUint32(p+4,true);
      check(p+8+n<=data.length,'invalid map section'); chunks[tag]=data.slice(p+8,p+8+n); p+=8+n;
    }
    const raw=chunks['STR '], v=new DataView(raw.buffer), strings=[''],rawStrings=[''];
    for (let i=0;i<v.getUint16(0,true);i++) {
      const a=v.getUint16(2+2*i,true); let b=a; while (b<raw.length && raw[b]) b++;
      rawStrings.push(new TextDecoder('windows-1252').decode(raw.subarray(a,b)));
      strings.push(rawStrings[rawStrings.length-1].replace(/[\x01-\x09\x0b\x0c\x0e-\x1f]/g,'').split(/\r?\n/).map(s=>s.trim()).join('\n').trim());
    }
    const briefing=[],actions=[]; let speaker='Adjutant',portraitUnit=106;
    if(chunks.MBRF) { const v=new DataView(chunks.MBRF.buffer);
      for(let t=0;t+2400<=v.byteLength;t+=2400) {
        if(player!==null){const owners=chunks.MBRF.subarray(t+2372,t+2399);if(owners.some(Boolean)&&!owners[player]&&!owners[17]&&!owners[18+(chunks.FORC?.[player]||0)])continue;}
        for(let a=t+320;a<t+2368;a+=32) {
        const type=v.getUint8(a+26); if(!type) break;
        if(v.getUint8(a+28)&2)continue;
        actions.push({type,text:v.getUint32(a+4,true),sound:v.getUint32(a+8,true),duration:v.getUint32(a+12,true),slot:v.getUint32(a+16,true),adjustment:v.getUint32(a+20,true),unit:v.getUint16(a+24,true),modifier:v.getUint8(a+27)});
        if(type===5) {portraitUnit=v.getUint16(a+24,true);speaker=({23:'General Duke',19:'Jim Raynor',20:'Jim Raynor',16:'Sarah Kerrigan',106:'Adjutant'})[portraitUnit]||'Transmission';}
        if(type===8) briefing.push({speaker,portraitUnit,text:strings[v.getUint32(a+4,true)]||'',sound:v.getUint32(a+8,true),duration:v.getUint32(a+12,true)});
      }
    }
    }
    return {strings,rawStrings,briefing,actions};
  }
  function ui(x,memory,audio,portraits,room,art={}) {
    const chk=new Uint8Array(memory.buffer,x.openbw_campaign_chk(),x.openbw_campaign_chk_len()).slice();
    const missionId=new URLSearchParams(location.search).get('campaign')||'terran01',mission=OpenBWMissions.find(m=>m.id===missionId).code;
    const {strings,rawStrings,briefing,actions}=parseChk(chk,OpenBWMissions.find(m=>m.id===missionId).player),history=[],missing=new Set();
    const entry=OpenBWMissions.find(m=>m.id===missionId);let nextScenario='';
    const initialObjectives=rawStrings[actions.find(a=>a.type===4)?.text]||'Complete the mission objectives.';
    const text = i => strings[i] || '';
    const briefText=i=>rawStrings[i]||'';
    const cstr = p => { const a=new Uint8Array(memory.buffer); let b=p; while(a[b]) b++;return new TextDecoder().decode(a.subarray(p,b)); };
    let suspended=false, briefIndex=-1, playing=false, left=0, last=performance.now(), finish=null, subtitleEnd=0, actionIndex=0, inBriefing=false, textLeft=0;
    const slots=[-1,-1,-1,-1];let talkingSlot=-1,briefPhase='closed',queuedExit=null,transmission=null;
    // CHK modifiers: Set To=7, Add=8, Subtract=9. The WAV duration and
    // adjustment occupy separate fields. Negative adjustments may shorten the
    // subtitle interval, but must never stop a speaker mid-word.
    const transmissionTime=(a,duration)=>Math.max(1,duration,a.modifier===7?a.adjustment:a.modifier===8?duration+a.adjustment:a.modifier===9?duration-a.adjustment:duration);
    const sound = i => {
      if(!i) return 0;
      const p=x.openbw_campaign_sound(i), n=x.openbw_campaign_sound_len(i);
      if(!n) { missing.add(text(i)); return 0; }
      return audio.play(i,p,n);
    };
    $('campaign-panel').hidden=false;
    const stopTalking=()=>{if(talkingSlot>=0)portraits?.briefing(slots[talkingSlot],false,talkingSlot);talkingSlot=-1;room.speaker(-1);};
    function advance(){
      stopTalking();
      if(transmission){audio.stop();transmission=null;room.text('');}
      while(actionIndex<actions.length){const a=actions[actionIndex++],slot=Math.min(3,a.slot);
        if(a.type===1){left=a.duration;return;}
        if(a.type===2)sound(a.sound);
        if(a.type===3){room.text(briefText(a.text),a.duration);textLeft=a.duration;}
        if(a.type===4)room.objectives(briefText(a.text));
        if(a.type===5){slots[slot]=a.unit;portraits?.briefing(a.unit,false,slot);}
        if(a.type===6){slots[slot]=-1;portraits?.briefing(-1,false,slot);}
        if(a.type===7){talkingSlot=slot;room.speaker(slot);portraits?.briefing(slots[slot],true,slot);left=a.duration;return;}
        if(a.type===8){briefIndex++;textLeft=0;talkingSlot=slot;room.speaker(slot);portraits?.briefing(slots[slot],true,slot);
          const duration=sound(a.sound);left=transmissionTime(a,duration||a.duration);
          transmission={action:a,position:0,waiting:0,fallback:!a.sound};room.text(briefText(a.text),left);room.progress(0,left);return;}
      }
      playing=false;
    }
    function replay(){if(briefPhase!=='ready')return;audio.stop();transmission=null;portraits?.clearBriefing();room.speaker(-1);slots.fill(-1);talkingSlot=-1;briefIndex=-1;actionIndex=0;left=0;textLeft=0;room.text('');room.objectives(initialObjectives);playing=true;last=performance.now();advance();}
    $('brief-replay').onclick=replay;
    async function leaveBriefing(toMenu){
      if(briefPhase==='entering'){queuedExit=toMenu;return;}
      if(briefPhase!=='ready')return;briefPhase='leaving';playing=false;transmission=null;textLeft=0;stopTalking();audio.stop();portraits?.clearBriefing();room.text('');room.objectives('');
      await room.leave();briefPhase='closed';inBriefing=false;
      if(toMenu){location.replace('./title.html?menu');return;}
      $('campaign-briefing').hidden=true;const resolve=finish;finish=null;resolve?.();
    }
    $('brief-cancel').onclick=()=>leaveBriefing(true);
    $('brief-start').onclick=async()=>{if(briefPhase==='ready'){await room.selectStart();await leaveBriefing(false);}};
    window.openbwBack=()=>{if(inBriefing)leaveBriefing(true);return true;};
    addEventListener('keydown',e=>{if(!inBriefing)return;if(['r','s','c','Enter','Escape'].includes(e.key)){e.preventDefault();e.stopImmediatePropagation();if(e.key==='r')replay();else if(e.key==='c'||e.key==='Escape')$('brief-cancel').click();else $('brief-start').click();}},true);
    $('campaign-objectives-button').hidden=false;
    $('campaign-objectives-button').onclick=()=>{ $('campaign-objectives').hidden=!$('campaign-objectives').hidden; };
    $('campaign-objectives-close').onclick=()=>{ $('campaign-objectives').hidden=true; };
    function tick(now) {
      if(inBriefing&&!suspended&&!document.hidden){const dt=Math.max(0,Math.min(200,now-last));
        if(playing){
          if(transmission){
            const t=transmission,state=audio.status();t.waiting+=dt;
            if(!t.fallback&&!state.ready&&(state.failed||t.waiting>10000)){
              t.fallback=true;missing.add(text(t.action.sound));audio.stop();
            }
            const duration=transmissionTime(t.action,!t.fallback&&state.duration||t.action.duration);
            if(t.fallback)t.position+=dt;else if(state.ready)t.position=state.position;
            left=duration-t.position;room.progress(t.position,duration);
          }else left-=dt;
          if(left<=0)advance();
        }
        if(textLeft>0){textLeft-=dt;if(textLeft<=0)room.text('');}
      }
      last=now;if(!document.hidden)poll();requestAnimationFrame(tick);
    }
    const messages=[];let messageKey='',objectivesKey='',timerKey='';
    function missionText(el,value,width=624){
      el.setAttribute('aria-label',value.replace(/[\x00-\x1f]/g,' '));
      if(art.speech){const c=art.speech(value,{width});c.className='original-text';el.replaceChildren(c);}
      else el.textContent=value.replace(/[\x01-\x09\x0b\x0c\x0e-\x1f]/g,'');
    }
    function poll() {
      for(const row of cstr(x.openbw_campaign_events()).trim().split('\n')) {
        if(!row) continue;
        const [type,idx,wav,duration,unit]=row.split('\t').map(Number);history.push({type,idx,wav,duration,frame:x.openbw_frame()});
        if(type===41)nextScenario=(rawStrings[idx]||'').replaceAll('\\','/').split('/').pop().toLowerCase();
        if(type===7 || type===8) sound(wav);
        if(type===7)portraits?.transmit(unit,x.openbw_frame()+Math.ceil(Math.max(duration,3000)/42));
        if(type===7 || type===9) {
          const value=rawStrings[idx]||'';if(value)messages.push({value,end:x.openbw_frame()+Math.ceil(Math.max(duration,6500)/42)});
          if(messages.length>8)messages.shift();
        }
      }
      for(let i=messages.length-1;i>=0;i--)if(x.openbw_frame()>messages[i].end)messages.splice(i,1);
      const key=messages.map(m=>m.value).join('\n');if(key!==messageKey){messageKey=key;missionText($('campaign-subtitle'),key);$('campaign-subtitle').hidden=!key;}
      const [idx,marines,barracks,raynor,alive,locked]=cstr(x.openbw_campaign_status()).split('\t').map(Number);
      const objective=rawStrings[idx]||initialObjectives;if(objective!==objectivesKey){objectivesKey=objective;missionText($('campaign-objectives-text'),objective,220);}
      const timer=cstr(x.openbw_campaign_timer()),showTimer=timer!=='0:00'||mission===3;
      $('campaign-progress').classList.toggle('original-timer',showTimer);
      if(showTimer&&timer!==timerKey){timerKey=timer;OpenBWOriginal.text($('campaign-progress'),timer,art.font,128,'center');}
      const error=cstr(x.openbw_campaign_ai_error()); $('campaign-ai-warning').hidden=!error; $('campaign-ai-warning').textContent=error ? 'AI stopped: '+error : '';
      $('campaign-ai-status').textContent=cstr(x.openbw_campaign_ai_trace())||'No attack wave yet.';
      $('campaign-cinematic').hidden=!locked;
    }
    requestAnimationFrame(tick);
    const next=()=>OpenBWMissions.find(m=>m.game===entry.game&&m.id!==entry.id&&m.prefix.split('/').slice(-2,-1)[0]===nextScenario.replace(/\.(?:scm|scx)$/i,''))||OpenBWMissions.find(m=>m.code===entry.next);
    return {next,briefing:async()=>{await OpenBWStory.mission(missionId,art.fontBytes);return new Promise(resolve=>{finish=resolve;inBriefing=true;briefPhase='entering';queuedExit=null;$('campaign-briefing').hidden=false;room.enter().then(()=>{briefPhase='ready';if(queuedExit!==null)leaveBriefing(queuedExit);else replay();});});}, suspend:on=>{suspended=on;OpenBWStory.suspend(on);room.suspend(on,inBriefing);last=performance.now();}, poll, stats:()=>({nextScenario,nextMission:next()?.id||null,history:[...history],missing:[...missing],briefIndex,briefPhase,playing,actionIndex,transmission:transmission?{position:transmission.position,remaining:left,fallback:transmission.fallback}:null,voice:audio.status(),slots:[...slots],messages:messages.map(m=>m.value),status:cstr(x.openbw_campaign_status()),ai:cstr(x.openbw_campaign_ai()),aiError:cstr(x.openbw_campaign_ai_error()),aiTrace:cstr(x.openbw_campaign_ai_trace())})};
  }
  return {load,parseChk,ui};
})();

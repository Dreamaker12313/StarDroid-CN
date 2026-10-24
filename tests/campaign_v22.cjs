// Private original game files are supplied externally; none are bundled.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game'),catalog=JSON.parse(fs.readFileSync(path.join(root,'missions.json'))),fixtures=process.env.OPENBW_V22_FIXTURES||'/tmp/openbw-v22-fixtures';
let mission='zerg02';const report={missions:{},checks:[],errors:[],method:'Startup runs periodically heal player units; Brood War Zerg 1 also heals its seven rescue Hives so unattended combat does not trigger the original defeat objective. This is a smoke test, not a campaign balance or complete-playthrough test.'};
const server=http.createServer((req,res)=>{
 const p=decodeURIComponent(new URL(req.url,'http://local').pathname);
 if(p==='/availability.json'){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({missions:catalog.map(m=>m.code)}));}
 const match=p.match(/^\/(data|interface|music-broodwar|music|story-broodwar|story|mission)\/(.*)$/);
 const f=match?path.join(match[1]==='data'?'/tmp/openbw-test-data':path.join(fixtures,match[1]==='mission'?mission:match[1]),match[2]):path.join(assets,p==='/'?'index.html':p);
 if(!fs.existsSync(f)||!fs.statSync(f).isFile()){res.writeHead(404);return res.end();}
 res.setHeader('Content-Type',({'.wasm':'application/wasm','.js':'text/javascript','.html':'text/html','.css':'text/css'})[path.extname(f)]||'application/octet-stream');fs.createReadStream(f).pipe(res);
});
async function boot(p,base,id){mission=id;await p.goto(base+'/?campaign='+id);
 await p.waitForFunction(()=>window.openbwStoryStats?.().active||window.openbwBriefingArtStats?.().phase==='ready'||document.querySelector('#msg')?.textContent.includes('failed'),null,{timeout:90000});
 for(let i=0;i<12&&await p.evaluate(()=>openbwStoryStats().active);i++){await p.locator('#story-screen').tap();await p.waitForTimeout(30);}
 await p.waitForFunction(()=>window.openbwBriefingArtStats?.().phase==='ready');
 await p.locator('#brief-start').tap();await p.waitForFunction(()=>window.__bw?.x.openbw_frame()>3);
 await p.evaluate(({owner,protectHives})=>{
  const{x,memory,lockstep}=__bw,str=p=>{const a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};
  const units=()=>str(x.openbw_debug_units()).trim().split('\n').filter(Boolean).map(r=>{const a=r.split('\t');return{id:+a[0],name:a[1],owner:+a[2],x:+a[3],y:+a[4],order:+a[5]};});
  const u16=n=>[n&255,n>>8&255],send=rows=>{const bytes=new Uint8Array(rows.flatMap(r=>[...u16(r.length),...r]));new Uint8Array(memory.buffer,x.openbw_in_ptr(bytes.length),bytes.length).set(bytes);x.openbw_apply(owner,bytes.length);};
  const select=ids=>{send([[9,ids.length,...ids.flatMap(u16)]]);ids.forEach((id,i)=>x.openbw_debug_select(id,i?1:0));};
  const advance=async(n,heal=false)=>{openbwAndroidSuspend();for(let i=0;i<n&&!x.openbw_outcome();i++){if(heal&&i%60===0)for(const u of units().filter(u=>u.owner===owner||(protectHives&&u.name==='Hive')))x.openbw_debug_set_life(u.id,10000,-1);lockstep.tick();if(i%120===0)await new Promise(r=>setTimeout(r,0));}openbwAndroidResume();};
  window.ct={x,str,units,owner,send,u16,select,advance};
 },{owner:catalog.find(m=>m.id===id).player,protectHives:id==='expzerg01'});
}
async function select(p,name,owner){await p.evaluate(({name,owner})=>{const u=ct.units().find(u=>u.name===name&&(owner===null||u.owner===(owner??ct.owner)));if(!u)throw Error('Missing '+name);ct.select([u.id]);}, {name,owner});await p.waitForTimeout(150);}
async function resume(p){await p.evaluate(()=>{for(let i=0;i<4&&openbwMenuStats().opened;i++)openbwBack();});}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
try{
 for(const id of (process.env.OPENBW_V22_MISSIONS||'zerg02,expprotoss01,expterran02,expzerg03,expbonus').split(',')){
  const p=await browser.newPage({viewport:{width:1536,height:708},hasTouch:true,isMobile:true}),entry=report.missions[id]={};
  p.on('pageerror',e=>{report.errors.push(id+': '+e.message);console.log('PAGE ERROR',id,e.message);});
  p.on('console',m=>{if(m.type()==='error'&&!m.text().includes('404'))console.log('CONSOLE',id,m.text());});
  await p.addInitScript(()=>{window.startedAudio=[];window.audioFingerprint=b=>JSON.stringify([b.length,b.sampleRate,b.numberOfChannels,...Array.from({length:20},(_,i)=>Math.round(b.getChannelData(0)[Math.floor((b.length-1)*i/20)]*32768))]);const start=AudioBufferSourceNode.prototype.start;AudioBufferSourceNode.prototype.start=function(...args){if(this.buffer)startedAudio.push(audioFingerprint(this.buffer));return start.apply(this,args);};});
  try{
   await boot(p,base,id);await p.evaluate(n=>ct.advance(n,true),+(process.env.OPENBW_V22_FRAMES||2400));
   entry.state=await p.evaluate(()=>({frame:ct.x.openbw_frame(),ai:ct.str(ct.x.openbw_campaign_ai()),error:ct.str(ct.x.openbw_campaign_ai_error()),outcome:ct.x.openbw_outcome(),units:ct.units().length,voices:openbwCampaignStats().decodedVoices,next:openbwCampaignStats().nextMission}));
   assert.equal(entry.state.error,'','Original campaign AI must keep running');assert(entry.state.units>0);
   assert.equal(entry.state.outcome,0,'Mission must not end before its objectives have been attempted');
   if(id==='zerg02'&&process.env.OPENBW_V22_DETAIL!=='0'){
    await p.evaluate(()=>{ct.x.openbw_test_money();ct.x.openbw_reveal_map();});
    await select(p,'Hatchery');entry.hatchery=await p.evaluate(()=>openbwClassicStats());assert(entry.hatchery.commandSlots.some(b=>b.label.startsWith('Lair')),'Mission 2 exposes Lair morph');
    await select(p,'Larva');entry.larva=await p.evaluate(()=>openbwClassicStats());assert(entry.larva.commandSlots.some(b=>b.label.startsWith('Mutalisk')),'Spire-locked Mutalisk stays visible');
    entry.locked=await p.locator('#card .cmd[aria-label^="Mutalisk"]').evaluate(el=>({disabled:el.getAttribute('aria-disabled')==='true',classes:el.className}));assert(entry.locked.disabled,'Locked Mutalisk disabled');
    await p.locator('#card .cmd[aria-label^="Drone"]').tap();await p.waitForFunction(()=>ct.units().some(u=>u.name==='Egg'),null,{timeout:5000});await select(p,'Egg');entry.egg=await p.evaluate(()=>({kind:ct.x.openbw_production_kind(),target:ct.x.openbw_production_queue_type(0),slots:[...document.querySelectorAll('#status .production-slot')].map(b=>({label:b.getAttribute('aria-label'),image:!!b.querySelector('.production-icon')}))}));assert.equal(entry.egg.target,41);assert.equal(entry.egg.slots.length,1);assert(entry.egg.slots[0].image);await p.screenshot({path:'/tmp/openbw-v22-egg.png'});
    const chrys=await p.evaluate(()=>ct.units().find(u=>/Chrysalis/.test(u.name)));await select(p,chrys.name,null);entry.chrysalis=await p.evaluate(()=>({details:openbwClassicStats().details,health:document.getElementById('unit-hp')?.textContent,unit:ct.str(ct.x.openbw_debug_dump())}));assert.equal(entry.chrysalis.details.length,0);
    await p.evaluate(()=>ct.x.openbw_test_instant(1));
    await select(p,'Hatchery');await p.locator('#card .cmd[aria-label^="Lair"]').tap();
    await p.waitForFunction(()=>ct.units().some(u=>u.owner===ct.owner&&u.name==='Lair'),null,{timeout:8000});
    entry.lairBuilt=true;
    await select(p,'Drone');
    entry.geyser=await p.evaluate(()=>{const worker=ct.units().find(u=>u.owner===ct.owner&&u.name==='Drone'),g=ct.units().filter(u=>u.name==='Vespene Geyser').sort((a,b)=>Math.hypot(a.x-worker.x,a.y-worker.y)-Math.hypot(b.x-worker.x,b.y-worker.y))[0];if(!g)throw Error('No geyser');ct.x.openbw_pan(-65536,-65536);ct.x.openbw_pan(Math.max(0,g.x-300),Math.max(0,g.y-150));return g;});
    await p.locator('#card .cmd[aria-label="Build"]').tap();await p.locator('#card .cmd[aria-label^="Extractor"]').tap();await p.waitForFunction(()=>ct.x.openbw_cursor()===2);await p.waitForTimeout(300);await p.evaluate(()=>startedAudio=[]);
    entry.placement=await p.evaluate(()=>{let pos;outer:for(let y=20;y<280;y+=8)for(let x=40;x<600;x+=8)if(ct.x.openbw_placement_valid(x,y)){pos={x,y};break outer;}if(!pos)throw Error('No valid Extractor site');ct.x.openbw_mouse_move(pos.x,pos.y);ct.x.openbw_mouse_button(1,1,pos.x,pos.y,1);ct.x.openbw_mouse_button(0,1,pos.x,pos.y,1);return pos;});
    await p.waitForFunction(()=>ct.x.openbw_cursor()!==2);await p.waitForTimeout(400);
    entry.buildSound=await p.evaluate(async()=>{const decoder=await MPQDecoder.create(),ctx=new AudioContext();let wav;for(const n of ['patch_rt.mpq','BROODAT.MPQ','STARDAT.MPQ']){const b=new Uint8Array(await fetch('./data/'+n).then(r=>r.arrayBuffer()));wav=decoder.read(b,'sound/misc/ZBldgPlc.wav');if(wav)break;}const buffer=await ctx.decodeAudioData(wav.slice().buffer),found=startedAudio.includes(audioFingerprint(buffer));await ctx.close();return found;});assert(entry.buildSound,'Original Zerg building placement DON cue played');
    await p.evaluate(()=>ct.advance(1700));await select(p,'Extractor');entry.extractor=await p.evaluate(()=>ct.str(ct.x.openbw_card()));assert.match(entry.extractor,/HP \d+\/750/);assert.match(entry.extractor,/Gas/);await p.screenshot({path:'/tmp/openbw-v22-extractor.png'});
    entry.beacon=await p.evaluate(async()=>{const beacon=ct.units().find(u=>/Beacon/.test(u.name)&&u.owner!==ct.owner),worker=ct.units().find(u=>u.owner===ct.owner&&u.name==='Drone');if(!beacon)throw Error('No mission beacon');const before=ct.str(ct.x.openbw_debug_dump()).match(/rescues=(\d+)/)[1];ct.x.openbw_debug_warp(worker.id,beacon.x,beacon.y);await ct.advance(160);return{before,after:ct.str(ct.x.openbw_debug_dump()).match(/rescues=(\d+)/)[1],owner:ct.units().find(u=>u.id===beacon.id)?.owner};});assert.equal(entry.beacon.after,entry.beacon.before,'Beacon transfer does not play rescue sound');assert.equal(entry.beacon.owner,catalog.find(m=>m.id===id).player);
    report.checks.push('Lair morph completes; Extractor placement plays the original DON sound and shows HP plus gas; beacon transfer is silent.');
    await p.locator('#settingsbtn').tap();await p.locator('#menu-options').tap();await p.locator('#menu-sound').tap();await p.screenshot({path:'/tmp/openbw-v22-sound-settings.png'});entry.settings=await p.evaluate(()=>{const b=document.querySelector('#game-menu .sc-dialog').getBoundingClientRect();return{page:openbwMenuStats().page,w:b.width,h:b.height,style:getComputedStyle(document.querySelector('#game-menu .sc-dialog')).backgroundImage.length};});assert(entry.settings.style>100);await resume(p);
    await p.locator('#settingsbtn').tap();await p.locator('#menu-options').tap();await p.evaluate(()=>startedAudio=[]);await p.locator('#menu-test-victory').tap();await p.waitForFunction(()=>openbwResultStats().phase==='message');await p.waitForTimeout(600);
    entry.victorySound=await p.evaluate(async()=>{const decoder=await MPQDecoder.create(),ctx=new AudioContext();let wav;for(const n of ['patch_rt.mpq','BROODAT.MPQ','STARDAT.MPQ']){const b=new Uint8Array(await fetch('./data/'+n).then(r=>r.arrayBuffer()));wav=decoder.read(b,'sound/misc/youwin.wav');if(wav)break;}const buffer=await ctx.decodeAudioData(wav.slice().buffer),found=startedAudio.includes(audioFingerprint(buffer));await ctx.close();return found;});assert(entry.victorySound,'Original youwin.wav was played');
    report.checks.push('Zerg 2: Lair command, disabled Mutalisk, Egg target icon, no Chrysalis armor, blue settings and original victory sound.');
   }
   console.log('PASS',id,JSON.stringify(entry.state));
  }catch(e){entry.failure=e.stack;report.errors.push(id+': '+e.message);console.log('FAIL',id,e.stack);await p.screenshot({path:'/tmp/openbw-v22-'+id+'-failure.png'});}
  await p.close();
 }
 if(process.env.OPENBW_V22_TITLE==='1'){
  const p=await browser.newPage({viewport:{width:1200,height:900},hasTouch:true});await p.addInitScript(()=>{localStorage.setItem('openbw-profiles','["Tester"]');localStorage.setItem('openbw-profile','Tester');});p.on('pageerror',e=>report.errors.push(e.message));await p.goto(base+'/title.html?menu');await p.waitForFunction(()=>window.openbwTitleStats?.().loaded,null,{timeout:60000}).catch(async e=>{console.log('TITLE FAILURE',await p.locator('#title-status').textContent());await p.screenshot({path:'/tmp/openbw-v22-title-failure.png'});throw e;});await p.locator('#title-single').tap();await p.screenshot({path:'/tmp/openbw-v22-game-chooser.png'});await p.locator('#game-broodwar').tap();await p.waitForTimeout(650);await p.locator('#registry-ok').tap();await p.waitForTimeout(950);await p.screenshot({path:'/tmp/openbw-v22-expansion-campaign.png'});report.title=await p.evaluate(()=>openbwTitleStats());assert.equal(report.title.game,'broodwar');await p.locator('#campaign-zerg').tap();await p.screenshot({path:'/tmp/openbw-v22-mission-list.png'});await p.close();report.checks.push('Original/Expansion chooser and original expansion campaign artwork.');
 }
 assert.deepEqual(report.errors,[]);
}finally{fs.writeFileSync(path.join(root,'validation/campaign-v22'+(process.env.OPENBW_V22_REPORT||'')+'.json'),JSON.stringify(report,null,2));await browser.close();server.close();}})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

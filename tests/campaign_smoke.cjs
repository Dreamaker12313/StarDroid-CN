const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game');
const report={checks:[],errors:[],logs:[]};
const server=http.createServer((req,res)=>{
 const p=decodeURIComponent(new URL(req.url,'http://local').pathname);
 if(p==='/music/manifest.json'){res.writeHead(200,{'Content-Type':'application/json'});return res.end(JSON.stringify({format:'openbw-music-bundle-v1',entries:[]}));}
 const file=p.startsWith('/data/')?path.join(process.env.OPENBW_TEST_MPQS||'/tmp/openbw-test-data',p.slice(6)):p.startsWith('/mission/')?path.join(process.env.OPENBW_MISSION_BUNDLE||'/tmp/terran01-bundle',p.slice(9)):path.join(assets,p==='/'?'index.html':p);
 if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
 const type=file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':file.endsWith('.css')?'text/css':'application/octet-stream';
 res.writeHead(200,{'Content-Type':type,'Content-Length':fs.statSync(file).size,'Content-Security-Policy':"default-src 'self' blob: data:; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; connect-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'"});fs.createReadStream(file).pipe(res);
});
async function installDriver(page) {
  await page.evaluate(()=>{
    const{x,memory,lockstep}=window.__bw;
    const str=p=>{const a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};
    const u16=n=>[n&255,n>>8&255];
    const send=rows=>{const bytes=new Uint8Array(rows.flatMap(r=>[...u16(r.length),...r]));const p=x.openbw_in_ptr(bytes.length);new Uint8Array(memory.buffer,p,bytes.length).set(bytes);x.openbw_apply(1,bytes.length);};
    const units=()=>str(x.openbw_debug_units()).trim().split('\n').map(r=>{const a=r.split('\t');return{id:+a[0],name:a[1],owner:+a[2],x:+a[3],y:+a[4],order:+a[5]};});
    const select=ids=>send([[9,ids.length,...ids.flatMap(u16)]]);
    const order=(kind,x,y,target=0)=>send([[21,...u16(x),...u16(y),...u16(target),...u16(228),kind,0]]);
    const advance=async n=>{window.openbwAndroidSuspend();for(let i=0;i<n&&!x.openbw_outcome();i++){lockstep.tick();if(i%40===0)await new Promise(r=>setTimeout(r,0));}window.openbwAndroidResume();};
    window.testMission={str,send,u16,units,select,order,advance};
  });
}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME||'/tmp/openbw-browser/chrome-headless-shell-linux64/chrome-headless-shell',headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
  const context=await browser.newContext({viewport:{width:900,height:412},isMobile:true,hasTouch:true});
  const page=await context.newPage();
  page.on('pageerror',e=>{report.errors.push(e.message);console.log('ERROR',e.message)});
  page.on('console',m=>{report.logs.push(m.type()+': '+m.text());if(m.type()==='error'||/WORKER|CARD|Build accepted/.test(m.text()))console.log(m.text());});
  await page.route('**/*',route=>{assert(route.request().url().startsWith(origin+'/'));return route.continue();});
  await page.goto(origin+'/?campaign=terran01');
  await page.waitForSelector('#campaign-briefing:not([hidden])',{timeout:60000});
  await page.waitForFunction(()=>window.openbwCampaignStats().decodedVoices>0);
  assert.match(await page.locator('#brief-text').getAttribute('aria-label'),/Adjutant Online/);
  report.briefing=await page.evaluate(()=>window.openbwCampaignStats());
  report.checks.push('User-provided sparse MPQ loads without full archive allocation; timed briefing voice decodes');
  await page.screenshot({path:path.join(root,'dist/mission-briefing.png')});
  await page.locator('#brief-start').tap();
  await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>32,{},{timeout:30000});
  report.start=await page.evaluate(()=>({game:window.openbwAndroidStats(),mission:window.openbwCampaignStats()}));
  const inspect=()=>page.evaluate(()=>{const{x,memory}=window.__bw;const str=p=>{const a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};return{units:str(x.openbw_debug_units()),resources:str(x.openbw_resources()),status:str(x.openbw_campaign_status())};});
  report.initial=await inspect();
  report.chkSha256=await page.evaluate(async()=>{const{x,memory}=window.__bw;const b=new Uint8Array(memory.buffer,x.openbw_campaign_chk(),x.openbw_campaign_chk_len()).slice();return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(n=>n.toString(16).padStart(2,'0')).join('');});
  console.log('Initial state',report.initial.status);
  assert.equal(report.chkSha256,'4b0e5009c4ae80cfb4cb13ede30842db0aa05bb3be2eedad695fb093fa5786f6','Fixture CHK must decode exactly');
  assert.equal(report.initial.status.split('\t')[1],'5');
  assert.equal(report.initial.resources.split('\t')[0],'40');
  report.checks.push('Original starting units and 40 minerals; original objectives active');
  await page.evaluate(async()=>{const{x,lockstep}=window.__bw;window.openbwAndroidSuspend();for(let i=0;i<300;i++){lockstep.tick();if(i%30===0)await new Promise(r=>setTimeout(r,0));}window.openbwAndroidResume();});
  await page.waitForFunction(()=>window.openbwCampaignStats().history.some(e=>e.type===7));
  report.firstDialogue=await page.evaluate(()=>window.openbwCampaignStats());
  assert(report.firstDialogue.history.some(e=>e.idx===25));
  await page.waitForFunction(()=>window.openbwCampaignStats().decodedVoices>=3);
  report.checks.push('SCV transmission fires from original elapsed-time trigger and its WAV decodes');
  await page.screenshot({path:path.join(root,'dist/mission-start.png')});
  await installDriver(page);
  await page.evaluate(async()=>{
    const t=window.testMission; await t.advance(350);
    t.select(t.units().filter(u=>u.owner===1 && /Marine|SCV/.test(u.name)).map(u=>u.id));
    t.order(14,1014,1031);await t.advance(2200);
  });
  report.rescue=await inspect(); report.rescueEvents=await page.evaluate(()=>window.openbwCampaignStats());
  console.log('Rescue state',report.rescue.status);
  assert.equal(report.rescue.status.split('\t')[3],'1','Raynor should be rescued through proximity');
  assert(report.rescueEvents.history.some(e=>e.idx===8),'Raynor introduction should fire');
  assert.equal(report.rescue.status.split('\t')[0],'9','Objectives should update after Raynor introduction');
  assert.equal(report.rescueEvents.history.filter(e=>e.idx===8).length,1,'Wait resumes without replaying prior actions');
  report.checks.push('Army crosses map, nearby Raynor transfers to player, introduction plays once and objectives update');
  await page.evaluate(async()=>{
    const t=window.testMission;t.select(t.units().filter(u=>u.owner===1 && /Marine|SCV|Raynor/.test(u.name)).slice(0,12).map(u=>u.id));
    t.order(14,1100,1580);await t.advance(1300);
  });
  console.log('Base state',(await inspect()).status);
  await page.screenshot({path:path.join(root,'dist/mission-rescue.png')});
  await page.evaluate(async()=>{
    const t=window.testMission;
    const workers=t.units().filter(u=>u.owner===1 && u.name==='SCV'), minerals=t.units().filter(u=>u.owner===11 && /Mineral/.test(u.name) && u.y>1750);
    if(!minerals.length) throw new Error('No mineral fields in diagnostics');
    workers.forEach((u,i)=>{const m=minerals[i%minerals.length];t.select([u.id]);t.send([[20,...t.u16(m.x),...t.u16(m.y),...t.u16(m.id),...t.u16(228),0]]);});
    await t.advance(1800);
  });
  report.mining=await inspect();console.log('Mining',report.mining.resources);
  assert(+report.mining.resources.split('\t')[0]>=250,'Workers must gather enough minerals for a Barracks');
  const initialEnemies=report.initial.units.split('\n').filter(r=>r.includes('\tZergling\t')).length;
  assert(report.mining.units.split('\n').filter(r=>r.includes('\tZergling\t')).length<initialEnemies,'Squad must defeat guard Zerglings on the route');
  report.checks.push('Normal gather orders mine resources; original Zergling guards fight on the route');
  await page.evaluate(async()=>{
    const t=window.testMission,worker=t.units().find(u=>u.owner===1 && u.name==='SCV');
    t.select([worker.id]);
    t.order(6,960,1620); await t.advance(260); t.select([worker.id]);
    const tries=[];
    outer:for(let row=48;row<=56;row++) for(let col=25;col<=40;col++) {
      t.send([[12,30,...t.u16(col),...t.u16(row),...t.u16(111)]]);
      await t.advance(4); const w=t.units().find(u=>u.id===worker.id);
      if(w.order===30) {tries.push([col,row]);break outer;}
    }
    console.log('Build accepted at',JSON.stringify(tries));
    if(!tries.length) {
      const x=window.__bw.x;x.openbw_debug_select(worker.id,0);x.openbw_render(performance.now());
      console.log('WORKER',t.str(x.openbw_debug_dump()));console.log('CARD',t.str(x.openbw_card()));
      x.openbw_key(1,0,5);x.openbw_key(0,0,5);x.openbw_render(performance.now());console.log('BUILDCARD',t.str(x.openbw_card()));
      throw new Error('No build location accepted');
    }
    await t.advance(1900);
  });
  report.barracks=await inspect();report.barracksEvents=await page.evaluate(()=>window.openbwCampaignStats());
  console.log('Barracks state',report.barracks.status);
  assert.equal(report.barracks.status.split('\t')[2],'1','Real SCV construction must complete');
  assert(report.barracksEvents.history.some(e=>e.idx===22),'Barracks advisor line must fire');
  await page.evaluate(async()=>{
    const t=window.testMission,b=t.units().find(u=>u.owner===1 && u.name==='Barracks');t.select([b.id]);
    t.send(Array.from({length:5},()=>[31,...t.u16(0)]));await t.advance(2500);
  });
  report.victory=await inspect(); report.outcome=await page.evaluate(()=>window.__bw.x.openbw_outcome());
  console.log('Victory state',report.victory.status,report.outcome);
  assert.equal(report.outcome,1,'Original win trigger must produce Victory after completing objectives');
  await page.waitForSelector('#gameover.show');
  await page.waitForFunction(()=>window.openbwCampaignStats().decodedVoices===6);
  report.finalAudio=await page.evaluate(()=>window.openbwCampaignStats());
  await page.screenshot({path:path.join(root,'dist/mission-victory.png')});
  report.checks.push('SCV builds Barracks, advisor transmission runs, training Marines meets original Victory trigger');
  const lose = await context.newPage();
  lose.on('pageerror',e=>report.errors.push(e.message));
  await lose.goto(origin+'/?campaign=terran01');
  await lose.waitForSelector('#campaign-briefing:not([hidden])',{timeout:60000});
  await lose.locator('#brief-start').tap();
  await lose.waitForFunction(()=>window.openbwAndroidStats?.().frame>5);
  await installDriver(lose);
  await lose.evaluate(async()=>{
    const t=window.testMission; t.select(t.units().filter(u=>u.owner===1 && /Marine|SCV/.test(u.name)).map(u=>u.id));
    t.order(14,1014,1031);await t.advance(2700);
    const r=t.units().find(u=>u.owner===1 && u.name==='Jim Raynor');if(!r)throw new Error('Raynor was not rescued for defeat test');
    // Lower HP to bound the test, then use real enemy damage and death processing.
    window.__bw.x.openbw_debug_set_life(r.id,1,-1); t.select([r.id]); t.order(6,1330,269);await t.advance(2200);
  });
  await lose.waitForSelector('#gameover.show');
  await lose.waitForFunction(()=>window.openbwCampaignStats().history.some(e=>e.idx===14));
  report.defeat=await lose.evaluate(()=>({outcome:window.__bw.x.openbw_outcome(),mission:window.openbwCampaignStats()}));
  console.log('Defeat outcome',report.defeat.outcome);
  assert.equal(report.defeat.outcome,2,'Raynor death must fire original defeat trigger');
  assert(report.defeat.mission.history.some(e=>e.idx===14),'Raynor death message must display');
  await lose.waitForSelector('#gameover.show');
  await lose.screenshot({path:path.join(root,'dist/mission-defeat.png')});
  report.checks.push('Raynor dies to actual enemy damage (HP lowered for test), original death message and Defeat trigger run');
  await lose.close();


  assert.deepEqual(report.errors,[]);
 }finally{fs.writeFileSync(path.join(root,'dist/campaign-smoke.json'),JSON.stringify(report,null,2));await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close()});

// Real campaign data supplied externally; none is included with this test/source.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game');
let mission=3;
const report={checks:[],errors:[]};
const server=http.createServer((req,res)=>{
 const p=decodeURIComponent(new URL(req.url,'http://local').pathname);
 if(p==='/music/manifest.json'){res.writeHead(200,{'Content-Type':'application/json'});return res.end(JSON.stringify({format:'openbw-music-bundle-v1',entries:[]}));}
 const file=p.startsWith('/data/')?path.join(process.env.OPENBW_TEST_MPQS||'/tmp/openbw-test-data',p.slice(6)):p.startsWith('/mission/')?path.join(process.env.OPENBW_CAMPAIGN_FIXTURES||'/tmp',`terran0${mission}-bundle`,p.slice(9)):path.join(assets,p==='/'?'index.html':p);
 if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
 const ext=path.extname(file),type={'.wasm':'application/wasm','.js':'text/javascript','.html':'text/html','.css':'text/css'}[ext]||'application/octet-stream';
 res.writeHead(200,{'Content-Type':type,'Content-Length':fs.statSync(file).size});fs.createReadStream(file).pipe(res);
});
async function driver(page){await page.evaluate(()=>{
 const{x,memory,lockstep}=window.__bw;
 const str=p=>{const a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};
 const units=()=>str(x.openbw_debug_units()).trim().split('\n').map(r=>{const a=r.split('\t');return{id:+a[0],name:a[1],owner:+a[2],x:+a[3],y:+a[4],order:+a[5]};});
 const advance=async n=>{window.openbwAndroidSuspend();for(let i=0;i<n&&!x.openbw_outcome();i++){lockstep.tick();if(i%80===0)await new Promise(r=>setTimeout(r,0));}window.openbwAndroidResume();};
 const status=()=>({frame:x.openbw_frame(),ai:str(x.openbw_campaign_ai()),error:str(x.openbw_campaign_ai_error()),trace:str(x.openbw_campaign_ai_trace()),timer:str(x.openbw_campaign_timer()),outcome:x.openbw_outcome(),units:units(),mission:window.openbwCampaignStats()});
 window.aiTest={x,str,units,advance,status};
});}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
  const context=await browser.newContext({viewport:{width:900,height:412},isMobile:true,hasTouch:true});
  const page=await context.newPage();page.on('pageerror',e=>{report.errors.push(e.message);console.log('ERROR',e.message);});page.on('console',m=>{if(m.type()==='error'||/AI |unknown trigger|error/.test(m.text()))console.log('CONSOLE',m.text());});
  await page.route('**/*',route=>{assert(route.request().url().startsWith(origin+'/'));return route.continue();});
  for(mission of [3,2]){
   await page.goto(origin+`/?campaign=terran0${mission}`);
   await page.waitForSelector('#campaign-briefing:not([hidden])',{timeout:60000});
   console.log('BRIEFING',mission,await page.locator('#brief-title').innerText());
   await page.locator('#brief-play').tap();await page.waitForFunction(()=>window.openbwCampaignStats().decodedVoices>0);
   await page.locator('#brief-start').tap();await page.waitForFunction(()=>window.__bw?.x.openbw_frame()>20,{},{timeout:30000});await driver(page);
   const initial=await page.evaluate(()=>window.aiTest.status());report['mission'+mission+'Initial']=initial;
   for(let k=0;k<(mission===3?5:1);k++){
    await page.evaluate(()=>window.aiTest.advance(1800));
    const state=await page.evaluate(()=>window.aiTest.status());
    console.log('STATE',mission,state.frame,state.ai,state.error,state.trace,state.timer,'outcome',state.outcome);
    report['mission'+mission+'Frame'+state.frame]=state;
    if(mission===3){const a=state.ai.trim().split('\t').map(Number);assert(a[5]>5000,'Drones must gather minerals');assert(a[6]>5000,'Drones must gather gas');assert(a[4]>0,'Original script must dispatch timed waves');}
    assert.equal(state.error,'');assert.equal(state.outcome,0);
   }
   if(mission===3){
    const removed=await page.evaluate(()=>{const t=window.aiTest,units=t.units();const removed=units.filter(u=>u.owner===4&&(u.name==='Spawning Pool'||u.name==='Drone')).slice(0,3);const pool=units.find(u=>u.owner===4&&u.name==='Spawning Pool');if(!removed.some(u=>u.id===pool.id))removed.push(pool);for(const u of removed)t.x.openbw_debug_kill(u.id);return removed;});
    report.removedForReplacementTest=removed;
    await page.evaluate(()=>window.aiTest.advance(3600));
    const rebuilt=await page.evaluate(()=>window.aiTest.status());report.replacement=rebuilt;
    console.log('REPLACEMENT',rebuilt.ai,rebuilt.error,rebuilt.units.filter(u=>u.name==='Drone'||u.name==='Spawning Pool'));
    assert.equal(rebuilt.error,'');const a=rebuilt.ai.trim().split('\t').map(Number);assert(a[2]>0,'Missing pool must be rebuilt');assert(a[3]>0,'Lost Drones must be replaced');
    assert(rebuilt.units.some(u=>u.owner===4&&u.name==='Spawning Pool'&&!removed.some(r=>r.id===u.id)));
    report.checks.push('Original Ter3 script mines both resources, sends timed waves, replaces removed workers and rebuilds the removed Spawning Pool.');
   }
   await page.screenshot({path:path.join(root,`dist/mission${mission}-ai.png`)});
   if(mission===3){
    // Isolate timer/evacuation logic: continually heal human buildings so this
    // unattended run does not depend on winning a 30-minute defensive battle.
    const ending=await page.evaluate(async()=>{
     const t=window.aiTest;window.openbwAndroidSuspend();
     const protectedIds=t.units().filter(u=>u.owner===1&&/Command Center|Barracks|Depot|Bunker|Turret|Academy|Engineering Bay/.test(u.name)).map(u=>u.id);
     const before=t.status();
     for(let i=0;i<35000&&!t.x.openbw_outcome();i++){
      for(const id of protectedIds)t.x.openbw_debug_set_life(id,99999,-1);
      window.__bw.lockstep.tick();if(i%120===0)await new Promise(r=>setTimeout(r,0));
     }
     window.openbwAndroidResume();return {before,after:t.status(),protectedIds};
    });
    report.timedEvacuation=ending;console.log('EVACUATION',ending.after.frame,ending.after.outcome,ending.after.timer,ending.after.error);
    assert.equal(ending.after.error,'');assert.equal(ending.after.timer,'0:00');assert.equal(ending.after.outcome,1,'Original timed evacuation trigger must win');
    report.checks.push('Mission 3 countdown reaches zero and original evacuation/Victory triggers finish, with test-only building healing to isolate the timer.');
   }else{
    await page.evaluate(async()=>{const t=window.aiTest;const cc=t.units().find(u=>u.owner===4&&u.name==='Infested Command Center');t.x.openbw_debug_kill(cc.id);await t.advance(2500);});
    report.mission2Victory=await page.evaluate(()=>window.aiTest.status());assert.equal(report.mission2Victory.outcome,1);
    report.checks.push('Mission 2 briefing/voice loads and the original Infested Command Center objective triggers Victory after controlled destruction.');
   }
   await page.screenshot({path:path.join(root,`dist/mission${mission}-ending.png`)});
   await page.goto(origin+`/?campaign=terran0${mission}`);
   await page.waitForSelector('#campaign-briefing:not([hidden])',{timeout:60000});await page.locator('#brief-start').tap();await page.waitForFunction(()=>window.__bw?.x.openbw_frame()>20);await driver(page);
   await page.evaluate(async mission=>{const t=window.aiTest;const targets=t.units().filter(u=>mission===2?/Raynor/.test(u.name):u.owner===1);for(const u of targets)t.x.openbw_debug_kill(u.id);await t.advance(2500);},mission);
   report['mission'+mission+'Defeat']=await page.evaluate(()=>window.aiTest.status());assert.equal(report['mission'+mission+'Defeat'].outcome,2);
   report.checks.push('Mission '+mission+' defeat trigger fires after controlled destruction of the protected hero/base.');
  }
  assert.deepEqual(report.errors,[]);
 }finally{await browser.close();server.close();fs.writeFileSync(path.join(root,'validation/campaign-ai.json'),JSON.stringify(report,null,2));}
})().catch(e=>{console.error(e);process.exitCode=1;});

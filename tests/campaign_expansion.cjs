// Requires external classic MPQs and locally exported campaign bundles.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game'),report={checks:[],missions:{},errors:[]};let mission='terran04';
const server=http.createServer((req,res)=>{const p=decodeURIComponent(new URL(req.url,'http://local').pathname),match=p.match(/^\/(data|interface|music|mission)\/(.*)$/),dirs={data:'/tmp/openbw-test-data',interface:'/tmp/openbw-interface-v14',music:'/tmp/openbw-music-v14',mission:'/tmp/'+mission+'-bundle'},file=match?path.join(dirs[match[1]],match[2]):path.join(assets,p==='/'?'index.html':p);if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}res.writeHead(200,{'Content-Type':({'.wasm':'application/wasm','.js':'text/javascript','.html':'text/html','.css':'text/css'})[path.extname(file)]||'application/octet-stream'});fs.createReadStream(file).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
try{for(mission of (process.env.OPENBW_MISSIONS||'terran04,zerg01,protoss01').split(',')){
 const page=await browser.newPage({viewport:{width:640,height:480},isMobile:true,hasTouch:true});let errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'||/fatal|unknown trigger/.test(m.text()))console.log(mission,m.text());});
 await page.goto(base+'/?campaign='+mission);
 try{await page.waitForFunction(()=>window.openbwBriefingArtStats?.().phase==='ready',null,{timeout:60000});
 await page.waitForFunction(()=>window.openbwCampaignStats?.().decodedVoices>0,null,{timeout:15000});
 await page.screenshot({path:path.join(root,'dist/v15-'+mission+'-brief.png')});
 await page.locator('#brief-start').tap();await page.waitForFunction(()=>window.__bw?.x.openbw_frame()>10,null,{timeout:15000});
 async function driver(){await page.evaluate(mission=>{const {x,memory,lockstep}=__bw;const owner={terran04:0,zerg01:3,protoss01:7}[mission];
 const str=p=>{const a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};
 const units=()=>str(x.openbw_debug_units()).trim().split('\n').map(r=>{const a=r.split('\t');return{id:+a[0],name:a[1],owner:+a[2],x:+a[3],y:+a[4],order:+a[5]};});
 const u16=n=>[n&255,n>>8&255],send=rows=>{const bytes=new Uint8Array(rows.flatMap(r=>[...u16(r.length),...r]));new Uint8Array(memory.buffer,x.openbw_in_ptr(bytes.length),bytes.length).set(bytes);x.openbw_apply(owner,bytes.length);};
 const select=id=>send([[9,1,...u16(id)]]);
 const advance=async n=>{openbwAndroidSuspend();for(let i=0;i<n&&!x.openbw_outcome();i++){lockstep.tick();if(i%100===0)await new Promise(r=>setTimeout(r,0));}openbwAndroidResume();};
 const dump=id=>{x.openbw_debug_select(id,0);return str(x.openbw_debug_dump());};
 const build=async(type,name,order)=>{const before=new Set(units().map(u=>u.id));const worker=units().find(u=>u.owner===owner&&/^(Drone|Probe)$/.test(u.name));if(!worker)throw Error('No worker');let found=false;
 outer:for(let r=2;r<12;r++)for(let dy=-r;dy<=r;dy++)for(let dx=-r;dx<=r;dx++){if(Math.max(Math.abs(dx),Math.abs(dy))!==r)continue;const tx=Math.floor(worker.x/32)+dx,ty=Math.floor(worker.y/32)+dy;if(tx<1||ty<1)continue;select(worker.id);send([[12,order,...u16(tx),...u16(ty),...u16(type)]]);await advance(1);const u=units().find(u=>u.id===worker.id);if(u&&(u.order===order||(order===25&&u.order===26)||u.name===name)){found=true;break outer;}}
 if(!found)throw Error('No build site: '+name);for(let f=0;f<900;f++){await advance(1);const u=units().find(u=>u.owner===owner&&u.name===name&&(!before.has(u.id)||u.id===worker.id));if(u&&dump(u.id).includes('completed=1 '))return u;}throw Error('Build incomplete: '+name);};
 const doodads=()=>str(x.openbw_debug_doodads()).trim().split('\n').map(r=>{const a=r.split('\t').map(Number);return{id:a[0],type:a[1],x:a[2],y:a[3],disabled:a[4],noCollide:a[5],order:a[6]};});
 window.ct={x,str,units,owner,send,select,u16,build,doodads,status:()=>({frame:x.openbw_frame(),outcome:x.openbw_outcome(),units:units(),ai:str(x.openbw_campaign_ai()),error:str(x.openbw_campaign_ai_error()),campaign:openbwCampaignStats(),art:openbwClassicStats()}),advance};},mission);}
 await driver();
 const initial=await page.evaluate(()=>ct.status());console.log('INITIAL',mission,initial.frame,initial.ai,initial.units.length);report.missions[mission]={initial};
 await page.evaluate(()=>ct.advance(6000));const after=await page.evaluate(()=>ct.status());report.missions[mission].after=after;console.log('AFTER',mission,after.frame,after.outcome,after.ai,after.error);assert.equal(after.error,'');assert.equal(after.outcome,0);assert.deepEqual(after.campaign.missing,[]);assert.deepEqual(errors,[]);await page.screenshot({path:path.join(root,'dist/v15-'+mission+'-game.png')});

 if(mission==='terran04'){
  report.missions[mission].interactions=await page.evaluate(async()=>{
   const hero=ct.units().find(u=>/Raynor/.test(u.name));if(!hero)throw Error('Raynor missing');
   const before=ct.doodads();ct.x.openbw_debug_warp(hero.id,3500,3760);await ct.advance(250);
   const afterDoor=ct.doodads(),opened=afterDoor.filter(d=>d.type===207&&d.noCollide&&before.some(b=>b.id===d.id&&!b.noCollide));if(!opened.length)throw Error('Door 1 did not open: '+JSON.stringify({hero:ct.units().find(u=>u.id===hero.id),before:before.filter(d=>d.x>3300&&d.y>3500),after:afterDoor.filter(d=>d.x>3300&&d.y>3500)}));
   ct.x.openbw_debug_warp(hero.id,3216,256);await ct.advance(200);const teleported=ct.units().find(u=>u.id===hero.id);if(!teleported||Math.abs(teleported.x-1008)>120||Math.abs(teleported.y-288)>100)throw Error('Teleport 2 failed: '+JSON.stringify(teleported));
   ct.x.openbw_debug_warp(hero.id,1488,2032);await ct.advance(400);const traps=ct.doodads().filter(d=>d.type===209&&d.disabled);if(traps.length<4)throw Error('Defense deactivation trigger failed');
   ct.x.openbw_debug_warp(hero.id,2448,2016);await ct.advance(3000);return {opened,teleported,traps:traps.length,ending:ct.status()};
  });assert.equal(report.missions[mission].interactions.ending.outcome,1);
  report.checks.push('Terran 4 original door, teleport, defense shutdown and plans/Victory triggers run after diagnostic movement.');
 }else{
  report.missions[mission].construction=await page.evaluate(async()=>{ct.x.openbw_test_money();ct.x.openbw_test_instant(1);if(ct.owner===3){const pool=await ct.build(142,'Spawning Pool',25),den=await ct.build(135,'Hydralisk Den',25);return {pool,den};}const nexus=ct.units().find(u=>u.name==='Nexus'),scout=ct.units().find(u=>u.owner===ct.owner&&u.name==='Zealot');if(!nexus||!scout)throw Error('Rescue targets missing');ct.x.openbw_debug_warp(scout.id,nexus.x,nexus.y+64);await ct.advance(120);const rescued=ct.units().find(u=>u.id===nexus.id);if(rescued.owner!==ct.owner)throw Error('Nexus rescue failed: '+JSON.stringify({nexus:rescued,scout:ct.units().find(u=>u.id===scout.id)}));ct.select(nexus.id);ct.send([[31,...ct.u16(64)]]);await ct.advance(120);return {rescued,pylon:await ct.build(156,'Pylon',31)};});
  if(mission==='zerg01'){await page.evaluate(()=>ct.advance(4000));const waves=await page.evaluate(()=>ct.status());report.missions[mission].waves=waves;assert.equal(waves.error,'');assert(+waves.ai.trim().split('\t')[4]>0,'Original Zerg 1 enemy AI must dispatch a wave');}
  await page.evaluate(async()=>{const enemy=ct.owner===3?5:0;for(const u of ct.units().filter(u=>u.owner===enemy))ct.x.openbw_debug_kill(u.id);await ct.advance(3000);});
  report.missions[mission].victory=await page.evaluate(()=>ct.status());assert.equal(report.missions[mission].victory.outcome,1);assert.equal(report.missions[mission].victory.error,'');
  report.checks.push(mission+': construction completes and original Victory trigger runs after controlled enemy destruction.');
 }
 // Fresh scenario: test original defeat trigger, without setting outcome directly.
 await page.goto(base+'/?campaign='+mission);await page.waitForFunction(()=>window.openbwBriefingArtStats?.().phase==='ready',null,{timeout:60000});await page.locator('#brief-start').tap();await page.waitForFunction(()=>window.__bw?.x.openbw_frame()>10);await driver();
 await page.evaluate(async()=>{const targets=ct.units().filter(u=>ct.owner===0?/Raynor/.test(u.name):ct.owner===7?/Fenix/.test(u.name):u.owner===ct.owner);if(!targets.length)throw Error('Defeat targets missing');for(const u of targets)ct.x.openbw_debug_kill(u.id);await ct.advance(7000);});
 report.missions[mission].defeat=await page.evaluate(()=>ct.status());assert.equal(report.missions[mission].defeat.outcome,2);assert.equal(report.missions[mission].defeat.error,'');assert.deepEqual(errors,[]);report.checks.push(mission+': original defeat trigger runs.');console.log('PASS',mission);
 }catch(e){console.log('FAIL',mission,e.message);report.missions[mission]={...report.missions[mission],failure:e.message,errors,screen:await page.locator('body').innerText()};report.errors.push(mission+': '+e.message);}
 await page.close();
}console.log('DONE',report.errors);if(report.errors.length)process.exitCode=1;
}finally{await browser.close();server.close();fs.writeFileSync(path.join(root,'validation/campaign-expansion-v15.json'),JSON.stringify(report,null,2));}
})().catch(e=>{console.error(e);process.exitCode=1;});

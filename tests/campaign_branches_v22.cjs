// Private original game files are supplied externally; none are bundled.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game'),catalog=JSON.parse(fs.readFileSync(path.join(root,'missions.json'))),fixtures=process.env.OPENBW_V22_FIXTURES||'/tmp/openbw-v22-fixtures';
let mission='zerg02';const report={missions:{},checks:[],errors:[]};
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
 await p.evaluate(owner=>{
  const{x,memory,lockstep}=__bw,str=p=>{const a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};
  const units=()=>str(x.openbw_debug_units()).trim().split('\n').filter(Boolean).map(r=>{const a=r.split('\t');return{id:+a[0],name:a[1],owner:+a[2],x:+a[3],y:+a[4],order:+a[5]};});
  const u16=n=>[n&255,n>>8&255],send=rows=>{const bytes=new Uint8Array(rows.flatMap(r=>[...u16(r.length),...r]));new Uint8Array(memory.buffer,x.openbw_in_ptr(bytes.length),bytes.length).set(bytes);x.openbw_apply(owner,bytes.length);};
  const select=ids=>{send([[9,ids.length,...ids.flatMap(u16)]]);ids.forEach((id,i)=>x.openbw_debug_select(id,i?1:0));};
  const advance=async(n,heal=false)=>{openbwAndroidSuspend();for(let i=0;i<n&&!x.openbw_outcome();i++){if(heal&&i%60===0)for(const u of units().filter(u=>u.owner===owner))x.openbw_debug_set_life(u.id,10000,-1);lockstep.tick();if(i%120===0)await new Promise(r=>setTimeout(r,0));}openbwAndroidResume();};
  window.ct={x,str,units,owner,send,u16,select,advance};
 },catalog.find(m=>m.id===id).player);
}
async function select(p,name,owner){await p.evaluate(({name,owner})=>{const u=ct.units().find(u=>u.name===name&&(owner===null||u.owner===(owner??ct.owner)));if(!u)throw Error('Missing '+name);ct.select([u.id]);}, {name,owner});await p.waitForTimeout(150);}
async function resume(p){await p.evaluate(()=>{for(let i=0;i<4&&openbwMenuStats().opened;i++)openbwBack();});}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
try{
 for(const task of [{id:'expterran04',target:'Physics Lab',next:'expterran05a'},{id:'expterran04',target:'Nuclear Silo',next:'expterran05b'},{id:'expzerg03',next:'expzerg04a'},{id:'expprotoss06',next:'expprotoss07'},{id:'expterran07',intro:true}]){
  const p=await browser.newPage({viewport:{width:1280,height:960},hasTouch:true});p.on('pageerror',e=>report.errors.push(e.message));
  await boot(p,base,task.id);await p.evaluate(()=>ct.advance(2400,true));assert.equal(await p.evaluate(()=>ct.x.openbw_outcome()),0);
  const name=task.id+(task.target?'-'+task.target.replaceAll(' ',''):''),entry=report.missions[name]={};
  if(task.intro){entry.duran=await p.evaluate(()=>ct.units().filter(u=>u.owner===ct.owner&&/Duran/.test(u.name)));assert.equal(entry.duran.length,1,'Duran is created during his original entrance');}
  else{
   entry.action=await p.evaluate(task=>{if(task.target){const a=ct.units().filter(u=>u.name===task.target&&u.owner!==ct.owner);if(!a.length)throw Error('Missing target '+task.target);for(const u of a)ct.x.openbw_debug_kill(u.id);return{destroyed:a.length};}
    if(task.id==='expzerg03'){ct.x.openbw_debug_resources(10000,1000);return{minerals:10000};}
    const probe=ct.units().find(u=>u.owner===ct.owner&&u.name==='Probe');ct.x.openbw_debug_warp(probe.id,3728,3455);return{probe:probe.id};},task);
   await p.evaluate(()=>ct.advance(6000,true));await p.waitForTimeout(200);
   entry.result=await p.evaluate(()=>({outcome:ct.x.openbw_outcome(),next:openbwCampaignStats().nextMission,scenario:openbwCampaignStats().nextScenario,error:openbwCampaignStats().aiError}));
   assert.equal(entry.result.outcome,1,'Original objective trigger reaches Victory');assert.equal(entry.result.next,task.next);assert.equal(entry.result.error,'');
  }
  console.log('PASS',name,entry);await p.close();
 }
 assert.deepEqual(report.errors,[]);report.checks.push('Original T4 Physics Lab/Nuclear Silo branches, Z3 Exact(0) infestation branch, P6 Khalis ground location, and T7 Duran entrance. Diagnostic movement/resources/combat used; objectives and outcome triggers are original.');
}finally{fs.writeFileSync(path.join(root,'validation/campaign-branches-v22.json'),JSON.stringify(report,null,2));await browser.close();server.close();}})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

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
    const send=rows=>{const bytes=new Uint8Array(rows.flatMap(r=>[...u16(r.length),...r]));const p=x.openbw_in_ptr(bytes.length);new Uint8Array(memory.buffer,p,bytes.length).set(bytes);x.openbw_apply(window.testOwner,bytes.length);};
    const units=()=>str(x.openbw_debug_units()).trim().split('\n').map(r=>{const a=r.split('\t');return{id:+a[0],name:a[1],owner:+a[2],x:+a[3],y:+a[4],order:+a[5]};});
    const select=ids=>send([[9,ids.length,...ids.flatMap(u16)]]);
    const order=(kind,x,y,target=0)=>send([[21,...u16(x),...u16(y),...u16(target),...u16(228),kind,0]]);
    const advance=async n=>{window.openbwAndroidSuspend();for(let i=0;i<n&&!x.openbw_outcome();i++){lockstep.tick();if(i%40===0)await new Promise(r=>setTimeout(r,0));}window.openbwAndroidResume();};
    window.testOwner=units().find(u=>u.owner<8).owner;
    const dump=id=>{x.openbw_debug_select(id,0);return str(x.openbw_debug_dump());};
    const status=id=>{x.openbw_debug_select(id,0);return str(x.openbw_status());};
    const build=async(type,name,order=30)=>{
      const before=new Set(units().map(u=>u.id));const worker=units().find(u=>u.owner===window.testOwner&&/^(SCV|Probe|Drone)$/.test(u.name));
      const tx=Math.floor(worker.x/32),ty=Math.floor(worker.y/32);let ok=false;
      outer:for(let radius=2;radius<12;radius++)for(let dy=-radius;dy<=radius;dy++)for(let dx=-radius;dx<=radius;dx++){
        if(Math.max(Math.abs(dx),Math.abs(dy))!==radius)continue;
        const a=tx+dx,b=ty+dy;if(a<1||b<1||a>=61||b>=61)continue;
        select([worker.id]);send([[12,order,...u16(a),...u16(b),...u16(type)]]);await advance(1);
        const current=units().find(u=>u.id===worker.id);
        if(current && (current.order===order || (order===25 && current.order===26) || current.name===name)){ok=true;break outer;}
      }
      if(!ok)throw Error('No build site for '+name);
      let created=null,first=null;
      for(let n=0;n<700;n++){
        await advance(1);created=units().find(u=>u.owner===window.testOwner&&u.name===name&&(!before.has(u.id)||u.id===worker.id));
        if(created){if(first===null)first=x.openbw_frame();if(dump(created.id).includes('completed=1 '))return {...created,buildFrames:x.openbw_frame()-first};}
      }
      throw Error('Build did not complete: '+name+' '+(created?dump(created.id):JSON.stringify(units())));
    };
    window.testMission={str,send,u16,units,select,order,advance,dump,status,build};
  });
}
(async()=>{
 fs.mkdirSync(path.join(root,'dist'),{recursive:true});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME||'/tmp/openbw-browser/chrome-headless-shell-linux64/chrome-headless-shell',headless:true,args:['--no-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:900,height:412},hasTouch:true,isMobile:true});page.on('pageerror',e=>{report.errors.push(e.message);console.log('ERROR',e.message)});
 async function game(race){await page.goto(origin);await page.locator('#slots select').first().selectOption(String(race));await page.locator('#start-game').click();await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>4);await installDriver(page);await page.evaluate(()=>{window.__bw.x.openbw_test_money();window.__bw.x.openbw_test_instant(1);});}
 await game(1);
 report.terran=await page.evaluate(async()=>{
   const t=window.testMission,x=window.__bw.x,own=window.testOwner;
   const cc=t.units().find(u=>u.owner===own&&u.name==='Command Center');const before=t.units().filter(u=>u.owner===own&&u.name==='SCV').length;
   t.select([cc.id]);t.send([[31,...t.u16(7)]]);await t.advance(40);
   const trained=t.units().filter(u=>u.owner===own&&u.name==='SCV').length;
   if(trained!==before+1)throw Error('Instant SCV training failed');
   const depot=await t.build(109,'Supply Depot'),bay=await t.build(122,'Engineering Bay');
   t.select([bay.id]);t.send([[50,0]]);
   const upgradeStart=t.dump(bay.id);await t.advance(40);const upgradeEnd=t.dump(bay.id),upgradeStatus=t.status(bay.id);
   const barracks=await t.build(111,'Barracks'),academy=await t.build(112,'Academy');
   t.select([academy.id]);t.send([[48,0]]);const researchStart=t.dump(academy.id);
   await t.advance(40);const researchEnd=t.dump(academy.id),researchStatus=t.status(academy.id);
   x.openbw_test_instant(0);t.select([cc.id]);t.send([[31,...t.u16(7)]]);await t.advance(40);
   const normalTraining=t.units().filter(u=>u.owner===own&&u.name==='SCV').length,normalStatus=t.status(cc.id);
   return {trained,before,depot,bay,barracks,academy,upgradeStart,upgradeEnd,upgradeStatus,researchStart,researchEnd,researchStatus,normalTraining,normalStatus};
 });console.log('TERRAN',JSON.stringify(report.terran));
 assert.match(report.terran.upgradeStart,/order=76 /);assert.doesNotMatch(report.terran.upgradeEnd,/order=76 /);assert.equal(report.terran.upgradeStatus,'');
 assert.match(report.terran.researchStart,/order=75 /);assert.doesNotMatch(report.terran.researchEnd,/order=75 /);assert.equal(report.terran.researchStatus,'');
 assert.match(report.terran.normalStatus,/SCV/);
 report.checks.push('Terran construction, SCV training, infantry armor upgrade, Stim research finish; disabling restores normal training');
 await game(2);
 report.protoss=await page.evaluate(async()=>{
   const t=window.testMission;const pylon=await t.build(156,'Pylon',31);
   return {pylon,dump:t.dump(pylon.id)};
 });assert(report.protoss.pylon.buildFrames<180);assert.match(report.protoss.dump,/completed=1 /);
 await page.waitForFunction(()=>window.openbwPortraitStats().surfaces[0].frames>0);
 report.protossPortrait=await page.evaluate(()=>window.openbwPortraitStats());report.checks.push('Protoss warp-in completes through normal animation and displays original portrait');
 await game(0);
 report.zerg=await page.evaluate(async()=>{
   const t=window.testMission,x=window.__bw.x,own=window.testOwner;
   const larva=t.units().find(u=>u.owner===own&&u.name==='Larva'),before=t.units().filter(u=>u.owner===own&&u.name==='Drone').length;
   t.select([larva.id]);t.send([[35,...t.u16(41)]]);await t.advance(120);
   const trained=t.units().filter(u=>u.owner===own&&u.name==='Drone').length;
   if(trained!==before+1)throw Error('Instant Zerg morph failed');
   const pool=await t.build(142,'Spawning Pool',25);return {trained,before,pool,dump:t.dump(pool.id)};
 });assert.match(report.zerg.dump,/completed=1 /);await page.waitForFunction(()=>window.openbwPortraitStats().surfaces[0].frames>0);
 report.zergPortrait=await page.evaluate(()=>window.openbwPortraitStats());report.checks.push('Zerg Drone and Spawning Pool morphs complete through normal engine paths');
 assert.deepEqual(report.errors,[]);fs.writeFileSync(path.join(root,'dist/production-testing.json'),JSON.stringify(report,null,2));console.log('PASS',JSON.stringify(report,null,2));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

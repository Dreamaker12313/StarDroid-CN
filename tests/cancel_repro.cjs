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
 fs.mkdirSync(path.join(root,'dist'),{recursive:true});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME||'/tmp/openbw-browser/chrome-headless-shell-linux64/chrome-headless-shell',headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:900,height:412},hasTouch:true,isMobile:true});
  page.on('console',m=>{if(m.type()==='error') console.log(m.text());});
  page.on('pageerror',e=>console.log('PAGEERROR',e.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/?campaign=terran01`);
  await page.locator('#brief-start').click();await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>4);
  await installDriver(page);
  const before=await page.evaluate(async()=>{
   const t=window.testMission,x=window.__bw.x;await t.advance(800);x.openbw_debug_resources(1000,0);
   const w=t.units().find(u=>u.owner===1&&u.name==='SCV');x.openbw_debug_select(w.id,0);await t.advance(3);
   let tile=null;
   outer:for(let y=4;y<10;y++)for(let a=5;a<12;a++){
    t.select([w.id]);t.send([[12,30,...t.u16(a),...t.u16(y),...t.u16(109)]]);await t.advance(1);
    if(t.units().find(u=>u.id===w.id).order===30){tile=[a,y];break outer;}
   }
   if(!tile)throw Error('No valid depot location');window.cancelWorker=w.id;
   return {tile,worker:t.units().find(u=>u.id===w.id),status:t.str(x.openbw_status()),frame:window.openbwAndroidStats().frame};
  });console.log('BEFORE',JSON.stringify(before));
  await page.locator('#status .q').first().click();
  console.log('AFTER CANCEL',await page.evaluate(()=>({status:window.testMission.str(window.__bw.x.openbw_status()),worker:window.testMission.units().find(u=>u.id===window.cancelWorker)})));
  await page.evaluate(()=>window.testMission.advance(900));
  const after=await page.evaluate(()=>({status:window.testMission.str(window.__bw.x.openbw_status()),frame:window.openbwAndroidStats().frame,units:window.testMission.units(),resources:window.testMission.str(window.__bw.x.openbw_resources()),ui:window.openbwClassicStats()}));
  assert.equal(after.status,'');assert(after.frame>=before.frame+900);assert.notEqual(after.units.find(u=>u.id===before.worker.id).order,30);assert.equal(after.resources.split('\t')[0],'1000');
  assert.equal(after.units.filter(u=>u.name==='Supply Depot' && u.owner===1).length,1);
  await page.screenshot({path:path.join(root,'dist/classic-console.png')});
  await page.evaluate(async tile=>{const t=window.testMission;t.select([window.cancelWorker]);t.send([[12,30,...t.u16(tile[0]),...t.u16(tile[1]),...t.u16(109)]]);await t.advance(1500);},before.tile);
  const rebuilt=await page.evaluate(()=>window.testMission.units().filter(u=>u.name==='Supply Depot' && u.owner===1));assert.equal(rebuilt.length,2);
  const depot=rebuilt.find(u=>u.x<600);await page.evaluate(id=>{window.__bw.x.openbw_debug_select(id,0);},depot.id);
  await page.waitForTimeout(80);
  assert.match(await page.locator('#unit-life').innerText(),/500\/500/);
  await page.screenshot({path:path.join(root,'dist/classic-depot.png')});
  fs.writeFileSync(path.join(root,'dist/cancel-regression.json'),JSON.stringify({before,after,rebuild:rebuilt,checks:['Actual depot queue chip canceled through touch UI','900 further frames without abort','No depot created and no resources charged','Same SCV subsequently builds a complete Supply Depot']},null,2));
  console.log('PASS: canceled construction, simulation continued, SCV rebuilt depot successfully.');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close()});

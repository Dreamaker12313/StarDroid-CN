const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game');
const report={checks:[],errors:[],logs:[]};
const server=http.createServer((req,res)=>{
 const p=decodeURIComponent(new URL(req.url,'http://local').pathname);
 if(p==='/music/manifest.json'){res.writeHead(200,{'Content-Type':'application/json'});return res.end(JSON.stringify({format:'openbw-music-bundle-v1',entries:[]}));}
 const file=p.startsWith('/interface/')?path.join('/tmp/openbw-interface-v17',p.slice(11)):p.startsWith('/data/')?path.join(process.env.OPENBW_TEST_MPQS||'/tmp/openbw-test-data',p.slice(6)):p.startsWith('/mission/')?path.join(process.env.OPENBW_MISSION_BUNDLE||'/tmp/terran01-bundle',p.slice(9)):path.join(assets,p==='/'?'index.html':p);
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
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
 const page=await browser.newPage({viewport:{width:640,height:480},hasTouch:true,isMobile:true});page.on('pageerror',e=>report.errors.push(e.message));
 await page.goto('http://127.0.0.1:'+server.address().port+'/?campaign=terran01');await page.waitForFunction(()=>window.openbwBriefingArtStats?.().phase==='ready',null,{timeout:90000});await page.locator('#brief-start').tap();await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>5);await installDriver(page);
 const site=await page.evaluate(async()=>{const t=testMission,{x}=__bw;await t.advance(800);x.openbw_debug_resources(1000,0);const w=t.units().find(u=>u.owner===1&&u.name==='SCV');window.buildWorker=w.id;
 let tile=null;outer:for(let y=4;y<10;y++)for(let a=5;a<12;a++){t.select([w.id]);t.send([[12,30,...t.u16(a),...t.u16(y),...t.u16(109)]]);await t.advance(1);if(t.units().find(u=>u.id===w.id).order===30){tile=[a,y];break outer;}}
 if(!tile)throw Error('No buildable test site');x.openbw_debug_select(w.id,0);return{tile,worker:w};});
 await page.waitForFunction(()=>document.querySelector('#status .q'));await page.locator('#status .q').first().tap();await page.waitForTimeout(150);
 await page.evaluate(()=>{const{x}=__bw;x.openbw_pan(-65536,-65536);x.openbw_debug_select(buildWorker,0);});await page.waitForTimeout(150);
 const choose=async()=>{await page.locator('#card .cmd[aria-label="Build"]').tap();await page.locator('#card .cmd[aria-label^="Supply Depot"]').tap();await page.waitForFunction(()=>__bw.x.openbw_cursor()===2);};
 await choose();const before=await page.evaluate(()=>({money:testMission.str(__bw.x.openbw_resources()),units:testMission.units(),frame:__bw.x.openbw_frame()}));
 const pos={x:site.tile[0]*32+48,y:site.tile[1]*32+32+48};
 const cdp=await page.context().newCDPSession(page);const touch=async(type,points)=>{await cdp.send('Input.dispatchTouchEvent',{type,touchPoints:points.map(([x,y],id)=>({x,y,id,radiusX:1,radiusY:1,force:1}))});await page.waitForTimeout(60);};
 await touch('touchStart',[[pos.x-20,pos.y-20]]);await touch('touchMove',[[pos.x,pos.y]]);await touch('touchEnd',[]);
 assert(await page.locator('#touch-build-confirm').isVisible());assert.equal(await page.evaluate(()=>__bw.x.openbw_cursor()),2);
 assert.equal(await page.evaluate(()=>testMission.str(__bw.x.openbw_resources())),before.money);const preview=await page.evaluate(()=>openbwTouchStats().placement);assert.equal(preview.y,pos.y-48);
 await page.screenshot({path:'/tmp/openbw-reference/v17/touch-preview.png'});await page.locator('#touch-build-cancel').tap();await page.waitForFunction(()=>__bw.x.openbw_cursor()!==2);assert.equal(await page.evaluate(()=>testMission.str(__bw.x.openbw_resources())),before.money);
 await choose();await page.touchscreen.tap(pos.x,pos.y);await page.locator('#touch-build-confirm').tap();await page.waitForFunction(()=>__bw.x.openbw_cursor()!==2);
 await page.evaluate(()=>testMission.advance(1500));const after=await page.evaluate(()=>({money:testMission.str(__bw.x.openbw_resources()),units:testMission.units(),frame:__bw.x.openbw_frame()}));
 assert.equal(after.units.filter(u=>u.owner===1&&u.name==='Supply Depot').length,before.units.filter(u=>u.owner===1&&u.name==='Supply Depot').length+1);assert.equal(+after.money.split('\t')[0],+before.money.split('\t')[0]-100);
 report.checks.push('Real touch drag leaves ghost 48 physical pixels above finger; release issues no build/spend; cancel is free; separate Build confirmation completes one depot and charges exactly 100 minerals');report.preview=preview;report.before=before;report.after=after;assert.deepEqual(report.errors,[]);console.log('PASS',report.checks);
 }catch(e){report.failure=e.stack;throw e;}finally{fs.writeFileSync(path.join(root,'validation/touch-building-v17.json'),JSON.stringify(report,null,2));await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

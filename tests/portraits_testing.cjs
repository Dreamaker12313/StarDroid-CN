// Historical v0.7 UI selectors; use tests/original_ui.cjs for the current interface.
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
 fs.mkdirSync(path.join(root,'dist'),{recursive:true});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME||'/tmp/openbw-browser/chrome-headless-shell-linux64/chrome-headless-shell',headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try {
  const page=await browser.newPage({viewport:{width:900,height:412},hasTouch:true,isMobile:true});
  page.on('pageerror',e=>{report.errors.push(e.message);console.log('ERROR',e.message);});
  await page.goto(origin+'/?campaign=terran01');
  await page.waitForFunction(()=>window.openbwPortraitStats?.().surfaces[1].frames>0);
  report.briefing=await page.evaluate(()=>window.openbwPortraitStats());
  await page.screenshot({path:path.join(root,'dist/v07-briefing.png')});
  await page.locator('#brief-play').tap();
  await page.waitForFunction(()=>window.openbwPortraitStats().surfaces[1].talking && /Tlk/i.test(window.openbwPortraitStats().surfaces[1].file));
  await page.evaluate(()=>window.openbwAndroidSuspend());await page.waitForTimeout(100);
  const paused=await page.evaluate(()=>window.openbwPortraitStats());await page.waitForTimeout(300);
  assert.equal((await page.evaluate(()=>window.openbwPortraitStats())).draws,paused.draws);
  await page.evaluate(()=>window.openbwAndroidResume());
  await page.locator('#brief-next').tap();
  await page.waitForFunction(()=>/UDuke/i.test(window.openbwPortraitStats().surfaces[1].file));
  report.duke=await page.evaluate(()=>window.openbwPortraitStats());
  report.checks.push('Original Adjutant and Duke portraits; speech animates; native pause freezes frames');
  await page.locator('#brief-start').tap();await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>4);await installDriver(page);
  await page.evaluate(async()=>{const t=window.testMission;await t.advance(900);const u=t.units().find(u=>u.name==='SCV'&&u.owner===1);window.testWorker=u.id;window.__bw.x.openbw_debug_select(u.id,0);});
  await page.waitForFunction(()=>/tSCV/i.test(window.openbwPortraitStats().surfaces[0].file));
  const f=await page.evaluate(()=>window.openbwPortraitStats().draws);await page.waitForFunction(n=>window.openbwPortraitStats().draws>n+3,f);
  report.scv=await page.evaluate(()=>window.openbwPortraitStats());
  await page.screenshot({path:path.join(root,'dist/v07-scv.png')});
  await page.locator('#settingsbtn').tap();await page.locator('#menu-options').tap();await page.locator('#menu-testing').tap();
  const before=await page.evaluate(()=>window.testMission.str(window.__bw.x.openbw_resources()).split('\t').map(Number));
  await page.locator('#test-money').tap();
  const after=await page.evaluate(()=>window.testMission.str(window.__bw.x.openbw_resources()).split('\t').map(Number));
  assert.equal(after[0],before[0]+10000);assert.equal(after[1],before[1]+10000);
  await page.locator('#test-instant').check();
  await page.evaluate(()=>openbwBack());await page.locator('#menu-game-options').tap();
  await page.locator('#opt-speed').selectOption('2.625');
  await page.evaluate(()=>{openbwBack();openbwBack();openbwBack();});
  assert.equal(await page.evaluate(()=>window.openbwTestingStats().speed),16);
  const speedStart=await page.evaluate(()=>window.openbwAndroidStats().frame);await page.waitForTimeout(500);
  const speedEnd=await page.evaluate(()=>window.openbwAndroidStats().frame);assert(speedEnd-speedStart>50);
  report.speed={framesInHalfSecond:speedEnd-speedStart};
  await page.locator('#settingsbtn').tap();await page.locator('#menu-options').tap();await page.locator('#menu-game-options').tap();
  await page.locator('#opt-speed').selectOption('42');
  await page.screenshot({path:path.join(root,'dist/v07-testing.png')});
  await page.evaluate(()=>{openbwBack();openbwBack();openbwBack();});
  report.depot=await page.evaluate(async()=>{
    const t=window.testMission,x=window.__bw.x;let tile=null;
    outer:for(let y=4;y<10;y++)for(let a=5;a<12;a++){
      t.select([window.testWorker]);t.send([[12,30,...t.u16(a),...t.u16(y),...t.u16(109)]]);await t.advance(1);
      if(t.units().find(u=>u.id===window.testWorker).order===30){tile=[a,y];break outer;}
    }
    if(!tile)throw Error('No depot tile');const start=x.openbw_frame();let foundation=null,completed=null;
    for(let i=0;i<400;i++){
      await t.advance(1);const depot=t.units().find(u=>u.owner===1&&u.name==='Supply Depot'&&u.x<600);
      if(depot){if(foundation===null)foundation=x.openbw_frame();x.openbw_debug_select(depot.id,0);
        const dump=t.str(x.openbw_debug_dump());if(dump.includes('completed=1 ')){completed=x.openbw_frame();break;}}
    }
    return {tile,start,foundation,completed};
  });
  assert(report.depot.completed!==null);assert(report.depot.completed-report.depot.foundation<12);
  report.checks.push('Money button grants 10,000/10,000; 16× speed advances faster; SCV builds full-health depot within 12 frames of foundation');
  await page.locator('#settingsbtn').tap();await page.locator('#menu-options').tap();await page.locator('#menu-testing').tap();await page.locator('#test-reset').tap();
  assert.deepEqual(await page.evaluate(()=>window.openbwTestingStats()),{instant:false,used:true,frameMs:42,speed:1});
  assert.equal(await page.locator('#go-replay').isDisabled(),true);
  await page.locator('#test-reveal').tap();
  report.checks.push('Reset disables instant production and restores speed; cheat-altered replays disabled');
  assert.deepEqual(report.errors,[]);
  fs.writeFileSync(path.join(root,'dist/portraits-testing.json'),JSON.stringify(report,null,2));console.log('PASS',JSON.stringify(report,null,2));
 } finally {await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

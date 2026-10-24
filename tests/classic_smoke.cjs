// Historical v0.4 UI harness. For the v0.7 menu/console/music flow use interface_smoke.cjs.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game');
const report={checks:[],errors:[],logs:[]};
const server=http.createServer((req,res)=>{
 const p=decodeURIComponent(new URL(req.url,'http://local').pathname);
 const file=p.startsWith('/data/')?path.join(process.env.OPENBW_TEST_MPQS||'/tmp/openbw-test-data',p.slice(6)):p.startsWith('/music/')?path.join(process.env.OPENBW_MUSIC_BUNDLE||'/tmp/openbw-music-fixture',p.slice(7)):p.startsWith('/mission/')?path.join(process.env.OPENBW_MISSION_BUNDLE||'/tmp/terran01-bundle',p.slice(9)):path.join(assets,p==='/'?'index.html':p);
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
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME||'/tmp/openbw-browser/chrome-headless-shell-linux64/chrome-headless-shell',headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
  const context=await browser.newContext({viewport:{width:900,height:412},hasTouch:true,isMobile:true});
  const page=await context.newPage();page.on('pageerror',e=>{report.errors.push(e.message);console.log('ERROR',e.message)});
  page.on('console',m=>{if(m.type()==='error')console.log('CONSOLE',m.text());});page.on('worker',w=>w.on('console',m=>console.log('WORKER',m.text())));
  await page.route('**/*',route=>{assert(route.request().url().startsWith(origin+'/') || route.request().url().startsWith('blob:'));return route.continue();});
  await page.goto(origin+'/?campaign=terran01');
  await page.waitForSelector('#campaign-briefing:not([hidden])');
  await page.waitForFunction(()=>window.openbwMusicStats?.().playing && window.openbwMusicStats().time>.15);
  report.originalWav=await page.evaluate(async()=>{
    const decoder=await MPQDecoder.create(),archive=await OpenBWCampaign.load('./mission/');
    const bytes=decoder.read(archive,'campaign/terran/terran01/staredit/wav/t1b00tad.wav');
    const size=bytes.length,a=new AudioContext(),buf=await a.decodeAudioData(bytes.buffer);const result={bytes:size,duration:buf.duration,channels:buf.numberOfChannels};await a.close();return result;
  });assert.equal(report.originalWav.bytes,1164692);assert(report.originalWav.duration>20);
  report.briefingMusic=await page.evaluate(()=>window.openbwMusicStats());assert.match(report.briefingMusic.track,/trdyroom/);
  await page.locator('#brief-play').tap();await page.waitForFunction(()=>window.openbwMusicStats().ducked);
  await page.evaluate(()=>window.openbwAndroidSuspend());
  const frozen=await page.evaluate(()=>window.openbwMusicStats());await page.waitForTimeout(220);assert.equal(await page.evaluate(()=>window.openbwMusicStats().time),frozen.time);assert.equal(frozen.playing,false);
  await page.evaluate(()=>window.openbwAndroidResume());await page.waitForFunction(()=>window.openbwMusicStats().playing);assert.equal(await page.evaluate(()=>window.openbwMusicStats().ducked),true);
  await page.screenshot({path:path.join(root,'dist/classic-briefing.png')});
  await page.locator('#brief-start').tap();await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>10);
  await page.waitForFunction(()=>window.openbwMusicStats().playing && /terran[12]/.test(window.openbwMusicStats().track));
  const first=await page.evaluate(()=>window.openbwMusicStats().track);
  await page.waitForFunction(name=>window.openbwMusicStats().track!==name && window.openbwMusicStats().playing,first,{timeout:15000});
  report.checks.push('Music imported by actual Java code plays in briefing, ducks voice, pauses/resumes, switches to in-game track and advances playlist');
  await page.locator('#settingsbtn').tap();await page.locator('#music-volume').fill('45');
  assert.equal(await page.evaluate(()=>window.openbwMusicStats().volume),.45);
  await page.locator('#music-track').selectOption('music\\terran1.wav');await page.waitForFunction(()=>window.openbwMusicStats().track==='music\\terran1.wav' && window.openbwMusicStats().playing);
  await page.locator('#opt-music').uncheck();assert.equal(await page.evaluate(()=>window.openbwMusicStats().playing),false);
  await page.locator('#opt-music').check();await page.waitForFunction(()=>window.openbwMusicStats().playing);
  await page.screenshot({path:path.join(root,'dist/classic-settings.png')});
  await page.locator('#settingsbtn').tap();await page.locator('#pausebtn').tap();
  const paused=await page.evaluate(()=>window.openbwMusicStats().time);await page.locator('#campaign-objectives-button').tap();await page.waitForTimeout(250);
  assert.equal(await page.evaluate(()=>window.openbwMusicStats().time),paused);assert.equal(await page.evaluate(()=>window.openbwAndroidStats().audio),'suspended');
  await page.evaluate(()=>{window.openbwAndroidSuspend();window.openbwAndroidResume();});assert.equal(await page.evaluate(()=>window.openbwMusicStats().playing),false);
  await page.locator('#campaign-objectives-close').tap();await page.locator('#pausebtn').tap();await page.waitForFunction(()=>window.openbwMusicStats().playing);
  await page.locator('#mute').tap();assert.equal(await page.evaluate(()=>window.openbwMusicStats().muted),true);await page.locator('#mute').tap();
  report.checks.push('Volume, specific track, music switch, global mute, and manual pause retained across native suspend/resume');
  await installDriver(page);await page.evaluate(async()=>{const t=window.testMission;await t.advance(800);const ids=t.units().filter(u=>u.owner===1&&/Marine|SCV/.test(u.name)).map(u=>u.id);ids.forEach((id,i)=>window.__bw.x.openbw_debug_select(id,i?1:0));});
  await page.waitForTimeout(80);await page.screenshot({path:path.join(root,'dist/classic-group.png')});
  for(const size of [{width:640,height:360},{width:900,height:412},{width:1280,height:720}]){
   await page.setViewportSize(size);await page.waitForTimeout(250);
   const boxes=await page.evaluate(()=>['card','classic-minimap','unit-info','resources'].map(id=>{const r=document.getElementById(id).getBoundingClientRect();return{id,x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};}));
   for(const b of boxes){assert(b.x>=0 && b.y>=0 && b.right<=size.width+1 && b.bottom<=size.height+1,JSON.stringify(b));}
   report.checks.push(`Console within ${size.width} × ${size.height} viewport`);
   if(size.width===640)await page.screenshot({path:path.join(root,'dist/classic-small.png')});
  }
  report.music=await page.evaluate(()=>window.openbwMusicStats());report.console=await page.evaluate(()=>window.openbwClassicStats());
  assert(report.console.originalConsole && report.console.commandIcons>=5);assert.deepEqual(report.errors,[]);
  console.log('PASS',report.checks);
 }finally{fs.writeFileSync(path.join(root,'dist/classic-smoke.json'),JSON.stringify(report,null,2));await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close()});

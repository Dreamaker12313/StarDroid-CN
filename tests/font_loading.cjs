// Real WASM startup regression with an unreadable base-MPQ font. External game
// data is copied to a temporary directory; the supplied original is untouched.
const fs=require('fs'),path=require('path'),os=require('os'),http=require('http');
const assert=require('assert/strict'),{spawnSync}=require('child_process');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game');
const base=process.env.OPENBW_TEST_MPQS||'/tmp/openbw-test-data';
const fonts=process.env.OPENBW_INTERFACE_BUNDLE||'/tmp/openbw-interface-reference';
const mission=process.env.OPENBW_MISSION_BUNDLE||'/tmp/terran03-bundle';
const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'openbw-font-regression-'));
const damaged=path.join(temporary,'STARDAT.MPQ');
const make=spawnSync('python3',[path.join(__dirname,'create_font_fault_fixture.py'),path.join(base,'STARDAT.MPQ'),damaged],{encoding:'utf8'});
if(make.status!==0)throw Error(make.stderr||make.stdout);
const baseline=!!process.env.OPENBW_EXPECT_FONT_FAILURE;
const report={checks:[],errors:[],scenarios:[]};let mode='valid';
const manifest=JSON.parse(fs.readFileSync(path.join(fonts,'manifest.json')));
const brokenBlock='/interface/blocks/'+manifest.entries.find(e=>/font8\.fnt$/.test(e.name)).block+'.bin';
const server=http.createServer((req,res)=>{
 const p=decodeURIComponent(new URL(req.url,'http://local').pathname);
 const json=value=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(value));};
 if(p==='/availability.json')return json({missions:[1]});
 if(p==='/music/manifest.json')return json({format:'openbw-music-bundle-v1',entries:[]});
 if(p==='/native/mission/1'||p==='/native/skirmish'){res.writeHead(302,{Location:p.endsWith('/1')?'/index.html?campaign=terran01':'/index.html'});return res.end();}
 if(p.startsWith('/interface/')&&(mode==='missing'||mode==='none')){res.writeHead(404);return res.end();}
 const file=p==='/data/STARDAT.MPQ'?damaged:p.startsWith('/data/')?path.join(base,p.slice(6)):p.startsWith('/interface/')?path.join(fonts,p.slice(11)):p.startsWith('/mission/')?path.join(mission,p.slice(9)):path.join(assets,p==='/'?'title.html':p);
 if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
 const type=file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':file.endsWith('.css')?'text/css':'application/octet-stream';
 if(p==='/ui-original.js'&&mode==='none'){res.writeHead(200,{'Content-Type':type});return res.end(fs.readFileSync(file,'utf8')+'\nOpenBWOriginal.fonts=async()=>({});OpenBWOriginal.recoverFonts=async(s,out={})=>out;');}
 res.writeHead(200,{'Content-Type':type,'Content-Length':fs.statSync(file).size});
 if(p===brokenBlock&&mode==='unreadable'){const bytes=fs.readFileSync(file);bytes.fill(0,0,16);return res.end(bytes);}
 fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
  const page=await browser.newPage({viewport:{width:900,height:412},hasTouch:true,isMobile:true});
  page.on('pageerror',e=>report.errors.push(e.message));
  if(baseline){
   await page.goto(origin+'/index.html');await page.locator('#start-game').tap({timeout:60000});
   await page.waitForFunction(()=>document.getElementById('msg').textContent.includes('too many compressed sectors'),null,{timeout:60000});
   report.baseline=await page.locator('#msg').innerText();
   assert.match(report.baseline,/font\/font8\.fnt: too many compressed sectors/);
   report.checks.push('Unfixed 0.8 reproduces the exact reported startup failure, even with a valid font import');
  }else for(mode of ['valid','missing','unreadable','none']){
   await page.goto(origin+'/title.html');await page.waitForFunction(()=>window.openbwTitleStats?.().loaded,null,{timeout:60000});
   const title=await page.evaluate(()=>openbwTitleStats());
   const readable=mode==='valid'||mode==='unreadable';
   assert.equal(title.animations.length,15);assert.equal(title.originalFont,readable);
   await page.goto(origin+'/index.html');
   await page.locator('#start-game').tap({timeout:60000});await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>30,null,{timeout:60000});
   const custom=await page.evaluate(()=>({game:openbwAndroidStats(),ui:openbwClassicStats()}));
   if(!readable)assert.equal(custom.ui.originalFonts.length,0);
   else for(const n of ['10','14','16','16x'])assert(custom.ui.originalFonts.includes(n),`${mode}: font${n} did not recover: ${custom.ui.originalFonts}`);
   // A visible command card and animated portrait prove the decoder used for
   // other art still works after the optional-font failure.
   await page.evaluate(()=>{const{x,memory}=__bw,p=x.openbw_debug_units(),a=new Uint8Array(memory.buffer);let end=p;while(a[end])end++;const row=new TextDecoder().decode(a.subarray(p,end)).split('\n').map(s=>s.split('\t')).find(v=>v[1]==='SCV');x.openbw_debug_select(+row[0],0);});
   await page.waitForFunction(()=>openbwPortraitStats().surfaces.some(s=>s.visible&&s.frames>0));
   assert(await page.locator('#card .cmd').count()>0);
   await page.locator('#settingsbtn').tap();assert.equal(await page.evaluate(()=>openbwMenuStats().opened),true);
   await page.locator('#menu-resume').tap();await page.waitForFunction(f=>openbwAndroidStats().frame>f,custom.game.frame);
   await page.goto(origin+'/index.html?campaign=terran03');await page.waitForFunction(()=>window.openbwBriefingArtStats?.().active,null,{timeout:60000});
   const briefing=await page.evaluate(()=>openbwBriefingArtStats());
   assert.deepEqual(briefing.fonts,{small:readable,large:readable,button:readable});
   assert.equal(briefing.animations.length,3);
   if(mode==='none'){
    await page.waitForFunction(()=>openbwCampaignStats().briefIndex===1&&openbwCampaignStats().voice.position>6000,null,{timeout:30000});
    const scroll=await page.evaluate(()=>({stats:openbwBriefingArtStats(),transform:document.querySelector('#brief-text .brief-scroll-content').style.transform}));
    assert.equal(scroll.stats.dialogueFont,'fallback');assert(scroll.stats.contentHeight>113);assert(scroll.stats.scrollOffset>0);assert.notEqual(scroll.transform,'translateY(-0px)');report.fallbackScroll=scroll;
    const r=await page.locator('#brief-text').boundingBox();await page.mouse.move(r.x+50,r.y+50);await page.mouse.down();await page.mouse.move(r.x+50,r.y+48);await page.mouse.up();
    assert.equal(await page.evaluate(()=>openbwBriefingArtStats().manualScroll),false,'Touch jitter must not cancel scrolling');
    const before=await page.evaluate(()=>openbwBriefingArtStats().scrollOffset);await page.waitForTimeout(600);assert(await page.evaluate(()=>openbwBriefingArtStats().scrollOffset)>before);
    await page.screenshot({path:path.join(root,'dist/ui13-brief-fallback.png')});
   }
   await page.locator('#brief-start').tap();await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>30,null,{timeout:60000});
   const campaign=await page.evaluate(()=>openbwAndroidStats());
   report.scenarios.push({fonts:mode,title,custom,briefing,campaign});
   report.checks.push(`${mode} font import: title, custom game, portraits/menu, briefing and campaign start with unreadable StarDat font8; ${readable?'readable fonts retained independently':'fallback remains playable'}`);
   console.log('PASS',mode);
  }
  assert.deepEqual(report.errors,[]);console.log('PASS',JSON.stringify(report.checks));
 }finally{
  fs.writeFileSync(path.join(root,'validation',baseline?'font-startup-v08-repro.json':(process.env.OPENBW_FONT_REPORT||'font-startup-v081.json')),JSON.stringify(report,null,2)+'\n');
  await browser.close();server.close();fs.rmSync(temporary,{recursive:true,force:true});
 }
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

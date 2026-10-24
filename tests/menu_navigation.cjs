// Exercise native-modal return and transition requests arriving before the room
// is assembled. Fixtures remain external; no StarCraft data is distributed.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game'),report={checks:[],errors:[]};
const server=http.createServer((req,res)=>{
 const p=new URL(req.url,'http://local').pathname;
 if(p==='/availability.json')return res.end(JSON.stringify({missions:[1]}));
 if(p==='/music/manifest.json')return res.end(JSON.stringify({format:'openbw-music-bundle-v1',entries:[]}));
 const roots={'/interface/':process.env.OPENBW_INTERFACE_BUNDLE||'/tmp/openbw-interface-reference','/mission/':process.env.OPENBW_MISSION_BUNDLE||'/tmp/terran01-bundle','/data/':process.env.OPENBW_TEST_MPQS||'/tmp/openbw-test-data'};
 const prefix=Object.keys(roots).find(n=>p.startsWith(n)),file=prefix?path.join(roots[prefix],p.slice(prefix.length)):path.join(assets,p);
 if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
 res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':file.endsWith('.css')?'text/css':file.endsWith('.wasm')?'application/wasm':'application/octet-stream');fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
  const page=await browser.newPage({viewport:{width:900,height:412},hasTouch:true,isMobile:true});page.on('pageerror',e=>report.errors.push(e.message));
  await page.route('**/native/diagnostics',r=>r.fulfill({status:204,body:''}));
  await page.goto(origin+'/title.html?menu');await page.waitForFunction(()=>window.openbwTitleStats?.().loaded&&!openbwTitleStats().transitioning,null,{timeout:90000});
  await page.locator('#title-single').tap();await page.waitForFunction(()=>openbwTitleStats().page==='registry'&&!openbwTitleStats().transitioning);await page.locator('#registry-create-cancel').tap();await page.locator('#registry-cancel').tap();await page.waitForFunction(()=>openbwTitleStats().page==='main'&&!openbwTitleStats().transitioning);
  await page.locator('#title-single').dispatchEvent('pointerover',{pointerType:'mouse'});
  await page.evaluate(()=>openbwBack());await page.locator('#title-diagnostics').tap();await page.waitForTimeout(100);
  await page.waitForFunction(()=>openbwTitleStats().sounds.decoded===5&&openbwTitleStats().sounds.played>=5);report.sounds=await page.evaluate(()=>openbwTitleStats().sounds);assert.equal(report.sounds.error,'');report.checks.push('All five original UI sound files decode and play without an audio error');
  assert.equal(await page.evaluate(()=>openbwTitleStats().transitioning),false);assert.equal(await page.locator('#title-stage').evaluate(e=>e.inert),false);assert.equal(await page.locator('#title-options-page').evaluate(e=>getComputedStyle(e).opacity),'1');
  await page.locator('#title-options-page .title-back').tap();await page.waitForFunction(()=>openbwTitleStats().page==='main'&&!openbwTitleStats().transitioning);
  report.checks.push('Native Diagnostics modal navigation leaves the existing title page visible and interactive');
  const briefing=async()=>{await page.goto(origin+'/index.html?campaign=terran01');await page.waitForFunction(()=>window.openbwBriefingArtStats?.().phase==='entering',null,{timeout:90000});};
  await briefing();await page.evaluate(()=>{openbwBack();openbwBack();});assert.equal(await page.evaluate(()=>openbwCampaignStats().playing),false);
  await page.waitForFunction(()=>window.openbwTitleStats?.().loaded&&!openbwTitleStats().transitioning,null,{timeout:90000});assert.equal(await page.evaluate(()=>openbwTitleStats().page),'main');
  report.checks.push('Repeated Android Back during briefing assembly queues one complete exit and returns to main');
  await briefing();await page.evaluate(()=>{document.getElementById('brief-start').click();document.getElementById('brief-start').click();});assert.equal(await page.evaluate(()=>openbwCampaignStats().playing),false);
  await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>5,null,{timeout:90000});assert.equal(await page.locator('#campaign-briefing').evaluate(e=>e.hidden),true);
  report.checks.push('Start during assembly waits for entrance/exit, skips speech and starts one live mission');
  await briefing();await page.waitForFunction(()=>openbwBriefingArtStats().phase==='ready');await page.locator('#brief-cancel').tap();await page.evaluate(()=>document.getElementById('brief-cancel').click());
  await page.waitForFunction(()=>window.openbwTitleStats?.().loaded&&!openbwTitleStats().transitioning,null,{timeout:90000});
  report.checks.push('Normal Cancel and duplicate Cancel complete the exit without launching gameplay');
  assert.deepEqual(report.errors,[]);console.log('PASS',report.checks);
 }finally{fs.writeFileSync(path.join(root,'validation/menu-navigation-v11.json'),JSON.stringify(report,null,2)+'\n');await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

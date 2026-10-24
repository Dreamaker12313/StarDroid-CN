const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game');
const report={checks:[],errors:[],layouts:[]};
const server=http.createServer((req,res)=>{
 const url=new URL(req.url,'http://local'),p=decodeURIComponent(url.pathname);
 if(p==='/availability.json'){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({missions:[1]}));}
 if(p==='/music/manifest.json'&&!process.env.OPENBW_MUSIC_BUNDLE){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({format:'openbw-music-bundle-v1',entries:[]}));}
 if(p==='/native/mission/1'||p==='/native/skirmish'){res.writeHead(302,{Location:p.endsWith('/1')?'/index.html?campaign=terran01':'/index.html'});return res.end();}
 const file=p.startsWith('/interface/')?path.join(process.env.OPENBW_INTERFACE_BUNDLE||'/tmp/no-interface',p.slice(11)):p.startsWith('/music/')?path.join(process.env.OPENBW_MUSIC_BUNDLE,p.slice(7)):p.startsWith('/data/')?path.join(process.env.OPENBW_TEST_MPQS||'/tmp/openbw-test-data',p.slice(6)):p.startsWith('/mission/')?path.join(process.env.OPENBW_MISSION_BUNDLE||'/tmp/terran01-bundle',p.slice(9)):path.join(assets,p==='/'?'title.html':p);
 if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
 const type=file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':file.endsWith('.css')?'text/css':'application/octet-stream';
 res.writeHead(200,{'Content-Type':type,'Content-Length':fs.statSync(file).size,'Content-Security-Policy':"default-src 'self' blob: data:; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; connect-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'"});fs.createReadStream(file).pipe(res);
});
async function select(page,name){await page.evaluate(name=>{const{x,memory}=__bw;const p=x.openbw_debug_units(),a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;const rows=new TextDecoder().decode(a.subarray(p,e)).trim().split('\n').map(s=>s.split('\t'));const row=rows.find(r=>r[1]===name);if(!row)throw Error('Missing '+name);x.openbw_debug_select(+row[0],0);},name);await page.waitForTimeout(200);}
async function layout(page,size,race){
 await page.setViewportSize(size);await page.waitForTimeout(250);
 const boxes=await page.evaluate(()=>{
  const rect=el=>{const r=el.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom};};
  return{s:+getComputedStyle(document.documentElement).getPropertyValue('--original-scale'),buttons:[...document.querySelectorAll('#card .cmd')].map(rect),card:rect(document.getElementById('card')),menu:rect(document.getElementById('settingsbtn')),portrait:rect(document.getElementById('unit-preview'))};
 });
 for(const b of [...boxes.buttons,boxes.card,boxes.menu,boxes.portrait])assert(b.x>=-1&&b.y>=-1&&b.right<=size.width+1&&b.bottom<=size.height+1,JSON.stringify(b));
 for(const b of boxes.buttons){assert(Math.abs(b.w-36*boxes.s)<.1);assert(Math.abs(b.h-34*boxes.s)<.1);assert(b.x>=boxes.card.x-.1&&b.right<=boxes.card.right+.1);assert(b.y>=boxes.card.y-.1&&b.bottom<=boxes.card.bottom+.1);}
 assert(boxes.menu.bottom<=boxes.portrait.y+.5,'Menu above portrait');assert(boxes.buttons.length<=9);
 report.layouts.push({race,...size,...boxes});
}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox']});
 try{const page=await browser.newPage({viewport:{width:640,height:480},hasTouch:true,isMobile:true});page.on('pageerror',e=>report.errors.push(e.message));
  await page.goto(origin+'/index.html');await page.locator('#start-game').tap();await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>5,null,{timeout:90000});
  await select(page,'Command Center');await page.evaluate(()=>__bw.x.openbw_test_money());
  const scv=page.locator('#card .cmd[data-key="s"]');await scv.tap();await scv.tap();await scv.tap();await page.waitForTimeout(100);
  assert.equal(await page.locator('#status .q[data-slot]').count(),3);
  assert.equal(await page.locator('#status .q img').count(),3);
  assert.equal(await page.locator('#resources .resource-value canvas').count(),3);
  assert.equal(await page.locator('#unit-name canvas').evaluate(c=>c.width),122);
  const status=await page.locator('#status').evaluate(el=>({box:el.getBoundingClientRect().toJSON(),cells:[...el.querySelectorAll('.q')].map(e=>({slot:e.dataset.slot,...e.getBoundingClientRect().toJSON()})),bar:el.querySelector('.bar').getBoundingClientRect().toJSON()}));
  assert.equal(status.cells[0].x,242);assert.equal(status.cells[0].y,402);assert.equal(status.cells[1].x,242);assert.equal(status.cells[1].y,441);assert.equal(status.bar.x,283);
  await page.screenshot({path:path.join(root,'dist/ui11-production.png')});
  await page.locator('#status .q[data-slot="1"]').tap();await page.waitForTimeout(100);assert.equal(await page.locator('#status .q[data-slot]').count(),2);
  const f=await page.evaluate(()=>openbwAndroidStats().frame);await page.waitForFunction(f=>openbwAndroidStats().frame>f+10,f);
  report.production=status;report.checks.push('Original-width 122px Command Center name, all resource counts are bitmap text, three icon queue cells, original queue/bar geometry and live-engine cancellation');
  // Original mission control bytes survive; multiple trigger messages stack on
  // the battlefield and remain visible in the paused objectives dialog.
  await page.goto(origin+'/index.html?campaign=terran01');await page.locator('#brief-start').tap({timeout:90000});await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>12,null,{timeout:90000});
  await page.waitForFunction(()=>!document.getElementById('campaign-subtitle').hidden,null,{timeout:30000});
  assert.equal(await page.locator('#campaign-subtitle canvas').count(),1);assert.equal(await page.locator('#campaign-subtitle').evaluate(e=>getComputedStyle(e).backgroundColor),'rgba(0, 0, 0, 0)');
  await page.locator('#settingsbtn').tap();await page.locator('#menu-objectives').tap();assert.equal(await page.locator('#campaign-objectives-text canvas').count(),1);
  report.checks.push('Actual mission trigger messages and mission objectives use bitmap glyphs; battlefield transmission has no card background');
  assert.deepEqual(report.errors,[]);console.log('PASS',report.checks);
 }finally{fs.writeFileSync(path.join(root,'validation/hud-v11.json'),JSON.stringify(report,null,2)+'\n');await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

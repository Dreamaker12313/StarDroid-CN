const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game');
let fixtureMission=3;
const report={checks:[],errors:[],layouts:[]};
const server=http.createServer((req,res)=>{
 const url=new URL(req.url,'http://local'),p=decodeURIComponent(url.pathname);
 if(p==='/availability.json'){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({missions:[1,2,3]}));}
 if(p==='/music/manifest.json'&&!process.env.OPENBW_MUSIC_BUNDLE){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({format:'openbw-music-bundle-v1',entries:[]}));}
 if(p==='/native/mission/1'||p==='/native/skirmish'){res.writeHead(302,{Location:p.endsWith('/1')?'/index.html?campaign=terran01':'/index.html'});return res.end();}
 const file=p.startsWith('/interface/')?path.join(process.env.OPENBW_INTERFACE_BUNDLE||'/tmp/no-interface',p.slice(11)):p.startsWith('/music/')?path.join(process.env.OPENBW_MUSIC_BUNDLE,p.slice(7)):p.startsWith('/data/')?path.join(process.env.OPENBW_TEST_MPQS||'/tmp/openbw-test-data',p.slice(6)):p.startsWith('/mission/')?path.join('/tmp/terran0'+fixtureMission+'-bundle',p.slice(9)):path.join(assets,p==='/'?'title.html':p);
 if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
 const type=file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':file.endsWith('.css')?'text/css':'application/octet-stream';
 res.writeHead(200,{'Content-Type':type,'Content-Length':fs.statSync(file).size,'Content-Security-Policy':"default-src 'self' blob: data:; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; connect-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'"});fs.createReadStream(file).pipe(res);
});
// Full retail mission-three briefing and the actual rendered HUD, using local assets.
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
  const page=await browser.newPage({viewport:{width:640,height:480},hasTouch:true,isMobile:true});
  page.on('pageerror',e=>{report.errors.push(e.message);console.log('PAGE ERROR',e.message);});
  await page.goto(origin+'/index.html?campaign=terran03');
  if(!process.env.OPENBW_REFERENCE_HUD_ONLY){
  await page.waitForFunction(()=>window.openbwCampaignStats?.().briefIndex===0&&openbwCampaignStats().voice.ready,null,{timeout:90000});
  await page.waitForFunction(()=>openbwPortraitStats().surfaces[4].visible);
  const sample=()=>page.evaluate(()=>({brief:openbwBriefingArtStats(),campaign:openbwCampaignStats(),portraits:openbwPortraitStats()}));
  report.first=await sample();assert.equal(report.first.campaign.transmission.fallback,false);assert.equal(report.first.brief.dialogueFont,'font14');
  assert.equal(report.first.portraits.surfaces[4].width,128);assert.equal(report.first.portraits.surfaces[4].height,118);
  const scanlines=await page.locator('#brief-portrait-3').evaluate(c=>{const a=c.getContext('2d').getImageData(0,0,128,118).data;let on=0,off=0;for(let y=3;y<113;y+=2)for(let x=10;x<118;x++)for(let k=0;k<3;k++){on+=a[(y*128+x)*4+k];off+=a[((y+1)*128+x)*4+k];}return off/on;});
  assert(scanlines>.42&&scanlines<.45,scanlines);report.scanlineRatio=scanlines;
  const hotkeys=await page.evaluate(()=>['brief-start','brief-replay','brief-cancel'].map(id=>{
    const c=document.querySelector('#'+id+' canvas'),a=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
    let brightFirst=0,brightRest=0;for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const i=(y*c.width+x)*4;if(a[i+3]&&a[i]>120&&a[i+1]>200&&a[i+2]>50){if(x<({'brief-start':14,'brief-replay':14,'brief-cancel':14}[id]))brightFirst++;else brightRest++;}}
    return{id,width:c.width,height:c.height,brightFirst,brightRest};
  }));for(const b of hotkeys){assert(b.brightFirst>0,JSON.stringify(b));assert.equal(b.brightRest,0,JSON.stringify(b));}report.hotkeys=hotkeys;
  await page.waitForFunction(()=>openbwCampaignStats().briefIndex===1&&openbwCampaignStats().voice.position>5000,null,{timeout:30000});
  await page.screenshot({path:path.join(root,'dist/ui13-briefing.png')});
  await page.evaluate(()=>openbwAndroidSuspend());await page.waitForTimeout(100);const paused=await sample();await page.waitForTimeout(300);const still=await sample();
  assert.equal(still.brief.scrollOffset,paused.brief.scrollOffset);assert.equal(still.campaign.voice.position,paused.campaign.voice.position);await page.evaluate(()=>openbwAndroidResume());
  await page.waitForFunction(()=>openbwCampaignStats().briefIndex===2&&openbwCampaignStats().voice.position>10000,null,{timeout:40000});
  const timed=await sample();assert(timed.brief.scrollOffset>0);assert(Math.abs(timed.brief.speechPosition-timed.campaign.voice.position)<90);assert.equal(timed.campaign.transmission.fallback,false);report.timed=timed;
  const rect=await page.locator('#brief-text').boundingBox();await page.mouse.move(rect.x+100,rect.y+70);await page.mouse.wheel(0,40);await page.waitForTimeout(100);assert.equal((await sample()).brief.manualScroll,true);
  await page.waitForFunction(()=>!openbwBriefingArtStats().manualScroll,null,{timeout:4000});
  await page.mouse.down();await page.mouse.move(rect.x+100,rect.y+68);await page.mouse.up();assert.equal((await sample()).brief.manualScroll,false,'Small touch jitter must not disable automatic scrolling');
  await page.waitForFunction(()=>openbwCampaignStats().briefIndex===4&&openbwCampaignStats().voice.position>19000,null,{timeout:85000});
  report.lastMengsk=await sample();assert.equal(report.lastMengsk.brief.manualScroll,false);
  const height=await page.locator('#brief-text canvas').evaluate(c=>c.height);assert.equal(height,171,'Nine 19px lines, as in the original recording');
  assert(report.lastMengsk.brief.scrollOffset>height-113,'Text must continue past the bottom-aligned position');
  await page.screenshot({path:path.join(root,'dist/ui13-briefing-scroll.png')});
  await page.waitForFunction(()=>!openbwCampaignStats().playing,null,{timeout:25000});
  assert.deepEqual((await sample()).campaign.missing,[]);assert.equal((await sample()).campaign.briefIndex,5);
  await page.locator('#brief-replay').tap();assert.equal((await sample()).campaign.briefIndex,-1);assert.equal((await sample()).brief.scrollOffset,0);
  report.checks.push('All six retail mission-three transmissions play in sequence without missing speech; scroll follows AudioContext time, pauses/resumes, permits manual reading and resets on replay; native 9-line wrapping and continued end scroll; doubled portraits have scanlines; hotkey initials use original bright-green glyph ramps');
  }
  await page.locator('#brief-start').tap({timeout:90000});await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>15,null,{timeout:45000});

  const readMini=()=>page.locator('#classic-minimap').evaluate(c=>Array.from(c.getContext('2d').getImageData(0,0,c.width,c.height).data));
  const before=await readMini();const mb=await page.locator('#classic-minimap').boundingBox();assert.equal(mb.width,96);assert.equal(mb.height,96);assert.equal(mb.x,22);assert.equal(mb.y,363);
  await page.locator('#minimap-terrain').tap();await page.waitForFunction(()=>!openbwClassicStats().minimapTerrain);await page.waitForTimeout(150);const off=await readMini();assert.notDeepEqual(before,off);assert.equal(await page.locator('#minimap-terrain').getAttribute('aria-pressed'),'false');
  const green=a=>a.reduce((n,v,i)=>n+(i%4===0&&a[i+1]>120&&a[i+1]>v*1.5&&a[i+1]>a[i+2]*1.5?1:0),0);assert(green(off)>0,'Unit markers must remain');
  await page.keyboard.press('Tab');await page.waitForFunction(()=>openbwClassicStats().minimapTerrain);await page.waitForTimeout(150);assert.equal(await page.locator('#minimap-terrain').getAttribute('aria-pressed'),'true');
  report.minimap={bounds:mb,unitPixels:green(off),art:await page.evaluate(()=>openbwClassicStats().dialogArt)};assert.equal(report.minimap.art,'dlgs/terran.grp');
  await page.evaluate(()=>{const{x,memory}=__bw;const p=x.openbw_debug_units(),a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;const rows=new TextDecoder().decode(a.subarray(p,e)).trim().split('\n').map(s=>s.split('\t'));const units=rows.filter(r=>+r[2]===1&&['Marine','SCV'].includes(r[1])).slice(0,5);if(units.length!==5)throw Error('Five test units required');units.forEach((u,i)=>x.openbw_debug_select(+u[0],i?1:0));});
  await page.waitForFunction(()=>document.getElementById('wires').children.length===5);await page.waitForTimeout(100);
  const boxes=await page.locator('#wires canvas').evaluateAll(cs=>cs.map(c=>c.getBoundingClientRect().toJSON()));assert.equal(boxes[0].width,34);assert.equal(boxes[0].height,34);assert.equal(boxes[0].y,boxes[2].y);assert.equal(boxes[3].x,boxes[0].x);assert.equal(boxes[3].y,boxes[4].y);assert(boxes[3].y>boxes[0].y);
  assert.equal(await page.locator('#campaign-progress canvas').count(),1);
  const timer=await page.locator('#campaign-progress canvas').evaluate(c=>({width:c.width,height:c.height,box:c.getBoundingClientRect().toJSON()}));assert.equal(timer.box.width,timer.width*1.25);assert.equal(timer.box.height,timer.height*1.25);assert.equal(timer.box.x+timer.box.width/2,256);
  const resourceIcons=await page.locator('#resources .rico').evaluateAll(cs=>cs.map(c=>({w:c.naturalWidth,h:c.naturalHeight,width:c.getBoundingClientRect().width,src:c.src})));for(const icon of resourceIcons){assert.equal(icon.w,14);assert.equal(icon.h,14);assert.equal(icon.width,14);}assert.deepEqual(await page.evaluate(()=>openbwClassicStats().resourceFrames),[0,2,5]);
  report.hud={timer,resourceIcons:resourceIcons.map(({src,...size})=>size)};
  await page.screenshot({path:path.join(root,'dist/ui13-mission3.png')});
  await page.evaluate(()=>{const{x,memory}=__bw,p=x.openbw_debug_units(),a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;const unit=new TextDecoder().decode(a.subarray(p,e)).split('\n').map(s=>s.split('\t')).find(s=>s[1]==='Marine'&&s[2]==='1');x.openbw_debug_select(+unit[0],0);});
  await page.waitForFunction(()=>document.querySelectorAll('#unit-details img').length===2&&[...document.querySelectorAll('#unit-details img')].every(i=>i.complete&&i.naturalWidth));
  assert.deepEqual(await page.locator('#unit-details .unit-stat').evaluateAll(es=>es.map(e=>e.dataset.kind)),['armor','weapon']);
  report.hud.details=await page.locator('#unit-details img').evaluateAll(cs=>cs.map(c=>({w:c.naturalWidth,h:c.naturalHeight,box:c.getBoundingClientRect().toJSON()})));for(const icon of report.hud.details){assert.equal(icon.w,36);assert.equal(icon.h,34);assert.equal(icon.box.width,36);assert.equal(icon.box.height,34);assert.equal(icon.box.y,439);}assert.equal(report.hud.details[0].box.x,242);assert.equal(report.hud.details[1].box.x,281);
  await page.screenshot({path:path.join(root,'dist/ui13-marine.png')});
  await page.locator('#settingsbtn').tap();await page.waitForFunction(()=>openbwMenuStats().opened);const frame=await page.evaluate(()=>openbwAndroidStats().frame);await page.waitForTimeout(200);assert.equal(await page.evaluate(()=>openbwAndroidStats().frame),frame);await page.screenshot({path:path.join(root,'dist/ui13-menu.png')});
  report.checks.push('Original dlgs/terran.grp Menu/terrain/dialog frames; 96×96 mission minimap centered without stretching; touch and keyboard terrain toggles agree and preserve green local unit markers on a black background; five framed units arranged 3+2; bitmap timer; menu pauses gameplay');
  assert.deepEqual(report.errors,[]);console.log('PASS',JSON.stringify(report.checks));
 }finally{fs.writeFileSync(path.join(root,process.env.OPENBW_REFERENCE_HUD_ONLY?'validation/reference-hud-v13.json':'validation/reference-v13.json'),JSON.stringify(report,null,2)+'\n');await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

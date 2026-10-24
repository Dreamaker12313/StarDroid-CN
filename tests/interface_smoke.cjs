// Historical v0.7 UI selectors; use tests/original_ui.cjs for the current interface.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game');
const report={checks:[],errors:[],layouts:[]};
const server=http.createServer((req,res)=>{
 const url=new URL(req.url,'http://local'),p=decodeURIComponent(url.pathname);
 if(p==='/availability.json'){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({missions:[1]}));}
 if(p==='/music/manifest.json'&&!process.env.OPENBW_MUSIC_BUNDLE){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({format:'openbw-music-bundle-v1',entries:[]}));}
 if(p==='/native/mission/1'||p==='/native/skirmish'){res.writeHead(302,{Location:p.endsWith('/1')?'/index.html?campaign=terran01':'/index.html'});return res.end();}
 const file=p.startsWith('/music/')?path.join(process.env.OPENBW_MUSIC_BUNDLE,p.slice(7)):p.startsWith('/data/')?path.join(process.env.OPENBW_TEST_MPQS||'/tmp/openbw-test-data',p.slice(6)):p.startsWith('/mission/')?path.join(process.env.OPENBW_MISSION_BUNDLE||'/tmp/terran01-bundle',p.slice(9)):path.join(assets,p==='/'?'title.html':p);
 if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
 const type=file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':file.endsWith('.css')?'text/css':'application/octet-stream';
 res.writeHead(200,{'Content-Type':type,'Content-Length':fs.statSync(file).size,'Content-Security-Policy':"default-src 'self' blob: data:; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; connect-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'"});fs.createReadStream(file).pipe(res);
});
async function select(page,name){await page.evaluate(name=>{const{x,memory}=__bw;const p=x.openbw_debug_units(),a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;const rows=new TextDecoder().decode(a.subarray(p,e)).trim().split('\n').map(s=>s.split('\t'));const row=rows.find(r=>r[1]===name);if(!row)throw Error('Missing '+name);x.openbw_debug_select(+row[0],0);},name);await page.waitForTimeout(200);}
async function layout(page,size,race){
 await page.setViewportSize(size);await page.waitForTimeout(250);
 const boxes=await page.evaluate(()=>{
  const rect=el=>{const r=el.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom};};
  return{s:+getComputedStyle(document.documentElement).getPropertyValue('--console-scale'),buttons:[...document.querySelectorAll('#card .cmd')].map(rect),card:rect(document.getElementById('card')),menu:rect(document.getElementById('settingsbtn')),portrait:rect(document.getElementById('unit-preview'))};
 });
 for(const b of [...boxes.buttons,boxes.card,boxes.menu,boxes.portrait])assert(b.x>=-1&&b.y>=-1&&b.right<=size.width+1&&b.bottom<=size.height+1,JSON.stringify(b));
 for(const b of boxes.buttons){assert(Math.abs(b.w-36*boxes.s)<.1);assert(Math.abs(b.h-34*boxes.s)<.1);assert(b.x>=boxes.card.x-.1&&b.right<=boxes.card.right+.1);assert(b.y>=boxes.card.y-.1&&b.bottom<=boxes.card.bottom+.1);}
 assert(boxes.menu.bottom<=boxes.portrait.y+.5,'Menu above portrait');assert(boxes.buttons.length<=9);
 report.layouts.push({race,...size,...boxes});
}
(async()=>{
 fs.mkdirSync(path.join(root,'dist'),{recursive:true});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
  const page=await browser.newPage({viewport:{width:900,height:412},hasTouch:true,isMobile:true});
  page.on('pageerror',e=>{report.errors.push(e.message);console.error('PAGE',e.message);});page.on('console',m=>{if(m.type()==='error')console.log('CONSOLE',m.text());});
  await page.goto(origin+'/title.html');await page.waitForFunction(()=>window.openbwTitleStats?.().loaded,{},{timeout:90000});
  const title=await page.evaluate(()=>openbwTitleStats());assert.equal(title.animations.length,4);report.title=title;
  if(process.env.OPENBW_MUSIC_BUNDLE){await page.waitForFunction(()=>openbwMusicStats().playing&&/title/.test(openbwMusicStats().track));report.titleMusic=await page.evaluate(()=>openbwMusicStats());}
  await page.screenshot({path:path.join(root,'dist/ui07-title.png')});
  await page.locator('#title-enter').tap();await page.waitForTimeout(350);await page.screenshot({path:path.join(root,'dist/ui07-main.png')});
  const anim1=await page.locator('#planet-single').evaluate(c=>c.toDataURL());await page.waitForTimeout(300);const anim2=await page.locator('#planet-single').evaluate(c=>c.toDataURL());assert.notEqual(anim1,anim2);
  await page.evaluate(()=>openbwAndroidSuspend());const freeze=await page.locator('#planet-single').evaluate(c=>c.toDataURL());await page.waitForTimeout(200);assert.equal(await page.locator('#planet-single').evaluate(c=>c.toDataURL()),freeze);await page.evaluate(()=>openbwAndroidResume());
  await page.locator('#title-options').tap();await page.locator('#music-volume').fill('40');assert.equal(await page.evaluate(()=>openbwMusicStats().volume),.4);await page.locator('#title-options-page .title-back').tap();
  await page.locator('#title-single').tap();assert(await page.locator('#title-mission2').isDisabled());await page.screenshot({path:path.join(root,'dist/ui07-missions.png')});
  report.checks.push('Original title PCX, four animated main-menu SMKs, font fallback, title suspend/resume, options, imported mission availability');
  await page.locator('#title-mission1').tap();await page.locator('#brief-start').tap({timeout:90000});await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>10);
  await select(page,'SCV');await page.waitForFunction(()=>window.openbwPortraitStats?.().surfaces.some(s=>s.visible&&s.frames>0));await layout(page,{width:900,height:412},'Terran');
  await page.screenshot({path:path.join(root,'dist/ui07-console.png')});
  await page.locator('#card .cmd[data-key="b"]').tap();await page.waitForTimeout(150);await layout(page,{width:900,height:412},'Terran build');await page.screenshot({path:path.join(root,'dist/ui07-build.png')});
  await page.locator('#card .cmd[aria-label="Cancel"]').tap();
  await page.waitForFunction(()=>!openbwClassicStats().submenu);
  await page.locator('#card .cmd[data-key="b"]').tap();await page.waitForFunction(()=>openbwClassicStats().submenu);
  await page.evaluate(()=>openbwBack());await page.waitForFunction(()=>!openbwClassicStats().submenu);
  assert.equal(await page.evaluate(()=>openbwMenuStats().opened),false);
  await page.locator('#settingsbtn').tap();await page.waitForFunction(()=>openbwMenuStats().opened);
  const frame=await page.evaluate(()=>openbwAndroidStats().frame);await page.waitForTimeout(250);assert.equal(await page.evaluate(()=>openbwAndroidStats().frame),frame);
  await page.evaluate(()=>{openbwAndroidSuspend();openbwAndroidResume();});assert.equal(await page.evaluate(()=>openbwAndroidStats().paused),true);
  if(process.env.OPENBW_MUSIC_BUNDLE){assert.equal(await page.evaluate(()=>openbwMusicStats().playing),false);const t=await page.evaluate(()=>openbwMusicStats().time);await page.waitForTimeout(150);assert.equal(await page.evaluate(()=>openbwMusicStats().time),t);}
  await page.screenshot({path:path.join(root,'dist/ui07-menu.png')});
  await page.locator('#menu-objectives').tap();assert(await page.locator('#campaign-objectives-text').isVisible());await page.evaluate(()=>openbwBack());assert.equal(await page.evaluate(()=>openbwMenuStats().page),'main');
  await page.locator('#menu-options').tap();await page.locator('#menu-testing').tap();await page.locator('#test-money').tap();await page.locator('#test-instant').check();assert.equal(await page.evaluate(()=>openbwTestingStats().instant),true);
  await page.evaluate(()=>openbwBack());await page.locator('#menu-game-options').tap();await page.locator('#opt-speed').selectOption('2.625');assert.equal(await page.evaluate(()=>openbwTestingStats().speed),16);
  await page.evaluate(()=>openbwBack());await page.locator('#menu-testing').tap();await page.locator('#test-reset').tap();assert.equal(await page.evaluate(()=>openbwTestingStats().instant),false);
  await page.evaluate(()=>openbwBack());await page.locator('#menu-sound').tap();await page.locator('#menu-mute').check();assert.equal(await page.evaluate(()=>openbwMusicStats().muted),true);await page.locator('#menu-mute').uncheck();
  await page.keyboard.press('Enter');assert.equal(await page.locator('#chatinput').isVisible(),false);assert.equal(await page.evaluate(()=>openbwAndroidStats().frame),frame);
  await page.evaluate(()=>{openbwBack();openbwBack();});await page.locator('#menu-resume').tap();await page.waitForFunction(f=>openbwAndroidStats().frame>f,frame);assert.equal(await page.evaluate(()=>openbwAndroidStats().paused),false);
  await page.evaluate(()=>document.getElementById('pausebtn').click());await page.locator('#settingsbtn').tap();await page.locator('#menu-resume').tap();assert.equal(await page.evaluate(()=>openbwAndroidStats().paused),true);await page.evaluate(()=>document.getElementById('pausebtn').click());
  await page.evaluate(()=>openbwBack());await page.locator('#menu-restart').tap();await page.locator('#menu-confirm .menu-back').tap();assert.equal(await page.evaluate(()=>openbwMenuStats().page),'main');
  await page.locator('#menu-restart').tap();await page.locator('#menu-confirm-yes').tap();await page.locator('#brief-start').tap({timeout:90000});await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>3);
  await page.evaluate(()=>openbwBack());await page.locator('#menu-end').tap();await page.locator('#menu-confirm-yes').tap();await page.waitForFunction(()=>window.openbwTitleStats?.().page==='main');
  if(process.env.OPENBW_MUSIC_BUNDLE)report.checks.push('Java-exported generated music: title track selected and played, menu freezes playback time, options controls remain available');
  report.checks.push('Menu pauses engine/audio; background/resume preserves menu pause; objectives, 16x speed, money, instant/reset, mute, keyboard isolation, manual pause, restart confirmation, end-to-title');
  for(const [race,name] of [[0,'Drone'],[2,'Probe']]){
   await page.goto(origin+'/index.html');await page.waitForSelector('#controls',{state:'visible'});await page.locator('#slots select').first().selectOption(String(race));await page.locator('#start-game').tap();await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>5,{},{timeout:90000});await select(page,name);
   for(const size of [{width:640,height:360},{width:900,height:412},{width:1280,height:720}])await layout(page,size,name);
   await page.locator('#card .cmd[data-key="b"]').tap();await page.waitForTimeout(100);await layout(page,{width:900,height:412},name+' build');await page.screenshot({path:path.join(root,'dist/ui07-'+name.toLowerCase()+'.png')});
  }
  report.checks.push('Original command-grid geometry, portrait and Menu bounds verified at 640×360, 900×412 and 1280×720; Terran/Zerg/Protoss command/build cards fit nine cells');
  assert.deepEqual(report.errors,[]);console.log('PASS',JSON.stringify(report.checks));
 }finally{fs.writeFileSync(path.join(root,'validation/interface-v07.json'),JSON.stringify(report,null,2));await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

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
 fs.mkdirSync(path.join(root,'dist'),{recursive:true});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
  const page=await browser.newPage({viewport:{width:900,height:412},hasTouch:true,isMobile:true});
  page.on('pageerror',e=>{report.errors.push(e.message);console.error('PAGE',e.message);});page.on('console',m=>{if(m.type()==='error')console.log('CONSOLE',m.text());});
  await page.goto(origin+'/title.html');await page.waitForFunction(()=>window.openbwTitleStats?.().loaded,{},{timeout:90000});
  const title=await page.evaluate(()=>openbwTitleStats());assert.equal(title.animations.length,15);report.title=title;if(process.env.OPENBW_INTERFACE_BUNDLE)assert.equal(title.originalFont,true);
  if(process.env.OPENBW_MUSIC_BUNDLE){await page.waitForFunction(()=>openbwMusicStats().playing&&/title/.test(openbwMusicStats().track));report.titleMusic=await page.evaluate(()=>openbwMusicStats());}
  await page.screenshot({path:path.join(root,'dist/ui08-title.png')});
  await page.locator('#title-enter').tap();await page.waitForFunction(()=>openbwTitleStats().page==='main'&&!openbwTitleStats().transitioning);
  assert.equal(await page.evaluate(()=>openbwTitleStats().slideAmount),0);
  await page.screenshot({path:path.join(root,'dist/ui11-main.png')});
  await page.locator('#title-single').dispatchEvent('pointerenter',{pointerType:'mouse'});await page.waitForTimeout(100);assert.equal(await page.locator('#planet-singleon').evaluate(c=>c.hidden),false);await page.locator('#title-single').dispatchEvent('pointerleave');
  await page.waitForFunction(()=>openbwTitleStats().sounds.decoded>0);report.menuSounds=await page.evaluate(()=>openbwTitleStats().sounds);assert.equal(report.menuSounds.error,'');assert.equal(report.menuSounds.available.length,5);
  const anim1=await page.locator('#planet-single').evaluate(c=>c.toDataURL());await page.waitForTimeout(300);const anim2=await page.locator('#planet-single').evaluate(c=>c.toDataURL());assert.notEqual(anim1,anim2);
  await page.evaluate(()=>openbwAndroidSuspend());const freeze=await page.locator('#planet-single').evaluate(c=>c.toDataURL());await page.waitForTimeout(200);assert.equal(await page.locator('#planet-single').evaluate(c=>c.toDataURL()),freeze);await page.evaluate(()=>openbwAndroidResume());
  await page.evaluate(()=>openbwBack());await page.locator('#music-volume').fill('40');assert.equal(await page.evaluate(()=>openbwMusicStats().volume),.4);await page.locator('#title-options-page .title-back').tap();
  await page.locator('#title-single').tap();await page.waitForFunction(()=>openbwTitleStats().page==='registry'&&!openbwTitleStats().transitioning);
  await page.locator('#registry-name').fill('JadedZerg');await page.locator('#registry-create').tap();
  assert.equal(await page.locator('#registry-list [aria-selected=true]').getAttribute('aria-label'),'JadedZerg');
  await page.screenshot({path:path.join(root,'dist/ui11-registry.png')});
  await page.locator('#registry-new').tap();await page.locator('#registry-name').fill('DeleteMe');await page.locator('#registry-create').tap();
  await page.locator('#registry-delete').tap();await page.locator('#registry-delete-yes').tap();assert.equal(await page.locator('#registry-list button').count(),1);
  await page.reload();await page.waitForFunction(()=>window.openbwTitleStats?.().loaded,null,{timeout:90000});await page.locator('#title-enter').tap();await page.locator('#title-single').tap();
  await page.waitForFunction(()=>openbwTitleStats().page==='registry'&&!openbwTitleStats().transitioning);assert.equal(await page.evaluate(()=>openbwTitleStats().modal),false);
  await page.locator('#registry-ok').tap();await page.waitForFunction(()=>openbwTitleStats().page==='campaign'&&!openbwTitleStats().transitioning);
  await page.screenshot({path:path.join(root,'dist/ui11-campaign.png')});
  assert.equal(await page.locator('#race-terr').evaluate(c=>getComputedStyle(c).filter),'brightness(0.25)');
  assert.equal(await page.locator('#race-terr').evaluate(c=>getComputedStyle(c.parentElement).transform),'none');
  await page.locator('#campaign-terran').dispatchEvent('pointerenter',{pointerType:'mouse'});await page.waitForTimeout(80);
  assert.equal(await page.locator('#race-terr').evaluate(c=>getComputedStyle(c).filter),'brightness(1)');
  await page.locator('#campaign-terran').dispatchEvent('pointerleave');
  report.checks.push('Original dark-until-hover race figures and stationary character widgets');

  const raceFrame=await page.locator('#race-terr').evaluate(c=>c.toDataURL());await page.waitForTimeout(200);assert.notEqual(await page.locator('#race-terr').evaluate(c=>c.toDataURL()),raceFrame);
  await page.locator('#campaign-zerg').tap();assert(await page.locator('#title-mission101').isDisabled());await page.locator('#title-mission-cancel').tap();await page.locator('#campaign-terran').tap();
  assert(await page.locator('#title-mission2').isDisabled());await page.screenshot({path:path.join(root,'dist/ui11-missions.png')});
  report.checks.push('Stationary main-menu planets; Registry create/select/delete/persistence; original three-race selector with seven SMKs; all-race mission lists with unimported missions guarded');
  await page.locator('#title-mission1').tap();await page.locator('#title-mission-go').tap();
  await page.waitForFunction(()=>window.openbwBriefingArtStats?.().active,{},{timeout:90000});
  assert.equal(await page.evaluate(()=>openbwBriefingArtStats().phase),'entering');assert.equal(await page.evaluate(()=>openbwCampaignStats().playing),false);
  await page.evaluate(()=>openbwAndroidSuspend());const briefEntering=await page.evaluate(()=>openbwBriefingArtStats().slideAmount);await page.waitForTimeout(150);assert.equal(await page.evaluate(()=>openbwBriefingArtStats().slideAmount),briefEntering);await page.evaluate(()=>openbwAndroidResume());
  await page.waitForFunction(()=>openbwBriefingArtStats().phase==='ready');assert.equal(await page.evaluate(()=>openbwBriefingArtStats().slideAmount),0);
  await page.locator('#brief-start').dispatchEvent('pointerenter',{pointerType:'mouse'});await page.waitForTimeout(2200);assert.equal(await page.locator('[data-clip="glue/readyt/proloop.smk"]').count(),0);assert.equal(await page.locator('[data-clip="glue/readyt/starton.smk"]').evaluate(c=>c.hidden),false);await page.locator('#brief-start').dispatchEvent('pointerleave');await page.waitForTimeout(300);assert.equal(await page.locator('[data-clip="glue/readyt/start.smk"]').evaluate(c=>c.hidden),false);
  await page.waitForFunction(()=>openbwPortraitStats().surfaces[4].visible&&openbwCampaignStats().briefIndex===0);
  const room=await page.evaluate(()=>({art:openbwBriefingArtStats(),state:openbwCampaignStats(),portraits:openbwPortraitStats()}));
  assert.equal(room.art.animations.length,4);assert.equal(room.state.slots[3],106);assert.equal(room.state.slots[0],-1);report.briefing=room;if(process.env.OPENBW_INTERFACE_BUNDLE)assert.deepEqual(room.art.fonts,{small:true,large:true,button:true});
  assert.equal(room.art.speakerFrames,4);assert.equal(room.art.glassIndex,138);assert.equal(room.art.sounds.error,'');
  assert.equal(await page.locator('.brief-active-speaker:not([hidden])').count(),1);
  await page.waitForTimeout(1300);
  report.briefingSurfaces=await page.evaluate(()=>[...document.querySelectorAll('.brief-original-portrait')].map(c=>({id:c.id,hidden:c.hidden,bounds:c.getBoundingClientRect().toJSON(),max:Math.max(...c.getContext('2d').getImageData(0,0,c.width,c.height).data)})));
  await page.screenshot({path:path.join(root,'dist/ui11-briefing.png')});
  await page.evaluate(()=>openbwAndroidSuspend());const bindex=await page.evaluate(()=>openbwCampaignStats().actionIndex);await page.waitForTimeout(250);assert.equal(await page.evaluate(()=>openbwCampaignStats().actionIndex),bindex);await page.evaluate(()=>openbwAndroidResume());
  await page.waitForTimeout(4000);if(process.env.OPENBW_INTERFACE_BUNDLE)assert(await page.evaluate(()=>openbwBriefingArtStats().scrollOffset)>0);
  await page.waitForFunction(()=>openbwCampaignStats().slots[0]===23&&openbwPortraitStats().surfaces[1].visible,{},{timeout:35000});
  assert.equal(await page.evaluate(()=>openbwCampaignStats().slots[3]),106);report.checks.push('Original briefing script: Adjutant in slot 4, simultaneous Duke in slot 1, scrolling original font text, Replay clears prior speakers');
  await page.locator('#brief-replay').tap();assert.equal(await page.evaluate(()=>openbwCampaignStats().briefIndex),-1);
  await page.locator('#brief-start').tap({timeout:90000});await page.waitForFunction(()=>openbwBriefingArtStats().phase==='leaving');await page.evaluate(()=>{document.getElementById('brief-start').click();openbwAndroidSuspend();});const leaving=await page.evaluate(()=>openbwBriefingArtStats().slideAmount);await page.waitForTimeout(200);assert.equal(await page.evaluate(()=>openbwBriefingArtStats().slideAmount),leaving);assert.equal(await page.evaluate(()=>!!window.openbwAndroidStats),false);await page.evaluate(()=>openbwAndroidResume());await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>10);
  report.checks.push('Registry/briefing slide entrance and exit freeze on suspend; speech waits for assembly; five original sounds available; hover projector reaches loop and fades away; original speaker frame; duplicate Start cannot skip exit');
  await select(page,'SCV');await page.waitForFunction(()=>window.openbwPortraitStats?.().surfaces.some(s=>s.visible&&s.frames>0));await layout(page,{width:900,height:412},'Terran');
  await page.screenshot({path:path.join(root,'dist/ui11-console.png')});
  await page.locator('#card .cmd[data-key="b"]').tap();await page.waitForTimeout(150);await layout(page,{width:900,height:412},'Terran build');await page.screenshot({path:path.join(root,'dist/ui08-build.png')});
  await page.locator('#card .cmd[aria-label="Cancel"]').tap();
  await page.waitForFunction(()=>!openbwClassicStats().submenu);
  await page.locator('#card .cmd[data-key="b"]').tap();await page.waitForFunction(()=>openbwClassicStats().submenu);
  await page.evaluate(()=>openbwBack());await page.waitForFunction(()=>!openbwClassicStats().submenu);
  assert.equal(await page.evaluate(()=>openbwMenuStats().opened),false);
  await page.locator('#settingsbtn').tap();await page.waitForFunction(()=>openbwMenuStats().opened);
  const frame=await page.evaluate(()=>openbwAndroidStats().frame);await page.waitForTimeout(250);assert.equal(await page.evaluate(()=>openbwAndroidStats().frame),frame);
  await page.evaluate(()=>{openbwAndroidSuspend();openbwAndroidResume();});assert.equal(await page.evaluate(()=>openbwAndroidStats().paused),true);
  if(process.env.OPENBW_MUSIC_BUNDLE){await page.waitForFunction(()=>openbwMusicStats().playing);const t=await page.evaluate(()=>openbwMusicStats().time);await page.waitForTimeout(150);assert(await page.evaluate(()=>openbwMusicStats().time)>t);}
  await page.screenshot({path:path.join(root,'dist/ui11-menu.png')});
  await page.locator('#menu-objectives').tap();assert(await page.locator('#campaign-objectives-text').isVisible());await page.evaluate(()=>openbwBack());assert.equal(await page.evaluate(()=>openbwMenuStats().page),'main');
  await page.locator('#menu-options').tap();await page.locator('#menu-testing').tap();await page.locator('#test-money').tap();await page.locator('#test-instant').check();assert.equal(await page.evaluate(()=>openbwTestingStats().instant),true);
  await page.evaluate(()=>openbwBack());await page.locator('#menu-game-options').tap();await page.locator('#opt-speed').selectOption('2.625');assert.equal(await page.evaluate(()=>openbwTestingStats().speed),16);
  await page.evaluate(()=>openbwBack());await page.locator('#menu-testing').tap();await page.locator('#test-reset').tap();assert.equal(await page.evaluate(()=>openbwTestingStats().instant),false);
  await page.evaluate(()=>openbwBack());await page.locator('#menu-sound').tap();await page.locator('#menu-mute').check();assert.equal(await page.evaluate(()=>openbwMusicStats().muted),true);await page.locator('#menu-mute').uncheck();
  await page.keyboard.press('Enter');assert.equal(await page.locator('#chatinput').isVisible(),false);assert.equal(await page.evaluate(()=>openbwAndroidStats().frame),frame);
  await page.evaluate(()=>{openbwBack();openbwBack();});await page.locator('#menu-resume').tap();await page.waitForFunction(f=>openbwAndroidStats().frame>f,frame);assert.equal(await page.evaluate(()=>openbwAndroidStats().paused),false);
  await page.evaluate(()=>document.getElementById('pausebtn').click());await page.locator('#settingsbtn').tap();await page.locator('#menu-resume').tap();assert.equal(await page.evaluate(()=>openbwAndroidStats().paused),true);await page.evaluate(()=>document.getElementById('pausebtn').click());
  await page.evaluate(()=>openbwBack());await page.locator('#menu-end').tap();await page.locator('#menu-restart').tap();await page.locator('#menu-confirm .menu-back').tap();assert.equal(await page.evaluate(()=>openbwMenuStats().page),'end');
  await page.locator('#menu-restart').tap();await page.locator('#menu-confirm-yes').tap();await page.locator('#brief-start').tap({timeout:90000});await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>3);
  await page.evaluate(()=>openbwBack());await page.locator('#menu-end').tap();await page.locator('#menu-quit').tap();await page.locator('#menu-confirm-yes').tap();await page.waitForFunction(()=>window.openbwTitleStats?.().page==='main');
  if(process.env.OPENBW_MUSIC_BUNDLE)report.checks.push('Java-exported generated music: title track selected and played, menu keeps music playing, options controls remain available');
  report.checks.push('Menu pauses engine/voices with music and button sounds active; background/resume preserves menu pause; objectives, 16x speed, money, instant/reset, mute, keyboard isolation, manual pause, restart confirmation, end-to-title');
  for(const [race,name] of [[0,'Drone'],[2,'Probe']]){
   await page.goto(origin+'/index.html');await page.waitForSelector('#controls',{state:'visible'});await page.locator('#slots select').first().selectOption(String(race));await page.locator('#start-game').tap();await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>5,{},{timeout:90000});await select(page,name);
   assert.deepEqual(await page.evaluate(()=>openbwClassicStats().resourceFrames),[0,race+1,race+4]);
   for(const icon of await page.locator('#resources .rico').evaluateAll(es=>es.map(e=>[e.naturalWidth,e.naturalHeight])))assert.deepEqual(icon,[14,14]);
   for(const size of [{width:640,height:360},{width:900,height:412},{width:1280,height:720}])await layout(page,size,name);
   await page.locator('#card .cmd[data-key="b"]').tap();await page.waitForTimeout(100);await layout(page,{width:900,height:412},name+' build');await page.screenshot({path:path.join(root,'dist/ui08-'+name.toLowerCase()+'.png')});
  }
  report.checks.push('Original command-grid geometry, portrait and Menu bounds verified at 640×360, 900×412 and 1280×720; Terran/Zerg/Protoss command/build cards fit nine cells');
  assert.deepEqual(report.errors,[]);console.log('PASS',JSON.stringify(report.checks));
 }finally{fs.writeFileSync(path.join(root,'validation',process.env.OPENBW_UI_REPORT||'interface-v08.json'),JSON.stringify(report,null,2));await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

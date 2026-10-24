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
async function installDriver(page) {
  await page.evaluate(()=>{
    const{x,memory,lockstep}=window.__bw;
    const str=p=>{const a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};
    const u16=n=>[n&255,n>>8&255];
    const send=rows=>{const bytes=new Uint8Array(rows.flatMap(r=>[...u16(r.length),...r]));const p=x.openbw_in_ptr(bytes.length);new Uint8Array(memory.buffer,p,bytes.length).set(bytes);x.openbw_apply(window.testOwner,bytes.length);};
    const units=()=>str(x.openbw_debug_units()).trim().split('\n').map(r=>{const a=r.split('\t');return{id:+a[0],name:a[1],owner:+a[2],x:+a[3],y:+a[4],order:+a[5]};});
    const select=ids=>send([[9,ids.length,...ids.flatMap(u16)]]);
    const order=(kind,x,y,target=0)=>send([[21,...u16(x),...u16(y),...u16(target),...u16(228),kind,0]]);
    const advance=async n=>{window.openbwAndroidSuspend();for(let i=0;i<n&&!x.openbw_outcome();i++){lockstep.tick();if(i%40===0)await new Promise(r=>setTimeout(r,0));}window.openbwAndroidResume();};
    window.testOwner=units().find(u=>u.owner<8).owner;
    const dump=id=>{x.openbw_debug_select(id,0);return str(x.openbw_debug_dump());};
    const status=id=>{x.openbw_debug_select(id,0);return str(x.openbw_status());};
    const build=async(type,name,order=30)=>{
      const before=new Set(units().map(u=>u.id));const worker=units().find(u=>u.owner===window.testOwner&&/^(SCV|Probe|Drone)$/.test(u.name));
      const tx=Math.floor(worker.x/32),ty=Math.floor(worker.y/32);let ok=false;
      outer:for(let radius=2;radius<12;radius++)for(let dy=-radius;dy<=radius;dy++)for(let dx=-radius;dx<=radius;dx++){
        if(Math.max(Math.abs(dx),Math.abs(dy))!==radius)continue;
        const a=tx+dx,b=ty+dy;if(a<1||b<1||a>=61||b>=61)continue;
        select([worker.id]);send([[12,order,...u16(a),...u16(b),...u16(type)]]);await advance(1);
        const current=units().find(u=>u.id===worker.id);
        if(current && (current.order===order || (order===25 && current.order===26) || current.name===name)){ok=true;break outer;}
      }
      if(!ok)throw Error('No build site for '+name);
      let created=null,first=null;
      for(let n=0;n<700;n++){
        await advance(1);created=units().find(u=>u.owner===window.testOwner&&u.name===name&&(!before.has(u.id)||u.id===worker.id));
        if(created){if(first===null)first=x.openbw_frame();if(dump(created.id).includes('completed=1 '))return {...created,buildFrames:x.openbw_frame()-first};}
      }
      throw Error('Build did not complete: '+name+' '+(created?dump(created.id):JSON.stringify(units())));
    };
    window.testMission={str,send,u16,units,select,order,advance,dump,status,build};
  });
}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
  const page=await browser.newPage({viewport:{width:640,height:480},hasTouch:true,isMobile:true});
  page.on('pageerror',e=>{report.errors.push(e.message);console.error('PAGE',e.message);});
  await page.goto(origin+'/index.html?campaign=terran03');await page.locator('#brief-start').tap({timeout:90000});
  await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>20,null,{timeout:90000});await installDriver(page);
  await page.evaluate(()=>window.testOwner=1);
  report.classic=await page.evaluate(async()=>{
   const t=testMission,{x}=__bw;
   const barracks=t.units().find(u=>u.owner===1&&u.name==='Barracks');x.openbw_debug_select(barracks.id,0);x.openbw_render(performance.now());
   const card=t.str(x.openbw_card());x.openbw_test_money();x.openbw_test_instant(1);
   const academy=t.units().find(u=>u.owner===1&&u.name==='Academy')||await t.build(112,'Academy');
   t.select([barracks.id]);t.send([[31,...t.u16(34)]]);await t.advance(120);
   const medics=t.units().filter(u=>u.owner===1&&u.name==='Medic');x.openbw_debug_select(barracks.id,0);x.openbw_render(performance.now());
   return {card,afterCard:t.str(x.openbw_card()),medics,academy,timer:t.str(x.openbw_campaign_timer()),aiError:t.str(x.openbw_campaign_ai_error())};
  });
  assert.doesNotMatch(report.classic.card,/Medic|Ghost/);assert.doesNotMatch(report.classic.afterCard,/Medic/);assert.equal(report.classic.medics.length,0);assert.equal(report.classic.aiError,'');
  const timer=await page.locator('#campaign-progress').evaluate(el=>({text:el.getAttribute('aria-label'),rect:el.getBoundingClientRect().toJSON(),fontHeight:el.querySelector('canvas').height}));
  assert.match(timer.text,/^\d+:\d{2}$/);assert.equal(timer.rect.y,0);assert.equal(timer.rect.x+timer.rect.width/2,256);assert.equal(timer.fontHeight,19);report.timer=timer;
  report.checks.push('Real Mission 3: no Medic or mission-locked Ghost in card; raw Medic train rejected even with completed Academy, money and instant production; original numeric top clock');
  await page.screenshot({path:path.join(root,'dist/ui11-mission3.png')});
  // A skirmish supplies the full technology tree for upgrade/expansion checks.
  await page.goto(origin+'/index.html');await page.locator('#slots select').first().selectOption('1');await page.locator('#start-game').tap();
  await page.waitForFunction(()=>window.openbwAndroidStats?.().frame>5,null,{timeout:90000});await installDriver(page);
  await page.evaluate(()=>{__bw.x.openbw_test_money();__bw.x.openbw_test_instant(1);});
  report.upgrade=await page.evaluate(async()=>{
   const t=testMission,{x}=__bw,own=testOwner;
   await t.build(109,'Supply Depot');const bay=await t.build(122,'Engineering Bay');
   x.openbw_debug_select(bay.id,0);x.openbw_render(performance.now());const upgradeCard=t.str(x.openbw_card());
   t.select([bay.id]);t.send([[50,0]]);await t.advance(40);
   const worker=t.units().find(u=>u.owner===own&&u.name==='SCV');x.openbw_debug_select(worker.id,0);x.openbw_render(performance.now());const stats=t.str(x.openbw_unit_details());
   const barracks=await t.build(111,'Barracks');await t.build(112,'Academy');
   t.select([barracks.id]);t.send([[31,...t.u16(34)]]);await t.advance(80);
   return{upgradeCard,stats,medics:t.units().filter(u=>u.owner===own&&u.name==='Medic').length,worker,bay};
  });
  assert(report.upgrade.upgradeCard.split('\n').slice(1).filter(r=>/Infantry/.test(r)).every(r=>+r.split('\t')[10]>=0));
  assert.match(report.upgrade.stats,/armor\t\d+\t1\t0\t1\t1/);assert.equal(report.upgrade.medics,1);
  await page.evaluate(id=>__bw.x.openbw_debug_select(id,0),report.upgrade.worker.id);
  await page.waitForFunction(()=>document.querySelector('.unit-stat[data-kind=armor]')?.dataset.level==='1');
  assert.equal(await page.locator('.unit-stat img').count(),2);await page.locator('.unit-stat[data-kind=armor]').tap();assert.match(await page.locator('#command-hint').getAttribute('aria-label'),/Upgrade level: 1/);
  await page.screenshot({path:path.join(root,'dist/ui11-upgrade-details.png')});
  await page.evaluate(id=>__bw.x.openbw_debug_select(id,0),report.upgrade.bay.id);await page.waitForTimeout(150);
  assert.equal(await page.locator('#card .cmd').count(),await page.locator('#card .cmd img').count());
  await page.evaluate(()=>__bw.x.openbw_test_instant(0));await page.locator('#card .cmd[data-key=w]').tap();
  await page.waitForFunction(()=>__bw.x.openbw_production_kind()===3);
  assert.equal(await page.locator('#status .q img').count(),1);assert.equal(await page.locator('#status .production-label').getAttribute('aria-label'),'Upgrading');
  assert(await page.evaluate(()=>__bw.x.openbw_production_icon()>=0));
  await page.locator('#status .q[data-slot="0"]').tap();await page.waitForFunction(()=>__bw.x.openbw_production_kind()===0);
  report.checks.push('Active upgrade production shows its original icon and Upgrading caption; tapping it cancels correctly');
  report.checks.push('Live Infantry Armor research raises selected SCV armor icon to level 1 with base+bonus tooltip; upgrade buttons have original icons; skirmish can still train Medics');
  // Position the camera deterministically, then use genuine Chromium touch input.
  await page.evaluate(()=>{
   const t=testMission,{x}=__bw;
   window.focusUnit=async id=>{const u=t.units().find(v=>v.id===id),c=document.getElementById('screen');x.openbw_mouse_move(-1,-1);x.openbw_pan(-65536,-65536);await new Promise(r=>setTimeout(r,160));
    const left=Math.max(0,Math.min(x.openbw_map_w()*32-c.width,u.x-c.width/2)),top=Math.max(0,Math.min(x.openbw_map_h()*32-c.height,u.y-c.height*.3));
    x.openbw_pan(left,top);await new Promise(r=>setTimeout(r,160));return{x:(u.x-left)*640/c.width,y:(u.y-top)*480/c.height};};
   window.wireIds=()=>t.str(x.openbw_wires()).trim().split('\n').filter(Boolean).map(s=>+s.split('\t')[0]);
  });
  const worker=await page.evaluate(()=>testMission.units().filter(u=>u.owner===testOwner&&u.name==='SCV')[1]);
  // Move away from overlapping spawn sprites before checking the exact tapped ID.
  await page.evaluate(async id=>{const t=testMission,u=t.units().find(v=>v.id===id),{x}=__bw;t.select([id]);t.order(6,Math.max(40,u.x-100),Math.min(x.openbw_map_h()*32-80,u.y+160));await t.advance(160);},worker.id);
  await page.evaluate(id=>{__bw.x.openbw_debug_select(id,0);__bw.x.openbw_key(1,115,0);__bw.x.openbw_key(0,115,0);},worker.id);await page.waitForTimeout(200);
  const pos=await page.evaluate(id=>focusUnit(id),worker.id);
  await page.evaluate(id=>__bw.x.openbw_debug_select(id,0),report.upgrade.bay.id);
  await page.screenshot({path:path.join(root,'dist/ui11-touch-debug.png')});
  await page.touchscreen.tap(pos.x,pos.y);await page.waitForTimeout(120);assert((await page.evaluate(()=>wireIds())).includes(worker.id));
  const before=await page.evaluate(id=>testMission.dump(id),worker.id);
  await page.touchscreen.tap(pos.x+70,pos.y+40);await page.waitForTimeout(150);
  const moving=await page.evaluate(id=>testMission.dump(id),worker.id);assert.notEqual(moving.match(/move_target=(.*)/)[1],before.match(/move_target=(.*)/)[1]);
  report.checks.push('One tap selects an own unit; a single ground tap issues an engine move order');
  // Gather tap targets a known mineral field, preserving the worker selection.
  const mineral=await page.evaluate(id=>{const u=testMission.units().find(u=>u.id===id);return testMission.units().filter(v=>/Mineral/.test(v.name)).sort((a,b)=>(a.x-u.x)**2+(a.y-u.y)**2-(b.x-u.x)**2-(b.y-u.y)**2)[0];},worker.id);
  const mp=await page.evaluate(id=>focusUnit(id),mineral.id);await page.touchscreen.tap(mp.x,mp.y);await page.waitForTimeout(150);
  const gathering=await page.evaluate(id=>testMission.dump(id),worker.id);assert.match(gathering,/order=(79|85|86|87|90) /);assert((await page.evaluate(()=>wireIds())).includes(worker.id));
  const cdp=await page.context().newCDPSession(page),touch=async(type,points)=>{await cdp.send('Input.dispatchTouchEvent',{type,touchPoints:points.map(([x,y],id)=>({x,y,id,radiusX:1,radiusY:1,force:1}))});await page.waitForTimeout(40);};
  await page.evaluate(id=>focusUnit(id),worker.id);
  await touch('touchStart',[[120,50]]);await touch('touchMove',[[450,290]]);assert.equal(await page.evaluate(()=>openbwTouchStats().mode),'box');await touch('touchEnd',[]);
  assert((await page.evaluate(()=>wireIds())).length>=2);
  const group=await page.evaluate(()=>wireIds());
  await touch('touchStart',[[160,65]]);await touch('touchMove',[[420,270]]);await touch('touchCancel',[]);assert.deepEqual(await page.evaluate(()=>wireIds()),group);
  await touch('touchStart',[[220,120]]);await touch('touchStart',[[220,120],[360,120]]);await touch('touchMove',[[180,155],[360,155]]);await touch('touchEnd',[]);
  assert.deepEqual(await page.evaluate(()=>wireIds()),group);assert.equal(await page.evaluate(()=>openbwTouchStats().mode),'idle');
  const width=await page.locator('#screen').evaluate(c=>c.width);assert(width<640);
  await touch('touchStart',[[170,80]]);await touch('touchMove',[[390,270]]);await page.evaluate(()=>openbwAndroidSuspend());await touch('touchEnd',[]);await page.evaluate(()=>openbwAndroidResume());assert.deepEqual(await page.evaluate(()=>wireIds()),group);
  report.checks.push('Mineral tap gathers; drag selects a group; cancelled drag, two-finger pan/pinch and background interruption preserve selection without stray orders; pinch changes engine resolution');
  assert.deepEqual(report.errors,[]);console.log('PASS',report.checks);
 }finally{fs.writeFileSync(path.join(root,'validation/polish-v11.json'),JSON.stringify(report,null,2)+'\n');await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

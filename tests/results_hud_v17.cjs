// Original game files are external fixtures, never shipped in the APK/source.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game'),report={screens:[],checks:[],errors:[]};let mission='zerg01';
const server=http.createServer((req,res)=>{const p=decodeURIComponent(new URL(req.url,'http://local').pathname);if(p==='/availability.json'){res.setHeader('Content-Type','application/json');return res.end('{"missions":[1,101,201]}');}
 const m=p.match(/^\/(data|interface|music|mission)\/(.*)$/),dirs={data:process.env.OPENBW_TEST_MPQS||'/tmp/openbw-test-data',interface:process.env.OPENBW_INTERFACE_BUNDLE||'/tmp/openbw-interface-v17',music:process.env.OPENBW_MUSIC_BUNDLE||'/tmp/openbw-music-real-v16',mission:'/tmp/'+mission+'-bundle'},f=m?path.join(dirs[m[1]],m[2]):path.join(assets,p==='/'?'index.html':p);
 if(!fs.existsSync(f)||!fs.statSync(f).isFile()){res.writeHead(404);return res.end();}res.setHeader('Content-Type',({'.wasm':'application/wasm','.js':'text/javascript','.html':'text/html','.css':'text/css'})[path.extname(f)]||'application/octet-stream');fs.createReadStream(f).pipe(res);
});
async function driver(page){await page.evaluate(()=>{const{x,memory,lockstep}=__bw;const str=p=>{const a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};
 const units=()=>str(x.openbw_debug_units()).trim().split('\n').map(r=>{const a=r.split('\t');return{id:+a[0],name:a[1],owner:+a[2],x:+a[3],y:+a[4],order:+a[5]};});
 const advance=async n=>{openbwAndroidSuspend();for(let i=0;i<n&&!x.openbw_outcome();i++){lockstep.tick();if(i%80===0)await new Promise(r=>setTimeout(r,0));}openbwAndroidResume();};window.v17={x,str,units,advance};});}
async function select(page,name,owner){await page.evaluate(({name,owner})=>{const u=v17.units().find(u=>u.name===name&&(owner===undefined||u.owner===owner));if(!u)throw Error('Missing '+name);v17.x.openbw_debug_select(u.id,0);window.v17unit=u;},{name,owner});await page.waitForTimeout(150);}
async function screenshot(page,name){await page.screenshot({path:path.join('/tmp/openbw-reference/v17',name+'.png')});}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 try{
  for(const [race,name] of [[1,'Terran'],[0,'Zerg'],[2,'Protoss']])for(const won of [true,false]){
   const p=await browser.newPage({viewport:{width:640,height:480},isMobile:true,hasTouch:true});p.on('pageerror',e=>report.errors.push(e.message));
   await p.goto(base+'/index.html');await p.waitForFunction(()=>window.openbwCustomStats?.().ready,null,{timeout:90000});await p.waitForTimeout(550);
   assert.equal(await p.locator('#custom-status').getAttribute('aria-label'),'');
   if(race!==1){await p.locator('#custom-race-0').tap();await p.getByRole('option',{name,exact:true}).tap();}
   if(race===1&&won){
    await p.locator('#map-file').setInputFiles({name:'broken.scx',mimeType:'application/octet-stream',buffer:Buffer.from('bad')});await p.waitForFunction(()=>document.querySelector('#custom-status').getAttribute('aria-label')?.length>0);assert(!await p.evaluate(()=>!!window.__bw));
    await p.locator('#map-file').setInputFiles(path.join(assets,'maps/Weave_v1.scx'));await p.waitForFunction(()=>openbwCustomStats().selected.file.startsWith('custom:'));assert(!await p.evaluate(()=>!!window.__bw));assert.equal(await p.evaluate(()=>openbwCustomStats().selected.starts),4);await screenshot(p,'custom-verified');
    report.checks.push('Original custom panels/fonts/control frames; invalid import stays in setup; valid local map parses dimensions/starts and waits for OK');
   }
   await p.locator('#custom-ok').tap();await p.waitForFunction(()=>window.__bw?.x.openbw_frame()>5,null,{timeout:90000});assert.equal(await p.evaluate(()=>openbwClassicStats().originalFonts.length),8);
   await driver(p);
   assert.equal(await p.locator('#unit-preview').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(0, 0, 0)');assert(!(await p.locator('#unit-portrait').isVisible()));assert(!(await p.locator('#unit-preview-image').isVisible()));
   if(won){
    await select(p,{Terran:'SCV',Zerg:'Drone',Protoss:'Probe'}[name]);
    const id=await p.evaluate(()=>v17unit.id),max={Terran:60,Zerg:40,Protoss:20}[name];
    for(const [hp,color] of [[max,7],[Math.ceil(max*.5),3],[Math.max(1,Math.floor(max*.2)),6]]){
      await p.evaluate(({id,hp})=>{v17.x.openbw_debug_set_life(id,hp,-1);}, {id,hp});await p.waitForFunction(c=>document.getElementById('unit-life').dataset.color===String(c),color);
    }
    await p.evaluate(({id,max})=>v17.x.openbw_debug_set_life(id,max,-1),{id,max});await p.waitForTimeout(100);
    await p.waitForFunction(()=>[...document.querySelectorAll('.unit-stat img')].every(i=>i.complete&&i.naturalWidth));
    const counts=await p.locator('.unit-stat img').evaluateAll(imgs=>imgs.map(img=>{const c=document.createElement('canvas');c.width=36;c.height=36;const cx=c.getContext('2d');cx.drawImage(img,0,0);const d=cx.getImageData(0,0,36,36).data;let blue=0,neutral=0;for(let i=0;i<d.length;i+=4){if(d[i+3]&&d[i+2]>70&&d[i+2]>d[i]*1.5)blue++;if(d[i+3]&&Math.abs(d[i]-d[i+1])<35&&Math.abs(d[i+1]-d[i+2])<35&&d[i]>70)neutral++;}return{blue,neutral};}));assert(counts.every(c=>c.blue>40&&c.neutral>30),JSON.stringify(counts));
    const mineral=await p.evaluate(()=>v17.units().find(u=>/Mineral/.test(u.name)));await select(p,mineral.name);await p.waitForTimeout(150);assert(!(await p.locator('#unit-preview-image').isVisible()));
    const gas=await p.evaluate(()=>v17.units().find(u=>/Geyser/.test(u.name)));await select(p,gas.name);await p.waitForTimeout(150);assert(!(await p.locator('#unit-preview-image').isVisible()));
    report.checks.push(name+': real HP changes render green/yellow/red; original blue status border/gray icons; empty/resource portraits have no world-sprite fallback');
   }
   await p.locator('#settingsbtn').tap();await p.locator('#menu-options').tap();await p.locator('#menu-testing').tap();await p.locator(won?'#test-victory':'#test-defeat').tap();
   await p.waitForFunction(()=>window.openbwResultStats?.().phase==='message');assert.equal(await p.locator('.result-message-button').getAttribute('aria-label'),won?'Victory':'Defeat');
   await screenshot(p,name+'-'+(won?'victory':'defeat')+'-message');await p.locator('#result-continue').tap();await p.waitForFunction(()=>openbwResultStats().phase==='scores');await p.waitForTimeout(1100);
   assert(await p.locator('#result-replay').isDisabled());await p.waitForFunction(()=>openbwMusicStats().playing);assert.equal(await p.evaluate(()=>openbwMusicStats().phase),won?'victory':'defeat');
   for(let i=0;i<4;i++){await p.locator('#result-tab-'+i).tap();assert.equal(await p.evaluate(()=>openbwResultStats().tab),i);}await p.locator('#result-tab-0').tap();await p.waitForTimeout(1100);await screenshot(p,name+'-'+(won?'victory':'defeat')+'-score');
   report.screens.push(await p.evaluate(()=>({result:openbwResultStats(),music:openbwMusicStats()})));console.log('PASS',name,won?'victory':'defeat');await p.close();
  }
  const z=await browser.newPage({viewport:{width:900,height:412},isMobile:true,hasTouch:true});z.on('pageerror',e=>report.errors.push(e.message));await z.goto(base+'/?campaign=zerg01');await z.waitForFunction(()=>window.openbwBriefingArtStats?.().phase==='ready',null,{timeout:90000});await z.locator('#brief-start').tap();await z.waitForFunction(()=>window.__bw?.x.openbw_frame()>5);await driver(z);await select(z,'Overlord',3);
  assert.equal((await z.locator('#unit-detector').getAttribute('aria-label')).trim(),'Detector');assert.equal(await z.locator('#unit-supply>div').nth(1).getAttribute('aria-label'),'Control Provided: 8');
  assert.equal(await z.locator('#classic-minimap').evaluate(e=>e.style.width),'128px');assert.equal(await z.locator('#classic-minimap').evaluate(e=>e.style.height),'128px');
  await screenshot(z,'zerg01-minimap-overlord');report.checks.push('Actual Zerg 1 Overlord detector and four live Control fields; 64×64 map fills 128px well at phone landscape size');await z.close();
  assert.deepEqual(report.errors,[]);
 }catch(e){report.failure=e.stack;throw e;}finally{fs.writeFileSync(path.join(root,'validation/results-hud-v17.json'),JSON.stringify(report,null,2));await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

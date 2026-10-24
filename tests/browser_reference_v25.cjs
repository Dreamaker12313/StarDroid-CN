// Private original game files are supplied externally; none are bundled.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'app/src/main/assets/game'),catalog=JSON.parse(fs.readFileSync(path.join(root,'missions.json'))),fixtures=process.env.OPENBW_V22_FIXTURES||'/tmp/openbw-v22-fixtures';
let mission='zerg02';const report={errors:[],method:'Retained 0.22 browser assets run unchanged in touch-enabled Chromium at 960 x 640. Original imported files are supplied externally. Captures cover menus, Zerg 2 HUD and settings, outcome/results, and custom setup. Diagnostic selection and forced victory make matched scenes repeatable.'};
const server=http.createServer((req,res)=>{
 const p=decodeURIComponent(new URL(req.url,'http://local').pathname);
 if(p==='/availability.json'){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({missions:catalog.map(m=>m.code)}));}
 const match=p.match(/^\/(data|interface|music-broodwar|music|story-broodwar|story|mission)\/(.*)$/);
 const f=match?path.join(match[1]==='data'?'/tmp/openbw-test-data':path.join(fixtures,match[1]==='mission'?mission:match[1]),match[2]):path.join(assets,p==='/'?'index.html':p);
 if(!fs.existsSync(f)||!fs.statSync(f).isFile()){res.writeHead(404);return res.end();}
 res.setHeader('Content-Type',({'.wasm':'application/wasm','.js':'text/javascript','.html':'text/html','.css':'text/css'})[path.extname(f)]||'application/octet-stream');fs.createReadStream(f).pipe(res);
});
async function boot(p,base,id){mission=id;await p.goto(base+'/?campaign='+id);
 await p.waitForFunction(()=>window.openbwStoryStats?.().active||window.openbwBriefingArtStats?.().phase==='ready'||document.querySelector('#msg')?.textContent.includes('failed'),null,{timeout:90000});
 for(let i=0;i<12&&await p.evaluate(()=>openbwStoryStats().active);i++){await p.locator('#story-screen').tap();await p.waitForTimeout(30);}
 await p.waitForFunction(()=>window.openbwBriefingArtStats?.().phase==='ready');
 await p.locator('#brief-start').tap();await p.waitForFunction(()=>window.__bw?.x.openbw_frame()>3);
 await p.evaluate(({owner,protectHives})=>{
  const{x,memory,lockstep}=__bw,str=p=>{const a=new Uint8Array(memory.buffer);let e=p;while(a[e])e++;return new TextDecoder().decode(a.subarray(p,e));};
  const units=()=>str(x.openbw_debug_units()).trim().split('\n').filter(Boolean).map(r=>{const a=r.split('\t');return{id:+a[0],name:a[1],owner:+a[2],x:+a[3],y:+a[4],order:+a[5]};});
  const u16=n=>[n&255,n>>8&255],send=rows=>{const bytes=new Uint8Array(rows.flatMap(r=>[...u16(r.length),...r]));new Uint8Array(memory.buffer,x.openbw_in_ptr(bytes.length),bytes.length).set(bytes);x.openbw_apply(owner,bytes.length);};
  const select=ids=>{send([[9,ids.length,...ids.flatMap(u16)]]);ids.forEach((id,i)=>x.openbw_debug_select(id,i?1:0));};
  const advance=async(n,heal=false)=>{openbwAndroidSuspend();for(let i=0;i<n&&!x.openbw_outcome();i++){if(heal&&i%60===0)for(const u of units().filter(u=>u.owner===owner||(protectHives&&u.name==='Hive')))x.openbw_debug_set_life(u.id,10000,-1);lockstep.tick();if(i%120===0)await new Promise(r=>setTimeout(r,0));}openbwAndroidResume();};
  window.ct={x,str,units,owner,send,u16,select,advance};
 },{owner:catalog.find(m=>m.id===id).player,protectHives:id==='expzerg01'});
}
async function select(p,name,owner){await p.evaluate(({name,owner})=>{const u=ct.units().find(u=>u.name===name&&(owner===null||u.owner===(owner??ct.owner)));if(!u)throw Error('Missing '+name);ct.select([u.id]);}, {name,owner});await p.waitForTimeout(150);}
async function resume(p){await p.evaluate(()=>{for(let i=0;i<4&&openbwMenuStats().opened;i++)openbwBack();});}
(async()=>{
 const out=process.env.OPENBW_PARITY_SHOTS||'/tmp/openbw-browser-reference';fs.mkdirSync(out,{recursive:true});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({executablePath:process.env.OPENBW_CHROME,headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 const p=await browser.newPage({viewport:{width:960,height:640},hasTouch:true,isMobile:true});
 p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>{localStorage.setItem('openbw-profiles','["Tester"]');localStorage.setItem('openbw-profile','Tester');});
 const shot=async n=>{await p.waitForTimeout(650);await p.screenshot({path:path.join(out,n+'.png')});};
 try {
 await p.goto(base+'/title.html?menu');await p.waitForFunction(()=>window.openbwTitleStats?.().loaded,null,{timeout:90000});await shot('title');
 await p.locator('#title-single').tap();await shot('chooser');await p.locator('#game-starcraft').tap();await shot('registry');await p.locator('#registry-ok').tap();await shot('campaign');await p.locator('#campaign-zerg').tap();await shot('missions');
 await p.addScriptTag({url:base+'/mpq-decoder.js'});report.layouts=await p.evaluate(async()=>{const d=await MPQDecoder.create(),a=[];for(const n of ['patch_rt.mpq','BROODAT.MPQ','STARDAT.MPQ'])a.push(new Uint8Array(await fetch('./data/'+n).then(r=>r.arrayBuffer())));let out={};for(const n of ['glulogin','gluhist','glucustm','stat_f10','stat_f10_1','stat_f10_2','glugamemode']){for(const b of a){const v=d.read(b,'rez/'+n+'.bin');if(v){out[n]=OpenBWOriginal.dialog(v).widgets;break;}}}return out;});
 await boot(p,base,'zerg02');await select(p,'Hatchery');await shot('hatchery');await select(p,'Larva');await shot('larva');
 await p.locator('#settingsbtn').tap();await shot('menu');await p.locator('#menu-options').tap();await shot('options');
 for(const [id,n] of [['menu-sound','sound'],['menu-game-options','speed'],['menu-video','video'],['menu-testing','testing']]){await p.locator('#'+id).tap();await shot(n);report[n]=await p.locator('#game-menu').innerText();await p.evaluate(()=>openbwBack());}
 await p.locator('#menu-test-victory').tap();await p.waitForFunction(()=>openbwResultStats().phase==='message');await shot('victory');await p.locator('#result-continue').tap();await shot('results');
 await p.goto(base+'/');await p.waitForFunction(()=>window.openbwCustomStats?.().ready,null,{timeout:90000});await shot('custom');report.custom=await p.evaluate(()=>openbwCustomStats());
 assert.deepEqual(report.errors,[]);report.passed=true;
 } finally { fs.writeFileSync(path.join(root,'validation/browser-reference-v25.json'),JSON.stringify(report,null,2));await browser.close();server.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});

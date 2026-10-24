// Isolate scheduling from SMK decoding; real data/decoding is checked in the browser.
const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..');let now=0,scheduled,selected=0,talking=false,roll=0,draws=0;const requested=[];
const canvases=new Map(),element=id=>{if(!canvases.has(id))canvases.set(id,{hidden:true,width:1,height:1,style:{},setAttribute(){},getContext(){return{clearRect(){},createImageData(w,h){return{data:new Uint8ClampedArray(w*h*4)}},putImageData(){draws++}}}});return canvases.get(id);};
const math=Object.create(Math);math.random=()=>((roll++%100)+.5)/100;
const context={window:{},document:{hidden:false,getElementById:element},Math:math,Map,DataView,TextDecoder,Uint8ClampedArray,performance:{now:()=>now},requestAnimationFrame:f=>scheduled=f,setTimeout,clearTimeout,
 Worker:class{postMessage({id}){queueMicrotask(()=>this.onmessage({data:{id,width:1,height:1,frames:4,interval:20,rgba:new Uint8Array(16).fill(255).buffer}}));}terminate(){}}};
vm.runInNewContext(fs.readFileSync(path.join(root,'web/portraits.js'),'utf8'),context);
// Two synthetic original-format entries: Marine weights and Dropship's unused fid02.
const dat=new Uint8Array(24),dv=new DataView(dat.buffer);for(let i=0;i<4;i++)dv.setUint32(i*4,i%2+1,true);[85,5,5,5].forEach((n,i)=>dat[(8+i)*2]=n);[90,5,0,5].forEach((n,i)=>dat[(8+i)*2+1]=n);
const text=Buffer.from('Marine0\0Dropship0\0'),tbl=Buffer.alloc(6+text.length);tbl.writeUInt16LE(2);tbl.writeUInt16LE(6,2);tbl.writeUInt16LE(14,4);text.copy(tbl,6);
const read=name=>{if(name==='arr/portdata.dat')return dat;if(name==='arr/portdata.tbl')return new Uint8Array(tbl);requested.push(name);return new Uint8Array([1]);};
const x={openbw_portrait_for_type:id=>id,openbw_selected_type:()=>selected,openbw_portrait_talking:()=>talking,openbw_frame:()=>0};
const api=context.window.OpenBWPortraits(x,read);async function tick(ms=80){now+=ms;scheduled(now);await new Promise(r=>setImmediate(r));}const surface=()=>api.stats().surfaces[0];
(async()=>{const checks=[];await tick();for(let i=0;i<1000;i++)await tick();assert.deepEqual([...surface().loops],[851,50,50,50]);checks.push('85% base idle; three rare variants each 5%; fid03 is reachable');
selected=1;roll=0;await tick();for(let i=0;i<1000;i++)await tick();assert.deepEqual([...surface().loops],[901,50,0,50]);checks.push('Per-portrait DAT weights respected; zero-weight fid02 never selected');
await tick(20);api.state(true);const paused={draws,frame:surface().frame,loops:[...surface().loops]};for(let i=0;i<30;i++)await tick(1000);assert.equal(draws,paused.draws);assert.equal(surface().frame,paused.frame);assert.deepEqual([...surface().loops],paused.loops);api.state(false);await tick(20);assert.equal(surface().frame,paused.frame+1);checks.push('Pause holds the current frame and resumes without restarting/cycling clips');
talking=true;await tick();let last=surface().variant;for(let i=0;i<10;i++){await tick();assert.notEqual(surface().variant,last);last=surface().variant;}checks.push('Speech uses its separate variants without immediate repeats');
selected=-1;talking=false;await tick();const empty=draws;for(let i=0;i<20;i++)await tick();assert.equal(draws,empty);assert.equal(surface().visible,false);checks.push('No selection stays black and does not continue decoding/painting');
api.close();fs.writeFileSync(path.join(root,'validation/portrait-scheduler-v18.json'),JSON.stringify({checks,errors:[]},null,2));console.log('PASS',checks);
})().catch(e=>{console.error(e);process.exitCode=1;api.close();});

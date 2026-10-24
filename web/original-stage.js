(() => {
 const stage=document.createElement('div');stage.id='game-stage';
 for(const el of [...document.body.children])if(el.tagName!=='SCRIPT')stage.append(el);
 document.body.append(stage);
 stage.addEventListener('scroll',()=>{stage.scrollLeft=0;stage.scrollTop=0;});
 // Title, story and briefing stay in their original 4:3 frame.
 const read=key=>{try{return localStorage.getItem(key)==='1';}catch{return false;}};
 let wide=read('openbw-widescreen'),allowZoomOut=read('openbw-zoom-out'),active=false,width=640,engine=null;
 function resize(){
   const previous=width;
   width=active&&wide?Math.max(640,Math.min(1600,Math.round(innerWidth/innerHeight*480))):640;
   const css=document.documentElement.style;
   css.setProperty('--original-scale',Math.min(innerWidth/width,innerHeight/480));
   css.setProperty('--game-width',width+'px');css.setProperty('--wide-extra',(width-640)+'px');
   stage.classList.toggle('wide',width>640);
   if(previous!==width)dispatchEvent(new CustomEvent('openbwdisplaychange',{detail:{previous,width}}));
 }
 function save(){try{localStorage.setItem('openbw-widescreen',wide?'1':'0');localStorage.setItem('openbw-zoom-out',allowZoomOut?'1':'0');}catch{}}
 const panel=document.createElement('div');panel.id='menu-display';
 panel.innerHTML='<label><input id="allow-zoom-out" type="checkbox"> Allow zoom out</label><label><input id="widescreen" type="checkbox"> Widescreen</label><label for="display-zoom">View zoom</label><select id="display-zoom" aria-label="View zoom"></select><p>Pinch to zoom. Drag to pan. Hold briefly, then drag to select units.</p>';
 const zoomSelect=panel.querySelector('select'),outCheck=panel.querySelector('#allow-zoom-out'),wideCheck=panel.querySelector('#widescreen');
 function update(){
   const value=engine?.getZoom()||1;
   const levels=[.5,.67,1,1.25,1.5,2].filter(v=>allowZoomOut||v>=1);
   if(!levels.some(v=>Math.abs(v-value)<.005))levels.push(value);
   zoomSelect.replaceChildren(...levels.sort((a,b)=>a-b).map(v=>new Option(Math.round(v*100)+'%',String(v),false,Math.abs(v-value)<.005)));
   outCheck.checked=allowZoomOut;wideCheck.checked=wide;
 }
 outCheck.onchange=()=>{allowZoomOut=outCheck.checked;save();if(!allowZoomOut&&engine?.getZoom()<1)engine.setZoom(1);update();};
 wideCheck.onchange=()=>{wide=wideCheck.checked;save();resize();};
 zoomSelect.onchange=()=>{engine?.setZoom(+zoomSelect.value);update();};
 window.OpenBWDisplay={width:()=>width,allowZoomOut:()=>allowZoomOut,panel,
   activate(){active=true;resize();},bind(value){engine=value;update();},update};
 window.openbwDisplayStats=()=>({active,width,height:480,widescreen:wide,allowZoomOut,zoom:engine?.getZoom()||1});
 resize();addEventListener('resize',resize);
})();

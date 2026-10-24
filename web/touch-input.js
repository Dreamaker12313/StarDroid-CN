  // Touch controls, inside bindInput. Mouse and keyboard paths stay native.
  // Tap own unit: select. Tap ground/enemy/resource: smart order if selected.
  // Drag: pan. Hold, then drag: selection box. Non-worker taps: attack-move.
  let holdTimer=0,gesture=null,lastTouchTap={time:-Infinity,x:0,y:0};
  // Keep the native tile-snapped ghost above the fingertip until confirmation.
  let placement=null;
  const placementBar=document.createElement('div');placementBar.id='touch-placement';placementBar.hidden=true;
  const confirmBuild=document.createElement('button'),cancelBuild=document.createElement('button');
  confirmBuild.id='touch-build-confirm';cancelBuild.id='touch-build-cancel';
  for(const [b,label] of [[confirmBuild,'Build'],[cancelBuild,'Cancel']]){b.type='button';b.textContent=label;placementBar.append(b);}
  document.getElementById('game-stage').append(placementBar);
  const clearPlacement=()=>{placement=null;placementBar.hidden=true;};
  const aimBuild=t=>{const r=canvas.getBoundingClientRect(),[px,py]=xy(t);placement={x:px,y:Math.max(1,Math.round(py-48*canvas.height/r.height))};x.openbw_mouse_move(placement.x,placement.y);placementBar.hidden=false;confirmBuild.disabled=!!x.openbw_placement_valid&&!x.openbw_placement_valid(placement.x,placement.y);};
  confirmBuild.onclick=()=>{if(!placement||touchBlocked()||x.openbw_cursor()!==2)return;window.openbwBuildClick?.();const p=placement;x.openbw_mouse_move(p.x,p.y);x.openbw_mouse_button(1,1,p.x,p.y,1);x.openbw_mouse_button(0,1,p.x,p.y,1);};
  cancelBuild.onclick=()=>{window.openbwBuildClick?.();x.openbw_key(1,27,41);x.openbw_key(0,27,41);clearPlacement();parkTouch();};
  const placementTick=()=>{if(placement&&x.openbw_cursor()!==2){clearPlacement();parkTouch();}if(placement&&x.openbw_placement_valid)confirmBuild.disabled=!x.openbw_placement_valid(placement.x,placement.y);if(window.openbwTouchLabel){openbwTouchLabel(confirmBuild,'Build');openbwTouchLabel(cancelBuild,'Cancel');}requestAnimationFrame(placementTick);};requestAnimationFrame(placementTick);
  const parkTouch=()=>x.openbw_mouse_move(-1,-1);
  const touchBlocked=()=>document.hidden||window.openbwAndroidStats?.().paused;
  function cancelTouch(){
    clearTimeout(holdTimer);
    if(gesture){x.openbw_touch_cancel?.();gesture=null;parkTouch();}
    clearPlacement();parkTouch();
    lastTouchTap.time=-Infinity;
  }
  window.openbwCancelTouch=cancelTouch;
  const midpoint=e=>({x:(e.touches[0].clientX+e.touches[1].clientX)/2,y:(e.touches[0].clientY+e.touches[1].clientY)/2,
    distance:Math.max(1,Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY))});
  canvas.addEventListener('touchstart',e=>{
    e.preventDefault();if(touchBlocked())return cancelTouch();
    if(e.touches.length>=2){
      if(gesture?.mode==='multi')return;
      clearTimeout(holdTimer);clearPlacement();
      x.openbw_touch_cancel?.();const m=midpoint(e);
      gesture={mode:'multi',...m,startDistance:m.distance,startZoom:zoom};return;
    }
    if(gesture)return;
    const t=e.touches[0],[px,py]=xy(t);
    if(x.openbw_cursor()===2){gesture={mode:'place',id:t.identifier};aimBuild(t);return;}
    gesture={mode:'tap',id:t.identifier,x0:px,y0:py,x:px,y:py,cx:t.clientX,cy:t.clientY,time:performance.now(),targeting:x.openbw_touch_action?.(px,py)===2};
    const pending=gesture;holdTimer=setTimeout(()=>{
      if(gesture===pending&&gesture.mode==='tap'&&!gesture.targeting&&!touchBlocked())gesture.mode='held';
    },350);
  },{passive:false});
  canvas.addEventListener('touchmove',e=>{
    e.preventDefault();if(!gesture)return;if(touchBlocked())return cancelTouch();
    const g=gesture;
    if(g.mode==='multi'){
      if(e.touches.length<2)return;
      const m=midpoint(e),r=canvas.getBoundingClientRect();
      x.openbw_pan(Math.round((g.x-m.x)*canvas.width/r.width),Math.round((g.y-m.y)*canvas.height/r.height));
      vx=(m.x-r.left)*canvas.width/r.width;vy=(m.y-r.top)*canvas.height/r.height;
      zoom=Math.min(zoomMax(),Math.max(zoomMin(),g.startZoom*m.distance/g.startDistance));applyZoom();
      g.x=m.x;g.y=m.y;parkTouch();return;
    }
    const t=[...e.touches].find(t=>t.identifier===g.id);if(!t)return;
    if(g.mode==='place'){aimBuild(t);return;}
    const [px,py]=xy(t);g.x=px;g.y=py;
    if((g.mode==='tap'||g.mode==='held')&&Math.hypot(t.clientX-g.cx,t.clientY-g.cy)>10){
      clearTimeout(holdTimer);
      g.mode=g.targeting?'aim':g.mode==='held'?'box':'pan';
      if(g.mode==='box'){x.openbw_mouse_move(g.x0,g.y0);x.openbw_mouse_button(1,1,g.x0,g.y0,1);}
    }
    if(g.mode==='pan'){
      const r=canvas.getBoundingClientRect();
      x.openbw_pan(Math.round((g.cx-t.clientX)*canvas.width/r.width),Math.round((g.cy-t.clientY)*canvas.height/r.height));
      g.cx=t.clientX;g.cy=t.clientY;parkTouch();
    }else if(g.mode==='box'||g.mode==='aim')x.openbw_mouse_move(px,py);
  },{passive:false});
  canvas.addEventListener('touchend',e=>{
    e.preventDefault();if(!gesture)return;if(touchBlocked())return cancelTouch();
    const g=gesture;clearTimeout(holdTimer);
    if(g.mode==='multi'){
      if(!e.touches.length){gesture=null;parkTouch();try{localStorage.setItem('openbw-zoom',zoom.toFixed(2));}catch{}}
      return;
    }
    const t=[...e.changedTouches].find(t=>t.identifier===g.id);if(!t)return;
    if(g.mode==='place'){aimBuild(t);gesture=null;return;}
    const [px,py]=xy(t),now=performance.now();
    if(g.mode==='box')x.openbw_mouse_button(0,1,px,py,1);
    else if(g.mode!=='pan'){
      const action=g.mode==='held'?0:(x.openbw_touch_action?.(px,py)||0);
      if(action===3)x.openbw_touch_attack?.();
      const button=action===1?3:1;
      const twice=button===1&&action===0&&now-lastTouchTap.time<300&&Math.hypot(t.clientX-lastTouchTap.x,t.clientY-lastTouchTap.y)<20;
      x.openbw_mouse_move(px,py);x.openbw_mouse_button(1,button,px,py,twice?2:1);x.openbw_mouse_button(0,button,px,py,twice?2:1);
      lastTouchTap={time:button===1&&action===0?now:-Infinity,x:t.clientX,y:t.clientY};
    }
    gesture=null;parkTouch();
  },{passive:false});
  canvas.addEventListener('touchcancel',cancelTouch,{passive:false});
  addEventListener('blur',cancelTouch);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)cancelTouch();});
  window.openbwTouchStats=()=>({mode:gesture?.mode||'idle',controls:'drag-pan-hold-select-tap-attack',placement});

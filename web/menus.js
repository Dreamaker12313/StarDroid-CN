window.OpenBWMenus = function({x,campaign,pause,getPaused,toMainMenu,art}) {
  const $=id=>document.getElementById(id),root=$('game-menu');
  let page='main',parent='main',wasPaused=false,opened=false,confirmAction=null;
  // Existing controls keep their handlers when moved into the new menu pages.
  const settings=$('settings'),general=document.createElement('div'),sound=document.createElement('div');
  general.id='menu-general';sound.id='menu-audio';
  for(const el of [...settings.children])if(el.id!=='music-settings' && el.id!=='testing-settings' && el.id!=='opt-resign')general.appendChild(el);
  general.querySelectorAll('h3').forEach(e=>e.remove());
  $('opt-resign').hidden=true;
  const muteLabel=document.createElement('label'),muteCheck=document.createElement('input');muteCheck.type='checkbox';muteCheck.id='menu-mute';
  muteCheck.checked=localStorage.getItem('openbw-muted')==='1';muteCheck.onchange=()=>$('mute').click();
  muteLabel.append(muteCheck,' Mute all sound');sound.append(muteLabel,$('music-settings'));
  const content={general,sound,video:OpenBWDisplay.panel,controls:$('help'),testing:$('testing-settings'),objectives:$('campaign-objectives')};
  // Keep every live control in the document even before the menu is first opened.
  // Music/outcome callbacks and settings diagnostics look them up by ID.
  for(const el of Object.values(content)){el.hidden=true;settings.append(el);}
  const titles={main:'Game Menu',options:'Game Options',end:'End Mission',general:'Game Speed',video:'Video Options',sound:'Sound & Music',controls:'Controls',testing:'Cheats',objectives:'Mission Objectives',confirm:'End Mission'};
  $('campaign-objectives-close').hidden=true;
  $('menu-objectives').hidden=!campaign;
  $('menu-restart').textContent='Restart Mission';
  $('menu-restart').hidden=!campaign;
  $('menu-end').textContent=campaign?'End Mission':'End Game';
  const assets=art||{};
  if(assets.sounds){OpenBWOriginal.buttonSounds(root,assets.sounds,true);OpenBWOriginal.buttonSounds($('settingsbtn'),assets.sounds,true);}
  const layoutBindings={main:[['menu-save',1],['menu-load',2],['menu-options',3],['menu-help',4],['menu-objectives',5],['menu-end',6],['menu-resume',65533]],options:[['menu-game-options',1],['menu-sound',2],['menu-video',3],['menu-network',4]],end:[['menu-restart',1],['menu-quit',2],['menu-exit',3]]};
  for(const [key,bindings] of Object.entries(layoutBindings)){const layout=assets.layouts?.[key];if(!layout)continue;for(const [id,index] of bindings){const w=layout.get(index),el=$(id);OpenBWOriginal.place(el,w);const label=document.createElement('span');OpenBWOriginal.buttonText(el,label,w.text.slice(1),w.flags&0x800?assets.font:assets.small,2,4);el.replaceChildren(label);} }
  $('menu-testing').style.top='172px';
  $('menu-test-victory').style.top='208px';
  $('menu-test-victory').hidden=!window.openbwTestingStats?.().offline;
  $('menu-test-victory').onclick=()=>$('test-victory').click();
  root.querySelectorAll('.sc-button').forEach(b=>{if(!b.querySelector('canvas')){const value=b.textContent,label=document.createElement('span');OpenBWOriginal.buttonText(b,label,value,assets.font,2,4);b.replaceChildren(label);}});
  // Reuse the original blue palette and bitmap labels on the app's settings controls.
  for(const section of [general,sound,content.video,content.testing]){
    for(const label of section.querySelectorAll('label')){
      for(const node of [...label.childNodes])if(node.nodeType===Node.TEXT_NODE&&node.textContent.trim()){
        const span=document.createElement('span');span.className='setting-label';
        OpenBWOriginal.text(span,node.textContent.trim(),assets.small);node.replaceWith(span);
      }
    }
    for(const heading of section.querySelectorAll('h3'))OpenBWOriginal.text(heading,heading.textContent,assets.small);
  }
  // Keep mouse-only controls with control help; speed remains easy to find.
  for(const id of ['opt-altesc','opt-mouselock']){const el=$(id)?.closest('label');if(el)content.controls.append(el);}
  if($('opt-lines')?.closest('label'))content.video.prepend($('opt-lines').closest('label'));
  if($('opt-fullscreen'))content.video.append($('opt-fullscreen'));
  function show(next) {
    if(next==='video')OpenBWDisplay.update();
    page=next;root.dataset.page=next;root.classList.toggle('settings-sheet',!!content[next]);
    const frame=assets.dialogFrame?.(content[next]?368:264,content[next]?330:288);if(frame)root.querySelector('.sc-dialog').style.backgroundImage='url('+frame+')';
    root.querySelectorAll('.menu-page').forEach(e=>e.hidden=true);
    for(const el of Object.values(content)){el.hidden=true;settings.append(el);}
    OpenBWOriginal.text($('game-menu-heading'),titles[next]||'Game Menu',assets.font); 
    if(next==='main' || next==='options' || next==='end' || next==='confirm')$('menu-'+(next==='main'?'main':next==='options'?'options-page':next==='end'?'end-page':'confirm')).hidden=false;
    else {const el=content[next];el.hidden=false;$('menu-content-body').replaceChildren(el);$('menu-content').hidden=false;}
    const first=root.querySelector('.menu-page:not([hidden]) button');first?.focus({preventScroll:true});
  }
  function open() {
    if(opened)return;window.openbwCancelTouch?.();wasPaused=getPaused();opened=true;pause(true);root.hidden=false;document.body.classList.add('menu-open');show('main');
  }
  function close() {
    if(!opened)return;root.hidden=true;opened=false;document.body.classList.remove('menu-open');pause(wasPaused);$('settingsbtn').focus({preventScroll:true});
  }
  const targeting=()=>!!x.openbw_cursor() || window.openbwClassicStats?.().submenu;
  function back(){if(!opened){if(targeting()){x.openbw_key(1,27,41);x.openbw_key(0,27,41);}else open();return;}if(page==='main'){close();return;}show(page==='options'||page==='end'?'main':parent);}
  $('settingsbtn').onclick=()=>opened?close():open();
  $('menu-resume').onclick=close;
  $('menu-options').onclick=()=>{parent='main';show('options');};
  for(const [id,next] of [['menu-game-options','general'],['menu-sound','sound'],['menu-help','controls'],['menu-video','video'],['menu-testing','testing'],['menu-objectives','objectives']])$(id).onclick=()=>{parent=next==='objectives'||next==='controls'?'main':'options';show(next);};
  root.querySelectorAll('.menu-back').forEach(b=>b.onclick=back);
  $('menu-restart').onclick=()=>{parent='end';titles.confirm=campaign?'Restart Mission':'Restart Game';$('menu-confirm-text').textContent='Restart from the beginning? Current progress will be lost.';confirmAction=()=>location.reload();show('confirm');};
  $('menu-end').onclick=()=>{parent='main';show('end');};
  $('menu-exit').onclick=()=>{parent='end';titles.confirm='Exit Program';$('menu-confirm-text').textContent='Exit StarDroid? Current progress will be lost.';confirmAction=()=>location.href='./native/exit';show('confirm');};
  $('menu-quit').onclick=()=>{parent='end';titles.confirm=campaign?'End Mission':'End Game';$('menu-confirm-text').textContent='Return to the main menu? Current progress will be lost.';confirmAction=toMainMenu;show('confirm');};
  $('menu-confirm-yes').onclick=()=>confirmAction?.();
  // Consume keyboard/game shortcuts while the dialog is active. Tab remains native.
  addEventListener('keydown',e=>{
    if(e.key==='F10'){e.preventDefault();e.stopImmediatePropagation();opened?close():open();return;}
    if(e.key==='Escape' && (opened || !targeting())) {e.preventDefault();e.stopImmediatePropagation();back();return;}
    if(opened){
      e.stopImmediatePropagation();
      if(e.key==='Tab'){
        const focusable=[...root.querySelectorAll('button,input,select')].filter(el=>!el.disabled && el.getClientRects().length);
        const index=focusable.indexOf(document.activeElement),next=(index+(e.shiftKey?-1:1)+focusable.length)%focusable.length;
        e.preventDefault();focusable[next]?.focus();
      }
    }
  },true);
  window.openbwBack=()=>{back();return true;};
  window.openbwMenuStats=()=>({opened,page,wasPaused});
  // Only the portrait Menu button remains on the battlefield.
  $('classic-console').appendChild($('settingsbtn'));
  $('topbar').hidden=true;
  return{open,close};
};

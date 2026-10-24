#!/usr/bin/env python3
"""Add the local title screen and original-style menu flow after classic prep."""
from pathlib import Path
import shutil
import re
r=Path(__file__).resolve().parents[1];d=r/'app/src/main/assets/game'
s=(d/'openbw.js').read_text()
def replace(old,new):
    global s
    assert old in s, 'Menu anchor changed: '+old[:100]
    s=s.replace(old,new,1)
replace("const toMainMenu = () => location.replace(location.origin + location.pathname);", "const toMainMenu = () => location.replace('./title.html?menu');")
replace('  OpenBWTesting(x, !link && !session.spectate);', '''  OpenBWTesting(x, !link && !session.spectate);
  OpenBWMenus({x, campaign:session.campaign, art:classicUI.art, toMainMenu,
    getPaused:()=>paused,
    pause(value){paused=value;stepClock=performance.now();missionUI?.suspend(value);
      x.openbw_set_paused?.(value?1:0);applyPause();}
  });''')
replace('x.openbw_key(1, sym, 0); x.openbw_key(0, sym, 0);', 'x.openbw_key(1, sym, sym===27?41:0); x.openbw_key(0, sym, sym===27?41:0);')
# Let the native Back button return from setup/briefing/loading; once the match is
# ready OpenBWMenus replaces this with its pause-preserving dialog navigation.
s="window.openbwBack = () => { location.replace('./title.html?menu'); return true; };\n"+s
# Expand the battlefield independently of the original menus and HUD pixels.
s=s.replace('Math.max(1, Math.min(window.innerWidth / 320, window.innerHeight / 240))', '2')
replace('const zoomMax = () => 2;', 'const zoomMax = () => 2;\nconst zoomMin = () => OpenBWDisplay.allowZoomOut() ? .5 : 1;')
s=s.replace('Math.max(1, parseFloat(localStorage', 'Math.max(zoomMin(), parseFloat(localStorage')
s=s.replace('Math.max(1, zoom * Math.exp', 'Math.max(zoomMin(), zoom * Math.exp')
replace('[Math.max(320, (window.innerWidth / zoom) | 0), Math.max(240, (window.innerHeight / zoom) | 0)]', '[Math.max(320, (OpenBWDisplay.width() / zoom) | 0), Math.max(240, (480 / zoom) | 0)]')
replace("  canvas.addEventListener('wheel', (e) => {", """  OpenBWDisplay.bind({getZoom:()=>zoom,setZoom(value){
    vx=canvas.width/2;vy=canvas.height/2;
    zoom=Math.max(zoomMin(),Math.min(zoomMax(),value));applyZoom();
    try{localStorage.setItem('openbw-zoom',zoom.toFixed(2));}catch{}
    x.openbw_mouse_move(-1,-1);
  }});
  addEventListener('openbwdisplaychange',e=>{
    window.openbwCancelTouch?.();
    x.openbw_resize(...winSize());
    x.openbw_pan(Math.round((e.detail.previous-e.detail.width)/(2*zoom)),0);
    vx=winSize()[0]/2;vy=winSize()[1]/2;x.openbw_mouse_move(-1,-1);
  });
  canvas.addEventListener('wheel', (e) => {""")
replace('    vx *= k; vy *= k;', '    vx *= k; vy *= k;\n    OpenBWDisplay.update();')
replace('  wireInput(canvas, x);', '  OpenBWDisplay.activate();\n  x.openbw_resize(...winSize());\n  wireInput(canvas, x);')
# Bitmap text on the battlefield, preserving the original fixed HUD rectangles.
replace('const r = [resIconURL(0), resIconURL(1), resIconURL(2)];', 'const r = classicUI.art.resourceIcons || [resIconURL(0), resIconURL(1), resIconURL(2)];')
replace("${ico(ri[0], 'min')}${min}", "${ico(ri[0], 'min')}<span class=\"resource-value\">${min}</span>")
replace("${ico(ri[1], 'gas')}${gas}", "${ico(ri[1], 'gas')}<span class=\"resource-value\">${gas}</span>")
replace('<span class="${cap}">${used}/${max}</span>', '<span class="resource-value ${cap}">${used}/${max}</span>')
replace("${used}/${max}</span></span>`;", "${used}/${max}</span></span>`;\n    for(const el of resEl.querySelectorAll('.resource-value'))OpenBWOriginal.text(el,el.textContent,classicUI.art.small,0,'left',el.classList.contains('cap')?6:7);")
replace('toastEl.textContent = msg;', "OpenBWOriginal.text(toastEl,msg,classicUI.art.small,624,'center',6);")
replace('d.textContent = line;', "OpenBWOriginal.text(d,line,classicUI.art.small,624);")
# The original statdata controls handle queues, research and incomplete units separately.
a=s.index('  // Producer status:');b=s.index('  // Resource HUD:',a)
s=s[:a]+"  const updateStatus = () => classicUI.production();\n\n"+s[b:]
# Replace the generic score table with the original result dialog and race artwork.
a=s.index('  // End-of-game score screen:');b=s.index('  // Debug (?debug',a)
s=s[:a]+'''  const toMainMenu = () => location.replace('./title.html?menu');
  const resultsUI = OpenBWResults({x,memory,classic:classicUI,race:interfaceRace,music:musicUI,saveReplay,
    exit:async()=>{
      if(session.campaign&&x.openbw_outcome()===1){
        const next=missionUI?.next();
        try{const available=await fetch('./availability.json').then(r=>r.json());if(next&&available.missions?.includes(next.code)){location.href='./native/mission/'+next.code;return;}}catch{}
      }
      toMainMenu();
    }
  });
  const showGameOver = (title, won) => { resultsUI.show(won); };

'''+s[b:]
# The custom file picker now selects a map; only the original OK button starts it.
a=s.index("$('map-file').addEventListener('change',");b=s.index('// --- multiplayer:',a)
s=s[:a]+s[b:]
s=s.replace('async function boot(session) {','async function boot(session) {\n  window.openbwCustomUI?.close();')
s=s.replace('  const out = [];\n  for (const item of MPQS)', '''  if(window.openbwSetupAssets){const out=window.openbwSetupAssets;window.openbwSetupAssets=null;return [...out,await fetchMap(mapFile)];}
  const out = [];
  for (const item of MPQS)''')
s+='''
if(!campaignMission&&!location.hash.startsWith('#i='))OpenBWCustom({
  maps:()=>MAPS,current:curMap,slots:slotsBox,
  select(file){const race=slotsBox._you.value;mapSelect.value=file;mapSelect.dispatchEvent(new Event('change'));slotsBox._you.value=race;},
  addMap(map,bytes){mapCache.set(map.file,bytes);const old=MAPS.findIndex(m=>m.file===map.file);if(old>=0)MAPS[old]=map;else{MAPS.push(map);mapSelect.add(new Option(map.name,map.file));}this.select(map.file);},
  start(){ $('start-game').click(); }
}).then(ui=>window.openbwCustomUI=ui).catch(e=>{document.body.classList.remove('custom-setup');document.getElementById('custom-game')?.remove();setMsg(e.message);console.error(e);});
'''
(d/'openbw.js').write_text(s)
h=(d/'index.html').read_text()
h=h.replace('</head>', '<link rel="stylesheet" href="menus.css"><link rel="stylesheet" href="original.css"><link rel="stylesheet" href="results.css"><link rel="stylesheet" href="custom.css"><script src="ui-assets.js"></script><script src="ui-original.js"></script><script src="production.js"></script><script src="story.js"></script><script src="briefing.js"></script><script src="menus.js"></script><script src="results.js"></script><script src="custom.js"></script></head>')
h=h.replace('<div id="gameover">',(r/'web/menus.html').read_text()+'\n<div id="gameover">')
h=h.replace('title="Settings">Menu','title="Game Menu" aria-label="Game Menu">MENU')
h=h.replace('Use Android Back for the app menu.','Android Back opens the Game Menu.')
h=h.replace('Android Back opens the app menu.','Android Back opens the Game Menu.')
h=h.replace('Choose up to 16× Fastest above.', 'Choose up to 16× Fastest in Game Speed & Display.')
h=re.sub(r'<h1><a id="home" href="\./" title="Start over on a clean URL">StarDroid · [^<]+</a></h1>', '<h1><a id="home" href="./title.html?menu" title="Main menu">Play Custom</a></h1>', h)
h=h.replace('<p><button id="start-game">Start Game</button></p>', '<p><button id="start-game" class="sc-button">Start Game</button></p><p><a class="setup-back" href="./title.html?menu">Previous</a></p>')
h=h.replace('<script type="module">', '<script src="original-stage.js"></script><script type="module">')
(d/'index.html').write_text(h)
for f in ['ui-assets.js','menus.js','menus.css','title.html','title.js','title.css','title-worker.js','ui-original.js','production.js','menu-codec.js','menu-worker.js','briefing.js','original.css','original-stage.js','story.js','cinematic.html','cinematic.css','cinematic.js','cinematic-worker.js','results.js','results.css','custom.js','custom.css']:
    shutil.copyfile(r/'web'/f,d/f)
print('Prepared original-asset title screen and paused game menus.')

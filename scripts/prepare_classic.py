#!/usr/bin/env python3
"""Install the original-asset console and local music host after campaign prep."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parents[1];d=r/'app/src/main/assets/game'
s=(d/'openbw.js').read_text()
def replace(old,new,count=1):
    global s
    assert old in s, 'Upstream anchor changed: '+old[:100]
    s=s.replace(old,new,count)
replace('  let audioCtx = null, masterGain = null;', '  let audioCtx = null, masterGain = null;\n  let paused = false, musicUI = null, classicUI = null, mediaSuspended = false;')
replace('  let paused = false, waiting = false, stepMs = 42;', '  let waiting = false, stepMs = 42;')
replace('    if (audioCtx) { audioCtx.resume(); return; }', '''    musicUI?.unlock();
    if (audioCtx) { if (!paused && !document.hidden) audioCtx.resume().catch(()=>{}); return; }''')
replace('    masterGain = audioCtx.createGain();', '    if (paused || document.hidden) audioCtx.suspend();\n    masterGain = audioCtx.createGain();')
replace('if (masterGain) masterGain.gain.value = muted ? 0 : 1;', 'if (masterGain) masterGain.gain.value = muted ? 0 : 1;\n    musicUI?.state(mediaSuspended || document.hidden,muted,!!soundChannels[100]?.playing);')
replace("  hb('boot:engine-ready');", """  hb('boot:engine-ready');
  const interfaceRace = session.campaign ? session.mission.race : (slots.find(s=>s.slot===mySlot)?.race ?? slots[0].race);
  musicUI = OpenBWMusic(interfaceRace);
  if (session.campaign) musicUI.phase('briefing');
  classicUI = await OpenBWClassic(x, memory, assets, interfaceRace, canvas, () => zoom);
  classicUI.portraits.voices(() => !!soundChannels[100]?.playing);
""")
replace('}, stop: stopVoice,\n    });', '}, stop: stopVoice,\n    }, classicUI.portraits, await OpenBWBriefing(classicUI.read,classicUI.fonts,classicUI.sounds,interfaceRace),classicUI.art);')
replace('await missionUI.briefing();', "await missionUI.briefing();\n    musicUI.phase('game');")
replace('stopVoice(); ensureAudio();', 'stopVoice(); ensureAudio(); musicUI?.duck(true);')
replace('audio.js_sound_stop(100);', 'audio.js_sound_stop(100); musicUI?.duck(false);')
replace('if (soundChannels[channel] === rec) rec.playing = false;', 'if (soundChannels[channel] === rec) { rec.playing = false; if (channel === 100) musicUI?.duck(false); }')
replace('missionUI.suspend(true); audioCtx?.suspend();', 'missionUI.suspend(true); classicUI?.portraits.state(true); musicUI?.state(true,muted,!!soundChannels[100]?.playing); audioCtx?.suspend();')
replace('missionUI.suspend(false); audioCtx?.resume();', 'missionUI.suspend(false); classicUI?.portraits.state(false); musicUI?.state(false,muted,!!soundChannels[100]?.playing); musicUI?.wake(); audioCtx?.resume();')
replace('if (session.campaign && audioCtx) { if (paused) audioCtx.suspend(); else audioCtx.resume(); }', 'if (audioCtx) { if (paused) audioCtx.suspend(); else audioCtx.resume(); }\n    musicUI?.state(mediaSuspended || document.hidden, muted, !!soundChannels[100]?.playing);\n    classicUI?.portraits.state(paused);')
replace('androidSuspended = true; androidWasPaused = paused; paused = true;', 'androidSuspended = true; androidWasPaused = paused; paused = true; mediaSuspended = true; classicUI?.sounds.suspend(true);')
replace('paused = androidWasPaused; androidSuspended = false;', 'paused = androidWasPaused; androidSuspended = false; mediaSuspended = false; classicUI?.sounds.suspend(false); musicUI?.wake();')
replace('    try { if (audioCtx) audioCtx.close(); }', '    classicUI?.portraits.close();\n    musicUI?.close();\n    classicUI?.sounds.close();\n    try { if (audioCtx) audioCtx.close(); }')
a=s.index('  const updateCard = () => {');b=s.index('  // Clicking a card button',a)
s=s[:a]+'''  const updateCard = () => {
    const ptr=x.openbw_card();
    classicUI.card(ptr ? readCString(ptr) : '', iconURL);
  };

'''+s[b:]
replace("statusEl.addEventListener('mousedown', (e) => {", "statusEl.addEventListener('pointerdown', (e) => {\n    if (paused) return;")
replace('if (q && q.dataset.slot !== undefined) x.openbw_cancel(+q.dataset.slot);', 'if (q && q.dataset.slot !== undefined) { e.preventDefault(); x.openbw_cancel(+q.dataset.slot); }')
replace("r[0] + ':' + r[4]", "r[0] + ':' + r.slice(4).join(':')")
replace('c.dataset.id = r[0];', '''c.dataset.id = r[0];
        c.dataset.type = r[5] || '';
        c.dataset.frame = r[6] || '13';
        if(box===32 && classicUI.art.groupFrames) c.style.backgroundImage='url('+classicUI.art.groupFrames[c.dataset.frame]+')';''')
replace('    updateCard();', '''    classicUI.draw();
    classicUI.portraits.state(paused);
    musicUI.state(mediaSuspended || document.hidden, muted, !!soundChannels[100]?.playing);
    $('android-cancel').style.display = x.openbw_cursor() ? 'block' : 'none';
    updateCard();''')
replace("  // Command card overlay:", "  OpenBWTesting(x, !link && !session.spectate);\n\n  // Command card overlay:")
replace("  optSpeed.onchange = () => {\n    stepMs = +optSpeed.value || 42;", "  optSpeed.onchange = () => {\n    stepMs = +optSpeed.value || 42;\n    stepClock = performance.now();")
(d/'openbw.js').write_text(s)
h=(d/'index.html').read_text()
h=h.replace('</head>', '''<link rel="stylesheet" href="classic.css">
<script src="mpq-decoder.js"></script><script src="portraits.js"></script><script src="testing.js"></script><script src="classic.js"></script><script src="music.js"></script>
</head>''')
h=h.replace('<div id="hud">',(r/'web/classic.html').read_text()+'\n<div id="command-hint" hidden></div>\n<div id="hud">')
h=h.replace('<button id="opt-resign"', '''<div id="music-settings"><h3>Music</h3>
  <label><input type="checkbox" id="opt-music"> Play original music</label>
  <div id="music-status" role="status">Checking imported music…</div>
  <label>Volume <input id="music-volume" type="range" min="0" max="100" value="30" aria-label="Music volume"></label>
  <label>Track <select id="music-track"><option value="auto">Automatic (your race)</option></select></label>
  <button id="music-next">Next track</button>
  </div>
  <button id="opt-resign"''')
h=h.replace('title="Settings">⚙️', 'title="Settings">Menu')
h=h.replace('<option value="42">Fastest</option>', '<option value="42">Fastest (1×)</option><option value="21">2× Fastest</option><option value="10.5">4× Fastest</option><option value="5.25">8× Fastest</option><option value="2.625">16× Fastest</option>')
h=h.replace('<div id="music-settings">', '''<div id="testing-settings" hidden><h3>Cheats</h3>
<p>For this game. Only your player gets resources and instant production. Placement, tech and supply requirements still apply.</p>
<button id="test-money">+10,000 minerals and gas</button>
<label><input type="checkbox" id="test-instant"> Instant construction, training &amp; research</label>
<button id="test-reveal">Reveal map</button><button id="test-reset">Normal production / reset speed</button>
<button id="test-victory">Force victory (end match)</button>
<div id="testing-status" role="status">Choose up to 16× Fastest above. Actual speed depends on your phone.</div></div>
<div id="music-settings">''')
(d/'index.html').write_text(h)
for f in ['classic.js','classic.css','music.js','music-worker.js','mpq-decoder.js','portraits.js','portrait-worker.js','testing.js']:shutil.copyfile(r/'web'/f,d/f)
licenses=r/'app/src/main/assets/licenses';licenses.mkdir(exist_ok=True)
shutil.copyfile(r/'vendor/libsmacker/COPYING',licenses/'libsmacker-LGPL-2.1.txt')
shutil.copyfile(r/'vendor/libsmacker/NOTICE.txt',licenses/'libsmacker-NOTICE.txt')
print('Prepared classic console, animated portraits, music and testing controls.')

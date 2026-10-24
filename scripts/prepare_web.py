#!/usr/bin/env python3
"""Apply the small, reviewable Android adaptation to the pinned web source."""
from pathlib import Path
import re
import json
import tarfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'app/src/main/assets/game'
with tarfile.open(ROOT / json.loads((ROOT/'UPSTREAM.json').read_text())['source_archive']['file']) as tar:
    for name in ['index.html', 'openbw.js', 'net.js', 'maps/Weave_v1.scx', 'maps/ATTRIBUTION.md']:
        path = DEST / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(tar.extractfile('web/' + name).read())

js = (DEST / 'openbw.js').read_text()
js = js.replace('__BUILD__', 'android-0.22-469d2037e2fd')
js = re.sub(r"const DEV = .*?;", 'const DEV = false;', js, count=1)
start = js.index('// Dev builds swap the favicon')
end = js.index('// BOT_LOG', start)
js = js[:start] + js[end:]
start = js.index('const ARCHIVE_BASE =')
end = js.index('const TILESETS =', start)
js = js[:start] + '''const MPQS = [
  { key: 'stardat', local: './data/STARDAT.MPQ' },
  { key: 'broodat', local: './data/BROODAT.MPQ' },
  { key: 'patch_rt', local: './data/patch_rt.mpq' },
];
const MAPS = [
  { name: 'Weave', file: './maps/Weave_v1.scx', starts: 4, w: 64, h: 64, tileset: 'Desert' },
];
''' + js[end:]
start = js.index('// IndexedDB cache for the MPQs')
end = js.index('// WASI shim', start)
js = js[:start] + '''// Android serves the user's imported MPQs from private app storage.
// Never download game data or duplicate large archives in IndexedDB.
async function loadAssets(mapFile = MAP_LOCAL) {
  setMsg('Reading imported game files…');
  const out = [];
  for (const item of MPQS) {
    const response = await fetch(item.local);
    if (!response.ok) throw new Error('Missing ' + item.local.split('/').pop() + '. Use Android Back → Game data files.');
    out.push(new Uint8Array(await response.arrayBuffer()));
    setBar(out.length / 4);
  }
  out.push(await fetchMap(mapFile));
  setBar(1);
  return out;
}

// ---------------------------------------------------------------------------
''' + js[end:]
js = js.replace('window.innerWidth / 640, window.innerHeight / 480', 'window.innerWidth / 320, window.innerHeight / 240')
start = js.index('  // --- Touch: gestures')
end = js.index('\n}\n\n// ---------------------------------------------------------------------------\n// Boot', start)
js = js[:start] + (ROOT / 'web/touch-input.js').read_text() + js[end:]
js = re.sub(r"^  'mcrave-[ptz]':.*\n", '', js, flags=re.M)
js = js.replace("sel.value = s === 1 ? DEFAULT_OPP : 'none';", "sel.value = 'none';")
js = js.replace("if (DEV) window.__bw = { x, memory, lockstep, link };", "window.__bw = { x, memory, lockstep, link }; // local test diagnostics")
js = js.replace("if (DEV) window.__bw = null;", "window.__bw = null;")
anchor = '  // Game speed lives in the settings popup;'
assert js.count(anchor) == 1
js = js.replace(anchor, '''  // Android lifecycle / menu pause. Preserve a pause the player chose.
  let androidSuspended = false, androidWasPaused = false;
  window.openbwAndroidSuspend = () => {
    if (androidSuspended) return;
    window.openbwCancelTouch?.();
    androidSuspended = true; androidWasPaused = paused; paused = true;
    x.openbw_set_paused?.(1); applyPause();
    if (audioCtx) audioCtx.suspend().catch(() => {});
  };
  window.openbwAndroidResume = () => {
    // Always reset wall-clock debt, even if suspend arrived after WebView froze.
    stepClock = performance.now();
    if (!androidSuspended) return;
    paused = androidWasPaused; androidSuspended = false;
    x.openbw_set_paused?.(paused ? 1 : 0); applyPause();
    if (audioCtx) audioCtx.resume().catch(() => {});
  };
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) window.openbwAndroidSuspend();
    else window.openbwAndroidResume();
  });
  $('android-cancel').onclick = () => {
    x.openbw_key(1, 0, 41); x.openbw_key(0, 0, 41);
  };
  window.openbwAndroidStats = () => ({ frame: lockstep.frame, paused,
    audio: audioCtx?.state || 'not-started', soundBuffers: soundBuffers.length });

''' + anchor)
js = js.replace('//   * fetch the 3 game MPQs from the Internet Archive on first run and cache\n//     them in IndexedDB (so no copyrighted bytes are ever hosted by the site);', '//   * read the user-imported game MPQs from local Android app storage;')
(DEST / 'openbw.js').write_text(js)

html = (DEST / 'index.html').read_text().replace('__BUILD__', 'android-0.22-469d2037e2fd')
html = re.sub(r'<link rel="icon"[^>]*>', '', html)
html = html.replace('OpenBW Web', 'StarDroid · 1.0')
html = html.replace('landscape. First run downloads ~90&nbsp;MB of game data.', 'landscape. Pinch to zoom. Android Back opens the app menu. Game files are read locally.')
html = re.sub(r'<div class="hint">Or <a href="https://retroonline.*?</div>', '', html)
html = html.replace('<button id="helpbtn" title="Controls">?</button>', '<button id="helpbtn" title="Controls">?</button>\n  <button id="android-cancel" title="Cancel targeting or building placement">Cancel</button>')
html = html.replace('<h3>Controls</h3>', '<h3>Touch controls</h3><div class="row">Tap your unit: select · Drag: pan · Hold briefly, then drag: select a group</div><div class="row">Tap ground/target: attack with non-workers, contextual orders with workers · Pinch: zoom</div><div class="row">Preview a building, then tap Build to confirm. Android Back opens the Game Menu.</div><h3>Mouse / keyboard</h3>')
html = html.replace('</style>', '''
  /* Features not wired to Android in this milestone are not offered. */
  #mp, #spectate-row, #go-replay, #opt-fullscreen { display: none !important; }
  #overlay { padding-top: 16px; }
  #overlay .card { max-width: 620px; padding: 0 10px; }
  #mobilewarn { margin: 6px 0; padding: 6px 10px; }
  #topbar #android-cancel { width: auto; min-width: 62px; padding: 0 8px; }
  select { min-height: 34px; }
</style>''')
(DEST / 'index.html').write_text(html)
print('Prepared local Android web assets from 469d2037e2fd.')

// Browser integration check of the exact packaged web assets. Requires Playwright,
// Chrome and separate original MPQs; this is not an Android emulator/device test.
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const root = path.resolve(__dirname, '..');
const assets = path.join(root, 'app/src/main/assets/game');
const mpqs = process.env.OPENBW_TEST_MPQS;
if (!mpqs) throw new Error('Set OPENBW_TEST_MPQS to a directory with the three MPQs.');
const report = { checks: [], errors: [], blockedRequests: [] };
const csp = "default-src 'self' blob: data:; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; connect-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'";
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const p = decodeURIComponent(url.pathname);
 if(p==='/music/manifest.json'){res.writeHead(200,{'Content-Type':'application/json'});return res.end(JSON.stringify({format:'openbw-music-bundle-v1',entries:[]}));}
  const file = p.startsWith('/data/') ? path.join(mpqs, path.basename(p)) : path.join(assets, p === '/' ? 'index.html' : p);
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); return res.end(); }
  const type = file.endsWith('.wasm') ? 'application/wasm' : file.endsWith('.js') ? 'text/javascript' : file.endsWith('.html') ? 'text/html' : file.endsWith('.css') ? 'text/css' : 'application/octet-stream';
  res.writeHead(200, { 'Content-Type': type, 'Content-Length': fs.statSync(file).size, 'Content-Security-Policy': csp });
  if (req.method === 'HEAD') return res.end();
  fs.createReadStream(file).pipe(res);
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ executablePath: process.env.OPENBW_CHROME, headless: true, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  try {
    const context = await browser.newContext({ viewport: { width: 900, height: 412 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1 });
    const page = await context.newPage();
    page.on('pageerror', e => report.errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') report.errors.push(m.text()); });
    await page.route('**/*', route => {
      if (route.request().url().startsWith(origin + '/')) return route.continue();
      report.blockedRequests.push(route.request().url()); return route.abort();
    });
    await page.goto(origin);
    await page.waitForFunction(() => document.querySelector('#slots select'));
    assert.equal(await page.locator('#map-select').inputValue(), './maps/Weave_v1.scx');
    assert.equal(await page.locator('#mp').isVisible(), false);
    assert.equal(await page.locator('#slots select').nth(1).inputValue(), 'none');
    report.checks.push('Mobile lobby, offline map and sandbox default');
    await page.locator('#start-game').tap();
    await page.waitForFunction(() => window.openbwAndroidStats?.().frame > 15, null, { timeout: 60000 });
    report.sandbox = await page.evaluate(() => window.openbwAndroidStats());
    await page.screenshot({ path: path.join(root, 'dist/01-sandbox.png') });
    report.checks.push('Imported MPQs loaded; WASM sandbox rendered and simulation advanced');
    await page.touchscreen.tap(450, 206);
    await page.waitForTimeout(150);
    // Select a worker through the engine's normal selection path, then issue an
    // actual touch long-press. The debug dump lets us assert a movement order.
    report.workerBefore = await page.evaluate(() => {
      const {x, memory} = window.__bw;
      const str = p => { const a = new Uint8Array(memory.buffer); let e = p; while(a[e]) e++; return new TextDecoder().decode(a.subarray(p,e)); };
      const unit = str(x.openbw_debug_units()).split('\n').map(s=>s.split('\t')).find(v=>/\bSCV\b/i.test(v[1] || ''));
      if (!unit) throw new Error('No starting worker');
      x.openbw_debug_select(+unit[0], 0);
      return str(x.openbw_debug_dump());
    });
    const input = await context.newCDPSession(page);
    await input.send('Input.dispatchTouchEvent', {type:'touchStart',touchPoints:[{x:570,y:300,id:1}]});
    await page.waitForTimeout(420);
    await input.send('Input.dispatchTouchEvent', {type:'touchEnd',touchPoints:[]});
    await page.waitForTimeout(250);
    report.workerAfter = await page.evaluate(() => {
      const {x,memory} = window.__bw, p=x.openbw_debug_dump(), a=new Uint8Array(memory.buffer); let e=p; while(a[e]) e++;
      return new TextDecoder().decode(a.subarray(p,e));
    });
    assert.notEqual(report.workerBefore.match(/pos=[^\n]+/)[0], report.workerAfter.match(/pos=[^\n]+/)[0]);
    report.checks.push('Worker selection and long-press move command changed unit position');
    await page.evaluate(() => window.openbwAndroidSuspend());
    const frame = await page.evaluate(() => window.openbwAndroidStats().frame);
    await page.waitForTimeout(250);
    assert.equal(await page.evaluate(() => window.openbwAndroidStats().frame), frame);
    await page.evaluate(() => window.openbwAndroidResume());
    await page.waitForFunction(f => window.openbwAndroidStats().frame > f, frame);
    await page.evaluate(()=>document.getElementById('pausebtn').click());
    await page.evaluate(() => { window.openbwAndroidSuspend(); window.openbwAndroidResume(); });
    assert.equal(await page.evaluate(() => window.openbwAndroidStats().paused), true);
    await page.evaluate(()=>document.getElementById('pausebtn').click());
    report.checks.push('Background/menu pause stops frames; resume works and preserves manual pause');
    const cdp = await context.newCDPSession(page);
    await cdp.send('Input.dispatchTouchEvent', {type:'touchStart',touchPoints:[{x:400,y:180,id:1},{x:480,y:180,id:2}]});
    await cdp.send('Input.dispatchTouchEvent', {type:'touchMove',touchPoints:[{x:370,y:180,id:1},{x:510,y:180,id:2}]});
    await cdp.send('Input.dispatchTouchEvent', {type:'touchEnd',touchPoints:[]});
    assert(Number(await page.evaluate(() => localStorage.getItem('openbw-zoom'))) > 1.1);
    report.checks.push('Two-finger touch pinch changes game zoom');
    await page.locator('#card .cmd[aria-label="Move"]').tap();
    await page.waitForFunction(()=>window.__bw.x.openbw_cursor()===1);
    await page.locator('#card .cmd[aria-label="Cancel"]').tap();
    await page.waitForFunction(()=>window.__bw.x.openbw_cursor()===0);
    report.checks.push('Cancel appears while targeting and clears the pending command');
    await page.evaluate(()=>document.getElementById('mute').click());
    await page.evaluate(()=>document.getElementById('mute').click());
    await page.waitForFunction(() => window.openbwAndroidStats().audio === 'running');
    report.audio = await page.evaluate(() => window.openbwAndroidStats());
    assert(report.audio.soundBuffers > 0);
    report.checks.push('Sound data loaded; Web Audio context running (not a listening test)');
    // Retired external Zerg-bot tests removed in 0.43; native AI is tested separately.
    assert.deepEqual(report.blockedRequests, []);
    assert.deepEqual(report.errors, []);
    report.checks.push('No remote network requests or browser errors');
    console.log(JSON.stringify(report, null, 2));
    fs.writeFileSync(path.join(root, 'dist/browser-smoke.json'), JSON.stringify(report, null, 2) + '\n');
  } catch (e) {
    console.error(JSON.stringify(report, null, 2)); throw e;
  } finally { await browser.close(); server.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; server.close(); });

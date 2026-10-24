#!/usr/bin/env python3
"""Render audited campaign unit facts and explicitly proposed one-per-player prices."""
from pathlib import Path
import csv, html, json, sys

root = Path(__file__).resolve().parents[1]
data = json.loads((root / 'docs/campaign-heroes.json').read_text())
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=True)
esc = html.escape

def attack(w):
    if not w:
        return '—'
    hits = f' × {w["hits"]}' if w['hits'] > 1 else ''
    reach = 'melee' if w['rangeTiles'] < 1 else f'{w["rangeTiles"]:g} tiles'
    return f'{w["damage"]}{hits} · {w["damageType"].lower()} · {reach} · {w["cooldownFrames"]} frames'

def cost(m, g):
    return f'{m} M / {g} G'

cards, summary, flat = [], [], []
for row in data['rows']:
    h, b = row['hero'], row['base']
    proposal = cost(row['proposedMinerals'], row['proposedGas'])
    original = cost(b['costMinerals'], b['costGas'])
    summary.append(f'<tr><td>{esc(row["race"])}</td><th scope="row">{esc(row["name"])}</th><td>{esc(b["name"])}</td><td>{original}</td><td>{row["equivalentUnits"]:g}×</td><td class="price">{proposal}</td></tr>')
    specs = [('HP', h['hp'], b['hp']), ('Shields', h['shields'], b['shields']),
             ('Base armor', h['armor'], b['armor']), ('Ground attack', attack(h['ground']), attack(b['ground'])),
             ('Air attack', attack(h['air']), attack(b['air'])), ('Maximum energy', h['energy'] or '—', b['energy'] or '—'),
             ('Sight', f'{h["sightTiles"]} tiles', f'{b["sightTiles"]} tiles'),
             ('Existing supply', f'{h["supply"]:g}', f'{b["supply"]:g}'),
             ('Build cost', 'Not normally buildable', original)]
    if h['unitId'] == 82:
        specs[3] = ('Ground attack', '6 per Interceptor; capacity 8', '6 per Interceptor; capacity 4, or 8 upgraded')
        specs[4] = ('Air attack', 'Same Interceptors', 'Same Interceptors')
    detail = ''.join(f'<tr><th scope="row">{esc(k)}</th><td>{esc(str(v))}</td><td>{esc(str(z))}</td></tr>' for k, v, z in specs)
    cards.append(f'<article data-name="{esc(row["name"].lower())}"><h2>{esc(row["name"])}</h2>'
                 f'<p class="price">Proposed: {proposal}<span>One at a time · {row["proposedSupply"]:g} supply</span></p>'
                 f'<div class="scroll"><table><thead><tr><th>Stat</th><th>Hero</th><th>{esc(b["name"])}</th></tr></thead><tbody>{detail}</tbody></table></div>'
                 f'<p><strong>Price basis:</strong> {esc(row["priceBasis"])}</p><p>{esc(row["notes"])}</p><p class="muted">{esc(row["race"])} · {esc(row["campaignExample"])}.</p></article>')
    flat.append({'Race': row['race'], 'Hero': row['name'], 'Suggested addition': row['suggestedAddition'], 'Equivalent units': row['equivalentUnits'], 'Price basis': row['priceBasis'], 'Base unit': b['name'], 'Hero HP': h['hp'], 'Hero shields': h['shields'],
                 'Hero armor': h['armor'], 'Hero ground attack': specs[3][1], 'Hero air attack': specs[4][1],
                 'Hero maximum energy': h['energy'], 'Hero sight tiles': h['sightTiles'], 'Hero existing supply': h['supply'],
                 'Base HP': b['hp'], 'Base shields': b['shields'], 'Base armor': b['armor'],
                 'Base ground attack': specs[3][2], 'Base air attack': specs[4][2],
                 'Base maximum energy': b['energy'], 'Base sight tiles': b['sightTiles'], 'Base supply': b['supply'],
                 'Original minerals': b['costMinerals'], 'Original gas': b['costGas'],
                 'Hero Mode minerals': row['proposedMinerals'], 'Hero Mode gas': row['proposedGas'], 'Hero Mode supply': row['proposedSupply'],
                 'Notes': row['notes']})

page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>StarDroid · 18 heroes · six per race · Hero Mode costs</title><style>
:root{color-scheme:dark;--ink:#e6e9ec;--muted:#a7b3bf;--line:#30414e;--green:#a2d58b}
*{box-sizing:border-box}body{margin:0;background:#10171d;color:var(--ink);font:16px/1.6 system-ui,sans-serif}main{max-width:1080px;margin:auto;padding:48px 22px}h1{font-size:clamp(30px,5vw,48px);line-height:1.15;max-width:850px;margin:10px 0 24px}h2{font-size:24px;margin:0 0 8px}.eyebrow{font:700 12px/1.5 system-ui;letter-spacing:.15em;color:var(--green)}p{max-width:920px}.muted{color:var(--muted)}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px;text-align:left}th,td{padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}thead{color:var(--muted)}tbody th{font-weight:600}article{padding:26px;margin:22px 0;background:#17222b;border:1px solid var(--line);border-radius:12px;break-inside:avoid}article table{table-layout:fixed;min-width:580px}article th:first-child{width:23%}.price{color:var(--green);font-weight:650}.price span{display:block;color:var(--muted);font-size:13px;font-weight:400}input{width:100%;background:#17222b;border:1px solid #50616e;border-radius:6px;color:white;padding:14px;font:inherit;margin:30px 0 0}aside{border-left:3px solid var(--green);padding:4px 20px;margin:32px 0}footer{font-size:13px;color:var(--muted);margin-top:40px}@media print{body{background:white;color:black}main{padding:0}article{background:white;border-color:#bbb}input{display:none}.muted,footer{color:#444}.price,.eyebrow{color:#245227}th,td{padding:6px;border-color:#ddd}article table{min-width:0}article{display:block!important}}@media(max-width:600px){main{padding:28px 22px}table.summary thead{display:none}table.summary tbody{display:block}table.summary tr{display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;padding:18px 0;border-bottom:1px solid var(--line)}table.summary tr>*{padding:0;border:0}table.summary td:nth-child(1){grid-column:1/-1;font-size:12px;color:var(--muted)}table.summary th{grid-column:1/-1;font-size:18px}table.summary td:nth-child(3){grid-column:1/-1;color:var(--muted)}table.summary td:nth-child(3):before{content:'Based on: '}table.summary td:nth-child(4):before{content:'Regular cost';display:block;font-size:12px;color:var(--muted)}table.summary td:nth-child(5){grid-column:1;grid-row:5;font-size:12px;color:var(--muted)}table.summary td:nth-child(5):after{content:' equivalents'}table.summary td:nth-child(6){grid-column:2;grid-row:4/6}table.summary td:nth-child(6):before{content:'Hero Mode cost';display:block;font-size:12px;color:var(--muted)}article{padding:16px}article table{min-width:0;font-size:12px}article th,article td{padding:8px 5px;overflow-wrap:anywhere}article th:first-child{width:30%}}</style>
<main><div class="eyebrow">STARDROID · HERO MODE ROSTER · OCTOBER 2026</div><h1>Six heroes per race.<br>One of each, at reduced cost.</h1>'''
data_note = f'<aside><p><strong>Stats follow original game data. Hero Mode prices are adjustable starting values.</strong> {esc(data["stats"])}</p><p>M = minerals; G = Vespene Gas. Damage is per attack before armor and size modifiers; “×2” means two hits. Cooldowns are simulation frames, so game speed affects real seconds. Shield armor starts at zero. Carrier attacks depend on Interceptor travel and cannot be reduced to a hull weapon cooldown.</p></aside>'
page += '<p>18 hero forms: six Terran, six Zerg and six Protoss. Zerg additions: Torrasque, Devouring One and Kukulza (Mutalisk).</p><p class="price">Price = regular unit cost × estimated equivalents × ⅔, rounded to 5.<br>Raynor Marine: 50 × 3 × ⅔ = 100 minerals.</p>'
page += '<div class="scroll"><table class="summary"><thead><tr><th>Race</th><th>Hero</th><th>Regular counterpart</th><th>Regular cost</th><th>Equivalent units</th><th>Hero Mode cost</th></tr></thead><tbody>' + ''.join(summary) + '</tbody></table></div>'
page += data_note
page += f'<p>{esc(data["pricing"])}</p><label for="search">Find a hero</label><input id="search" type="search" placeholder="Raynor, Fenix, Kerrigan…"><section>' + ''.join(cards) + '</section>'
page += f'<aside><h2>Roster and campaign differences</h2><p>{esc(data["exclusions"])}</p><p>Map scripts, starting damage, and player upgrades can change the values visible during a mission. Fourteen forms retain their playable-campaign provenance; Duke’s tank and the three Zerg additions are identified separately. The normal Ghost comparison for Infested Kerrigan describes her origin; her melee weapon and spells make her a distinct unit.</p></aside>'
page += '<footer>Source: supplied original units.dat and weapons.dat, original campaign CHK ownership and triggers across 64 scenarios, and engine rules for intrinsic hero upgrades. No game artwork or audio is included in this report. These costs are used only when Hero Mode is enabled in StarDroid.</footer></main><script>document.getElementById("search").addEventListener("input",function(){const q=this.value.toLowerCase().trim();document.querySelectorAll("article").forEach(c=>c.hidden=!c.dataset.name.includes(q));});</script></html>'
(out / 'StarDroid-Hero-Chart.html').write_text(page)
with (out / 'StarDroid-Hero-Chart.csv').open('w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=flat[0].keys()); writer.writeheader(); writer.writerows(flat)
print('Wrote 18 hero comparisons and Hero Mode costs')

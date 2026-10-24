#!/usr/bin/env python3
"""Reproduce native engine input from the pinned source and reviewed campaign patch."""
import hashlib, json, pathlib, re, subprocess, tarfile, tempfile, shutil
ROOT = pathlib.Path(__file__).resolve().parents[1]
def write(path,text):
    if not path.exists() or path.read_text()!=text:path.write_text(text)
stage = ROOT / 'native-engine'
up = json.loads((ROOT/'UPSTREAM.json').read_text())
assert hashlib.sha256((ROOT/'patches/campaign.patch').read_bytes()).hexdigest() == json.loads((ROOT/'CAMPAIGN-BUILD.json').read_text())['patchSha256']
archive = ROOT/up['source_archive']['file']
assert hashlib.sha256(archive.read_bytes()).hexdigest() == up['source_archive']['sha256']
# Reconstruct the ordered patch stack from pinned input. Later fixes may touch
# earlier patch context, so reverse-dry-run detection is no longer sufficient.
# Promote changed bytes only, keeping incremental builds fast.
from prepare_presentation import prepare as presentation
from prepare_feedback import prepare as feedback
stage.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='openbw-native-source-') as temp:
    fresh = pathlib.Path(temp)
    with tarfile.open(archive) as t: t.extractall(fresh, filter='data')
    for name in ('campaign.patch', 'native-gameplay.patch'):
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(ROOT/'patches'/name)],
                       cwd=fresh,check=True,stdout=subprocess.DEVNULL)
    presentation(fresh)
    feedback(fresh)
    for name in ('native-revision.patch', 'native-missions.patch', 'native-polish33.patch', 'native-saves34.patch', 'native-campaign36.patch', 'native-finale37.patch', 'native-controls38.patch', 'native-polish39.patch', 'native-polish40.patch', 'native-polish41.patch', 'native-polish42.patch', 'native-ai43.patch', 'native-polish44.patch', 'native-ai45.patch', 'native-polish46.patch', 'native-polish54.patch', 'native-polish55.patch', 'native-polish56.patch', 'native-polish57.patch', 'native-polish58.patch', 'native-polish59.patch', 'native-upgrades1.patch', 'native-placement68.patch', 'native-scroll69.patch'):
        subprocess.run(['patch','--batch','--forward','-p1','-i',str(ROOT/'patches'/name)],
                       cwd=fresh,check=True,stdout=subprocess.DEVNULL)
    for source in fresh.rglob('*'):
        if not source.is_file(): continue
        target = stage / source.relative_to(fresh)
        if not target.exists() or target.read_bytes() != source.read_bytes():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source,target)
# Native builds retain the same entry points but use real pointers and exceptions.
f=stage/'web/sandbox.h'
write(f,f.read_text().replace('std::min(200,st.supply_available[u->owner][ri].raw_value / 2)', 'std::min<int>(200,st.supply_available[u->owner][ri].raw_value / 2)'))
out=ROOT/'native/generated';out.mkdir(parents=True,exist_ok=True)
for name in ['wasm_main.cpp','wasm_backend.cpp']:
    text=(stage/'web'/name).read_text()
    text=re.sub(r'__attribute__\(\(import_module\("env"\), import_name\("[^"]+"\)\)\)', '', text)
    text=text.replace('__attribute__((export_name(#name))) ', '')
    text=text.replace('fprintf(stderr, "openbw fatal: %s\\n", str.c_str()); abort();','throw std::runtime_error(str.c_str());')
    write(out/name,text)
print('Native engine source prepared')
# Retry deferred creep cleanup when the engine's bounded recession pool is full.
# Keep the dead provider alive until its remaining tiles have been queued.
p=stage/'bwgame.h';s=p.read_text();s=s.replace('error("update_dead_unit: fixme some creep stuff?");','if (!remove_creep_provider(u)) return;\n\t\t\tu_unset_status_flag(u, unit_t::status_flag_4000);');write(p,s)
# Native HUD owns a fixed 128px minimap, independently of the source map size.
p=stage/'ui/ui.h';s=p.read_text();anchor='\t\tif (minimap_scale > 0 && minimap_scale != 1) {'
if 'OPENBW_NATIVE_MINIMAP' not in s:s=s.replace(anchor,'\t\t// OPENBW_NATIVE_MINIMAP\n\t\tconst size_t largest = std::max(minimap_width, minimap_height);\n\t\tminimap_width = (minimap_width * 128 + largest / 2) / largest;\n\t\tminimap_height = (minimap_height * 128 + largest / 2) / largest;\n'+anchor,1)
write(p,s)

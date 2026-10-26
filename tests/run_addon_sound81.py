#!/usr/bin/env python3
"""Validate accepted Terran add-on construction audio against caller-owned data."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('core',type=Path);p.add_argument('--map',type=Path,default=r/'app/src/main/assets/native/weave.scx');p.add_argument('--skip-build',action='store_true');a=p.parse_args()
files=['patches/native-addon-sound81.patch','scripts/prepare_native.py','tests/build_native_host.py','tests/native_addon_sound81.cpp','tests/run_addon_sound81.py','native/runtime.cpp','native/replay.h','native/generated/wasm_main.cpp','native/generated/wasm_backend.cpp']
engine=['bwgame.h','actions.h','web/sandbox.h','ui/ui.h']
def sources():return {name:hashlib.sha256((r/name).read_bytes()).hexdigest() for name in files}
def prepared():return {name:hashlib.sha256((r/'native-engine'/name).read_bytes()).hexdigest() for name in engine}
before=sources();engine_before=prepared()
if not a.skip_build:subprocess.run([sys.executable,str(r/'tests/build_native_host.py'),'addon_sound81','--fast','--skip-prepare'],cwd=r,check=True)
result=subprocess.run([str(r/'build-native/host/native-addon_sound81'),str(a.core.resolve()),str(a.map.resolve())],cwd=r,text=True,capture_output=True)
(r/'build-native/addon-sound81-test.log').write_text(result.stdout+result.stderr)
print(result.stdout,end='');print(result.stderr,file=sys.stderr,end='');result.check_returncode()
assert before==sources() and engine_before==prepared(),'Sources changed during validation; rerun after final integration.'
(r/'validation/addon-sound-v81.json').write_text(json.dumps(dict(passed=True,physicalAndroid=False,originalArchivesTested=True,sourceSha256=before,preparedEngineSha256=engine_before,checks=[line for line in result.stdout.splitlines() if line.startswith('PASS ')]),indent=2)+'\n')

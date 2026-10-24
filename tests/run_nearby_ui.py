#!/usr/bin/env python3
"""Current original-artwork multiplayer/setup renderer checks."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
data=Path(sys.argv[1]) if len(sys.argv)>1 else root/'build-native/game-data'
subprocess.run([sys.executable,str(root/'tests/run_ui54.py'),str(data)],check=True)

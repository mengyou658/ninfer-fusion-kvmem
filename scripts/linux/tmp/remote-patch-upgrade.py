#!/usr/bin/env python3
from pathlib import Path

p = Path("/f/ninfer-fusion-kvmem/src-tree/fusion-engine-src/tools/upgrade_ninfer_v2_to_v3.py")
text = p.read_text()
old = '("qwen3.8-27b", "groupwise-int"): (1124, 1190),'
new = '("qwen3.8-27b", "groupwise-int"): (1124, 1126, 1190),'
if old not in text:
    raise SystemExit("pattern missing")
p.write_text(text.replace(old, new, 1))
print("patched")

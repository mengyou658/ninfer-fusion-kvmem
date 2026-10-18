#!/usr/bin/env python3
import os
import struct
from pathlib import Path

print("=== minq4 magic ===")
with open("/f/qwen3_8_27b_minq4.ninfer", "rb") as f:
    h = f.read(16)
    print(h[:8], "ver", h[7])

print("=== search dirs ===")
roots = ["/f", "/home/yun", "/f/models"]
for root in roots:
    p = Path(root)
    if not p.exists():
        continue
    try:
        for child in p.iterdir():
            name = child.name.lower()
            if "qwen" in name or "bonsai" in name:
                print(child, "dir" if child.is_dir() else child.stat().st_size)
    except PermissionError:
        pass

print("=== packer README head ===")
readme = Path("/f/ninfer-Bonsai-2-5060/packer/README.md")
if readme.exists():
    print(readme.read_text(encoding="utf-8", errors="replace")[:2500])

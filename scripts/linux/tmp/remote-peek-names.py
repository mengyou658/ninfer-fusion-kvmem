#!/usr/bin/env python3
import json
import struct
from collections import Counter

p = "/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer"
with open(p, "rb") as f:
    h = f.read(16)
    count = struct.unpack_from("<Q", h, 8)[0]
    d = json.loads(f.read(count))
names = [o["name"] for o in d["objects"]]
# classify by path pattern
patterns = Counter()
for n in names:
    parts = n.split("/")
    if n.startswith("text/layers/"):
        # text/layers/N/ROLE...
        role = "/".join(parts[3:])
        patterns[("layer", role)] += 1
    elif n.startswith("mtp/"):
        patterns[("mtp", "/".join(parts[1:4]))] += 1
    elif n.startswith("vision/"):
        patterns[("vision", "/".join(parts[:3]))] += 1
    else:
        patterns[("top", n)] += 1
for k, v in sorted(patterns.items()):
    if k[0] == "layer" and v not in (48, 16, 64, 1):  # show unusual
        print(v, k)
    elif k[0] != "layer":
        print(v, k)
print("--- unique layer roles ---")
roles = sorted({k[1] for k in patterns if k[0] == "layer"})
for r in roles:
    print(patterns[("layer", r)], r)

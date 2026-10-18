#!/usr/bin/env python3
import json
import struct
from collections import Counter

p = "/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer"
with open(p, "rb") as f:
    h = f.read(16)
    count = struct.unpack_from("<Q", h, 8)[0]
    d = json.loads(f.read(count))
objs = d["objects"]
pairs = Counter((o.get("format"), o.get("layout")) for o in objs)
for k, n in pairs.most_common():
    print(n, k)
# show one PQ2 object fully
for o in objs:
    if o.get("format") == "PQ2_0_G128":
        print("sample", json.dumps(o, ensure_ascii=False)[:800])
        break

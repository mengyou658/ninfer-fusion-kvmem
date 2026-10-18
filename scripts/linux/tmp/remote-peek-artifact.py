#!/usr/bin/env python3
import json, struct
p = "/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer"
with open(p, "rb") as f:
    header = f.read(16)
    print("magic", header[:8])
    count = struct.unpack_from("<Q", header, 8)[0]
    directory = json.loads(f.read(count))
ident = directory.get("identity", {})
objs = directory.get("objects", [])
print("identity", json.dumps(ident, ensure_ascii=False)[:2000])
print("objects", len(objs))
names = [o["name"] for o in objs]
print("sample", names[:12])
print("has_mtp", any(n.startswith("mtp/") for n in names))
print("has_dflash", any("dflash" in n for n in names))
print("has_vision", any(n.startswith("vision/") or "mmproj" in n for n in names))

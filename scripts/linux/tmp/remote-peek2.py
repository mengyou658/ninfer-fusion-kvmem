#!/usr/bin/env python3
import json
import struct

for p in ["/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer", "/f/qwen3_8_27b_minq4.ninfer"]:
    with open(p, "rb") as f:
        h = f.read(16)
        print("===", p, "magic", h[:8], "byte7", h[7])
        if h[:7] != b"NINFER\0":
            print("not ninfer")
            continue
        if h[7] == 3:
            f.seek(0)
            hdr = f.read(32)
            dlen = struct.unpack_from("<Q", hdr, 8)[0]
            data = f.read(dlen)
            d = json.loads(data)
            print("v3 keys", list(d.keys())[:12])
            print("meta", d.get("metadata"))
            print("components", list((d.get("components") or {}).keys()))
            objs = d.get("objects") or []
            fmts = sorted({o.get("format") for o in objs if isinstance(o, dict)})
            print("objects", len(objs), "formats", fmts[:40])
        else:
            count = struct.unpack_from("<Q", h, 8)[0]
            d = json.loads(f.read(count))
            print("identity", d.get("identity"))
            objs = d.get("objects", [])
            print("objects", len(objs))
            fmts = sorted({o.get("format") for o in objs if isinstance(o, dict)})
            print("formats", fmts)

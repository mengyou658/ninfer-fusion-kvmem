#!/usr/bin/env python3
import json
import struct

p = "/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer"
with open(p, "rb") as f:
    h = f.read(16)
    count = struct.unpack_from("<Q", h, 8)[0]
    d = json.loads(f.read(count))
for o in d["objects"]:
    if "hadamard" in o["name"] or o["name"] in (
        "text/token_embedding",
        "text/output_head",
        "text/draft_head",
        "text/draft_head_token_ids",
    ):
        print(json.dumps(o, ensure_ascii=False))

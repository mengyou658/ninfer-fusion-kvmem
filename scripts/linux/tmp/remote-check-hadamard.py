#!/usr/bin/env python3
import json
import struct
from pathlib import Path

import numpy as np

HEADER = struct.Struct("<8sQ16s")


def align_up(v, a=256):
    return (v + a - 1) // a * a


def entry_start(directory):
    encoded = json.dumps(
        directory, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode()
    reserve = 4096 - 32
    while len(encoded) > reserve:
        reserve = align_up(32 + len(encoded)) - 32
    return reserve + 32


path = Path("/f/Bonsai-2-27B-PQ2_0-CRACK.v3.ninfer")
with path.open("rb") as f:
    magic, dlen, _ = HEADER.unpack(f.read(32))
    d = json.loads(f.read(dlen))
    start = entry_start(d)
    print("uses with hadamard", sum(1 for u in d["uses"] if "hadamard_signs" in (u.get("auxiliaries") or {})))
    print("sample use", json.dumps([u for u in d["uses"] if "hadamard_signs" in (u.get("auxiliaries") or {})][0], ensure_ascii=False)[:300])
    for name in ("text/hadamard_signs_5120", "text/hadamard_signs_6144", "text/hadamard_signs_17408"):
        obj = next(o for o in d["objects"] if o["id"] == name)
        f.seek(start + obj["offset"])
        raw = f.read(obj["bytes"])
        # bf16 bits -> interpret as float via pad to f32
        u16 = np.frombuffer(raw, dtype="<u2").astype(np.uint32) << 16
        vals = u16.view(np.float32)
        print(name, "shape", obj["shape"], "unique", np.unique(vals)[:8], "count", len(vals),
              "pos", int((vals > 0).sum()), "neg", int((vals < 0).sum()), "abs1", int(np.isclose(np.abs(vals), 1.0).sum()))

# Compare with v2 fp32 signs
v2 = Path("/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer")
with v2.open("rb") as f:
    h = f.read(16)
    count = struct.unpack_from("<Q", h, 8)[0]
    d2 = json.loads(f.read(count))
    start2 = align_up(16 + count)
    obj = next(o for o in d2["objects"] if o["name"] == "text/hadamard_signs")
    f.seek(start2 + obj["offset"])
    f32 = np.frombuffer(f.read(obj["bytes"]), dtype="<f4")
    print("v2 signs unique", np.unique(f32)[:8], "len", len(f32),
          "pos", int((f32 > 0).sum()), "neg", int((f32 < 0).sum()))

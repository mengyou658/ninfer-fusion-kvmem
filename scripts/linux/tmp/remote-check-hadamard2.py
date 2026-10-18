#!/usr/bin/env python3
import json
import struct
from pathlib import Path

import numpy as np

HEADER = struct.Struct("<8sQ16s")


def align(value, amount=4096):
    return (value + amount - 1) // amount * amount


def align256(value):
    return align(value, 256)


def entry_start(directory):
    encoded = json.dumps(
        directory, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode()
    reserve = 4096 - 32
    while len(encoded) > reserve:
        reserve = align(32 + len(encoded)) - 32
    return reserve + 32, len(encoded)


# --- v2 signs with correct 4096 align ---
v2 = Path("/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer")
with v2.open("rb") as f:
    h = f.read(16)
    assert h[:8] == b"NINFER\0\2"
    count = struct.unpack_from("<Q", h, 8)[0]
    d2 = json.loads(f.read(count))
    start2 = align(16 + count)
    print("v2 dir_len", count, "payload_start", start2)
    obj = next(o for o in d2["objects"] if o["name"] == "text/hadamard_signs")
    print("v2 hadamard obj", obj)
    f.seek(start2 + obj["offset"])
    f32 = np.frombuffer(f.read(obj["bytes"]), dtype="<f4")
    print(
        "v2 signs",
        "len",
        len(f32),
        "unique_sample",
        np.unique(f32)[:10],
        "all_abs1",
        bool(np.all(np.abs(f32) == 1.0)),
        "pos",
        int((f32 == 1).sum()),
        "neg",
        int((f32 == -1).sum()),
    )

# --- v3 sign object offsets ---
v3 = Path("/f/Bonsai-2-27B-PQ2_0-CRACK.v3.ninfer")
with v3.open("rb") as f:
    magic, dlen, _ = HEADER.unpack(f.read(32))
    d = json.loads(f.read(dlen))
    start, enc_len = entry_start(d)
    print("v3 entry_start", start, "enc_len", enc_len, "dlen", dlen)
    for o in d["objects"]:
        if "hadamard" in o["id"] or o["id"].endswith("chat_template.jinja") or o["id"] == "frontend/chat_template.jinja":
            print("obj", o)
            f.seek(start + o["offset"])
            raw = f.read(min(o["bytes"], 64))
            print("  first16", raw[:16].hex())
            if o.get("format") == "bf16":
                u16 = np.frombuffer(f.read(0) or raw, dtype="<u2")
                # re-read full
                f.seek(start + o["offset"])
                raw = f.read(o["bytes"])
                u16 = np.frombuffer(raw, dtype="<u2").astype(np.uint32) << 16
                vals = u16.view(np.float32)
                print(
                    "  abs1",
                    int(np.isclose(np.abs(vals), 1.0).sum()),
                    "/",
                    len(vals),
                    "unique",
                    np.unique(np.round(vals, 6))[:8],
                )

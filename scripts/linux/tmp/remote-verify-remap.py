#!/usr/bin/env python3
"""Sanity-check PQ2->T2 remap: sample a known tensor's first code byte histogram."""
from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np

HEADER = struct.Struct("<8sQ16s")


def align_up(v, a=4096):
    return (v + a - 1) // a * a


def entry_start(directory):
    encoded = json.dumps(
        directory, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode()
    reserve = 4096 - 32
    while len(encoded) > reserve:
        reserve = align_up(32 + len(encoded)) - 32
    return reserve + 32


def code_hist(path: Path, name: str, n_bytes: int = 1_000_000):
    with path.open("rb") as f:
        magic, dlen, _ = HEADER.unpack(f.read(32))
        assert magic == b"NINFER\0\3", magic
        directory = json.loads(f.read(dlen))
        start = entry_start(directory)
        obj = next(o for o in directory["objects"] if o["id"] == name)
        n, k = obj["shape"]
        groups = align_up(k, 128) // 128
        base_bytes = n * groups * 32
        f.seek(start + obj["offset"])
        buf = np.frombuffer(f.read(min(n_bytes, base_bytes)), dtype=np.uint8)
    # flatten 2-bit fields
    fields = np.stack([buf & 3, (buf >> 2) & 3, (buf >> 4) & 3, (buf >> 6) & 3], axis=1).reshape(-1)
    uniq, counts = np.unique(fields, return_counts=True)
    return dict(zip(uniq.tolist(), counts.tolist())), base_bytes, start + obj["offset"]


def main():
    v3 = Path("/f/Bonsai-2-27B-PQ2_0-CRACK.v3.ninfer")
    for name in ("text/token_embedding", "text/output_head", "text/layers/0/mlp/down"):
        hist, base, off = code_hist(v3, name)
        print(name, "offset", off, "base_bytes", base, "hist", hist)
        # After T2 remap, expect codes in {0,1,3} only (not 2).
        bad = [c for c in hist if c == 2]
        print("  has_pq2_code2", bool(bad), "has_t2_code3", 3 in hist)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Vectorized PQ2 trit -> T2 two's-complement remap of a v3 artifact's code planes.

PQ2 stores 0=-1, 1=0, 2=+1. fusion-kvmem t2_g128_fp16 stores two's complement
(0=0, 1=+1, 3=-1). Scales and row-split layout stay put.

IN-PLACE: copies then patches the primary .ninfer. Back up first.

Must use the same payload entry_start as
src-tree/fusion-engine-src/tools/upgrade_ninfer_v2_to_v3.py (align 4096),
not a naive 256-byte pad — off-by-768B corrupts every weight.
"""
from __future__ import annotations

import json
import os
import struct
import sys
from pathlib import Path

import numpy as np

HEADER = struct.Struct("<8sQ16s")


def align_up(value: int, amount: int = 4096) -> int:
    """Match upgrade_ninfer_v2_to_v3.layout(): directory reserve grows on 4096 boundaries."""
    return (value + amount - 1) // amount * amount


def entry_start_for(directory: dict, dlen: int) -> tuple[int, bytes]:
    encoded = json.dumps(
        directory, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode()
    reserve = 4096 - 32
    while len(encoded) > reserve:
        reserve = align_up(32 + len(encoded)) - 32
    start = reserve + 32
    if dlen != reserve:
        print(f"note: dlen={dlen} reserve={reserve} enc={len(encoded)}", flush=True)
    return start, encoded


def lut() -> np.ndarray:
    table = np.array([3, 0, 1, 0], dtype=np.uint8)  # PQ2 code -> T2 code; 3 unused
    out = np.zeros(256, dtype=np.uint8)
    for b in range(256):
        packed = 0
        for i in range(4):
            packed |= int(table[(b >> (2 * i)) & 3]) << (2 * i)
        out[b] = packed
    return out


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(
            "usage: remap-pq2-codes-in-place.py <model.v3.ninfer>\n"
            "  Back up the file first; this rewrites code planes in place."
        )
    path = Path(sys.argv[1])
    mapping = lut()
    with path.open("r+b") as f:
        magic, dlen, _ident = HEADER.unpack(f.read(32))
        if magic != b"NINFER\0\3":
            raise SystemExit(f"not ninfer v3: {magic!r}")
        directory = json.loads(f.read(dlen))
        start, encoded = entry_start_for(directory, dlen)
        f.seek(32)
        on_disk = f.read(dlen).rstrip(b" ")
        if on_disk != encoded:
            raise SystemExit("directory mismatch; refuse to patch")
        print(f"entry_start={start} (expect payload at file offset {start})", flush=True)
        objs = [
            o
            for o in directory["objects"]
            if o.get("kind") == "tensor" and o.get("format") == "t2_g128_fp16"
        ]
        print(f"tensors {len(objs)} entry_start {start}", flush=True)
        done = 0
        for obj in objs:
            n, k = obj["shape"]
            groups = (k + 127) // 128
            base_bytes = n * groups * 32
            off = start + obj["offset"]
            mm = np.memmap(
                f, dtype=np.uint8, mode="r+", offset=off, shape=(base_bytes,)
            )
            mm[:] = mapping[mm]
            mm.flush()
            del mm
            done += 1
            if done % 32 == 0 or done == len(objs):
                print(f"  {done}/{len(objs)} {obj['id']}", flush=True)
        f.flush()
        os.fsync(f.fileno())
    print("REMAP_DONE", flush=True)


if __name__ == "__main__":
    main()

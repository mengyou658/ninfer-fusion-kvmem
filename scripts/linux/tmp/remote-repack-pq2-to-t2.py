#!/usr/bin/env python3
"""In-place remaps PQ2 trit codes -> T2 two's-complement codes in a v3 artifact.

CRACK packer stored PQ2_0 codes (0=-1, 1=0, 2=+1) under a row-split layout.
fusion-kvmem's t2_g128_fp16 decoder expects two's complement (0=0, 1=+1, 3=-1).
Scales and plane layout are unchanged; only the 2-bit code fields are rewritten.
"""
from __future__ import annotations

import json
import os
import struct
import sys
from pathlib import Path

HEADER = struct.Struct("<8sQ16s")
PQ2_TO_T2 = bytes([3, 0, 1, 0xFF])  # 0xFF = illegal


def align_up(value: int, amount: int = 256) -> int:
    return (value + amount - 1) // amount * amount


def row_split_base_bytes(shape: list[int]) -> tuple[int, int, int]:
    """Return (base_bytes, high_bytes, scale_offset) for t2_g128_fp16."""
    n, k = shape
    k_pad = align_up(k, 128)
    groups = k_pad // 128
    base_bytes = n * groups * 32
    high_bytes = 0
    high_offset = align_up(base_bytes, 256)
    scale_offset = high_offset + align_up(high_bytes, 256)
    return base_bytes, high_bytes, scale_offset


def remap_code_plane(buf: bytearray) -> int:
    """Remap every byte's four 2-bit PQ2 fields to T2. Returns illegal-code count."""
    table = PQ2_TO_T2
    illegal = 0
    # Precompute full byte LUT
    lut = bytearray(256)
    for b in range(256):
        out = 0
        bad = False
        for i in range(4):
            c = (b >> (2 * i)) & 3
            t = table[c]
            if t == 0xFF:
                bad = True
                t = 0
            out |= t << (2 * i)
        lut[b] = out
        if bad:
            # count later per occurrence
            pass
    for i, b in enumerate(buf):
        c0 = b & 3
        c1 = (b >> 2) & 3
        c2 = (b >> 4) & 3
        c3 = (b >> 6) & 3
        if c0 > 2 or c1 > 2 or c2 > 2 or c3 > 2:
            illegal += 1
        buf[i] = lut[b]
    return illegal


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "/f/Bonsai-2-27B-PQ2_0-CRACK.v3.ninfer")
    with path.open("r+b") as f:
        hdr = f.read(32)
        magic, dlen, _ident = HEADER.unpack(hdr)
        if magic != b"NINFER\0\3":
            raise SystemExit(f"not ninfer v3: {magic!r}")
        directory = json.loads(f.read(dlen))
        # directory JSON is followed by padding to entry_start; find payload base
        # layout() uses reserve then start = reserve+32. Reconstruct from files[0].
        # Official writer: header 32 + directory (padded) then payload.
        # We used upgrade's layout(): data padded inside first 4096-aligned region.
        # Safer: compute entry_start from file structure used by upgrade.layout.
        # After header(32)+len(data) with data padded to reserve, start = len(padded_dir)+32
        # In practice upgrade writes: HEADER + data + zeros to entry_start.
        # Re-read: seek to 32, the directory JSON may have trailing spaces.
        f.seek(32)
        raw = f.read(dlen)
        # Find entry_start: next 4096 boundary after 32+dlen, but layout uses custom reserve.
        # From upgrade: `data, entry_start = mod.layout(...)` then writes data then pads to entry_start.
        # Inspect first tensor offset relative to payload — payload starts at entry_start.
        # Probe: objects[0] offset is relative to payload start.
        # Find entry_start by scanning: after header+data, zeros until first non-matching...
        # Easiest: entry_start = align_up(32 + dlen, 4096) is WRONG if reserve > that.
        #
        # Reconstruct the way upgrade.layout does:
        reserve = 4096 - 32
        while True:
            start = reserve + 32
            # we don't need files split check; just match the written directory bytes length
            encoded = json.dumps(
                directory, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode()
            if len(encoded) <= reserve:
                entry_start = start
                break
            reserve = align_up(32 + len(encoded)) - 32
        # Verify directory at 32 matches
        f.seek(32)
        on_disk = f.read(len(encoded))
        if on_disk != encoded:
            # directory may have been space-padded; compare stripped
            f.seek(32)
            on_disk = f.read(dlen).rstrip(b" ")
            if on_disk != encoded.rstrip(b" "):
                raise SystemExit("directory mismatch; refuse to patch")

        t2_objs = [
            o
            for o in directory["objects"]
            if o.get("kind") == "tensor" and o.get("format") == "t2_g128_fp16"
        ]
        print(f"patching {len(t2_objs)} t2 tensors in {path}")
        total_illegal = 0
        total_bytes = 0
        for obj in t2_objs:
            base_bytes, _high, _scale_off = row_split_base_bytes(obj["shape"])
            # base plane may be smaller than align; only remap true base_bytes
            payload_off = entry_start + obj["offset"]
            f.seek(payload_off)
            buf = bytearray(f.read(base_bytes))
            if len(buf) != base_bytes:
                raise SystemExit(f"{obj['id']}: short read")
            illegal = remap_code_plane(buf)
            total_illegal += illegal
            total_bytes += base_bytes
            f.seek(payload_off)
            f.write(buf)
            if illegal:
                print(f"  WARN {obj['id']}: {illegal} bytes had code 3")
        f.flush()
        os.fsync(f.fileno())
    print(f"done: remapped {total_bytes:,} code bytes, illegal_fields_in_bytes={total_illegal}")


if __name__ == "__main__":
    main()

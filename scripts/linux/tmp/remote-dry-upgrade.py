#!/usr/bin/env python3
"""Patch upgrade_ninfer_v2_to_v3 for ternary CRACK and dry-run make_directory."""
from __future__ import annotations

import importlib.util
from pathlib import Path

src = Path(
    "/f/ninfer-fusion-kvmem/src-tree/fusion-engine-src/tools/upgrade_ninfer_v2_to_v3.py"
)
text = src.read_text(encoding="utf-8")

# object count already may contain 1126 from earlier patch
if "(1124, 1126, 1190)" not in text:
    text = text.replace(
        '("qwen3.8-27b", "groupwise-int"): (1124, 1190),',
        '("qwen3.8-27b", "groupwise-int"): (1124, 1126, 1190),',
    )

if '"PQ2_0_G128"' not in text:
    text = text.replace(
        '"FP8_E4M3FN_ROW_BF16S": "fp8_e4m3fn_row_bf16",',
        '"FP8_E4M3FN_ROW_BF16S": "fp8_e4m3fn_row_bf16",\n    "PQ2_0_G128": "t2_g128_fp16",',
    )

if 'format == "t2_g128_fp16"' not in text:
    text = text.replace(
        'if layout == "row_scale_v1" and format == "fp8_e4m3fn_row_bf16":\n'
        "        return align(n * k, 256) + n * 2\n"
        "    raise ValueError",
        'if layout == "row_scale_v1" and format == "fp8_e4m3fn_row_bf16":\n'
        "        return align(n * k, 256) + n * 2\n"
        '    if layout == "row_split_k128_v1" and format == "t2_g128_fp16":\n'
        "        groups = align(k, 128) // 128\n"
        "        low = n * groups * 32\n"
        "        return align(low, 256) + n * groups * 2\n"
        "    raise ValueError",
    )

if "text/hadamard_signs" not in text:
    text = text.replace(
        'raise ValueError(f"unknown stored tensor {name}")',
        'if name in ("text/hadamard_signs", "text/hadamard_widths"):\n'
        "            continue\n"
        '        raise ValueError(f"unknown stored tensor {name}")',
    )

# relax binding count for ternary (no dflash2 + hadamard skipped)
text = text.replace(
    'expected_bindings = 32713 if moe else 1513 if has_dflash2 else 1422\n'
    "    if len(bindings) != expected_bindings:\n"
    '        raise ValueError("the known logical parameter mapping is incomplete")',
    'expected_bindings = 32713 if moe else 1513 if has_dflash2 else 1422\n'
    "    # Ternary CRACK (1126 objects, no dflash2) shares the same logical map as 1422.\n"
    "    if len(bindings) != expected_bindings:\n"
    '        raise ValueError(\n'
    '            f"the known logical parameter mapping is incomplete: "\n'
    '            f"{len(bindings)} != {expected_bindings}"\n'
    "        )",
)

tmp = Path("/tmp/upgrade_try.py")
tmp.write_text(text, encoding="utf-8")
print("wrote", tmp, "bytes", tmp.stat().st_size)

spec = importlib.util.spec_from_file_location("up", tmp)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

inp = Path("/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer")
old, start, payload = mod.read_v2(inp)
print("identity", old["identity"], "objects", len(old["objects"]), "payload", payload)
try:
    directory = mod.make_directory(old["identity"], old["objects"])
    print(
        "OK bindings",
        len(directory["bindings"]),
        "uses",
        len(directory["uses"]),
        "objects",
        len(directory["objects"]),
    )
    t2 = sum(1 for o in directory["objects"] if o.get("format") == "t2_g128_fp16")
    print("t2 objects", t2)
except Exception as exc:
    print("FAIL", type(exc).__name__, exc)

#!/usr/bin/env python3
"""Upgrade ternary Bonsai CRACK v2 (PQ2_0_G128) to NInfer v3 for fusion-kvmem.

Builds on tools/upgrade_ninfer_v2_to_v3.py:
  - maps PQ2_0_G128 -> t2_g128_fp16 (payload already row-split)
  - skips binding text/hadamard_* then rewrites signs as bf16 auxiliaries
  - attaches hadamard_signs to every t2_g128_fp16 Use by input width

After this script, run remap-pq2-codes-in-place.py on the output (after a
backup): CRACK stores PQ2 trit codes (0=-1,1=0,2=+1); the engine's
t2_g128_fp16 decoder expects two's-complement (0=0,1=+1,3=-1).
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import struct
import sys
import tempfile
import uuid
from pathlib import Path

SIGN_WIDTHS = (5120, 6144, 17408)  # hidden, attn query rows, intermediate


def _repo_upgrade_py() -> Path:
    here = Path(__file__).resolve()
    return (
        here.parents[2]
        / "src-tree"
        / "fusion-engine-src"
        / "tools"
        / "upgrade_ninfer_v2_to_v3.py"
    )


def _chat_templates_dir() -> Path:
    return _repo_upgrade_py().parent / "chat_templates"


def load_upgraded_module() -> object:
    src = _repo_upgrade_py()
    text = src.read_text(encoding="utf-8")
    if "(1124, 1126, 1190)" not in text:
        text = text.replace(
            '("qwen3.8-27b", "groupwise-int"): (1124, 1190),',
            '("qwen3.8-27b", "groupwise-int"): (1124, 1126, 1190),',
        )
    if '"PQ2_0_G128"' not in text:
        text = text.replace(
            '"FP8_E4M3FN_ROW_BF16S": "fp8_e4m3fn_row_bf16",',
            '"FP8_E4M3FN_ROW_BF16S": "fp8_e4m3fn_row_bf16",\n'
            '    "PQ2_0_G128": "t2_g128_fp16",',
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
    text = text.replace(
        "        objects.append(obj)\n"
        '    by_id = {o["id"]: o for o in objects}',
        '        if obj["id"] in ("text/hadamard_signs", "text/hadamard_widths"):\n'
        "            continue\n"
        "        objects.append(obj)\n"
        '    by_id = {o["id"]: o for o in objects}',
    )
    tmp = Path(tempfile.gettempdir()) / "upgrade_ternary_mod.py"
    tmp.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("upgrade_ternary_mod", tmp)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def f32_to_bf16_bytes(values_f32: bytes) -> bytes:
    n = len(values_f32) // 4
    out = bytearray(n * 2)
    for i in range(n):
        (word,) = struct.unpack_from("<I", values_f32, i * 4)
        struct.pack_into("<H", out, i * 2, (word >> 16) & 0xFFFF)
    return bytes(out)


def read_hadamard_f32(input_path: Path, old: dict, source_start: int) -> bytes:
    obj = next(o for o in old["objects"] if o["name"] == "text/hadamard_signs")
    with input_path.open("rb") as stream:
        stream.seek(source_start + obj["offset"])
        data = stream.read(obj["bytes"])
    if len(data) != 28672 * 4:
        raise ValueError(f"unexpected hadamard_signs size {len(data)}")
    widths = next(o for o in old["objects"] if o["name"] == "text/hadamard_widths")
    with input_path.open("rb") as stream:
        stream.seek(source_start + widths["offset"])
        w = struct.unpack("<3i", stream.read(12))
    if tuple(w) != SIGN_WIDTHS:
        raise ValueError(f"unexpected hadamard_widths {w}")
    return data


def logical_input_width(bindings: dict, name: str, objects_by_id: dict) -> int | None:
    binding = bindings[name]
    if "object" in binding:
        shape = objects_by_id[binding["object"]]["shape"]
        return int(shape[1]) if len(shape) == 2 else None
    parts = binding.get("parts") or []
    if not parts:
        return None
    parent = objects_by_id[parts[0]["object"]]
    if len(parent["shape"]) != 2:
        return None
    return int(parent["shape"][1])


def attach_hadamard(directory: dict, sign_ids: dict[int, str]) -> None:
    objects_by_id = {o["id"]: o for o in directory["objects"]}
    formats = {}
    for name, binding in directory["bindings"].items():
        if "object" in binding:
            formats[name] = objects_by_id[binding["object"]]["format"]
        else:
            formats[name] = objects_by_id[binding["parts"][0]["object"]]["format"]
    attached = 0
    for use in directory["uses"]:
        param = use["parameter"]
        if formats.get(param) != "t2_g128_fp16":
            continue
        width = logical_input_width(directory["bindings"], param, objects_by_id)
        if width not in sign_ids:
            raise ValueError(f"{param}: unexpected t2 input width {width}")
        aux = dict(use.get("auxiliaries") or {})
        aux["hadamard_signs"] = {"object": sign_ids[width]}
        use["auxiliaries"] = aux
        attached += 1
    if attached == 0:
        raise ValueError("no t2 uses received hadamard_signs")
    print(f"attached hadamard_signs to {attached} uses")


def upgrade(input_path: Path, output_path: Path) -> None:
    mod = load_upgraded_module()
    if input_path.resolve() == output_path.resolve():
        raise ValueError("input and output must differ")
    old, source_start, source_payload = mod.read_v2(input_path)
    directory = mod.make_directory(old["identity"], old["objects"])

    f32 = read_hadamard_f32(input_path, old, source_start)
    cursor = 0
    sign_payloads: list[tuple[str, int, bytes]] = []
    for width in SIGN_WIDTHS:
        chunk_f32 = f32[cursor : cursor + width * 4]
        cursor += width * 4
        sign_payloads.append(
            (f"text/hadamard_signs_{width}", width, f32_to_bf16_bytes(chunk_f32))
        )
    if cursor != len(f32):
        raise ValueError("hadamard_signs length mismatch")

    template_name = (
        "qwen3_8.jinja"
        if old["identity"]["model_id"].startswith("qwen3.8-")
        else "qwen3_6.jinja"
    )
    template = (_chat_templates_dir() / template_name).read_bytes()

    template_id = directory["components"]["text"]["resources"]["chat_template.jinja"]
    template_object = next(o for o in directory["objects"] if o["id"] == template_id)
    offset = mod.align(source_payload, 256)
    template_object.update(offset=offset, bytes=len(template))
    directory["objects"].remove(template_object)
    directory["objects"].append(template_object)
    offset = mod.align(offset + len(template), 256)

    sign_ids: dict[int, str] = {}
    for name, width, blob in sign_payloads:
        obj = {
            "id": name,
            "kind": "tensor",
            "shape": [width],
            "format": "bf16",
            "layout": "contiguous_le_v1",
            "offset": offset,
            "bytes": len(blob),
        }
        directory["objects"].append(obj)
        sign_ids[width] = name
        offset = mod.align(offset + len(blob), 256)

    attach_hadamard(directory, sign_ids)
    directory["metadata"] = {"name": "bonsai2-27b"}
    directory["provenance"] = {
        "upgraded_from": {
            "version": 2,
            "model_id": old["identity"]["model_id"],
            "weights_id": old["identity"]["weights_id"],
            "note": "ternary PQ2_0_G128 -> t2_g128_fp16 + hadamard bf16 auxiliaries",
        }
    }

    payload = offset
    template_offset = mod.align(source_payload, 256)
    data, entry_start = mod.layout(output_path, directory, payload)
    targets = [output_path] + [
        output_path.parent / f["path"] for f in directory["files"][1:]
    ]
    if any(path.exists() for path in targets):
        raise FileExistsError("an output file already exists")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    identity = uuid.uuid4().bytes
    temporary, published = [], []

    try:
        with input_path.open("rb") as source:
            source.seek(source_start)
            cursor = 0
            for index, (target, file) in enumerate(zip(targets, directory["files"])):
                fd, temp = tempfile.mkstemp(
                    prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
                )
                temporary.append(Path(temp))
                with os.fdopen(fd, "wb") as output:
                    output.write(
                        mod.HEADER.pack(
                            b"NINFER\0\3" if index == 0 else b"NINPRT\0\3",
                            len(data) if index == 0 else index,
                            identity,
                        )
                    )
                    if index == 0:
                        output.write(data)
                    start = entry_start if index == 0 else 4096
                    output.write(bytes(start - output.tell()))
                    remaining = file["payload_bytes"]
                    pending = output.tell()

                    def write_chunk(chunk: bytes) -> None:
                        nonlocal remaining, pending, cursor
                        output.write(chunk)
                        cursor += len(chunk)
                        remaining -= len(chunk)
                        pending += len(chunk)

                    while remaining:
                        if cursor < source_payload:
                            chunk = source.read(
                                min(remaining, mod.CHUNK, source_payload - cursor)
                            )
                            if not chunk:
                                raise ValueError("v2 payload ended prematurely")
                            mod.drop_cache(
                                source.fileno(), source.tell() - len(chunk), len(chunk)
                            )
                            write_chunk(chunk)
                        elif cursor < template_offset:
                            write_chunk(
                                bytes(min(remaining, template_offset - cursor))
                            )
                        elif cursor < template_offset + len(template):
                            begin = cursor - template_offset
                            write_chunk(
                                template[
                                    begin : begin
                                    + min(remaining, mod.CHUNK, len(template) - begin)
                                ]
                            )
                        else:
                            abs_off = cursor
                            written = False
                            for name, width, blob in sign_payloads:
                                obj = next(
                                    o for o in directory["objects"] if o["id"] == name
                                )
                                if abs_off < obj["offset"]:
                                    write_chunk(
                                        bytes(min(remaining, obj["offset"] - abs_off))
                                    )
                                    written = True
                                    break
                                if abs_off < obj["offset"] + len(blob):
                                    begin = abs_off - obj["offset"]
                                    write_chunk(
                                        blob[
                                            begin : begin
                                            + min(
                                                remaining, mod.CHUNK, len(blob) - begin
                                            )
                                        ]
                                    )
                                    written = True
                                    break
                            if not written:
                                write_chunk(bytes(min(remaining, mod.CHUNK)))
                        if pending >= mod.WRITEBACK:
                            output.flush()
                            mod.datasync(output.fileno())
                            mod.drop_cache(output.fileno())
                            pending = 0
                    output.flush()
                    mod.datasync(output.fileno())
                    mod.drop_cache(output.fileno())
            mod.drop_cache(source.fileno())
        for index in [*range(1, len(targets)), 0]:
            os.link(temporary[index], targets[index])
            published.append(targets[index])
    except BaseException:
        for path in published:
            path.unlink(missing_ok=True)
        raise
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)
    print(
        f"upgraded {input_path} -> {output_path}: "
        f"t2={sum(1 for o in directory['objects'] if o.get('format')=='t2_g128_fp16')} "
        f"bindings={len(directory['bindings'])} uses={len(directory['uses'])}",
        flush=True,
    )


if __name__ == "__main__":
    inp = Path(sys.argv[1] if len(sys.argv) > 1 else "Bonsai-2-27B-PQ2_0-CRACK.ninfer")
    out = Path(
        sys.argv[2] if len(sys.argv) > 2 else "Bonsai-2-27B-PQ2_0-CRACK.v3.ninfer"
    )
    upgrade(inp, out)
    print("size", out.stat().st_size)

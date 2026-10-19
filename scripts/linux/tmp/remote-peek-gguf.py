#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from gguf import GGUFReader

# Expected kinds from gguf_blocks.expected_tensors for GDN layers:
# ssm_alpha/beta -> BF16; ssm_a/dt/conv/norm -> F32; rest blocks OK
MUST_BF16 = ("ssm_alpha.weight", "ssm_beta.weight")
MUST_F32 = (
    "ssm_a",
    "ssm_dt.bias",
    "ssm_conv1d.weight",
    "ssm_norm.weight",
    "attn_norm.weight",
    "post_attention_norm.weight",
    "output_norm.weight",
)


def type_name(t) -> str:
    return t.tensor_type.name if hasattr(t.tensor_type, "name") else str(t.tensor_type)


def main() -> None:
    for path in (
        Path("/f/gguf/RVN-IQ3_S-multilingual-mtp.gguf"),
        Path("/f/gguf/RVN-Q3_K_S-multilingual-mtp.gguf"),
    ):
        print("===", path.name, path.stat().st_size)
        reader = GGUFReader(str(path))
        bad = defaultdict(Counter)
        for t in reader.tensors:
            name = t.name
            typ = type_name(t)
            for suffix in MUST_BF16:
                if name.endswith(suffix) and typ not in ("BF16", "F16"):
                    bad[suffix][typ] += 1
            for suffix in MUST_F32:
                if name.endswith(suffix) and typ != "F32":
                    bad[suffix][typ] += 1
        if not bad:
            print("  dense tensors OK (alpha/beta BF16, scalars F32)")
        else:
            for k, c in sorted(bad.items()):
                print(f"  BAD {k}: {dict(c)}")
        # sample blk.0 GDN-related
        for t in reader.tensors:
            if t.name.startswith("blk.0.") and (
                "ssm_" in t.name or "attn_qkv" in t.name or "attn_gate" in t.name
            ):
                print(f"  {t.name:40s} {type_name(t):10s} {tuple(t.shape)}")


if __name__ == "__main__":
    main()

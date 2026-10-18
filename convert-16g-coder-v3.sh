#!/usr/bin/env bash
# 在 192.168.1.5 的 Ubuntu 上执行。把 coder GGUF 转成 NInfer v3。
# 先不要跑：等 download-16g-coder.sh 下完再执行。
#
# 输入：
#   /f/gguf/RVN-Q3_K_S-multilingual-mtp.gguf
#   /f/Qwen3.8-27B-config          （官方 config + tokenizer，无权重）
# 输出：
#   /f/qwen3.8-27b-rvn-q3ks-coder.v3.ninfer
#
# 组件只有 text,mtp。不带 vision / dflash2。
# 默认 --device cpu。要 GPU 转换：NINFER_CONVERT_DEVICE=cuda ./convert-16g-coder-v3.sh
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SRC="${NINFER_SRC:-/f/ninfer-fusion-kvmem/src-tree/fusion-engine-src}"
BASE="${NINFER_BASE:-/f/Qwen3.8-27B-config}"
GGUF="${NINFER_GGUF:-/f/gguf/RVN-Q3_K_S-multilingual-mtp.gguf}"
OUT="${NINFER_OUT:-/f/qwen3.8-27b-rvn-q3ks-coder.v3.ninfer}"
DEVICE="${NINFER_CONVERT_DEVICE:-cpu}"

if [[ -f "$OUT" ]]; then
  echo "[convert-16g-coder] FATAL: output already exists: $OUT" >&2
  exit 2
fi
for need in "$GGUF" "$BASE/config.json" "$BASE/tokenizer.json" "$BASE/tokenizer_config.json" "$BASE/generation_config.json"; do
  if [[ ! -f "$need" ]]; then
    echo "[convert-16g-coder] FATAL: missing $need" >&2
    echo "  run download-16g.sh on this machine first" >&2
    exit 2
  fi
done
if [[ ! -d "$SRC/tools/convert" ]]; then
  echo "[convert-16g-coder] FATAL: converter tree not found: $SRC" >&2
  exit 2
fi

PY=python3
if command -v python3.11 >/dev/null 2>&1; then
  PY=python3.11
fi

echo "[convert-16g-coder] src=$SRC"
echo "[convert-16g-coder] gguf=$GGUF"
echo "[convert-16g-coder] out=$OUT device=$DEVICE"
echo "[convert-16g-coder] start with: ARTIFACT=$OUT $ROOT/start-16g-coder.sh"

cd "$SRC"
exec "$PY" -m tools.convert \
  --model "$BASE" \
  --recipe qwen3_8_27b_gguf \
  --source "gguf=${GGUF}" \
  --components text,mtp \
  --resource chat_template.jinja=tools/chat_templates/qwen3_8.jinja \
  --proposal \
  --device "$DEVICE" \
  --name qwen3.8-27b-rvn-q3ks-coder \
  --out "$OUT"

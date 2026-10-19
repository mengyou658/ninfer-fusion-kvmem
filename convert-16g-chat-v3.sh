#!/usr/bin/env bash
# 在 192.168.1.5 的 Ubuntu 上执行。把 chat GGUF 转成 NInfer v3。
# 先不要跑：等 download-16g-chat.sh 下完再执行。
#
# 输入：
#   /f/gguf/RVN-IQ3_S-multilingual-mtp.gguf
#   /f/Qwen3.8-27B-config          （官方 config + tokenizer，无权重）
# 输出：
#   /f/qwen3.8-27b-rvn-iq3s-chat.v3.ninfer
#
# 组件只有 text,mtp。不带 vision / dflash2。
# --proposal 把抽样头写进文件，启动时不加 --lm-head-draft 就不会装进显存。
# 默认 --device cpu，避免和正在用的 GPU 抢显存。要 GPU 转换：
#   NINFER_CONVERT_DEVICE=cuda ./convert-16g-chat-v3.sh
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SRC="${NINFER_SRC:-/f/ninfer-fusion-kvmem/src-tree/fusion-engine-src}"
BASE="${NINFER_BASE:-/f/Qwen3.8-27B-config}"
GGUF="${NINFER_GGUF:-/f/gguf/RVN-IQ3_S-multilingual-mtp.gguf}"
OUT="${NINFER_OUT:-/f/qwen3.8-27b-rvn-iq3s-chat.v3.ninfer}"
DEVICE="${NINFER_CONVERT_DEVICE:-cpu}"

if [[ -f "$OUT" ]]; then
  echo "[convert-16g-chat] FATAL: output already exists: $OUT" >&2
  exit 2
fi
for need in "$GGUF" "$BASE/config.json" "$BASE/tokenizer.json" "$BASE/tokenizer_config.json" "$BASE/generation_config.json"; do
  if [[ ! -f "$need" ]]; then
    echo "[convert-16g-chat] FATAL: missing $need" >&2
    echo "  run download-16g.sh on this machine first" >&2
    exit 2
  fi
done
if [[ ! -d "$SRC/tools/convert" ]]; then
  echo "[convert-16g-chat] FATAL: converter tree not found: $SRC" >&2
  exit 2
fi

# Prefer activated venv (same as download-16g.sh: source comfyenv/bin/activate).
if [[ -n "${NINFER_PYTHON:-}" ]]; then
  PY="$NINFER_PYTHON"
elif [[ -n "${VIRTUAL_ENV:-}" ]] && command -v python >/dev/null 2>&1; then
  PY=python
elif command -v python3.11 >/dev/null 2>&1; then
  PY=python3.11
else
  PY=python3
fi

echo "[convert-16g-chat] src=$SRC"
echo "[convert-16g-chat] gguf=$GGUF"
echo "[convert-16g-chat] out=$OUT device=$DEVICE"
echo "[convert-16g-chat] start with: ARTIFACT=$OUT $ROOT/start-16g-chat.sh"

cd "$SRC"
exec "$PY" -m tools.convert \
  --model "$BASE" \
  --recipe qwen3_8_27b_gguf \
  --source "gguf=${GGUF}" \
  --components text,mtp \
  --resource chat_template.jinja=tools/chat_templates/qwen3_8.jinja \
  --proposal \
  --device "$DEVICE" \
  --name qwen3.8-27b-rvn-iq3s-chat \
  --out "$OUT"

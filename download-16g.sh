#!/usr/bin/env bash
# 在 192.168.1.5 的 Ubuntu 上执行。只下载，不转换。
#
# 官方 Qwen3.8-27B 的 config / tokenizer 两套转换共用，只下一次。
# 两个 GGUF 不是同一个文件，各下一次；本地已有且非空则跳过。
#
# Chat（start-16g-chat.sh，窗口 16384）：
#   /f/gguf/RVN-IQ3_S-multilingual-mtp.gguf ≈ 11.99 GiB
# Coder（start-16g-coder.sh，窗口 32768）：
#   /f/gguf/RVN-Q3_K_S-multilingual-mtp.gguf ≈ 11.67 GiB
set -euo pipefail

DEST=/f
BASE="${DEST}/Qwen3.8-27B-config"
GGUF_DIR="${DEST}/gguf"
REPO="0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF"
BASE_REPO="Qwen/Qwen3.8-27B"
BASE_FILES=(config.json generation_config.json tokenizer.json tokenizer_config.json)
GGUF_FILES=(
  RVN-IQ3_S-multilingual-mtp.gguf
  RVN-Q3_K_S-multilingual-mtp.gguf
)

export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"
export HF_HUB_ENABLE_HF_TRANSFER=0

mkdir -p "$BASE" "$GGUF_DIR"

if command -v hf >/dev/null 2>&1; then
  hf_download() { hf download "$@"; }
elif command -v huggingface-cli >/dev/null 2>&1; then
  hf_download() { huggingface-cli download "$@"; }
else
  python3 -m pip install -U 'huggingface_hub>=0.26'
  hf_download() { python3 -m huggingface_hub.commands.huggingface_cli download "$@"; }
fi

base_missing=()
for name in "${BASE_FILES[@]}"; do
  if [[ ! -s "${BASE}/${name}" ]]; then
    base_missing+=("$name")
  fi
done
if ((${#base_missing[@]} == 0)); then
  echo "[download-16g] skip base config, already in $BASE"
else
  echo "[download-16g] base config -> $BASE (${base_missing[*]})"
  hf_download "$BASE_REPO" "${base_missing[@]}" --local-dir "$BASE"
fi

for name in "${GGUF_FILES[@]}"; do
  path="${GGUF_DIR}/${name}"
  if [[ -s "$path" ]]; then
    echo "[download-16g] skip $name"
    continue
  fi
  echo "[download-16g] gguf -> $path"
  hf_download "$REPO" "$name" --local-dir "$GGUF_DIR"
done

ls -lh "${GGUF_DIR}/RVN-IQ3_S-multilingual-mtp.gguf" \
  "${GGUF_DIR}/RVN-Q3_K_S-multilingual-mtp.gguf" \
  "$BASE/config.json" "$BASE/tokenizer.json"
echo "[download-16g] done. convert with ./convert-16g-chat-v3.sh and ./convert-16g-coder-v3.sh"

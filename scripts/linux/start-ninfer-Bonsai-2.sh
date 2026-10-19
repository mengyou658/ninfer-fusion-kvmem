#!/usr/bin/env bash
# start-ninfer-Bonsai.sh — Ternary Bonsai 2 27B on a 16 GB NVIDIA card (sm_120a).
# Do NOT use this on 8 GB cards (use start-8g.bat / a 8 GB Linux port instead).
#
# Same KVMem contract as start-16g-chat.sh (README + docs/12 §2/§5). Ternary
# early-stops on rk4v4 (docs/03 §7), so the resident cache stays k8v4.
# Spec is MTP only. Do not add --lm-head-draft / --vision / --spec dflash2
# unless the artifact actually contains those components.
#
set -euo pipefail

ARTIFACT="${ARTIFACT:-/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer}"
EXE="${EXE:-/f/ninfer-Bonsai-2-5060/build/apps/ninfer-serve}"
HOST="${NINFER_HOST:-0.0.0.0}"
PORT="${NINFER_PORT:-8080}"
MODELID="${NINFER_MODEL_ID:-bonsai2-27b}"
DRAFT="${NINFER_DRAFT_TOKENS:-3}"

export PATH="/usr/local/cuda/bin:${PATH:-}"

if [[ ! -f "$ARTIFACT" ]]; then
  echo "[start-ninfer-Bonsai] FATAL: model not found: $ARTIFACT" >&2
  exit 2
fi
if [[ ! -x "$EXE" ]]; then
  echo "[start-ninfer-Bonsai] FATAL: ninfer-serve not found: $EXE" >&2
  exit 2
fi

# KVMem ring (must be env vars; there are no CLI equivalents). B30: ring gate is WINDOW.
export NINFER_KV_WINDOW="${NINFER_KV_WINDOW:-16384}"
export NINFER_KV_RETRIEVE="${NINFER_KV_RETRIEVE:-8192}"
export NINFER_KV_RING="${NINFER_KV_RING:-1}"
export NINFER_HOST_PAGEABLE="${NINFER_HOST_PAGEABLE:-1}"
export NINFER_KV_REUSE_HOSTBACKED="${NINFER_KV_REUSE_HOSTBACKED:-1}"
export NINFER_TERNARY_KVMEM_SCORE_QUERY_TAIL="${NINFER_TERNARY_KVMEM_SCORE_QUERY_TAIL:-64}"

echo "[start-ninfer-Bonsai] model=$ARTIFACT"
echo "[start-ninfer-Bonsai] engine=$EXE"
echo "[start-ninfer-Bonsai] http://${HOST}:${PORT}/v1  model-id=${MODELID}"
echo "[start-ninfer-Bonsai] window=${NINFER_KV_WINDOW} retrieve=${NINFER_KV_RETRIEVE} kv=k8v4 pool=auto ctx=32768 mtp-draft=${DRAFT}"
echo "[start-ninfer-Bonsai] this engine requires kv-capacity >= max-context"
echo

exec "$EXE" "$ARTIFACT" \
  --host "$HOST" --port "$PORT" --model-id "$MODELID" \
  --max-context 32768 --kv-capacity auto --kv-dtype k8v4 \
  --host-kv-mib 16384 --prefill-chunk 1024 \
  --max-concurrency 1 --max-shared-prefixes 0 \
  --spec mtp --draft-tokens "$DRAFT" \
  --default-max-tokens 2048 \
  --default-thinking-budget 1024 \
  --temperature 0.7 --top-p 0.9 --top-k 20 \
  --cors \
  "$@"

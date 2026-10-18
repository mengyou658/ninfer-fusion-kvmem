#!/usr/bin/env bash
# start-16g-chat.sh — 16 GB NVIDIA card, conversational chat.
# Do NOT use this on 8 GB cards (use start-8g.bat / a 8 GB Linux port instead).
#
# Sources:
#   README.md "启动一个文本服务" (16 GiB host KV, k8v4, pool 17920, window 16384)
#   docs/12-给接收方-agent-的操作手册.md §2 / §5 (KVMem env, --max-shared-prefixes 0)
#   docs/03-基础部署后的调优方案.md §1.5.3 (16 GB row) — window/pool kept at the
#     README k8v4 shape because Bonsai ternary early-stops on rk4v4 (docs/03 §7)
#   docs/00-三档口径与读数.md — PQ2 chat sampling
#
# Hardware this was written for: RTX 5060 Ti 16 GB (sm_120a), artifact
#   ARTIFACT=/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer (~7.8 GiB, MTP; no dflash2 assumed)
# Spec: --spec mtp only. Do not add --lm-head-draft / --vision / --spec dflash2
# unless model check shows those components.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Prefer the v3 upgrade of the ternary CRACK pack (v2 is rejected by fusion-kvmem).
ARTIFACT="${ARTIFACT:-${NINFER_MODEL:-}}"
EXE="${NINFER_SERVER:-$ROOT/src-tree/fusion-engine-src/build-120a/apps/ninfer-serve}"
HOST="${NINFER_HOST:-0.0.0.0}"
PORT="${NINFER_PORT:-8091}"
MODELID="${NINFER_MODEL_ID:-ninfer-chat}"

export PATH="/usr/local/cuda/bin:${PATH:-}"

if [[ -z "$ARTIFACT" || ! -f "$ARTIFACT" ]]; then
  echo "[start-16g-chat] FATAL: set ARTIFACT or NINFER_MODEL to a v3 .ninfer path" >&2
  echo "  example: ARTIFACT=/path/to/Bonsai-2-27B-PQ2_0-CRACK.v3.ninfer $0" >&2
  exit 2
fi
if [[ ! -x "$EXE" ]]; then
  echo "[start-16g-chat] FATAL: engine not found: $EXE" >&2
  echo "Build first: bash scripts/linux/configure-sm120a.sh && bash scripts/linux/build-ninfer-serve.sh" >&2
  exit 2
fi

# KVMem ring (must be env vars; there are no CLI equivalents). B30: ring gate is WINDOW.
export NINFER_KV_WINDOW="${NINFER_KV_WINDOW:-16384}"
export NINFER_KV_RETRIEVE="${NINFER_KV_RETRIEVE:-8192}"
export NINFER_KV_RING="${NINFER_KV_RING:-1}"
export NINFER_HOST_PAGEABLE="${NINFER_HOST_PAGEABLE:-1}"
export NINFER_KV_REUSE_HOSTBACKED="${NINFER_KV_REUSE_HOSTBACKED:-1}"
export NINFER_TERNARY_KVMEM_SCORE_QUERY_TAIL="${NINFER_TERNARY_KVMEM_SCORE_QUERY_TAIL:-64}"

echo "[start-16g-chat] model=$ARTIFACT"
echo "[start-16g-chat] engine=$EXE"
echo "[start-16g-chat] http://${HOST}:${PORT}/v1  model-id=${MODELID}"
echo "[start-16g-chat] window=${NINFER_KV_WINDOW} retrieve=${NINFER_KV_RETRIEVE} kv=k8v4 pool=17920 ctx=262144"
echo "[start-16g-chat] after ready, check: capacity | KV 17,920 tokens, k8v4 | reuse host-backed: on"
echo

exec "$EXE" "$ARTIFACT" \
  --host "$HOST" --port "$PORT" --model-id "$MODELID" \
  --max-context 262144 --kv-capacity 17920 --kv-dtype k8v4 \
  --host-kv-mib 16384 --prefill-chunk 1024 \
  --max-concurrency 1 --max-shared-prefixes 0 \
  --spec mtp --draft-tokens 4 \
  --gdn-state-fp16 \
  --default-max-tokens 2048 --default-reasoning-effort none \
  --default-thinking-budget 1024 \
  --temperature 0.7 --top-p 0.9 --top-k 20 \
  --cors \
  "$@"

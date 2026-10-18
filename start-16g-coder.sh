#!/usr/bin/env bash
# start-16g-coder.sh — 16 GB NVIDIA card, coding / agent sessions.
# Do NOT use this on 8 GB cards.
#
# Same KVMem contract as start-16g-chat.sh (README + docs/12 §2/§5), with a larger
# resident window so repo-sized prompts stay on-device more often.
#
# Pool math (docs/12 §5.2, docs/03 §1):
#   pages = WINDOW/64 + prefill/64 + 8
#         = 32768/64 + 1024/64 + 8 = 512 + 16 + 8 = 536 pages = 34,304 tokens
#   --kv-capacity auto sizes the pool from the window (startup.cpp kvmem_resident_pages).
# 16 GB headroom: PQ2 CRACK ~7.8 GiB weights + ~3–4 GiB k8v4 runtime for this pool
# (extrapolated from docs/00 280-page runtime 2.63–2.95 GiB). Unverified on this card
# until the capacity line is read after start.
#
# Differences vs chat:
#   longer window / auto pool, 32k default output, sampling cooler, no thinking budget,
#   reasoning off (agent loops must not re-inject reasoning — docs/12 §9).
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Prefer the v3 upgrade of the ternary CRACK pack (v2 is rejected by fusion-kvmem).
ARTIFACT="${ARTIFACT:-${NINFER_MODEL:-}}"
EXE="${NINFER_SERVER:-$ROOT/src-tree/fusion-engine-src/build-120a/apps/ninfer-serve}"
HOST="${NINFER_HOST:-0.0.0.0}"
PORT="${NINFER_PORT:-8092}"
MODELID="${NINFER_MODEL_ID:-ninfer-coder}"

export PATH="/usr/local/cuda/bin:${PATH:-}"

if [[ -z "$ARTIFACT" || ! -f "$ARTIFACT" ]]; then
  echo "[start-16g-coder] FATAL: set ARTIFACT or NINFER_MODEL to a v3 .ninfer path" >&2
  echo "  example: ARTIFACT=/path/to/Bonsai-2-27B-PQ2_0-CRACK.v3.ninfer $0" >&2
  exit 2
fi
if [[ ! -x "$EXE" ]]; then
  echo "[start-16g-coder] FATAL: engine not found: $EXE" >&2
  echo "Build first: bash scripts/linux/configure-sm120a.sh && bash scripts/linux/build-ninfer-serve.sh" >&2
  exit 2
fi

export NINFER_KV_WINDOW="${NINFER_KV_WINDOW:-32768}"
export NINFER_KV_RETRIEVE="${NINFER_KV_RETRIEVE:-8192}"
export NINFER_KV_RING="${NINFER_KV_RING:-1}"
export NINFER_HOST_PAGEABLE="${NINFER_HOST_PAGEABLE:-1}"
export NINFER_KV_REUSE_HOSTBACKED="${NINFER_KV_REUSE_HOSTBACKED:-1}"
export NINFER_TERNARY_KVMEM_SCORE_QUERY_TAIL="${NINFER_TERNARY_KVMEM_SCORE_QUERY_TAIL:-64}"

echo "[start-16g-coder] model=$ARTIFACT"
echo "[start-16g-coder] engine=$EXE"
echo "[start-16g-coder] http://${HOST}:${PORT}/v1  model-id=${MODELID}"
echo "[start-16g-coder] window=${NINFER_KV_WINDOW} retrieve=${NINFER_KV_RETRIEVE} kv=k8v4 pool=auto ctx=262144"
echo "[start-16g-coder] after ready, check: capacity | KV … tokens, k8v4, auto | reuse host-backed: on"
echo "[start-16g-coder] if startup refuses VRAM, lower NINFER_KV_WINDOW to 16384 and retry"
echo

exec "$EXE" "$ARTIFACT" \
  --host "$HOST" --port "$PORT" --model-id "$MODELID" \
  --max-context 262144 --kv-capacity auto --kv-dtype k8v4 \
  --host-kv-mib 16384 --prefill-chunk 1024 \
  --max-concurrency 1 --max-shared-prefixes 0 \
  --spec mtp --draft-tokens 4 \
  --gdn-state-fp16 \
  --default-max-tokens 32768 --default-reasoning-effort none \
  --temperature 0.2 --top-p 0.9 --top-k 20 \
  --cors \
  "$@"

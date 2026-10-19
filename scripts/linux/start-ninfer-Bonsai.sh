#!/bin/bash
# ============================================================
#  NInfer · Ternary Bonsai 2 27B  (RTX 5060 Ti / sm_120a / Linux)
#  engine: /f/ninfer-Bonsai-2-5060  (CraneBW/ninfer-ternary-bonsai-ada)
#  artifact packed from Bonsai-2-27B-PQ2_0-CRACK.gguf via ModelScope packer
#
#  knobs (edit below, then: bash /f/start-ninfer-Bonsai.sh):
#    CTX      context limit (tokens). 32k recommended on 16GB
#    MODELID  public model name — clients must send the same "model"
#    KVTYPE   KV cache: bf16 | fp8 | int8 | nvfp4 | k8v4
#    PORT     listen port
#    DRAFT    MTP draft tokens (0 = disable speculative decoding)
# ============================================================
set -euo pipefail

CTX=100000
MODELID=bonsai2-27b
KVTYPE=fp8
PORT=8080
DRAFT=3
HOST=0.0.0.0

ARTIFACT=/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer
EXE=/f/ninfer-Bonsai-2-5060/build/apps/ninfer-serve

if [[ ! -f "$ARTIFACT" ]]; then
  echo "[ERROR] artifact not found: $ARTIFACT" >&2
  exit 1
fi
if [[ ! -x "$EXE" ]]; then
  echo "[ERROR] ninfer-serve not found (build first): $EXE" >&2
  exit 1
fi

export PATH=/usr/local/cuda/bin:${PATH:-}

echo "loading model (first start may take 10-30s) ..."
echo "  artifact : $ARTIFACT"
echo "  endpoint : http://${HOST}:${PORT}/v1/models   (OpenAI compatible)"
echo "  model-id : $MODELID"
echo "  context  : $CTX  kv=$KVTYPE  mtp-draft=$DRAFT"
echo "press Ctrl+C to stop"
echo

exec "$EXE" "$ARTIFACT" \
  --host "$HOST" --port "$PORT" \
  --model-id "$MODELID" \
  --max-context "$CTX" --kv-capacity auto --kv-dtype "$KVTYPE" \
  --max-concurrency 2 \
  --spec mtp --draft-tokens "$DRAFT" \
  --cors

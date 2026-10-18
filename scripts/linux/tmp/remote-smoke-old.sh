#!/bin/bash
# Smoke the ORIGINAL v2 CRACK on the old ternary fork (known-good path).
set -euo pipefail
pkill -f '/build-120a/apps/ninfer-serve' 2>/dev/null || true
pkill -f '/ninfer-Bonsai-2-5060/build/apps/ninfer-serve' 2>/dev/null || true
sleep 1
EXE=/f/ninfer-Bonsai-2-5060/build/apps/ninfer-serve
ART=/f/Bonsai-2-27B-PQ2_0-CRACK.ninfer
nohup "$EXE" "$ART" \
  --host 127.0.0.1 --port 8095 --model-id old-crack \
  --max-context 8192 --kv-capacity auto --kv-dtype fp8 \
  --max-concurrency 1 --spec mtp --draft-tokens 3 \
  >/f/ninfer-fusion-kvmem/old-smoke.log 2>&1 </dev/null &
echo PID=$!
for i in $(seq 1 60); do
  if grep -q 'engine ready\|listening on\|FATAL' /f/ninfer-fusion-kvmem/old-smoke.log 2>/dev/null; then
    break
  fi
  sleep 2
done
grep -E 'engine ready|FATAL|listening|capacity ' /f/ninfer-fusion-kvmem/old-smoke.log | tail -n 10 || true
curl -sS -m 120 http://127.0.0.1:8095/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"old-crack","messages":[{"role":"user","content":"What is 17 + 25? Reply with the number only."}],"max_tokens":16,"temperature":0,"stream":false}' || true
echo

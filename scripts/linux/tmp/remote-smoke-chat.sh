#!/bin/bash
set -euo pipefail
curl -sS -m 180 http://127.0.0.1:8091/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "ninfer-chat",
    "messages": [{"role":"user","content":"What is 17 + 25? Reply with the number only."}],
    "max_tokens": 32,
    "temperature": 0,
    "stream": false,
    "reasoning_effort": "none"
  }'
echo

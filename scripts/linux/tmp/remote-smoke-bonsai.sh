#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, urllib.request
body = json.dumps({
    "model": "bonsai2-27b",
    "messages": [{"role": "user", "content": "What is 17 + 25? Reply with the number only."}],
    "max_tokens": 128,
}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8080/v1/chat/completions",
    data=body,
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=60) as resp:
    print(resp.read().decode())
PY

#!/usr/bin/env bash
set -euo pipefail
ROOT=/f/ninfer-fusion-kvmem
LOG="$ROOT/convert-16g-both.log"
PIDF="$ROOT/convert-16g-both.pid"
WRAPPER="$ROOT/convert-16g-both.sh"

# Stop prior run if still alive.
if [[ -f "$PIDF" ]]; then
  old=$(cat "$PIDF" || true)
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    kill "$old" 2>/dev/null || true
    sleep 1
    kill -9 "$old" 2>/dev/null || true
  fi
  rm -f "$PIDF"
fi
pkill -f 'tools.convert' 2>/dev/null || true
pkill -f 'convert-16g-' 2>/dev/null || true

# Drop any partial outputs so convert scripts can start clean.
rm -f /f/qwen3.8-27b-rvn-iq3s-chat.v3.ninfer* \
  /f/qwen3.8-27b-rvn-q3ks-coder.v3.ninfer* \
  /f/.qwen3.8-27b-rvn-*.tmp 2>/dev/null || true

cat >"$WRAPPER" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
cd /f/comfyui20260902
set +u
source comfyenv/bin/activate
set -u
export NINFER_PYTHON="$(command -v python)"
echo "[both] python=$NINFER_PYTHON"
"$NINFER_PYTHON" -c 'import torch, gguf, numpy; print("deps ok", torch.__version__)'
echo "[both] chat start $(date -Is)"
bash /f/ninfer-fusion-kvmem/convert-16g-chat-v3.sh
echo "[both] chat done $(date -Is)"
ls -lh /f/qwen3.8-27b-rvn-iq3s-chat.v3.ninfer
echo "[both] coder start $(date -Is)"
bash /f/ninfer-fusion-kvmem/convert-16g-coder-v3.sh
echo "[both] coder done $(date -Is)"
ls -lh /f/qwen3.8-27b-rvn-q3ks-coder.v3.ninfer
EOS
chmod +x "$WRAPPER" "$ROOT/convert-16g-chat-v3.sh" "$ROOT/convert-16g-coder-v3.sh"

nohup bash "$WRAPPER" >"$LOG" 2>&1 </dev/null &
echo $! >"$PIDF"
echo "[relaunch] pid=$! log=$LOG"
sleep 8
tail -n 60 "$LOG" || true

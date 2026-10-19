#!/usr/bin/env bash
# Root launcher: comfyenv's python -> /root/.pyenv/... (yun cannot exec it).
# Same activate path as download-16g.sh; convert does not need hf login.
set -euo pipefail
ROOT=/f/ninfer-fusion-kvmem
LOG="$ROOT/convert-16g-both.log"
PIDF="$ROOT/convert-16g-both.pid"
WRAPPER="$ROOT/convert-16g-both.sh"

if [[ -f "$PIDF" ]] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
  echo "[launch] already running pid=$(cat "$PIDF")"
  exit 0
fi

cat >"$WRAPPER" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
cd /f/comfyui20260902
set +u
# shellcheck disable=SC1091
source comfyenv/bin/activate
set -u
export NINFER_PYTHON="$(command -v python)"
echo "[both] python=$NINFER_PYTHON VIRTUAL_ENV=${VIRTUAL_ENV:-}"
"$NINFER_PYTHON" -c 'import torch, gguf, numpy; print("deps ok", torch.__version__, numpy.__version__)'
echo "[both] chat start $(date -Is)"
bash /f/ninfer-fusion-kvmem/convert-16g-chat-v3.sh
echo "[both] chat done $(date -Is) size=$(ls -lh /f/qwen3.8-27b-rvn-iq3s-chat.v3.ninfer | awk '{print $5}')"
echo "[both] coder start $(date -Is)"
bash /f/ninfer-fusion-kvmem/convert-16g-coder-v3.sh
echo "[both] coder done $(date -Is) size=$(ls -lh /f/qwen3.8-27b-rvn-q3ks-coder.v3.ninfer | awk '{print $5}')"
EOS
chmod +x "$WRAPPER"

# Re-upload convert scripts must already be in place; ensure executable.
chmod +x "$ROOT/convert-16g-chat-v3.sh" "$ROOT/convert-16g-coder-v3.sh"

nohup bash "$WRAPPER" >"$LOG" 2>&1 </dev/null &
echo $! >"$PIDF"
echo "[launch] both pid=$! log=$LOG"
sleep 3
head -n 50 "$LOG" || true
ps -p "$(cat "$PIDF")" -o pid,etime,cmd || true

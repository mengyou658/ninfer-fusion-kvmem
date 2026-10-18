#!/bin/bash
set -euo pipefail
# Stop the byte-loop remapper and any serve process. Do not pkill this shell.
if [[ -n "$(pgrep -f '/tmp/remote-repack-pq2-to-t2.py' || true)" ]]; then
  pkill -f '/tmp/remote-repack-pq2-to-t2.py' || true
fi
if [[ -n "$(pgrep -f '/build-120a/apps/ninfer-serve' || true)" ]]; then
  pkill -f '/build-120a/apps/ninfer-serve' || true
fi
sleep 2
rm -f /f/Bonsai-2-27B-PQ2_0-CRACK.v3.ninfer
echo "upgrade start $(date -Is)"
python3 /tmp/remote-upgrade-ternary.py
echo "remap start $(date -Is)"
/f/comfyui20260902/comfyenv/bin/python /tmp/remote-repack-fast.py
echo "ALL_DONE $(date -Is)"

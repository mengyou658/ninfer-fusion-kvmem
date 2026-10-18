#!/bin/bash
set -euo pipefail
# Kill only ninfer-serve, not this script's process group.
pids=$(pgrep -f '/build-120a/apps/ninfer-serve' || true)
if [[ -n "${pids}" ]]; then
  echo "stopping: $pids"
  kill $pids || true
  sleep 2
fi
python3 /tmp/remote-repack-pq2-to-t2.py
echo REPACK_DONE

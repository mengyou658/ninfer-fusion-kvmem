#!/usr/bin/env bash
set -euo pipefail
PIDF=/f/ninfer-fusion-kvmem/convert-16g-both.pid
LOG=/f/ninfer-fusion-kvmem/convert-16g-both.log
echo "=== $(date -Is) ==="
if [[ -f "$PIDF" ]]; then
  pid=$(cat "$PIDF")
  if kill -0 "$pid" 2>/dev/null; then
    ps -p "$pid" -o pid,etime,pcpu,pmem,cmd
  else
    echo "wrapper dead pid=$pid"
  fi
else
  echo "no pidfile"
fi
pgrep -af 'tools.convert|convert-16g' || true
echo "--- log tail ---"
tail -n 25 "$LOG"
echo "--- outputs ---"
ls -lh /f/qwen3.8-27b-rvn-*.ninfer 2>/dev/null || echo "(none yet)"
grep -n 'ssm_alpha\|dequant\|BF16\|ValueError\|Traceback\|chat done\|coder done\|FATAL' "$LOG" | tail -n 30 || true

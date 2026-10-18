#!/bin/bash
set -euo pipefail
pkill -f '/build-120a/apps/ninfer-serve' 2>/dev/null || true
sleep 1
rm -f /f/ninfer-fusion-kvmem/chat-16g.log
nohup /f/start-16g-chat.sh >/f/ninfer-fusion-kvmem/chat-16g.log 2>&1 </dev/null &
echo "PID=$!"
sleep 1
pgrep -af '/build-120a/apps/ninfer-serve' || echo 'no serve yet'
head -n 15 /f/ninfer-fusion-kvmem/chat-16g.log || true

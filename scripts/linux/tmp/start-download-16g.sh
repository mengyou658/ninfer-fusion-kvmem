#!/usr/bin/env bash
# Launch download-16g.sh under comfyenv as root on 192.168.1.5.
set -euo pipefail
sed -i 's/\r$//' /tmp/download-16g.sh
chmod 755 /tmp/download-16g.sh
: >/f/download-16g.log
# Detach fully so su/ssh can exit without killing the download.
setsid bash /tmp/download-16g.sh >>/f/download-16g.log 2>&1 </dev/null &
echo "STARTED:$!"
sleep 1
pgrep -af '/tmp/download-16g.sh' || echo NOT_RUNNING

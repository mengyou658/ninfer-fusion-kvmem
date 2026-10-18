#!/bin/bash
set -euo pipefail
python3 /tmp/remote-patch-upgrade.py
python3 /f/ninfer-fusion-kvmem/src-tree/fusion-engine-src/tools/upgrade_ninfer_v2_to_v3.py \
  /f/Bonsai-2-27B-PQ2_0-CRACK.ninfer \
  /f/Bonsai-2-27B-PQ2_0-CRACK.v3.ninfer
ls -lh /f/Bonsai-2-27B-PQ2_0-CRACK.v3.ninfer

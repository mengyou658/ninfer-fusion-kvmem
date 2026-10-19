#!/usr/bin/env bash
set -euo pipefail
whoami
id
ls -la /f/ninfer-fusion-kvmem/convert-16g-chat-v3.sh /f/ninfer-fusion-kvmem/convert-16g-coder-v3.sh
cd /f/comfyui20260902
set +u
# shellcheck disable=SC1091
source comfyenv/bin/activate
set -u
which python python3
python - <<'PY'
import torch, gguf, numpy
print("torch", torch.__version__)
print("gguf", getattr(gguf, "__version__", "?"))
print("numpy", numpy.__version__)
PY

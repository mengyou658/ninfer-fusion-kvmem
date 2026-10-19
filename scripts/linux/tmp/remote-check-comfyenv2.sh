#!/usr/bin/env bash
set -euo pipefail
ls -la /f/comfyui20260902/comfyenv/bin/python /f/comfyui20260902/comfyenv/bin/python3 /f/comfyui20260902/comfyenv/bin/hf 2>&1
echo "--- activate ---"
cd /f/comfyui20260902
set +u
source comfyenv/bin/activate
set -u
echo "VIRTUAL_ENV=${VIRTUAL_ENV:-unset}"
command -v python
command -v python3
command -v hf
/f/comfyui20260902/comfyenv/bin/python -c 'import sys; print(sys.executable)'
/f/comfyui20260902/comfyenv/bin/python -c 'import torch; print("torch", torch.__version__)'
/f/comfyui20260902/comfyenv/bin/python -c 'import gguf; print("gguf ok")'
/f/comfyui20260902/comfyenv/bin/python -c 'import numpy; print("numpy", numpy.__version__)'

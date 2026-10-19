#!/usr/bin/env bash
set -euo pipefail
ls -la /f/comfyui20260902 | head -30
ls -la /f/comfyui20260902/comfyenv/bin 2>&1 | head -40
echo "---"
cd /f/comfyui20260902
set +u
source comfyenv/bin/activate
set -u
echo "VIRTUAL_ENV=${VIRTUAL_ENV:-}"
echo "PATH=$PATH"
type -a python python3 || true
python -c 'import sys; print(sys.executable); print(sys.path[:5])'
python -c 'import gguf; print("gguf ok", gguf)' 2>&1 || true
python -c 'import numpy; print("numpy", numpy.__version__)' 2>&1 || true
hf --help 2>&1 | head -3 || true

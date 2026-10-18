#!/bin/bash
set -euo pipefail
export PATH=/usr/local/cuda/bin:/usr/bin:/bin:$PATH
export CC=/usr/bin/gcc-13
export CXX=/usr/bin/g++-13
export CUDACXX=/usr/local/cuda/bin/nvcc
export CUDAHOSTCXX=/usr/bin/g++-13
SRC=/f/ninfer-fusion-kvmem/src-tree/fusion-engine-src
LOG=/f/ninfer-fusion-kvmem/build-120a.log
cd "$SRC"
echo "build start $(date -Is)" | tee -a "$LOG"
# docs: CUDA compile -j 8, not core count (ptxas RAM)
cmake --build build-120a --target ninfer-serve -j 8 2>&1 | tee -a "$LOG"
echo "build end $(date -Is) rc=${PIPESTATUS[0]}" | tee -a "$LOG"
ls -lh build-120a/apps/ninfer-serve
build-120a/apps/ninfer-serve --help | head -20

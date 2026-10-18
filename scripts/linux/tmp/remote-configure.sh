#!/bin/bash
set -euo pipefail
export PATH=/usr/local/cuda/bin:/usr/bin:/bin:$PATH
export CC=/usr/bin/gcc-13
export CXX=/usr/bin/g++-13
export CUDACXX=/usr/local/cuda/bin/nvcc
export CUDAHOSTCXX=/usr/bin/g++-13
SRC=/f/ninfer-fusion-kvmem/src-tree/fusion-engine-src
cd "$SRC"
echo "cwd=$(pwd)"
nvcc --version
which cmake ninja gcc-13 g++-13
cmake -S . -B build-120a -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$CC" \
  -DCMAKE_CXX_COMPILER="$CXX" \
  -DCMAKE_CUDA_COMPILER="$CUDACXX" \
  -DCMAKE_CUDA_HOST_COMPILER="$CUDAHOSTCXX" \
  -DCMAKE_CUDA_ARCHITECTURES=120a \
  -DNINFER_BUILD_APPS=ON \
  -DBUILD_TESTING=OFF \
  -DNINFER_BUILD_BENCHMARKS=OFF

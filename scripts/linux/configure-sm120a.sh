#!/usr/bin/env bash
# Configure a clean sm_120a (RTX 50) Release build on Linux.
# Requires: CUDA Toolkit (nvcc), gcc-13/g++-13, cmake>=3.28, ninja, pkg-config,
#           libav*-dev, libcurl4-openssl-dev (see README Linux section).
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/src-tree/fusion-engine-src"
export PATH="/usr/local/cuda/bin:${PATH:-}"
export CC="${CC:-/usr/bin/gcc-13}"
export CXX="${CXX:-/usr/bin/g++-13}"
export CUDACXX="${CUDACXX:-/usr/local/cuda/bin/nvcc}"
export CUDAHOSTCXX="${CUDAHOSTCXX:-$CXX}"
ARCH="${NINFER_CUDA_ARCH:-120a}"
BUILD="$SRC/build-${ARCH}"

cd "$SRC"
cmake -S . -B "$BUILD" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$CC" \
  -DCMAKE_CXX_COMPILER="$CXX" \
  -DCMAKE_CUDA_COMPILER="$CUDACXX" \
  -DCMAKE_CUDA_HOST_COMPILER="$CUDAHOSTCXX" \
  -DCMAKE_CUDA_ARCHITECTURES="$ARCH" \
  -DNINFER_BUILD_APPS=ON \
  -DBUILD_TESTING=OFF \
  -DNINFER_BUILD_BENCHMARKS=OFF
echo "configured $BUILD"

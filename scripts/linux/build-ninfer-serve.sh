#!/usr/bin/env bash
# Build ninfer-serve. Use a fresh build dir per arch (see README).
# CUDA compile: prefer -j 8 (ptxas RAM), not core count.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/src-tree/fusion-engine-src"
export PATH="/usr/local/cuda/bin:${PATH:-}"
ARCH="${NINFER_CUDA_ARCH:-120a}"
BUILD="$SRC/build-${ARCH}"
JOBS="${NINFER_BUILD_JOBS:-8}"

if [[ ! -f "$BUILD/build.ninja" ]]; then
  echo "missing $BUILD — run scripts/linux/configure-sm120a.sh first (or set NINFER_CUDA_ARCH)" >&2
  exit 2
fi
cd "$SRC"
cmake --build "$BUILD" --target ninfer-serve -j "$JOBS"
ls -lh "$BUILD/apps/ninfer-serve"
"$BUILD/apps/ninfer-serve" --help | head -n 20

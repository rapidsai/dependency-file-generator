#!/bin/bash
set -euo pipefail

./ci/update-versions.sh "${RELEASE_VERSION:-}"

mamba install -y rattler-build
rattler-build build \
  --output-dir "${OUTPUT_DIR:-"/tmp/output"}" \
  --recipe-dir recipe/

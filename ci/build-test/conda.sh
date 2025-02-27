#!/bin/bash
set -euo pipefail

./ci/update-versions.sh "${RELEASE_VERSION:-}"

mamba install -y conda-build
conda build \
  --output-folder "${OUTPUT_DIR:-"/tmp/output"}" \
  recipe/

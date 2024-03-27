#!/bin/bash
set -euo pipefail

./ci/update-versions.sh "${RELEASE_VERSION:-}"

mamba install -y boa conda-build
conda mambabuild \
  --output-folder "${OUTPUT_DIR:-"/tmp/output"}" \
  recipe/

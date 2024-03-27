#!/bin/bash
set -euo pipefail

./ci/update-versions.sh "${BUILD_VERSION:-}"

pip install build pytest

python -m build \
  --outdir "${OUTPUT_DIR:-"/tmp/output"}" \
  .

for PKG in dist/*; do
  echo "$PKG"
  pip uninstall -y rapids-dependency-file-generator
  pip install "$PKG"
  pytest
  rapids-dependency-file-generator -h # test CLI output
done

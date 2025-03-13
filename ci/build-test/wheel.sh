#!/bin/bash
set -euo pipefail

OUTPUT_DIR="${OUTPUT_DIR:-"/tmp/output"}"

./ci/update-versions.sh "${RELEASE_VERSION:-}"

pip install build pytest 'packaging>=24.2' 'twine>=6.1.0'

python -m build \
  --outdir "${OUTPUT_DIR}" \
  .

twine check --strict "${OUTPUT_DIR}"/*

for PKG in "${OUTPUT_DIR}/"*; do
  echo "$PKG"
  pip uninstall -y rapids-dependency-file-generator
  pip install "$PKG"
  pytest
  rapids-dependency-file-generator -h # test CLI output
done

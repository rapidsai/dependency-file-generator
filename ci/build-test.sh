#!/bin/bash
# Builds and tests Python package
set -ue

pip install build pytest

python -m build .

for PKG in dist/*; do
  echo "$PKG"
  pip uninstall -y rapids-dependency-file-generator
  pip install "$PKG"
  pytest
  rapids-dependency-file-generator -h # test CLI output
done

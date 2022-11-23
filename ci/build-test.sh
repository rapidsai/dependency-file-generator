#!/bin/bash
# Builds and tests Python package
# Per https://github.com/semantic-release/exec:
#  - stderr is used for logging
#  - stdout is used for printing why verification failed
set -ue

{
  pip install build pytest

  python -m build .

  for PKG in dist/*; do
    echo "$PKG"
    pip uninstall -y rapids-dependency-file-generator
    pip install "$PKG"
    pytest
    rapids-dependency-file-generator -h # test CLI output
  done
} 1>&2

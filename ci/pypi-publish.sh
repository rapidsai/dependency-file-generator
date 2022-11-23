#!/bin/bash
# Uploads packages to PyPI
# Per https://github.com/semantic-release/exec:
#  - stderr is used for logging
#  - stdout is used for returning release information
set -ue

{
  pip install twine

  twine upload \
    --username __token__ \
    --password "${PYPI_TOKEN}" \
    --disable-progress-bar \
    dist/*
} 1>&2

jq -ncr '{name: "PyPI release", url: "https://pypi.org/project/rapids-dependency-file-generator/"}'

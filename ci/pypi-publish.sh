#!/bin/bash
# Uploads packages to PyPI
set -ue

twine upload \
  --username __token__ \
  --password "${PYPI_TOKEN}" \
  --disable-progress-bar \
  dist/*

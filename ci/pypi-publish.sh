#!/bin/bash
# Uploads packages to PyPI
set -ue

pip install twine

twine upload \
  --username __token__ \
  --password "${PYPI_TOKEN}" \
  --disable-progress-bar \
  dist/*

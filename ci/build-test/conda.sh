#!/bin/bash
set -euo pipefail

./ci/update-versions.sh "${BUILD_VERSION:-}"

mamba install -y boa conda-build
conda mambabuild recipe/

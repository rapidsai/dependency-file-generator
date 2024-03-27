#!/bin/bash
# Uploads packages to PyPI
# Per https://github.com/semantic-release/exec:
#  - stderr is used for logging
#  - stdout is used for returning release information
set -euo pipefail

{
  . /usr/share/miniconda/etc/profile.d/conda.sh
  conda activate base
  conda install -y anaconda-client
  pkgs_to_upload=$(find "${CONDA_OUTPUT_DIR}" -name "*.tar.bz2")

  anaconda \
    -t "${ANACONDA_TOKEN}" \
    upload \
    --no-progress \
    ${pkgs_to_upload}
} 1>&2

jq -ncr '{name: "Conda release", url: "https://anaconda.org/rapidsai/rapids-dependency-file-generator"}'

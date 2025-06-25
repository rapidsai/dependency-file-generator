#!/bin/bash
# Uploads packages to PyPI
# Per https://github.com/semantic-release/exec:
#  - stderr is used for logging
#  - stdout is used for returning release information
set -euo pipefail

{
  # shellcheck disable=SC1091
  . /usr/share/miniconda/etc/profile.d/conda.sh
  conda activate base
  conda install -y anaconda-client
  pkgs_to_upload=$(find "${CONDA_OUTPUT_DIR}" -name "*.conda" -o -name "*.tar.bz2")

  export CONDA_ORG="${1}"

  case "${CONDA_ORG}" in
    "rapidsai")
      TOKEN="${ANACONDA_STABLE_TOKEN}"
      ;;
    "rapidsai-nightly")
      TOKEN="${ANACONDA_NIGHTLY_TOKEN}"
      ;;
    *)
      echo "Unknown conda org: ${CONDA_ORG}"
      exit 1
      ;;
  esac

  anaconda \
    -t "${TOKEN}" \
    upload \
    --no-progress \
    "${pkgs_to_upload[@]}"
} 1>&2

jq -ncr '{name: "Conda release - \(env.CONDA_ORG)", url: "https://anaconda.org/\(env.CONDA_ORG)/rapids-dependency-file-generator"}'

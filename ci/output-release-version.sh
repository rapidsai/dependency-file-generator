#!/bin/bash
set -euo pipefail

RELEASE_VERSION="${1}"

echo "release_version=${RELEASE_VERSION}" | tee --append "${GITHUB_OUTPUT:-/dev/null}"

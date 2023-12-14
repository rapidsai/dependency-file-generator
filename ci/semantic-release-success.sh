#!/bin/bash
set -euo pipefail

echo "RELEASE_PUBLISHED=true" | tee --append "${GITHUB_OUTPUT:-/dev/null}"

#!/bin/bash
set -euo pipefail

FLAGS=()
if [[ "${DRY_RUN}" == "true" ]]; then
  FLAGS+=("--dry-run")
fi
npm install
npx semantic-release "${FLAGS[@]}"

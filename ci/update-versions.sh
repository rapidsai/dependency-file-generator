#!/bin/bash
# Updates the version string throughout the project
set -euo pipefail

RELEASE_VERSION="${1:-}"

# no `RELEASE_VERSION` is computed for PRs
if [[ -z "${RELEASE_VERSION}" ]]; then
  echo "No release version provided."
  echo "Skipping version replacement."
  exit 0
fi

if ! [[ "${RELEASE_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid version string: ${RELEASE_VERSION}."
  exit 1
fi

sed -i "/__version__/ s/\".*\"/\"${RELEASE_VERSION}\"/" src/rapids_dependency_file_generator/_version.py
sed -i "/\$id/ s|/v[^/]*/|/v${RELEASE_VERSION}/|" src/rapids_dependency_file_generator/schema.json
sed -i "/\"version\":/ s|: \".*\"|: \"${RELEASE_VERSION}\"|" package.json
sed -i "/version:/ s|: .*|: ${RELEASE_VERSION}|" recipe/meta.yaml


cat \
  src/rapids_dependency_file_generator/_version.py \
  src/rapids_dependency_file_generator/schema.json \
  package.json \
  recipe/meta.yaml

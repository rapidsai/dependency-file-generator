#!/bin/bash
# Updates the version string throughout the project
set -euo pipefail

BUILD_VERSION="${1:-}"

# no `BUILD_VERSION` is computed for PRs
if [[ -z "${BUILD_VERSION}" ]]; then
  echo "No build version provided."
  echo "Skipping version replacement."
  exit 0
fi

if ! [[ "${BUILD_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid version string: ${BUILD_VERSION}."
  exit 1
fi

sed -i "/__version__/ s/\".*\"/\"${BUILD_VERSION}\"/" src/rapids_dependency_file_generator/_version.py
sed -i "/\$id/ s|/v[^/]*/|/v${BUILD_VERSION}/|" src/rapids_dependency_file_generator/schema.json
sed -i "/\"version\":/ s|: \".*\"|: \"${BUILD_VERSION}\"|" package.json
sed -i "/version:/ s|: .*|: ${BUILD_VERSION}|" recipe/meta.yaml


cat \
  src/rapids_dependency_file_generator/_version.py \
  src/rapids_dependency_file_generator/schema.json \
  package.json \
  recipe/meta.yaml

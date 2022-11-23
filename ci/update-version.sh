#!/bin/bash
# Updates the version string in `_version.py`
# Per https://github.com/semantic-release/exec:
#  - stderr is used for logging
#  - stdout is used for printing why verification failed
set -ue

NEXT_VERSION=$1

{
  sed -i "/__version__/ s/\".*\"/\"${NEXT_VERSION}\"/" src/rapids_dependency_file_generator/_version.py

  cat src/rapids_dependency_file_generator/_version.py
} 1>&2

#!/bin/bash
set -euo pipefail

mamba install -y boa conda-build
mamba build recipe

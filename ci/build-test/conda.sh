#!/bin/bash
set -euo pipefail

mamba install -y boa conda-build
conda mambabuild recipe/

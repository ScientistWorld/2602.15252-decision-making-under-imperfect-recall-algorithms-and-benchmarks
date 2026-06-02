#!/bin/bash
# Download all data and models needed for this environment.
#
# Run on a node with internet access BEFORE building the container
# or submitting compute jobs.
#
# This script should be idempotent — safe to run multiple times.
# It should skip files that already exist.
#
# Update the storage estimate below as you add downloads.
#
# Estimated total download size: 0 GB
# Estimated disk usage after extraction: <1 MB
#
# This paper uses generated tree-form benchmark instances only; there are no
# external datasets, model weights, or package downloads in this script.

set -e

cd /home/user

mkdir -p data/instances
python - <<'PY'
from data.tree_games import write_default_suite
write_default_suite("data/instances")
print("Generated bundled synthetic tree-form benchmark instances.")
PY

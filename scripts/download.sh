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
# This paper uses first-party synthetic tree-form benchmark instances tracked in
# data/instances. There are no external datasets, model weights, or package
# downloads in this script.

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p data/downloads
echo "No external artifacts to download; tracked synthetic instances are in data/instances."

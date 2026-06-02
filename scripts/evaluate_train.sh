#!/bin/bash
# Train-slice evaluation entry point.
#
# Mirrors scripts/evaluate.sh's artifact contract: read a pre-generated
# optimization result JSON and write a scoring JSON with the same experiment
# and metric names as scoring/reference.json. This script only rescores
# existing method outputs; it does not run method code.

set -e

cd /home/user

mkdir -p scoring

INPUT="${1:-results/optimization_results.json}"
OUTPUT="${2:-scoring/scores_train.json}"
TARGET_GAP="${TARGET_GAP:-1e-6}"

python eval/train/evaluate.py \
  --input "$INPUT" \
  --output "$OUTPUT" \
  --target-gap "$TARGET_GAP"

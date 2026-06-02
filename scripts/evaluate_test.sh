#!/bin/bash
# Held-out test-slice evaluation entry point.
#
# Mirrors scripts/evaluate.sh's artifact contract and writes the held-out
# scores to scoring/scores_test.json. When scoring/scores_train.json exists,
# the same method entries scored on train are scored on test.

set -e

cd /home/user

mkdir -p scoring

INPUT="${1:-results/optimization_results.json}"
OUTPUT="${2:-scoring/scores_test.json}"
TARGET_GAP="${TARGET_GAP:-1e-6}"
TRAIN_SCORES="${TRAIN_SCORES:-scoring/scores_train.json}"

python eval/test/evaluate.py \
  --input "$INPUT" \
  --output "$OUTPUT" \
  --target-gap "$TARGET_GAP" \
  --train-scores "$TRAIN_SCORES"

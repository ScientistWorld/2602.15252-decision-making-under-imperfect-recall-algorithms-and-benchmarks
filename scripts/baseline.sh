#!/bin/bash
# Run a baseline method from the paper.
#
# Baselines are simple reference methods the paper compares against. 
# Implement this only if applicable, i.e. the paper has baselines.
# You do not need to implement all baselines to begin — 
# just enough to validate that the evaluation pipeline works 
# and provide a reference point. You can decide to expand more baselines later.
# Each baseline must be actually run and scored through evaluate.sh
# so the numbers are verified, not self-reported.
# You can decide what this baseline script should do yourself.
#
# Usage:
#   bash scripts/baseline.sh <name>

set -e

cd /home/user

python baseline/run_baseline.py \
  --generate-instances \
  --instances data/instances \
  --output results/baseline_gd_results.json \
  --algorithms gd,ogd \
  --iterations "${ITERATIONS:-3000}" \
  --runs "${RUNS:-5}" \
  --eta "${ETA:-0.1}" \
  --target-gap "${TARGET_GAP:-1e-6}"

bash scripts/evaluate.sh results/baseline_gd_results.json scoring/baseline_scores.json

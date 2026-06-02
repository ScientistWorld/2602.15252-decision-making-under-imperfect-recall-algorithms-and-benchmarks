#!/bin/bash
# Run the paper's proposed method.
#
# This script trains/runs the paper's method using code in method/.
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user

python method/solve.py \
  --generate-instances \
  --instances data/instances \
  --output results/optimization_results.json \
  --algorithms gd,ogd,ams,rm,rm_plus,prm,prm_plus \
  --iterations "${ITERATIONS:-3000}" \
  --runs "${RUNS:-5}" \
  --eta "${ETA:-0.1}" \
  --target-gap "${TARGET_GAP:-1e-6}"

bash scripts/evaluate.sh results/optimization_results.json

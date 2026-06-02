#!/bin/bash
set -euo pipefail

cd /home/user

export TARGET_GAP="${TARGET_GAP:-1e-6}"

bash scripts/evaluate_train.sh results/optimization_results.json scoring/scores_train.json
bash scripts/evaluate_test.sh results/optimization_results.json scoring/scores_test.json

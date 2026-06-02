#!/bin/bash
set -euo pipefail

cd /home/user

export TARGET_GAP="${TARGET_GAP:-1e-6}"

bash scripts/evaluate.sh results/optimization_results.json scoring/scores.json
python validate.py --compare

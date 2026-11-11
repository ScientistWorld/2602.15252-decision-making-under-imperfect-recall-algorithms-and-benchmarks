#!/bin/bash
# Run the paper's gradient-based comparators (GD, OGD, AMSGrad in
# baseline/solver.py) on the training problems through the evaluator.
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p results
python eval/train/evaluate.py --only gd,ogd,ams --output results/baseline_scores_train.json

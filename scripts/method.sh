#!/bin/bash
# Run the paper's method (RM, RM+, PRM, PRM+ solvers in method/solver.py) on the
# training problems through the evaluator; scores go to results/method_scores_train.json.
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p results
python eval/train/evaluate.py --only rm,rm_plus,prm,prm_plus --output results/method_scores_train.json

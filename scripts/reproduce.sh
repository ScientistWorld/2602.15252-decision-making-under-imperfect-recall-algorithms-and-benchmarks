#!/bin/bash
# Reproduce the reference end to end: all solvers on the training problems
# (scores.json, scores_train.json) and on the held-out problems (scores_test.json).
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
bash scripts/evaluate_train.sh
cp scoring/scores_train.json scoring/scores.json
bash scripts/evaluate_test.sh
python validate.py --compare

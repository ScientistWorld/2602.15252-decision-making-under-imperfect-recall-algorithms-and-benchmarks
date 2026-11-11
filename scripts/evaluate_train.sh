#!/bin/bash
# Training-slice evaluation (the paper's public problems). Same interface and
# metrics as the held-out evaluation; writes scoring/scores_train.json.
# Extra arguments are passed through (e.g. --only rm_plus).
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
python eval/train/evaluate.py "$@"

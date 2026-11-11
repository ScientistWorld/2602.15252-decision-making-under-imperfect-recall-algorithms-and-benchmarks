#!/bin/bash
# Standard evaluation: score every solver in scripts/solvers.json on the
# training problems and write scoring/scores.json (same metrics as
# scores_train.json / scores_test.json). Uses only eval/ and data/.
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p scoring
python eval/train/evaluate.py --output scoring/scores.json "$@"

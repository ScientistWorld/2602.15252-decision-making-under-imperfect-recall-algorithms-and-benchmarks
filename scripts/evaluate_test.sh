#!/bin/bash
# Held-out evaluation. Runs with no arguments: starts every solver listed in
# scripts/solvers.json on the hidden problems through the evaluator's oracle,
# and writes every method's metrics to scoring/scores_test.json.
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
python eval/test/evaluate.py

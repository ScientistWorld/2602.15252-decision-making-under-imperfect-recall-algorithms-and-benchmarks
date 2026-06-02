#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export TARGET_GAP="${TARGET_GAP:-1e-6}"

bash scripts/evaluate.sh results/optimization_results.json scoring/scores.json
python validate.py --compare

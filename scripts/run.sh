#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export TARGET_GAP="${TARGET_GAP:-1e-6}"
export ITERATIONS="${ITERATIONS:-6000}"
export RUNS="${RUNS:-12}"
export ETA="${ETA:-0.1}"

bash scripts/method.sh
python validate.py --compare

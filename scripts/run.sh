#!/bin/bash
# Example job script submitted via the end-of-turn YAML block.
#
# This runs inside the compute container with:
#   - Your workspace mounted at /home/user
#   - GPU(s) available
#   - No internet access
#
# Make sure all data, code, and dependencies are already in the
# workspace or baked into the container before submitting.

set -e

cd /home/user

export ITERATIONS="${ITERATIONS:-6000}"
export RUNS="${RUNS:-12}"
export TARGET_GAP="${TARGET_GAP:-1e-6}"

bash scripts/reproduce.sh
python validate.py --compare

#!/bin/bash
set -euo pipefail
cd /home/user
for case in gd_reference_seed_123 gd_reference_seed_234 gd_reference_seed_345 stronger_gd_eta1_seed_234 stronger_gd_eta1_seed_345 weaker_gd_one_step cached_answers_shortcut; do
  bash "redteam/$case/run.sh"
done
python redteam/summarize.py

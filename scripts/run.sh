#!/bin/bash
# Job entry point (runs in the container, workspace at /home/user, no internet).
#
# Reproduces the reference end to end:
#   1. oracle correctness checks (vs a pure-Python evaluator and the paper's logs)
#   2. every registered solver on the training problems -> scoring/scores_train.json
#      (+ run-by-run comparison with the authors' logged runs)
#   3. the held-out comparator field (only if eval/test/field.json is missing)
#   4. every registered solver on the held-out problems -> scoring/scores_test.json
#   5. hardening cases (variants, shortcuts, seed noise) -> redteam/hardening/scores/
#   6. python validate.py --compare
# Stages resume from their outputs if the job is restarted.  MODE=smoke runs a
# short version on three held-out problems (outputs under tmp/).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
MODE="${MODE:-$(cat tmp/run_mode 2>/dev/null || echo full)}"
mkdir -p results eval/test/_runs tmp
# a killed held-out evaluation can leave the hidden-problem files unreadable
chmod 755 eval/test/instances 2>/dev/null || true
chmod 644 eval/test/generate_instances.py 2>/dev/null || true
python -c "import sys, numpy; print('python', sys.version.split()[0], 'numpy', numpy.__version__)"
echo "cpus: $(nproc)  mode: $MODE  start: $(date)"

stage() { echo; echo "=== $1  ($(date +%H:%M:%S))"; }

stage "1. oracle checks"
[ -f redteam/hardening/checks.json ] || python redteam/hardening/checks.py

if [ "$MODE" = smoke ]; then
  stage "2s. train evaluation (subset)"
  python eval/train/evaluate.py --only rm_plus,prm_plus,gd,ams --output tmp/smoke_scores_train.json \
    --cache tmp/smoke_train_cache.json --details tmp/smoke_train_details.json > /dev/null
  python redteam/hardening/compare_paper_runs.py tmp/smoke_train_details.json
  stage "3s. comparator field on three held-out problems"
  python eval/test/build_field.py --instances detection_b1,random_a2,simulation_b3 \
    --output tmp/field_smoke.json --partial tmp/field_smoke_partial.json
  stage "4s. held-out evaluation on the smoke field"
  python eval/test/evaluate.py --field tmp/field_smoke.json --output tmp/smoke_scores_test.json \
    --details eval/test/_runs/smoke_details.json
  stage "5s. a few hardening cases on the smoke field"
  HARDENING_TAG=smoke HARDENING_FIELD=tmp/field_smoke.json python redteam/hardening/run_cases.py \
    shortcut_forge_files shortcut_crash shortcut_invalid_strategy shortcut_no_query \
    shortcut_unregistered_rm_plus better_gd_adaptive better_rm_plus_restarts shortcut_brute_force_vertices \
    shortcut_cached_train_answers
  cat tmp/smoke_scores_test.json
  echo "smoke done: $(date)"
  exit 0
fi

stage "2. training-slice evaluation"
if [ ! -f results/train_details.json ]; then
  python eval/train/evaluate.py --cache results/train_cache.json --details results/train_details.json > /dev/null
fi
cp scoring/scores_train.json scoring/scores.json
python redteam/hardening/compare_paper_runs.py results/train_details.json

stage "3. held-out comparator field"
[ -f eval/test/field.json ] || python eval/test/build_field.py

stage "4. held-out evaluation (reference)"
if [ ! -f eval/test/_runs/reference_details.json ]; then
  python eval/test/evaluate.py --cache tmp/reference_test_cache.json \
    --details eval/test/_runs/reference_details.json > /dev/null
fi
cat scoring/scores_test.json

stage "5. hardening cases"
if [ -f redteam/hardening/run_cases.py ]; then
  python redteam/hardening/run_cases.py
fi

stage "6. validate"
python validate.py --compare || echo "validate.py reported problems"
echo "done: $(date)"

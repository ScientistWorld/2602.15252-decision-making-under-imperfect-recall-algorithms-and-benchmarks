#!/bin/bash
# Job entry point (runs in the container, workspace at /home/user, no internet).
#
# Reproduces the reference end to end:
#   1. oracle correctness checks (vs a pure-Python evaluator and the paper's logs)
#   2. every registered solver on the training problems -> scoring/scores_train.json
#      (+ run-by-run comparison with the authors' logged runs)
#   3. the held-out problems (written only if missing; stored ones must regenerate
#      byte for byte) and their frozen comparator field (only missing problems run)
#   4. every registered solver on the held-out problems -> scoring/scores_test.json
#   5. (RUN_HARDENING=1) variant / shortcut / seed-noise cases -> redteam/hardening/
#   6. python validate.py --compare
# Stages resume from their outputs if the job is restarted.  Solver x problem
# tasks run in parallel on the available CPUs (IRTREE_EVAL_WORKERS overrides).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
RUN_HARDENING="${RUN_HARDENING:-$(cat tmp/run_hardening 2>/dev/null || echo 0)}"
mkdir -p results eval/test/_runs tmp
# a killed held-out evaluation can leave the hidden-problem files unreadable
chmod 755 eval/test/instances 2>/dev/null || true
chmod 644 eval/test/generate_instances.py eval/test/field.json eval/test/build_field.py 2>/dev/null || true
chmod 644 eval/test/field_partial.json 2>/dev/null || true
python -c "import sys, numpy; print('python', sys.version.split()[0], 'numpy', numpy.__version__)"
echo "nproc: $(nproc)  cpu.max: $(cat /sys/fs/cgroup/cpu.max 2>/dev/null || echo n/a)  memory.max: $(cat /sys/fs/cgroup/memory.max 2>/dev/null || echo n/a)"
export IRTREE_EVAL_WORKERS="${IRTREE_EVAL_WORKERS:-$(python -c "import sys; sys.path.insert(0, 'eval/test'); import harness; print(harness.default_workers())")}"
echo "evaluator workers (measured parallelism): $IRTREE_EVAL_WORKERS"
echo "start: $(date)"

stage() { echo; echo "=== $1  ($(date +%H:%M:%S))"; }

stage "1. oracle checks"
[ -f redteam/hardening/checks.json ] || python redteam/hardening/checks.py

stage "2. training-slice evaluation"
# diagnostic: every registered solver from the paper's own starts (seeds 33-44) retraces the authors' logs
if [ ! -f results/train_details.json ]; then
  python eval/train/evaluate.py --start-seeds 33,34,35,36,37,38,39,40,41,42,43,44 \
    --output results/scores_train_paperstarts.json --cache results/train_cache.json \
    --details results/train_details.json > /dev/null
fi
python redteam/hardening/compare_paper_runs.py results/train_details.json
# scored: every registered solver from the evaluator's own starts -> scoring/scores_train.json
if [ ! -f tmp/train_rows_done ]; then
  python eval/train/evaluate.py --cache results/train_cache_rows.json --details results/train_details_rows.json > /dev/null
  touch tmp/train_rows_done
fi
cp scoring/scores_train.json scoring/scores.json

stage "3. held-out problems and comparator field"
python eval/test/generate_instances.py | awk '{print $2}' | sort | uniq -c
python eval/test/build_field.py

stage "4. held-out evaluation (reference, fresh run of every registered solver)"
if [ ! -f eval/test/_runs/reference_details.json ] || [ ! -f tmp/reference_done ]; then
  python eval/test/evaluate.py --cache tmp/reference_test_cache.json \
    --details eval/test/_runs/reference_details.json > /dev/null
  touch tmp/reference_done
fi
cat scoring/scores_test.json
# determinism: the fresh rm_plus row vs an earlier rm_plus run from the same starts
python redteam/hardening/compare_reference_runs.py tmp/rm_plus_seeds1001_details.json \
  eval/test/_runs/reference_details.json redteam/hardening/reference_rerun_agreement.json || true

if [ "$RUN_HARDENING" = 1 ]; then
  stage "5. hardening cases"
  python redteam/hardening/run_cases.py
  python redteam/hardening/summarize.py > /dev/null
fi

stage "6. validate"
python validate.py --compare || echo "validate.py reported problems"
echo "done: $(date)"

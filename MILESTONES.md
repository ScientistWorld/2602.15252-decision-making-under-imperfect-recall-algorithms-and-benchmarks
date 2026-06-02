# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-06-02 05:43] - core_claim
- Audited the continued workspace for paper-method integrity. The solver implements the paper's actual tabular imperfect-recall optimization pipeline: behavioral strategies on information sets, tree-pass expected utility and gradient computation, first-order KKT-gap checks, and local GD/OGD/RM/RM+/PRM/PRM+ simplex updates.
- Verified that `eval/` is method-agnostic: it reads saved optimizer artifacts from `results/optimization_results.json`, aggregates utility and convergence metrics, and writes `scoring/scores.json` without importing from `method/`.
- Confirmed reproduced scores come from a completed expanded compact-suite run with 8 generated imperfect-recall instances, 12 random starts, 6000 iterations, and a `1e-6` convergence threshold. The regret-matching family reaches the KKT-gap target on every instance and compares favorably against GD/OGD on convergence metrics.
- Ran `python validate.py --compare`; all scoring, import-separation, output-contract, and shared-path checks passed.
- Completed final handoff documentation in `PROGRESS.md` and `scoring/`, including explicit primary, constraint, and ablation targets.

### [2026-06-02 06:06] - core_claim
- Re-ran `python validate.py --compare`; all checks passed and the checked-in scores still support the core claim on the compact suite.
- Checked the paper appendix's Google Drive artifact for the original benchmark instances. The URL redirected to Google Drive download infrastructure but returned HTTP 404, so the compact generated suite remains the available reproducible benchmark.
- Made the GD/OGD baseline runner self-contained under `baseline/` instead of importing the proposed-method solver.

### [2026-06-02 06:14] - core_claim
- Audited the scheduler entrypoint and found that `scripts/run.sh` only evaluated an existing artifact.
- Updated `scripts/run.sh` to regenerate the compact-suite optimizer artifact via `scripts/method.sh` before running `python validate.py --compare`.

### [2026-06-02 06:20] - core_claim
- Performed final gym verification across folder structure, method-agnostic documentation, scoring coefficients, evaluator independence, train/test artifacts, and validation checks.
- Updated evaluators so future artifact method keys are scored automatically, while retaining the documented exclusion of the unclaimed compact AMS comparator.
- Re-ran `python validate.py --compare`; all checks passed.

## Stop Justification
- Completed at milestone `core_claim`.

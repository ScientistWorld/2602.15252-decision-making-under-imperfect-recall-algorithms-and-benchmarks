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

### [2026-11-12] - core_claim (hardening, final iteration)
- Replaced the artifact-based evaluator (which trusted self-reported values, gaps, iterations and comparator rows) with an evaluator that runs every solver through a counted first-order oracle on hidden problems and computes every scored number itself.
- Recovered the paper's benchmark artifact (Drive ID had been mangled): training = the paper's 20 public instances with the authors' logged runs as comparators; test = 48 hidden draws from a port of the paper's generators.
- Ported the authors' RM/RM+/PRM/PRM+/GD/OGD/AMSGrad code; it retraces the authors' logged runs (1678/1680 identical iteration counts).
- The paper's claim reproduces in its direction on the held-out problems (RM+ vs GD: convergence rank 3.15 vs 5.69, log10 iterations 1.22 vs 1.91, 75% vs 54% best utility). All red-team shortcuts score at most the reference; a better variant beats the reference beyond seed noise. See HARDENING.md.

### [2026-11-14] - core_claim (hardening follow-up to REVIEW.md)
- Enlarged the held-out test from 48 to 176 problems (paper's generators and presets, weighted toward the largest preset of each family); froze comparators for the new problems; generator made interpreter-independent (byte-identical regeneration under Python 3.11 and 3.12).
- Found and closed a pairing shortcut: solvers were given the comparators' own starting points, so ignoring the given start raised RM+'s score by about as much as an honest improvement. Solvers now start elsewhere (test 1001-1012, train 45-56). Hid the comparator field (per-problem best utilities) during solver runs.
- Fresh reference run of all 7 solvers on train and test. Seed-noise range 0.105 (Δ ALL) vs paired gains of a better solver of +0.16 to +0.30 on four start sets (pooled bootstrap CI [0.06, 0.44]); GD sits 4.3 below RM+. All shortcuts score at or below the reference (own start +0.06, within noise).

## Stop Justification
- Completed at milestone `core_claim`.

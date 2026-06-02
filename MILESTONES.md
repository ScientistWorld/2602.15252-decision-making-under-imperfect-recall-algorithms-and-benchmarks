# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-06-02 05:43] - core_claim
- Audited the continued workspace for paper-method integrity. The solver implements the paper's actual tabular imperfect-recall optimization pipeline: behavioral strategies on information sets, tree-pass expected utility and gradient computation, first-order KKT-gap checks, and local GD/OGD/RM/RM+/PRM/PRM+ simplex updates.
- Verified that `eval/` is method-agnostic: it reads saved optimizer artifacts from `results/optimization_results.json`, aggregates utility and convergence metrics, and writes `scoring/scores.json` without importing from `method/`.
- Confirmed reproduced scores come from a completed expanded compact-suite run with 8 generated imperfect-recall instances, 12 random starts, 6000 iterations, and a `1e-6` convergence threshold. The regret-matching family reaches the KKT-gap target on every instance and compares favorably against GD/OGD on convergence metrics.
- Ran `python validate.py --compare`; all scoring, import-separation, output-contract, and shared-path checks passed.
- Completed final handoff documentation in `PROGRESS.md` and `scoring/`, including explicit primary, constraint, and ablation targets.

## Stop Justification

Final status is `core_claim`. The environment is usable: the paper's core algorithm family runs end-to-end, produces scored artifacts, and supports the central claim that regret-matching-style first-order methods are strong scalable optimizers for imperfect-recall decision problems compared with projected-gradient baselines.

The milestone is kept at `core_claim` rather than a higher final claim because the original 61 benchmark instances from the paper were not available as bundled data in the workspace. This reproduction uses a fixed compact generated suite covering absentminded-driver, simulation-style, subgroup-detection-style, and random imperfect-recall problems. The expanded compact run supports the main effect, but it does not reproduce a majority of the paper's full reported benchmark table.

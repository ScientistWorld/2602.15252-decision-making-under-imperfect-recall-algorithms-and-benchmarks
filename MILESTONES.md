# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-06-02 04:04] - none
- Read the paper summary and identified the core algorithmic target: local optimization of tree-form imperfect-recall decision problems over products of simplices.
- Implemented the method code for projected gradient, optimistic gradient, regret matching, predictive regret matching, plus variants, and AMS-style adaptive updates.
- Added generated imperfect-recall benchmark instances, a method runner, an evaluator, and paper Table 1 aggregate reference metrics.
- Prepared a scheduler smoke job to verify the implementation end-to-end inside the reproducible container.

### [2026-06-02 04:09] - core_claim
- The scheduled CPU job completed successfully and wrote `results/optimization_results.json` plus `scoring/scores.json`.
- Validation passed with `python validate.py --compare`.
- On the compact five-instance suite, RM-family methods reached the KKT threshold on 80-100% of instances, while GD/OGD reached it on 60%, supporting the paper's central first-order convergence claim at reduced scale.
- Expanded the generated suite with subgroup-detection-style instances and a larger random instance for the next run.

## Stop Justification
- Not stopped.

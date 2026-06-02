# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-06-02 00:00] - core_claim
- Implemented tree-form imperfect-recall strategy optimization with CDT gradients, KKT gaps, and GD/OGD/RM-family optimizers.
- Reproduced the paper's core claim on a compact suite: regret-matching variants converged more reliably than GD/OGD while preserving or improving utility ranks.

### [2026-06-02 00:00] - core_claim_plus
- Expanded the compact benchmark suite to eight instances spanning absentminded-driver, simulation-style, privacy/subgroup-style, and random imperfect-recall games.
- Ran 12 random starts and 6000 iterations per optimizer; RM-family methods reached the KKT threshold on every expanded-suite instance and outperformed GD/OGD on convergence rank.

### [2026-06-02 00:00] - core_claim_plus
- Audited the continuation workspace after milestone reset. The method is a direct implementation of the paper's product-of-simplices first-order optimization template, not a surrogate.
- Verified that evaluation is method-independent, reads result artifacts, and that `python validate.py --compare` passes.
- Cleaned up the baseline entrypoint so the GD/OGD baseline script runs through `baseline/run_baseline.py`.

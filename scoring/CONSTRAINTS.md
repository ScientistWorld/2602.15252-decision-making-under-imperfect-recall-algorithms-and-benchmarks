# Scientist Constraints

## Problem Formulation

Submissions must solve the same tabular tree-form imperfect-recall decision problems. They may not convert the task into a different solution concept, remove imperfect recall, split merged information sets, or evaluate a strategy with additional information unavailable in the original instance.

## Data

Use the fixed benchmark instances supplied by this reproduction for headline scores. Additional generated instances may be used for development or robustness analysis, but they must not replace the fixed suite in `scores.json`.

## Evaluation

Use the shared utility and KKT-gap measurements. Keep the convergence threshold at `1e-6` and apply the same iteration budget to every compared method. Wall-clock speed is not a scored metric because hardware varies across runs.

## Resources

Compare methods under the same initialization policy, number of random starts, and iteration budget. Improvements should come from the optimization method, not from giving one method more starts or easier instances.

## Exact Solvers

Exact global solvers may be reported as references on small instances, but a submission cannot claim the main scalable benchmark result by using only an exact global optimizer that fails or times out on the large suite.

## Compliance Checklist

- [ ] Strategy evaluation uses the original imperfect-recall information sets.
- [ ] Headline scores use the fixed benchmark suite.
- [ ] Utility and KKT gap are computed by the shared evaluation pipeline.
- [ ] Convergence threshold is `1e-6`.
- [ ] Every method is rerun under the same documented iteration budget.
- [ ] Number of random starts is equal across compared methods.
- [ ] Exact-solver results are not used as the sole scalable-method claim.

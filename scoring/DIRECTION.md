# Research Direction

## Research Problem

The gym studies scalable strategy optimization for tabular sequential decision problems with imperfect recall. A valid method must output a behavioral strategy over the original information sets and should improve both expected utility and first-order convergence behavior.

## Approach Family

Future work should remain within the paper's optimization problem: local or structured optimization over products of action simplices for imperfect-recall tree-form decision problems. Acceptable directions include improved first-order updates, regret-matching variants, predictive or adaptive local updates, better initialization, hybrid local-search schedules, and faster tree-based gradient or KKT-gap computation.

## What Must Stay Comparable

The method should still optimize strategies for the original tabular instances and be judged by the shared utility and KKT-gap metrics. It may change the optimizer, but not the decision problem, information structure, solution concept, or evaluation objective.

## Out of Scope

- Replacing imperfect-recall strategy optimization with a different task or formalism.
- Giving the agent extra memory or observations beyond the original information sets.
- Solving only tiny instances with an exact global solver and presenting that as the scalable benchmark result.
- Training a generic model to imitate known outputs instead of optimizing the strategy objective.
- Reporting scores on a different instance suite as the headline result.

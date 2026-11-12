# Research Direction

## Research Problem
Scalable first-order optimization for tabular imperfect-recall decision problems: reach KKT (CDT-equilibrium) points quickly and reliably, and end on strategies with high expected utility.

## Approach Family
Optimizers over products of probability simplices that use utility/gradient queries: improved local update rules, adaptive or parameter-free step sizes, predictive/optimistic updates, momentum, line searches, restart schemes within the budget, better initialisation, hybrid schedules.

## What Must Stay Comparable
Same problems, starting points, oracle, 6000-evaluation budget and 1e-6 threshold for every solver; the solution concept (first-order optimality) and the utility objective.

## Out of Scope
- Changing the decision problem, its information structure, or the solution concept.
- Using information other than oracle answers for the current run (problem files, cached answers, other runs).
- Exhaustive enumeration of pure strategies (it exceeds the budget on almost every problem and is not a scalable method).

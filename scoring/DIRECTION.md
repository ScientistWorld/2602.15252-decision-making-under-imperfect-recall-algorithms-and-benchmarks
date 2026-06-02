# Research Direction

## Research Problem

This benchmark asks how to solve tabular sequential decision problems with imperfect recall at scale. The relevant output is a behavioral strategy over the original information sets that attains high expected utility while satisfying a first-order local-optimality criterion.

## Core Contribution

The paper's contribution is a scalable first-order optimization approach for products of simplices arising from imperfect-recall decision problems, together with benchmark families that expose scalability and convergence behavior. Future work should improve this optimization direction, not sidestep it by changing the problem or solution concept.

## Approach Scope

Scientists may design alternative first-order or local-search optimizers, change local simplex update rules, use adaptive or hybrid update schedules, improve initialization, exploit tree structure for faster gradient computation, or add convergence diagnostics. The submitted method must still optimize behavioral strategies on the original tabular instances and be judged by utility, KKT gap, and iteration-efficient convergence.

## Out of Bounds

- Replacing the benchmark with a different formalism, dataset, or problem family for headline scores.
- Expanding information available to the strategy beyond the original imperfect-recall information sets.
- Reporting only globally optimized tiny instances while ignoring the scalable benchmark suite.
- Changing the target from first-order strategy computation to a different objective that is not comparable under the shared metrics.
- Using domain-specific shortcuts that solve only one benchmark family while presenting the result as a general imperfect-recall solver.

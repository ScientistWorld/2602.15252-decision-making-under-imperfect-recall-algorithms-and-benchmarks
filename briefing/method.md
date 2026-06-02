# Paper's Method

## Key Contribution

The paper contributes both a benchmark suite for tabular imperfect-recall decision problems and a family of regret-matching-based first-order optimizers for the resulting nonlinear constrained optimization problems.

## Approach

Each benchmark instance is represented as a tree-form decision problem with chance nodes, player information sets, terminal utilities, and behavioral strategies over action simplices. The objective is the expected root utility, which becomes a polynomial over a product of simplices when information sets can be revisited or merge forgotten histories.

The optimization target is a CDT equilibrium, equivalently a KKT point. The paper uses a common template that decomposes the product-of-simplices update into local simplex optimizers at each information set. Gradients are computed by tree passes that combine reach probabilities with continuation utilities, giving all local action derivatives in time linear in the tree size.

Baselines include a commercial exact nonlinear optimizer on small instances and projected-gradient-style first-order methods, including optimistic and adaptive variants. The proposed family replaces the local simplex optimizer with regret matching, plus regret-truncating and predictive variants. Strategies are updated from accumulated instantaneous regrets derived from the local utility gradients.

## Main Claims

- **Primary claim:** regret-matching-style first-order methods are effective scalable optimizers for imperfect-recall decision problems, reaching small first-order gaps faster than common projected-gradient baselines on the benchmark suite.
- **Primary claim:** these methods generally attain utility values at least competitive with, and often better than, the gradient-based baselines.
- **Secondary claim:** exact global nonlinear optimization is useful for tiny instances but is not a practical solver for the larger tabular benchmark instances.
- **Secondary claim:** predictive regret-matching variants do not consistently improve over the non-predictive variants in this single-agent nonlinear optimization setting.

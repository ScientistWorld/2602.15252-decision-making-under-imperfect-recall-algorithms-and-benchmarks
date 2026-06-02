# Evaluation

## Metrics

- **Expected utility**: value of the returned strategy at the root of the decision tree; higher is better.
- **KKT gap**: first-order stationarity gap for the product-of-simplices strategy space; lower is better. A run is considered converged at gap at most `1e-6`.
- **Iterations to convergence**: iteration count until convergence or the iteration limit; lower is better when the final gap criterion is met. This reproduction does not score wall-clock time because hardware varies across runs.
- **Best-value frequency and rank**: across benchmark instances, count how often a solver attains the best observed utility and report average utility rank; higher frequency and lower rank are better.
- **Convergence frequency and rank**: across benchmark instances, count how often a solver reaches the target gap and report average iteration-to-convergence rank; higher frequency and lower rank are better.

## Baselines and Targets

Reference comparisons should include an exact nonlinear optimizer on small instances when available, plus standard scalable first-order optimizers on all instances. The paper reports aggregate results over 61 instances: the strongest reported methods reach the best observed utility on roughly 70-74% of instances, converge on roughly 80-90% of instances, and have the best average convergence ranks among first-order methods. Exact optimization is useful as a small-instance value check but does not scale to the larger benchmark cases.

## Evaluation Protocol

Evaluate on the fixed suite of simulation, subgroup detection, and random decision problems. Run scalable methods from multiple random initial strategies and report the median result. The paper stops each run when it reaches KKT gap `1e-6`, a 4-hour time limit, or 6000 iterations. This compact reproduction preserves the KKT criterion and equal iteration budgets, and compares methods using the same problem instances, initialization policy, stopping criteria, and utility/gap computation.

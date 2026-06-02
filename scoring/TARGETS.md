# Evaluation Targets

## first_order_optimizer_aggregate

This is the headline target for the compact reproduction. It evaluates solvers on a fixed suite of imperfect-recall tree-form decision problems and aggregates each algorithm's final utility and first-order convergence behavior.

- **Metric**: `value_percent_best` (higher is better)
- **Metric**: `value_avg_rank` (lower is better)
- **Metric**: `convergence_percent_reached` (higher is better)
- **Metric**: `convergence_percent_best` (higher is better)
- **Metric**: `convergence_avg_rank` (lower is better)

The benefit side of the claim is represented by final expected utility (`value_percent_best`, `value_avg_rank`). The constraint side is represented by first-order stationarity under the shared KKT-gap threshold (`convergence_percent_reached`, `convergence_percent_best`, `convergence_avg_rank`).

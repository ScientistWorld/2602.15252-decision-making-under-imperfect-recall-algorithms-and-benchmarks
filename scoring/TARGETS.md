# Evaluation Targets

Run evaluation with:

```bash
bash scripts/evaluate.sh results/optimization_results.json scoring/scores.json
python validate.py --compare
```

## first_order_optimizer_aggregate

This scored experiment evaluates submitted solvers on the fixed compact imperfect-recall suite in `data/instances/`. It corresponds to the aggregate comparison structure of the paper's Table 1, with wall-clock time intentionally excluded.

### Primary Target

- **What it tests:** Whether a method finds high expected utility on the same tabular imperfect-recall decision problems.
- **Primary metrics:** `value_percent_best` higher is better; `value_avg_rank` lower is better.
- **Scored entries:** all method entries present in `scoring/scores.json` for this experiment.

### Constraint Target

- **What it tests:** Whether high utility is achieved while satisfying the paper's first-order local-optimality criterion.
- **Constraint metrics:** `convergence_percent_reached` higher is better; `convergence_percent_best` higher is better; `convergence_avg_rank` lower is better.
- **Fixed threshold:** KKT gap at or below `1e-6`.

### Comparator Target

- **What it tests:** Whether a submitted solver improves on the checked-in comparator set under the same resource and stopping rules.
- **Comparison:** Compare each method entry within the same `first_order_optimizer_aggregate` experiment using the shared utility and convergence metrics.
- **Expected effect:** A meaningful improvement should increase utility quality while maintaining or improving first-order convergence behavior on the compact suite.

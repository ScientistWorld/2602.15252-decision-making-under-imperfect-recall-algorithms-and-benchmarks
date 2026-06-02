# Evaluation Targets

Run evaluation with:

```bash
bash scripts/evaluate.sh results/optimization_results.json scoring/scores.json
python validate.py --compare
```

## first_order_optimizer_aggregate

This scored experiment evaluates optimizers on the fixed compact imperfect-recall suite in `data/instances/`. It corresponds to the aggregate comparison structure of the paper's Table 1, with wall-clock time intentionally excluded.

### Primary Target

- **What it tests:** Whether a method finds high expected utility on the same tabular imperfect-recall decision problems.
- **Primary metrics:** `value_percent_best` higher is better; `value_avg_rank` lower is better.
- **Scored entries:** `gd`, `ogd`, `rm`, `rm_plus`, `prm`, and `prm_plus` in `scoring/scores.json`.

### Constraint Target

- **What it tests:** Whether high utility is achieved while satisfying the paper's first-order local-optimality criterion.
- **Constraint metrics:** `convergence_percent_reached` higher is better; `convergence_percent_best` higher is better; `convergence_avg_rank` lower is better.
- **Fixed threshold:** KKT gap at or below `1e-6`.

### Ablation Target

- **What it tests:** What breaks when the regret-matching local optimizer is replaced by projected-gradient-style local updates.
- **Comparison:** Treat `gd` and `ogd` as ablated non-regret-matching variants and compare them against `rm`, `rm_plus`, `prm`, and `prm_plus` within the same `first_order_optimizer_aggregate` experiment.
- **Expected effect:** The ablated variants should have worse convergence reach/rank on the compact suite, even when final utility is sometimes competitive.

# Evaluation Targets

```bash
bash scripts/evaluate_train.sh   # scoring/scores_train.json (training problems)
bash scripts/evaluate_test.sh    # scoring/scores_test.json  (held-out problems, no arguments)
python validate.py --compare
```

## first_order_optimizer_aggregate

One row per solver listed in `scripts/solvers.json`; the reference rows `gd`, `ogd`, `ams`, `rm`, `rm_plus`, `prm`, `prm_plus` are always present (worst values if missing or failing).

### Primary (utility) targets
- `value_percent_best` (higher), `value_avg_rank` (lower): median-run utility against the frozen comparator field.
- `utility_gain_mean` (higher): continuous utility relative to the uniform strategy and the best known utility; can exceed 1.

### Constraint / convergence targets
- `convergence_percent_reached` (higher): median run ends on a strategy with KKT gap <= 1e-6 within 6000 gradient evaluations.
- `restart_convergence_percent` (higher): fraction of all starts that do.
- Only runs that reach the threshold earn utility or speed credit.

### Speed targets
- `convergence_percent_best` (higher), `convergence_avg_rank` (lower): iterations to the threshold against the field.
- `log10_iterations_mean` (lower): gradient evaluations on a log scale (6001 if unsolved).

### Expected effect (paper)
The paper's regret-matching solvers converge more often and in far fewer iterations than projected gradient descent and its optimistic variant, with utility at least as high. A better method should improve speed/reliability without lowering utility, or raise utility without losing convergence.

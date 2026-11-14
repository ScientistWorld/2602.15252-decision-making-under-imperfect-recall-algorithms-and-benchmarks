# Evaluation

## How solvers are run

A solver is a program listed in `scripts/solvers.json` (`{"name": {"command": [...]}}`). The evaluator never gives a solver the decision problem. It starts the solver once per random start and talks to it over stdin/stdout:

1. The evaluator sends one JSON header line: `{"protocol": "irtree-oracle-1", "infoset_sizes": [...], "budget": 6000, "target_gap": 1e-06, "x0": [...], "run": k}`. A strategy is a flat vector of probabilities, one block per information set (block sizes `infoset_sizes`); `x0` is the starting strategy.
2. The solver queries strategies: it writes the byte `Q` followed by the strategy as little-endian float64. The evaluator answers with `1 + D` float64 values: the expected utility and the gradient (partial derivative for every action). Each query is one iteration of the budget.
3. The solver writes `D` when done. The run's result is the **last strategy it queried**. After 6000 answered queries the evaluator stops answering.

`data/oracle_client.py` implements the client side (`OracleClient().query(x) -> (utility, gradient)`, plus `kkt_gap`). Queries must be valid strategies (non-negative, each block summing to 1 within 1e-6); an invalid query, a crash, no query at all, or exceeding the time limits fails the run (held-out: 300 s per message, 1800 s per problem, 45 s x number of problems per solver; training: 300 s, 1200 s, 5400 s). Starts run in separate processes; the evaluator computes every scored number itself and reads nothing a solver writes. The held-out evaluator runs (solver, problem) pairs in parallel on the available CPUs; this does not change any result.

## Metrics

A run is **solved** if its result has KKT gap at most 1e-6. Unsolved and failed runs count as the worst possible run (no utility; iterations = 6001). The median run of the 12 starts is taken separately for utility and for iterations (the 7th best of 12). Every row is compared with a frozen field of reference solvers (the paper's comparators, fixed by the evaluator), excluding the reference solver of the same name. The field's runs were made from 12 other random starting points than the ones solvers receive, so no solver is matched start-for-start with a reference run.

- `value_percent_best` (higher): problems where the median utility is within 1e-4 (relative) of the field's best median utility.
- `value_avg_rank` (lower): tie-aware rank of the median utility in the field.
- `utility_gain_mean` (higher): mean over problems and starts of (utility - uniform-strategy utility) / (best known utility - uniform-strategy utility); unsolved runs score 0. Values above 1 beat every reference run.
- `convergence_percent_reached` (higher): problems whose median run is solved.
- `convergence_percent_best` (higher): problems where the median run is solved in no more iterations than any field entry.
- `convergence_avg_rank` (lower): tie-aware rank of the median iterations in the field.
- `log10_iterations_mean` (lower): mean log10 iterations over all runs (6001 for unsolved runs).
- `restart_convergence_percent` (higher): solved runs among all runs.

Wall-clock time is not scored.

## Protocol

- `bash scripts/evaluate_train.sh`: every listed solver on the 20 training problems (the paper's public instances) from 12 random starting points per problem; comparators = the paper's own logged runs (from the paper's own starting points). Writes `scoring/scores_train.json`.
- `bash scripts/evaluate_test.sh` (no arguments): every listed solver on the 176 held-out problems with frozen comparators. The problem files, their generator and the comparator field are unreadable while solvers run. Writes `scoring/scores_test.json`. For the seven reference solvers this takes about 1.5 hours with 4 CPUs (roughly 3.5 hours on one CPU).
- Every reference row (`gd`, `ogd`, `ams`, `rm`, `rm_plus`, `prm`, `prm_plus`) always appears; a row with no working solver gets the worst value of every metric.

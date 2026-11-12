# Progress

## Current state (hardened gym, final iteration)

- **Problems:** training = the paper's own 20 public small/medium benchmark instances (`data/instances/train/`, compiled from the paper's artifact by `data/prepare_train.py`); held-out test = 48 hidden instances drawn with a port of the paper's generators at the same size presets (`eval/test/`).
- **Evaluation:** solvers are programs in `scripts/solvers.json` that query a counted first-order oracle run by the evaluator (`briefing/evaluation.md`). Every scored number is computed by the evaluator. Rows are compared against frozen comparator fields (train: the authors' logged runs; test: the paper protocol frozen in `eval/test/field.json`).
- **Method:** `method/solver.py` (RM, RM+, PRM, PRM+) and `baseline/solver.py` (GD, OGD, AMSGrad) are ports of the authors' code. On the training problems they retrace the authors' logged runs (1678/1680 identical iteration counts, all convergence outcomes identical).
- **Result:** the paper's claim reproduces in its direction on the held-out problems. RM+ beats GD/OGD in convergence rank (3.15 vs 5.69/6.83), iterations (log10 1.22 vs 1.91/2.79), fastest-convergence share (47.9% vs 10.4%/0%) and utility (75% best vs 54%/52%). Details, shortcut audit and headroom check: `HARDENING.md`.

## Deviations from the paper

- Size presets a/b/c only (≤ ~47k nodes); no Gurobi; convergence measured in gradient evaluations, not wall-clock time.
- The comparator grids are restricted to the settings the paper's own runs selected on the training problems (GD/OGD step sizes {1, 0.1} / {1, 0.1, 0.01}, two AMSGrad settings); the registered GD/OGD/AMSGrad rows use one train-chosen setting.
- A run's utility counts only if the run reaches the KKT threshold.
- Fixed-setting AMSGrad reaches better utility than RM+ on the held-out problems (but converges much more slowly).

## History

Iterations 1-10 built and audited an artifact-based gym on 8 generated toy problems; the red-team audit (`REDTEAM.md`) showed it trusted self-reported numbers and could be brute-forced. Iteration 11 replaced it (see `HARDENING.md`).

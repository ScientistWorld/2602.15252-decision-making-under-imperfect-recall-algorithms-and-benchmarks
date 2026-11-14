# Progress

## Current state (hardened gym, final iteration)

- **Problems:** training = the paper's own 20 public small/medium benchmark instances (`data/instances/train/`, compiled from the paper's artifact by `data/prepare_train.py`); held-out test = 176 hidden instances drawn with a port of the paper's generators at the same size presets, weighted toward the largest preset of each family (`eval/test/`).
- **Evaluation:** solvers are programs in `scripts/solvers.json` that query a counted first-order oracle run by the evaluator (`briefing/evaluation.md`). Every scored number is computed by the evaluator. Rows are compared against frozen comparator fields (train: the authors' logged runs; test: the paper protocol frozen in `eval/test/field.json`), which were run from different starting points than the ones solvers receive.
- **Method:** `method/solver.py` (RM, RM+, PRM, PRM+) and `baseline/solver.py` (GD, OGD, AMSGrad) are ports of the authors' code. On the training problems they retrace the authors' logged runs (1678/1680 identical iteration counts, all convergence outcomes identical).
- **Result:** the paper's claim reproduces in its direction on the held-out problems. RM+ beats GD/OGD in convergence rank (2.50 vs 5.20/6.67), iterations (log10 1.37 vs 2.05/2.89), fastest-convergence share (51% vs 10%/0%), convergence reached (98.9% vs 93.8%/86.9%) and utility (79% vs 52%/51% best). A better solver (RM+ with a gradient fallback) beats the reference on every start set by more than the start-point noise. Details, shortcut audit and headroom check: `HARDENING.md`.

## Deviations from the paper

- Size presets a/b/c only (≤ ~47k nodes); no Gurobi; convergence measured in gradient evaluations, not wall-clock time.
- The comparator grids are restricted to the settings the paper's own runs selected on the training problems (GD/OGD step sizes {1, 0.1} / {1, 0.1, 0.01}, two AMSGrad settings); the registered GD/OGD/AMSGrad rows use one train-chosen setting.
- A run's utility counts only if the run reaches the KKT threshold.
- Fixed-setting AMSGrad reaches the best utility on more held-out problems than RM+ (84% vs 79%, all of it on random problems; RM+ leads on detection problems), but converges much more slowly.
- Solvers start from different random points than the comparator runs (the paper compares methods from shared starts); this closes a shortcut, at the cost of slightly noisier value comparisons.

## History

Iterations 1-10 built and audited an artifact-based gym on 8 generated toy problems; the red-team audit (`REDTEAM.md`) showed it trusted self-reported numbers and could be brute-forced. Iteration 11 replaced it; the final iteration enlarged the held-out test to 176 problems, separated solver and comparator starting points, and hid the comparator field during solver runs (see `HARDENING.md`).

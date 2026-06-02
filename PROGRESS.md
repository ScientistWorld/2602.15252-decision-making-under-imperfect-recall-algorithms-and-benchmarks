# Progress

## What Works

- Paper analysis is captured in `briefing/`.
- The compact benchmark generator creates absentminded-driver, simulation, and random imperfect-recall tree-form instances.
- `method/solve.py` implements the paper's local first-order optimization setup: evaluate expected utility, compute information-set gradients and KKT gaps, and run GD, OGD, AMS, RM, RM+, PRM, and PRM+.
- `scripts/method.sh` runs the optimizer suite and calls the method-agnostic evaluator.
- `eval/evaluate_results.py` reads method outputs and writes `scoring/scores.json`.
- `scoring/reference.json` records the paper's Table 1 aggregate metrics.

## Results

No reproduced scores yet. The first scheduled CPU test job will run the full compact suite with 3 random starts and 1500 iterations per optimizer.

## Remaining

- Run the scheduled job inside the container to establish `method_runs`.
- Inspect `scoring/scores.json`; if the RM-family methods show the expected value/convergence advantage over GD/OGD on the compact suite, update to `core_claim`.
- If results are weak, tune the common step size or expand the generated suite while preserving the paper's optimization procedure.

## Issues

- Local Python on the login node lacks NumPy, so end-to-end execution is deferred to the container where `environment/setup.sh` installs NumPy.

## Deviations from Paper

- The paper evaluates 61 benchmark instances including a subgroup-detection family. This compact reproduction currently uses a generated five-instance suite covering absentminded-driver, simulation-style, and random imperfect-recall problems because the exact paper benchmark files were not provided in the workspace.
- The paper reports full runs with up to 6000 iterations and a 4-hour timeout. The first submitted smoke job uses 1500 iterations and 3 starts to validate the environment; the scripts expose `ITERATIONS` and `RUNS` for scaling back toward the paper protocol.

# Progress

## What Works

- Paper analysis is captured in `briefing/`.
- The compact benchmark generator creates absentminded-driver, simulation, and random imperfect-recall tree-form instances.
- `method/solve.py` implements the paper's local first-order optimization setup: evaluate expected utility, compute information-set gradients and KKT gaps, and run GD, OGD, AMS, RM, RM+, PRM, and PRM+.
- `scripts/method.sh` runs the optimizer suite and calls the method-agnostic evaluator.
- `eval/evaluate_results.py` reads method outputs and writes `scoring/scores.json`.
- `scoring/reference.json` records the paper's Table 1 aggregate metrics.

## Results

Job `6064235d-e52` completed successfully on the compact five-instance suite with 3 random starts and 1500 iterations per optimizer. `python validate.py --compare` passed.

Reproduced aggregate scores:

| Method | Value % Best | Value Avg Rank | Convergence % Reached | Convergence % Best | Convergence Avg Rank |
|---|---:|---:|---:|---:|---:|
| GD | 60.0 | 2.4 | 60.0 | 0.0 | 5.0 |
| OGD | 60.0 | 3.2 | 60.0 | 0.0 | 5.8 |
| AMS | 0.0 | 6.6 | 0.0 | 0.0 | 6.0 |
| RM | 60.0 | 3.6 | 100.0 | 80.0 | 2.2 |
| RM+ | 80.0 | 3.0 | 80.0 | 80.0 | 3.6 |
| PRM | 60.0 | 5.2 | 100.0 | 40.0 | 2.4 |
| PRM+ | 100.0 | 4.0 | 100.0 | 40.0 | 3.0 |

The core claim is supported at reduced scale: the regret-matching family consistently satisfies the first-order KKT convergence constraint more often and with better convergence ranks than GD/OGD on this suite.

## Remaining

- Run the expanded suite with subgroup-detection-style instances, a larger random instance, 12 starts, and 6000 iterations to move toward `core_claim_plus`.
- If expanded-suite results are weak, tune only common optimizer hyperparameters or add more fixed generated instances while preserving the paper's optimization procedure.

## Issues

- Local Python on the login node lacks NumPy, so end-to-end execution is performed inside the scheduler container where `environment/setup.sh` installs NumPy.

## Deviations from Paper

- The paper evaluates 61 benchmark instances. This reproduction uses generated compact instances covering absentminded-driver, simulation-style, subgroup-detection-style, and random imperfect-recall problems because the exact paper benchmark files were not provided in the workspace.
- The first successful smoke job used 1500 iterations and 3 starts to validate the environment. The next run uses the paper's 6000-iteration and 12-start settings on the expanded compact suite.

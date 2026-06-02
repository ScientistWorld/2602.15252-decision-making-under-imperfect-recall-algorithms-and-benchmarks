# Progress

## What Works

- Paper analysis is captured in `briefing/`.
- The compact benchmark generator creates absentminded-driver, simulation, subgroup-detection-style, and random imperfect-recall tree-form instances.
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
| RM | 60.0 | 3.6 | 100.0 | 80.0 | 2.2 |
| RM+ | 80.0 | 3.0 | 80.0 | 80.0 | 3.6 |
| PRM | 60.0 | 5.2 | 100.0 | 40.0 | 2.4 |
| PRM+ | 100.0 | 4.0 | 100.0 | 40.0 | 3.0 |

Job `29695a0b-7dd` completed successfully on the expanded eight-instance suite with 12 random starts and 6000 iterations per optimizer. `python validate.py --compare` passed.

Expanded-suite aggregate scores:

| Method | Value % Best | Value Avg Rank | Convergence % Reached | Convergence % Best | Convergence Avg Rank |
|---|---:|---:|---:|---:|---:|
| GD | 62.5 | 2.875 | 75.0 | 0.0 | 5.25 |
| OGD | 62.5 | 3.5 | 75.0 | 0.0 | 6.125 |
| RM | 75.0 | 2.875 | 100.0 | 37.5 | 2.625 |
| RM+ | 75.0 | 3.25 | 100.0 | 62.5 | 2.5 |
| PRM | 87.5 | 4.125 | 100.0 | 62.5 | 2.25 |
| PRM+ | 87.5 | 4.375 | 100.0 | 25.0 | 3.375 |

The core claim is supported across additional settings: the regret-matching family satisfies the first-order KKT convergence constraint on every expanded-suite instance and has substantially better convergence ranks than GD/OGD, while also matching or exceeding the paper's reported value-best rates on this compact suite.

AMS was run and remains in `results/optimization_results.json`, but it is not emitted in `scoring/scores.json` because this compact AMS implementation does not reproduce the paper's AMS baseline closely enough. The scored reproduction claim covers GD/OGD baselines and the RM/PRM family.

## Remaining

- Full-paper coverage would require the original 61-instance benchmark suite, which was not provided in the workspace.
- A closer AMS comparator would require a more faithful reconstruction of the paper's AMS configuration. It is intentionally not claimed in `scoring/scores.json`.

## Issues

- Local Python on the login node lacks NumPy, so end-to-end execution is performed inside the scheduler container where `environment/setup.sh` installs NumPy.

## Deviations from Paper

- The paper evaluates 61 benchmark instances. This reproduction uses generated compact instances covering absentminded-driver, simulation-style, subgroup-detection-style, and random imperfect-recall problems because the exact paper benchmark files were not provided in the workspace.
- The first successful smoke job used 1500 iterations and 3 starts to validate the environment. The final expanded run uses the paper's 6000-iteration and 12-start settings on the compact suite.

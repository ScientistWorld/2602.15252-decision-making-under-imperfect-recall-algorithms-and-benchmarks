# Progress

## What Works

- Paper analysis is captured in `briefing/`.
- `data/tree_games.py` defines the reusable tabular tree-form problem representation and generates the fixed compact benchmark suite.
- `method/solve.py` implements expected-utility evaluation, information-set gradients, KKT-gap measurement, random starts, and optimizer-suite execution.
- `method/optimizers.py` implements the local simplex update rules for GD, OGD, AMS, RM, RM+, PRM, and PRM+.
- `scripts/method.sh` runs the paper-method optimizer suite and calls the method-agnostic evaluator.
- `baseline/run_baseline.py` and `scripts/baseline.sh` run GD/OGD reference methods in the same artifact format.
- `eval/evaluate_results.py` reads saved result artifacts and writes `scoring/scores.json`; it does not import from `method/`.
- `environment/container.def` and `environment/setup.sh` provide a CPU Python container with NumPy installed through `uv pip install --system`.

## Results Achieved

The checked-in score file comes from a completed expanded compact-suite run with 8 generated instances, 12 random starts per method, 6000 iterations, `eta=0.1`, and KKT-gap target `1e-6`. `python validate.py --compare` passes.

| Method | Value % Best | Value Avg Rank | Convergence % Reached | Convergence % Best | Convergence Avg Rank |
|---|---:|---:|---:|---:|---:|
| GD | 62.5 | 2.875 | 75.0 | 0.0 | 5.25 |
| OGD | 62.5 | 3.5 | 75.0 | 0.0 | 6.125 |
| RM | 75.0 | 2.875 | 100.0 | 37.5 | 2.625 |
| RM+ | 75.0 | 3.25 | 100.0 | 62.5 | 2.5 |
| PRM | 87.5 | 4.125 | 100.0 | 62.5 | 2.25 |
| PRM+ | 87.5 | 4.375 | 100.0 | 25.0 | 3.375 |

The core claim is supported on this compact suite: every scored regret-matching variant reaches the first-order convergence threshold on all instances, while GD and OGD reach it on 75% of instances. RM/RM+/PRM/PRM+ also match or exceed the paper's reported aggregate value-best rates on the compact generated suite.

## What Remains

- Full-paper coverage would require the original 61-instance benchmark suite or a faithful reconstruction of all parameter settings used in the paper's appendix.
- The checked-in scorer omits AMS from `scores.json`; AMS traces are retained in `results/optimization_results.json`, but the compact AMS implementation was not close enough to the paper's AMS baseline to claim as reproduced.
- Exact nonlinear optimization with Gurobi is not reproduced because it requires a commercial solver and is a secondary paper claim.

## Issues Encountered

- The original paper benchmark files were not present in the workspace. The reproduction therefore uses generated compact instances that preserve the same problem formalism and benchmark families.
- The appendix Google Drive artifact for original benchmark instances was checked on 2026-06-02 via the paper's file ID; the verified download URL redirected successfully but returned HTTP 404, so the original 61 instances were not available for this package.
- Local login-node Python initially lacked NumPy, so validation of the end-to-end method was done through the scheduler/container path where `environment/setup.sh` installs NumPy. NumPy is now declared in setup.
- A previous baseline packaging issue was fixed before wrap-up: `scripts/baseline.sh` now calls `baseline/run_baseline.py`, and that entrypoint writes evaluator-compatible artifacts.
- The GD/OGD baseline runner is self-contained in `baseline/` and no longer imports the proposed-method solver.

## Deviations from Paper

- The paper evaluates 61 benchmark instances. This reproduction uses a fixed compact suite of 8 generated instances because the exact paper benchmark files were not available in the workspace.
- The paper reports wall-clock times, but this gym does not score wall-clock speed because hardware varies across runs. It scores utility and machine-independent convergence/iteration-rank aggregates instead.
- Exact global optimization is documented in `scoring/reference.json` through the paper's numbers but is not included in reproduced `scores.json`.

## Final Status

Final milestone: `core_claim`. The reproduction is packaged, validated, and ready for future agents to run with `bash scripts/reproduce.sh` followed by `python validate.py --compare`.

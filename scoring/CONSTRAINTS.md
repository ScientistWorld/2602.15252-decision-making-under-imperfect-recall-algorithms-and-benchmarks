# Scientist Constraints

## Fixed by the evaluator (not by submissions)
- Problems: training = the paper's 20 public instances (`data/instances/train/`); held-out = 48 hidden instances in `eval/test/`.
- Starting points: 12 per problem (training: the paper's seeds 33-44; held-out: hidden seeds), sent to every solver.
- Budget: 6000 gradient evaluations per run; convergence threshold: KKT gap <= 1e-6.
- Comparators: frozen per-run results of GD, OGD, AMSGrad (per-problem best setting from the paper's grids), RM, RM+, PRM, PRM+ (`eval/train/field.json`, `eval/test/field.json`).
- All utilities, gaps and iteration counts are computed by the evaluator from the strategies a solver queries.

## What a submission controls
- The solver program(s) in `scripts/solvers.json` and their code. A solver may implement any procedure that uses the oracle: its own initialisation, step rules, restarts within the budget, line searches. Every query counts.

## Rules
- A solver must interact with problems only through the oracle protocol (`data/oracle_client.py`). Reading problem files, evaluator files, other runs' outputs, or sharing information between runs/processes is not allowed.
- Strategies must be behavioural strategies on the given information sets (no extra memory, no splitting of information sets).
- Starts are independent runs: one start may not use another start's results.
- Wall-clock time is not scored, but the time limits in `briefing/evaluation.md` apply.

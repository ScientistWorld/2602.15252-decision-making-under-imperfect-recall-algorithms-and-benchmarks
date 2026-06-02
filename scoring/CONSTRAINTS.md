# Scientist Constraints

## Fixed Problem Suite

Headline scores must use the fixed JSON instances in `data/instances/`:

- `absentminded_driver.json`
- `simulation_3.json`
- `simulation_5.json`
- `subgroup_detection_small.json`
- `subgroup_detection_large.json`
- `random_depth6.json`
- `random_depth7.json`
- `random_depth8.json`

Additional instances may be used for development or supplemental reporting, but they must not replace this suite in `scoring/scores.json`.

## Fixed Problem Formulation

Submissions must solve the original tabular tree-form imperfect-recall decision problems. They must preserve the given nodes, chance probabilities, terminal payoffs, action sets, and information-set merges. A method may not split merged information sets, add memory to the strategy, remove absentmindedness, or evaluate decisions using history information that the strategy is not allowed to observe.

## Fixed Output Format

Methods must write artifacts compatible with `eval/evaluate_results.py`: per-instance method names, run records, selected runs, final values, final KKT gaps, and iterations-to-gap. Evaluation must be performed by `bash scripts/evaluate.sh`, which writes `scoring/scores.json`.

## Fixed Evaluation Settings

- Convergence threshold: `1e-6`.
- Headline run settings used for the checked-in scores: 12 random starts, 6000 iterations, seed 123, and `eta=0.1`.
- Every compared method in a headline result must use the same instances, start count, seed policy, iteration budget, and threshold.
- Wall-clock speed must not be used as a scored metric.

## Resource Scaling

Improvement should come from a better optimization method, not from changing the benchmark, giving one method more starts, using a larger iteration budget for only one method, or replacing the local strategy optimization problem with an exact global solve on tiny instances only.

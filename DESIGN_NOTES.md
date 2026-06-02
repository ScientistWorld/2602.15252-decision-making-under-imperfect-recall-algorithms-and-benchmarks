# Train/Test Evaluation Design Notes

Checked:
- Reviewed `eval/train/evaluate.py`, `eval/test/evaluate.py`, `scripts/evaluate_train.sh`, `scripts/evaluate_test.sh`, and `scoring/reference.json`.
- Confirmed train and test scripts point at their own evaluator folders and write `scoring/scores_train.json` and `scoring/scores_test.json`.
- Confirmed the split remains artifact-based: evaluators read `results/optimization_results.json` and do not import or rerun `method/`.
- Confirmed no `scoring/scores_train.json` or `scoring/scores_test.json` stubs are present.
- Ran `bash -n` on both train/test shell scripts.

Changed:
- Hardened both slice evaluators against comparator omission. They now require the fixed paper comparator set (`gd`, `ogd`, `ams`, `rm`, `rm_plus`, `prm`, `prm_plus`) to be present on every scored slice instance, while still scoring additional methods present across the slice.
- Added `_slice` markers to train/test score outputs so copied or mislabeled artifacts are easier to spot.
- Added continuous utility and convergence metrics to both slices:
  - `value_avg_gap_to_best`
  - `selected_iterations_to_gap_mean`
  - `selected_log10_kkt_gap_mean`
  - `restart_convergence_percent`
- Added required metric descriptions to `scoring/reference.json` and registered the new metrics there. Paper-reported result values were left unchanged.

Fixed pattern:
- Rank/win-count gaming by omitted comparators. Before this pass, an artifact containing only one method could make rank and percent-best metrics trivially perfect.
- Binary convergence saturation. The new log-gap and iteration-count metrics retain signal when several methods all reach the same KKT threshold.
- Cherry-picked selected runs. The restart convergence metric uses all recorded runs when available.

Runtime concerns for the next iteration:
- I did not run either evaluator or generate scores in this file-only pass. The runner should verify that the new score keys are emitted as valid JSON numbers on the current artifact.
- `scripts/evaluate.sh` still uses the older top-level aggregate evaluator and does not emit the new train/test-only metrics. This pass focused on the split harness requested here; a later pass should decide whether to mirror the new metrics in the standard evaluator or keep them split-only.
- The split has only four instances per side because the compact reproduction ships eight instances total. The added restart and continuous metrics improve triangulation, but the held-out signal is still limited by small slice size.
- Future methods that introduce new method names may be scored by the split evaluators, but the existing validator may reject unknown method names against `scoring/reference.json`. Improve-mode agents can avoid this by writing compatible results under the existing optimizer names.

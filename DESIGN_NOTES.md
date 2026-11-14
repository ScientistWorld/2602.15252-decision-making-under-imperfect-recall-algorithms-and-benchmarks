# Design Notes (hardened gym)

- `eval/train/` and `eval/test/` are independent copies of the same harness (`harness.py`: oracle + solver protocol; `metrics.py`; `evaluate.py`). They share no code; `eval/` never imports `method/`.
- The held-out problems, their generator (with seeds), the comparator start seeds and the frozen comparator field live only in `eval/test/`. While solvers run, the problem files, generator, comparator field and field builder are unreadable; everything is loaded before the first solver starts.
- Solvers start from different seeds (test 1001-1012, train 45-56) than the comparator runs (test: frozen seeds in `build_field.py`; train: the paper's 33-44), so no solver is matched start-for-start with a comparator.
- The held-out evaluator runs (solver, problem) pairs in parallel (`harness.run_tasks`, worker count measured at start); results do not depend on it.
- Train comparators = the authors' logged runs (`eval/train/build_field_from_paper_logs.py`). Test comparators were frozen once by `eval/test/build_field.py` (run through the same oracle protocol as any submission).
- Rows: every comparator family (`gd`, `ogd`, `ams`, `rm`, `rm_plus`, `prm`, `prm_plus`) plus every registered solver; missing or failing solvers get worst values.
- Checks and audit tooling: `redteam/hardening/` (oracle checks, run-by-run agreement with the paper's logs, variant/shortcut cases, summary).

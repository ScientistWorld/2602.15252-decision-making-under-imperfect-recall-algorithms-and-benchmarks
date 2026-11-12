# Design Notes (hardened gym)

- `eval/train/` and `eval/test/` are independent copies of the same harness (`harness.py`: oracle + solver protocol; `metrics.py`; `evaluate.py`). They share no code; `eval/` never imports `method/`.
- The held-out problems, their generator (with seeds), the start seeds and the frozen comparator field live only in `eval/test/`. While solvers run, the problem files and generator are unreadable; everything is loaded before the first solver starts.
- Train comparators = the authors' logged runs (`eval/train/build_field_from_paper_logs.py`). Test comparators were frozen once by `eval/test/build_field.py` (run through the same oracle protocol as any submission).
- Rows: every comparator family (`gd`, `ogd`, `ams`, `rm`, `rm_plus`, `prm`, `prm_plus`) plus every registered solver; missing or failing solvers get worst values.
- Checks and audit tooling: `redteam/hardening/` (oracle checks, run-by-run agreement with the paper's logs, variant/shortcut cases, summary).

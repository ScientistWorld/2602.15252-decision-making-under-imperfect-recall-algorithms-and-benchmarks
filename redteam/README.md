# Gym scoring audit

Run the bundled CPU job with `python redteam/audit.py all`. Each case also has
`redteam/<case>/run.sh`; it installs the method artifact as a scientist would,
runs `scripts/evaluate_train.sh`, and invokes the unchanged
`bash scripts/evaluate_test.sh` with **no arguments** in a new process. Every
case restores the game JSONs and default result/score files when it finishes.
Nothing changes the evaluator, Python imports, environment, or a running
evaluation process. The scripts also work after a container restart: their
only carried state is files on disk.

`fixtures/reference_outputs.json` is the existing trained reference output,
reused as explicitly permitted by the audit request. It freezes comparators
for isolated checks and contains all original strategies and random starts.
Shortcuts do not use paper content or hidden evaluator IDs to construct
answers; they target **all** public JSON instances. Scalar-score fixtures are
for reference comparison/restoration only. New candidate results come from
the visible method, visible game files, or deliberate artifact shortcuts.

The reference and the three seed checks target RM+ (12 starts, 6000 updates,
eta 0.1, seeds 123/234/345). Comparators remain frozen. The coordinate solver
is a genuine structured local alternative with exact one-dimensional
polynomial maximizations. It counts full coordinate sweeps and also records
its value-evaluation work, since sweeps and simultaneous first-order updates
are not equal-cost units. The eta-1 GD check restores a paper learning rate
omitted by the reproduction. The longer run uses a 24000-update ceiling but
the original early stopping criterion. The weaker run allows one update.

Additional GD controls run eta 0.1 and eta 1 with seeds 123/234/345 and a
one-step GD ablation. These use the same validated vectorized tree passes
as the tuned GD control and recompute final results independently. They
measure GD seed variation separately from the RM+ reference variation.

The brute-force check enumerates all deterministic policies, including all
3^16 policies on the largest instance. If its best pure solution is not
stationary, it performs coordinate polishing. Its reported cost includes
enumeration; the separately named cached-answer shortcut deliberately omits
preparation cost and reuses a fixed lookup table of the public answers.

`summary.json` and `summary.tsv` give raw hidden-test metrics and two disclosed
audit-cohort rank normalizations. Future attempts determine their own metric
standard deviations, which are unknowable now. Each score uses experiment
weight, absolute coefficient, and the declared better direction. Zero-variance
metrics contribute zero in the audit calculation. No unit-based weighting or
coefficient-sign reversal is used. Failed evaluations are recorded as failed
and never treated as fresh scores.
The `honest_variants` normalization is deliberately fixed to the seven RM+
controls listed in `summary.json`; it is an example of a plausible future
cohort, not a claim that the other scientific controls are shortcuts.

Large intermediate case outputs and logs are ignored by `redteam/.gitignore`;
scores, status, solver diagnostics, source, lookup tables, and the comparator
fixture are tracked. Case scripts recreate ignored intermediate files.

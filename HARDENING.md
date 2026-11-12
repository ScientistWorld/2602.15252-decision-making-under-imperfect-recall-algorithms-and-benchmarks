# Hardening report (final iteration)

## Verdict

**Better results now score higher, worse ones lower, and every red-team shortcut is closed.** The old gym scored a JSON file the submission wrote: self-reported values, gaps, iteration counts and comparator rows, on 4 public toy problems that exhaustive search solved in seconds. The hardened gym runs every solver itself, on 48 hidden problems, through a counted first-order oracle. It computes every scored number from the strategies the solver queries, and compares against a frozen field of the paper's comparators.

What changed:

1. **Paper's own data.** The benchmark artifact cited in the paper's appendix was reachable after all: the earlier 404 came from an ID mangled in the markdown (`..._N1S7`). Training problems are the paper's 20 public small/medium instances (Det-86 … Rand-42k, Sim-245 … Sim-13k). Held-out problems are 48 new draws from a port of the paper's own generators (simulation, subgroup detection on graphs with hit memory and miss forgetting, random), at the same size presets, with hidden seeds (`eval/test/generate_instances.py`; instances in `eval/test/instances/`). The substitute subgroup game and the toy random/simulation games are gone. The generator port reproduces the paper's instance sizes, including a quirk of the released random generator (chance probabilities summing to < 1).
2. **Solvers never see a problem.** A solver is a command in `scripts/solvers.json`. The evaluator starts it once per start (12 fixed starts per problem; separate processes, run in lockstep) and answers `Q <strategy>` with utility and gradient. Every query is one of the 6000 budgeted iterations; the result is the last queried strategy (`eval/*/harness.py`, `data/oracle_client.py`). The evaluator validates every query as a behavioural strategy and computes utility, KKT gap and iterations itself. Instances, field and registry are loaded before any solver starts. The files holding or regenerating the hidden problems are made unreadable while solvers run. Each solver's process group is killed when its run ends.
3. **Comparators fixed by `eval/`.** Train field = the authors' own logged runs (all 20 configurations × 12 starts) from the same starting points the evaluator sends (`eval/train/field.json`). Test field = the same paper protocol frozen once (`eval/test/field.json`): GD/OGD with per-problem best step size, AMSGrad with per-problem best setting, plus RM, RM+, PRM, PRM+. The grids are restricted to the settings the paper's runs ever selected on the training problems. A row is ranked against the field minus its own family.
4. **Failure accounting.** A run that does not end on a strategy with KKT gap ≤ 1e-6 earns no utility and counts 6001 iterations. Crash, invalid query, no query, or timeout count the same. A field family with no working solver still gets a row with the worst value of every metric, and any extra registered solver gets a row too. `evaluate_test.sh` runs with no arguments and writes every row to `scoring/scores_test.json`.
5. **Paper-faithful solvers.** `method/solver.py` (RM family) and `baseline/solver.py` (GD, OGD, AMSGrad with the authors' weighted projection) are ports of the authors' code. On the training problems they retrace the authors' logged runs: 1678/1680 runs have identical iteration counts (the other two are one long RM and one long PRM run that drift by floating point), convergence status is identical in all 1680, and utilities agree to ≤ 4e-9 (`redteam/hardening/paper_run_agreement.json`). The oracle matches a pure-Python evaluator to 1e-14 on all 68 problems, and the authors' iteration-0 logs to 6e-15 (`checks.json`). The GD/OGD/AMS rows use one setting each, chosen on the training problems (GD 0.1, OGD 0.01, AMSGrad 0.1/0.9/0.999). This restores the paper's grids, which the old gym had replaced by a single η = 0.1 and a single AMS configuration; the per-problem best setting lives in the field.
6. **New metric set** (`scoring/reference.json`). The paper's Table 1 metrics (value % best, value rank, convergence % reached, convergence % best, convergence rank), computed with tie-aware ranks and a 1e-4 relative tie tolerance. Plus continuous metrics: `utility_gain_mean` (gain over the uniform strategy relative to the best known gain; can exceed 1), `log10_iterations_mean` and `restart_convergence_percent`. Wall-clock time is not scored. Coefficient magnitudes: speed 1.0 (log10) + 0.75 (rank) + 0.5 (fastest); reliability 1.0 (reached) + 0.5 (all starts); utility 1.0 (% best) + 0.5 (rank) + 1.0 (gain). This follows the paper's headline ("orders of magnitude" faster, utility at least as high). The old zero-coefficient diagnostic and the log-gap metric, which rewarded the numerical floor, were dropped.

All numbers below come from the unchanged `eval/test/evaluate.py` restricted to one row (`redteam/hardening/run_cases.py`; scores in `redteam/hardening/scores/`, table in `summary.md`). "Δ" is the ranker's quantity relative to the reference row of the same name: Σ |coef| × improvement in the better direction / std of the metric across attempts. **ALL** uses the std over all 44 evaluated rows (7 reference rows + 37 cases); **HONEST** uses the 21 reference rows, seed reruns and honest variants. The future population is unknown.

## Reference before and after

| | best% | value rank | utility | conv% | fastest% | conv rank | log10 iters | all starts % |
|---|---|---|---|---|---|---|---|---|
| RM+ old gym (4 public toy problems, self-reported) | 75 | 4.5 | shortfall .0021 | 100 | 50 | 3 | 1.372 | 100 |
| **RM+ hardened test (48 hidden problems)** | 75.0 | 3.698 | gain 0.944 | 97.9 | 47.9 | 3.146 | 1.216 | 98.3 |
| RM+ hardened train (paper's 20 instances) | 80.0 | 3.600 | gain 0.944 | 100 | 45.0 | 3.025 | 1.258 | 97.5 |

Train and test agree for every honest row (e.g. GD 65/4.38/0.865 train vs 54/4.72/0.909 test), so an honest method scores alike on both. The cached-answer shortcut below shows the opposite case: a method tuned to train loses on test.

**The paper's claim, in the paper's direction (test):**

| | paper RM+ vs GD | old gym | hardened test |
|---|---|---|---|
| value % best | 70.5 vs 44.3 | 75 vs 75 | **75.0 vs 54.2** |
| value rank (↓) | 3.79 vs 4.99 | 4.5 vs 2.25 (reversed) | **3.70 vs 4.72** |
| convergence % reached | 90.2 vs 72.1 | 100 vs 75 | 97.9 vs 97.9 (tie; GD row uses its best single step size) |
| convergence % best | 21.3 vs 11.5 | 50 vs 0 | **47.9 vs 10.4** |
| convergence rank (↓) | 2.70 vs 5.08 | 3 vs 5.75 | **3.15 vs 5.69** |

In Δ units the GD row is −3.60 (ALL) below RM+, OGD −6.06 and AMSGrad −2.35. That is about 10× the seed noise. RM (−0.16), PRM (−0.48) and PRM+ (+0.00) are close to RM+; the paper also finds the RM family close together.

## Do better results score higher? (before → after)

Seed noise: the reference rerun from three other fixed start sets gives Δ = +0.27, +0.36, +0.16 (ALL; range **0.36**, std 0.13); HONEST range 0.68. On the old gym the RM+ seed range was 1.23 (ΔA). All methods see the same starts, so official comparisons are paired.

| Variant (row) | old gym ΔA | hardened Δ ALL / HONEST | what it does |
|---|---|---|---|
| **RM+ → adaptive-step GD fallback after 50 iterations** (`rm_plus`) | — | **+0.42 / +1.09** | better on all 8 metrics (79.2% best, gain 0.959, 100% converged, log10 1.166). Paired vs RM+ on start sets B/C/D: +0.29, +0.17, +0.31 (ALL), all positive |
| same, fallback after 200 (`rm_plus`) | — | +0.32 / +0.93 | paired +0.28, +0.11, +0.27 |
| adaptive-step GD (`gd`) | — | **+3.27 / +6.10** | GD seed noise 0.02 |
| GD η=1 (`gd`) | +3.08 (vs η=0.1) | −0.60 / −4.35 | faster but converges on 77% only |
| adaptive GD submitted as `rm_plus` | — | −0.24 / −0.65 | faster, more reliable, worse utility (58% best); paired vs RM+ on B/C/D: −0.59, −0.30, −0.55 |
| RM+ with restarts (`rm_plus`) | — | −2.10 / −2.69 | 95.8% best, gain 0.977, but ~10× the iterations |
| PRM+ as `rm_plus` | — | +0.12 / +0.30 | within noise (better utility, slower) |
| discounted RM+ (`rm_plus`) | — | −0.98 / −2.91 | worse |
| RM+ capped at 100 iterations (`rm_plus`) | — | −2.70 / −7.98 | weaker |
| RM+ stopping at gap 1e-4 (`rm_plus`) | — | −5.24 / −15.20 | weaker |
| one-step / uniform (`rm_plus`) | −10.27 | −15.13 / −44.24 | weakest |

To get here, the held-out set was enlarged from 24 to 48 problems. On 24 problems the noise range (0.76) was as large as the best variant's gain.

## Shortcuts (before → after)

| Red-team shortcut | before (ΔA) | fix | after Δ ALL |
|---|---|---|---|
| cached answers (public lookup table) | +3.13 | test problems hidden and new; lookup by fingerprint fails | **−15.13** on test (on the public train slice it still gets +3.86, which is the intended contrast) |
| forged fields (value 1e6, gap −1, iters −100) | +3.86 | nothing a solver reports is read; utility/gap/iterations are computed from queried strategies; a non-strategy query (`x0×3`) fails the run | invalid strategy **−15.19**; files planted during the run **0.00** |
| empty strategy with copied scalars | 0 (tie) | a run with no query fails | **−15.19** |
| comparison shift (degrade comparator rows) | +3.25 | comparators frozen in `eval/test/field.json`; degrading gd/ogd/ams solvers leaves the `rm_plus` row unchanged | **0.00** |
| train-score allowlist filtering comparators | +3.25 | the test no longer reads `scores_train.json`; rows = frozen field families ∪ registered solvers | closed in code (not re-run) |
| replace public payoffs | +3.73 | test problems live in `eval/test/`, are preloaded and hidden; overwriting all of them during the run (`forge_files`) changes nothing | **0.00** |
| failed-task trade-off (huge utility, 1 iteration, gap 1) | +0.31 (cohort C) | unconverged runs earn no utility and count 6001 iterations | **−15.13** |
| unscored extra method | 0 (tie) | every registered solver gets a row; a crashing one gets the worst row | **−15.97** |
| prewritten score file | 0 | output always rewritten by the evaluator | **0.00** (no gain) |
| null value / omitted comparator → no score | test exited 1 | missing or crashing rows get the worst value of every metric, exit 0 | **−15.19** |
| longer iteration ceiling | 0 (tie) | the evaluator stops answering after 6000 queries | over-budget solver **−15.13** |
| brute force over pure strategies | −0.85 (solved every test case exactly in 4.7 s) | enumeration costs one counted query per strategy; problems hidden | **−8.26** (54% converged, worst speed) |
| *new:* read hidden problem files and optimise privately | — | hidden files unreadable while solvers run | **0.00** on test (falls back to honest RM+); +2.64 on the public train slice, showing the attack would pay if the files were readable |

## Headroom

The reference sits at the bound of no scored metric: 75% best, rank 3.70, gain 0.944 (values > 1 are possible), 97.9% converged, 47.9% fastest, convergence rank 3.15, log10 1.22, 98.3% of starts. Convergence % is near saturation; the fallback variants reach 100% there. Every other metric keeps room above the best variant (79.2% best, gain 0.959). The fallback variant beats the reference beyond noise on all metrics at once, and restarts show utility headroom up to 95.8% best and gain 0.977. Simple baselines sit clearly below (GD −3.60, OGD −6.06). Brute force cannot fit the budget. No extra experiment was needed.

## Left open (stated plainly)

- **No OS sandbox.** Solvers run as ordinary processes. A solver could still read other evaluator files (e.g. `eval/test/field.json`, which holds comparator results, not answers). It could share information between its own runs through the filesystem, read the evaluator's memory via `/proc`, escape its process group with `setsid`, or ignore the permission lock if the hidden test runs as root. These need deliberate malicious code and are left to the shortcut grader; `scoring/CONSTRAINTS.md` forbids them.
- **Scale.** Problems go up to ~47k nodes and 884 dimensions, against the paper's 23M nodes and ~800 information sets. Gurobi is not run. Convergence is counted in gradient evaluations, not seconds. The paper's large-scale runtime claims are not tested.
- **Partial deviations from the paper.** The fixed-setting AMSGrad row reaches better utility than RM+ on the test (85% best vs 75%), while converging much more slowly (rank 6.40). The paper reports RM+ at least as good as AMS in utility. PRM+ vs RM+ is mixed: PRM+ has better utility and is slower; the paper finds RM+ faster, which holds here.
- **Hidden-test cost.** About 60 minutes on one CPU for the 7 reference rows (time limits: 300 s per message, 1200 s per problem, 5400 s per solver; these are hard failures, not metrics).
- The pre-hardening red-team cases in `redteam/<case>/` target the old artifact interface and no longer run. They are kept as evidence for the "before" column.

Reproduce: `bash scripts/run.sh` (reference; add `RUN_HARDENING=1` for all cases, then `python redteam/hardening/summarize.py`).

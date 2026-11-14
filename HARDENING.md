# Hardening report (final iteration)

## Verdict

**Better results score higher, worse ones lower, and a genuinely better solver now beats the reference on every set of starting points, by more than the starting-point noise.** This iteration answers `REVIEW.md`, which found two weaknesses:
- the better variant's gain (+0.42) was only just above the seed range (0.36);
- AMSGrad beat the reference on percent of problems best (85.4 vs 75.0).

Two changes fix this, and a third leak was closed on the way:

1. **The held-out test grew from 48 to 176 problems** (128 new draws from the paper's generators, at the same size presets).
   - The new draws are weighted toward the largest preset of each family: detection c 48, simulation b 48, random a 24, random b 24, detection b 16, detection a 8, simulation a 8.
   - The smallest presets are ties for every solver. Random problems carry most of the noise: which local optimum the median run lands in flips between start sets.
   - The 48 old problems are unchanged. The generator now sums floats exactly as Python 3.12 does, so it reproduces all 176 stored files byte for byte under Python 3.11 too.
   - The comparator field was frozen for the new problems with the paper's protocol. Each problem's SHA-256 is stored in the field and checked by the evaluator.
2. **Scored solvers no longer start from the comparators' starting points.** This is a new shortcut, found while measuring noise.
   - Before, the evaluator sent each solver the same 12 starts the frozen comparator runs had used. The comparator RM, PRM and PRM+ runs from those same starts are systematically a little faster than RM+ on many problems: an RM-family run is strictly faster than RM+'s median on 85 of 176 problems from the same starts, versus 61–64 from other starts.
   - So the same RM+ code scored about +0.25 higher just by ignoring its start (`fieldstarts_rm_plus` below). That is as much as the honest better variant gained, and it explains why every "seed noise" rerun in the old report came out positive.
   - Now solvers start from seeds 1001–1012 on the hidden test and 45–56 on training. The comparators keep their own starts: frozen seeds on the hidden test, and the authors' logged runs from seeds 33–44 on training. No solver can now gain by using or ignoring the start it is given.
3. **Comparator results are no longer readable during the hidden test.**
   - `eval/test/field.json` stores each hidden problem's uniform-strategy utility, which identifies the problem, and the final utility of every comparator run, which gives the best known value.
   - It, its builder and its resume file are now unreadable while solvers run, like the problem files and their generator.

The hidden test still runs every solver itself through the counted oracle and computes every number from the strategies queried. It now runs (solver, problem) pairs in parallel on the CPUs that really run in parallel (measured at start). The per-solver time limit is 45 s × number of problems, a hard failure and not a metric.

All numbers below come from the unchanged `eval/test/evaluate.py`, restricted to one row (`redteam/hardening/run_cases.py`; scores in `redteam/hardening/scores/`, table in `summary.md`).
- **Δ** is the ranker's quantity relative to the reference row of the same name: Σ |coef| × improvement in the better direction / std of the metric across attempts.
- **ALL** takes the std over all evaluated rows (7 reference rows + 37 cases).
- **HONEST** takes it over the reference rows, seed reruns and honest variants only.
- The previous report's Δ values (48 problems) used their own cohort, so compare ratios rather than raw Δ between the two reports.

## Reference before and after

| | best% | value rank | utility gain | conv% | fastest% | conv rank | log10 iters | all starts % |
|---|---|---|---|---|---|---|---|---|
| RM+ before: 48 problems, comparators' starts | 75.0 | 3.698 | 0.944 | 97.9 | 47.9 | 3.146 | 1.216 | 98.3 |
| **RM+ now: 176 problems, own starts** | **79.0** | **3.713** | **0.958** | **98.9** | **51.1** | **2.500** | **1.371** | **98.6** |
| RM+ training before (paper's starts) | 80.0 | 3.600 | 0.944 | 100 | 45.0 | 3.025 | 1.258 | 97.5 |
| **RM+ training now (own starts)** | **85.0** | **3.475** | **0.950** | **100** | **45.0** | **3.000** | **1.219** | **97.5** |

The reference reruns are fresh: all 7 registered solvers, from the final code.
- The new RM+ row is identical, run by run, to an earlier RM+ run from the same starts (2112/2112 runs; `reference_rerun_agreement.json`).
- The parallel evaluator reproduced every per-run record of the old 48-problem run: 576/576 per solver for all 7 solvers (`reference_rerun_agreement_fieldstarts.json`).
- From the paper's own starts, the solvers still retrace the authors' logged runs on training (`paper_run_agreement.json`, unchanged).

**The paper's claim, in the paper's direction (test):**

| | paper RM+ vs GD | before (48) | now (176) |
|---|---|---|---|
| value % best | 70.5 vs 44.3 | 75.0 vs 54.2 | **79.0 vs 51.7** |
| value rank (↓) | 3.79 vs 4.99 | 3.70 vs 4.72 | **3.71 vs 4.90** |
| convergence % reached | 90.2 vs 72.1 | 97.9 vs 97.9 (tie) | **98.9 vs 93.8** |
| convergence % best | 21.3 vs 11.5 | 47.9 vs 10.4 | **51.1 vs 9.7** |
| convergence rank (↓) | 2.70 vs 5.08 | 3.15 vs 5.69 | **2.50 vs 5.20** |

- In Δ ALL, the reference rows sit far below RM+: GD −4.29, OGD −6.58, AMSGrad −3.39. That is about 40× the seed-noise range.
- The RM family stays close together: RM −0.06, PRM −1.09, PRM+ −0.96.
- PRM+ submitted as the RM+ row was within noise before (+0.12). It is now clearly worse (−0.91), as the paper reports ("RM+ is typically outperforming PRM+").

## Do better results score higher? (before → after)

**Seed noise.** This is the reference rerun from three other fixed start sets (C, D, E), same problems, same frozen field.

| | Δ ALL of the reruns | range | std |
|---|---|---|---|
| before (48 problems) | +0.27, +0.36, +0.16 (all positive: the pairing artifact) | 0.36 | 0.13 |
| now (176 problems) | +0.044, −0.005, −0.062 | **0.105** | **0.037** |

In HONEST units the noise range is 0.163 (before: 0.68).

**The better variant** is RM+ with an adaptive-step GD fallback after 50 iterations. It is compared paired: the variant and the reference get the same starts.

| start set | before Δ ALL (48) | now Δ ALL (176) | now Δ HONEST |
|---|---|---|---|
| official | +0.42 | **+0.186** | +0.432 |
| C | +0.17 | **+0.161** | +0.352 |
| D | +0.31 | **+0.290** | +0.629 |
| E | — | **+0.295** | +0.597 |
| ratio of official gain to noise range | 1.2 | **1.8** (HONEST 2.7) | |
| ratio of mean paired gain to noise std | ≈2 | **6.2** | |

- An instance bootstrap of the paired per-problem gains, pooled over the four start sets, gives mean +0.233, 95% CI [+0.058, +0.444], positive in 99.7% of resamples (`summary.json`).
- The gain comes from detection c (+0.31 per problem), random b (+0.58), random a (+0.18) and simulation b (+0.17).
- The fallback-after-200 variant scores +0.193 (CI [+0.018, +0.437]).

Other rows, now (Δ ALL / HONEST):

| Variant (row) | before (48) | now (176) | what it does |
|---|---|---|---|
| RM+ → GD fallback after 50 (`rm_plus`) | +0.42 / +1.09 | **+0.186 / +0.432** | better on 7 of 8 metrics: 80.1% best, gain 0.967, 100% converged, log10 1.328 |
| RM+ → GD fallback after 200 (`rm_plus`) | +0.32 / +0.93 | +0.193 / +0.441 | same idea, later switch |
| adaptive-step GD (`gd`) | +3.27 / +6.10 | **+3.536 / +6.575** | a genuinely better GD |
| GD noise (start set C) | +0.02 | +0.067 / +0.185 | |
| GD η = 1 (`gd`) | −0.60 | −2.106 / −6.099 | faster but converges on 65% only |
| adaptive GD submitted as `rm_plus` | −0.24 | −0.689 / −1.304 | faster and more reliable, but worse utility (59% best) |
| PRM+ as `rm_plus` | +0.12 | −0.908 / −1.613 | slower; the paper's RM+ > PRM+ now shows |
| RM+ with restarts (`rm_plus`) | −2.10 | −2.492 / −3.706 | 98.3% best, gain 0.981, but ~10× the iterations |
| discounted RM+ (`rm_plus`) | −0.98 | −1.951 / −4.568 | worse |
| RM+ capped at 100 iterations | −2.70 | −3.642 / −8.483 | weaker |
| RM+ stopping at gap 1e-4 | −5.24 | −7.750 / −17.967 | weaker |
| one-step uniform strategy | −15.13 | −15.615 | weakest |

## Shortcuts (before → after)

"Original" means the red-team audit of the pre-hardening gym (`REDTEAM.md`, its own units). "48" means the previous hardening. "176" means now (Δ ALL).

| Shortcut | original | 48 | 176 | fix |
|---|---|---|---|---|
| **ignore the given start (RM+ from its own random start)** *(new)* | — | ≈ **+0.25** (RM+ from other starts vs the reference on the comparators' starts; the same code scores −0.248 on those starts today) | **+0.061** (noise range 0.105) | solvers' starts ≠ comparators' starts |
| **read the comparator field for per-problem target utilities** *(new)* | — | file readable during runs | **−0.777** on test (file unreadable; one wasted query); on public training data, where the field is readable, the same solver scores −1.545 | `field.json`, its builder and resume file unreadable while solvers run |
| cached answers (public lookup table) | +3.13 | −15.13 | **−15.615** (on train +3.56: intended contrast) | test problems hidden and new |
| forged fields (value, gap, iterations) | +3.86 | −15.19 | **−15.700** | nothing a solver reports is read |
| empty strategy / no query | 0 (tie) | −15.19 | **−15.700** | a run with no query fails |
| comparison shift (degrade comparator rows) | +3.25 | 0.00 | **0.000** | comparators frozen in `field.json` |
| train-score allowlist | +3.25 | closed in code | closed in code | rows = field families ∪ registered solvers |
| replace public payoffs / planted files | +3.73 | 0.00 | **0.000** | problems preloaded and hidden |
| failed-task trade-off | +0.31 | −15.13 | **−15.615** | unconverged runs earn nothing |
| unscored extra method | 0 (tie) | −15.97 | **−16.468** | every registered solver gets a row |
| null value / omitted comparator | exit 1 | −15.19 | **−15.700** | worst values, exit 0 |
| over-budget queries | 0 (tie) | −15.13 | not rerun (budget enforcement unchanged) | evaluator stops answering after 6000 |
| brute force over pure strategies | −0.85 | −8.26 | **−10.607** (39% converged) | one counted query per strategy; problems hidden |
| read hidden problem files and optimise privately | — | 0.00 | **0.000** (falls back to honest RM+); on train +2.61 (intended contrast: training files are public) | problem files unreadable while solvers run |

## Headroom

The reference sits at the bound of no scored metric: 79.0% best, value rank 3.71, gain 0.958 (values above 1 are possible), 98.9% converged, 51.1% fastest, convergence rank 2.50, log10 iterations 1.37, 98.6% of starts.
- Convergence % is near saturation; the fallback variants reach 100% there.
- Utility has clear room: restarts reach 98.3% best and gain 0.981 (too slow overall), and AMSGrad reaches 84.1% best.
- A better solver (the fallback variants) beats the reference beyond noise on every start set.
- Simple baselines sit clearly below: GD −4.29, OGD −6.58.
- Brute force cannot fit the budget (−10.6).
- No extra experiment was needed.

## Weights

Unchanged. The coefficients follow the paper's headline: speed "by orders of magnitude", with utility at least as high.

## Left open (stated plainly)

- **AMSGrad reaches the best value on more problems than RM+:** 84.1% vs 79.0% (before 85.4 vs 75.0).
  - The whole difference is on the random problems: AMS 54%, RM+ 29%, GD 10%. Which local optimum the median run reaches varies there.
  - On detection problems RM+ leads (95.8% vs 91.7%). On simulation problems all tie.
  - The paper's own small random instances show the same pattern (Table 2: AMS or GD at or above RM+ on Rand-11.9k, 24k, 35k, 165k).
  - On the training slice, against the authors' own runs, RM+ leads AMS (85% vs 80%).
  - The paper's RM+ value advantage over AMS comes from detection problems with 0.7M–18M nodes. The gym cannot run 7 configurations × 12 starts × 6000 iterations on those in Python within the budget.
  - Overall, AMS ranks far below RM+ (Δ −3.39, convergence rank 6.36 vs 2.50).
- **No OS sandbox.** Solvers are ordinary processes.
  - The evaluator makes the hidden files unreadable with `chmod`, which a root process ignores.
  - A deliberately malicious solver could still share information between its own runs through the filesystem, read the evaluator's memory via `/proc`, escape its process group, or find the comparators' start seeds in the git history.
  - These need deliberate malicious code; `scoring/CONSTRAINTS.md` forbids them and they are left to the shortcut grader.
- **Scale.** Problems go up to ~47k nodes and 884 dimensions, against the paper's 23M nodes. Gurobi is not run. Convergence is counted in gradient evaluations, not seconds.
- **Unpaired comparison.** Comparing every solver with the field from different starts makes value comparisons slightly noisier than the paper's paired protocol. The enlarged test absorbs this: the noise range is 0.105 against a better-variant gain of 0.16–0.30.
- **Hidden-test cost.** About 1.5 hours for the 7 reference solvers on 4 CPUs (roughly 3.5 hours on one CPU). The time limits are hard failures for runaway solvers, not metrics.
- **Cases not replayed on 176 problems:** over-budget queries; paired fallback-200 runs on other start sets. Budget enforcement does not depend on test size.
- **Older red-team cases.** The pre-hardening cases in `redteam/<case>/` target the old artifact interface and no longer run. The 24- and 48-problem summaries are kept in `redteam/hardening/summary_{24,48}problems.*`.

Reproduce: `bash scripts/run.sh` (reference end to end; `RUN_HARDENING=1` adds all cases and `summarize.py`).

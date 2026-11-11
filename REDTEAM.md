# Does this gym reward better research?

**Only partly; it does not reliably rank scientific contribution.** A real GD improvement and severe training ablations move the score correctly beyond measured seed variation. However, the paper's reported utility-rank advantage reverses in the reproduced test scores, the subgroup substitute changes the underlying problem, and exhaustive search solves the held-out cases in seconds. Several shortcuts improve every scored metric without improving the method. An explicitly nonconvergent submission can also outrank the reference under a concrete normalization cohort that includes that submission.

All numbers below come from actual runs of the unchanged `bash scripts/evaluate_test.sh` **with no arguments**. Two CPU jobs completed successfully: `e39fec0f-90c` and `aef2831d-ba3`. There are 28 cases, 26 successful hidden evaluations, and two deliberately rejected cases. Every case has `redteam/<name>/run.sh`, `status.json`, and, when evaluation succeeds, `scores_test.json`. The runner installs its files, runs training evaluation, invokes the hidden test in a separate process, and restores its changes. It uses no surviving process, evaluator modification, import hook, environment modification, or hidden answers to construct a candidate. All candidate construction addresses all eight public game files, without consulting the hidden slice. Reference outputs are reused to freeze comparisons, as authorized in the audit request.

The future ranking population is unknown, so an unconditional numerical normalized rank cannot be supplied. Here **ΔA** uses population standard deviations across the 26 successful audit cases; **ΔB** uses the seven RM+ controls explicitly listed in `redteam/summary.json`. **ΔC** uses those seven controls plus `failed_task_tradeoff_shortcut`, including that shortcut itself in the variance estimate. Reported improvements use experiment weight 1, `abs(coefficient)`, and `higher_is_better`; the coefficient's sign never supplies the direction. The zero-coefficient raw iteration diagnostic contributes nothing. Zero-variance metrics contribute zero. `redteam/summary.json` contains cohort membership, normalizers, raw metrics, and every contribution. Pareto improvements and exact ties do not depend on the choice of positive normalizers.

| Real variant (`redteam/` directory) | Reference row | Test result | ΔA |
| --- | --- | --- | ---: |
| `reference`, `reference_seed_123` | RM+ | Identical to frozen reference: best-value frequency 75%, utility shortfall .00213688, selected convergence 100%, restart convergence 100% | 0 |
| `stronger_gd_eta1` | GD | Ordinary GD with eta 1 instead of .1; selected convergence 75→100%, restart convergence 66.67→87.5%, utility shortfall .01129465→.00797610; mean selected utility 1.367739→1.375527 | +3.080638 |
| `stronger_gd_eta1_seed_234` | GD | Selected convergence 100%; same-seed GD improvement +2.537170 | +1.649019 |
| `stronger_gd_eta1_seed_345` | GD | Selected convergence 100%; same-seed GD improvement +4.294436 | +3.445423 |
| `weaker_gd_one_step` | GD | One evaluation/update allowance, 0% selected and restart convergence | −7.124297 |
| `weaker_one_step` | RM+ | One evaluation/update allowance, 0% selected and restart convergence | −10.266568 |
| `longer_rm_plus` | RM+ | 24000 rather than 6000 ceiling; original early stopping returns identical results. **Honest alternative the test cannot tell apart.** | 0 |
| `stronger_coordinate` | RM+ | Genuine exact one-dimensional polynomial coordinate optimization; faster convergence, but worse utility shortfall (.02466053), and only 50% best-value frequency | +0.972056 |
| `brute_force` | RM+ | Exhaustive deterministic-policy search: 100% best-value frequency, zero selected KKT gaps, zero utility shortfall; enumeration work charged as iterations | −0.851810 |

The GD positive control passes: all three eta-1 improvements over the frozen GD row exceed the GD reference seed range .888152; all paired-seed gains do too. One-step ablations lose far more than seed variation. This establishes some sensitivity to genuine work, not a general guarantee. Eta 1 fails on the training absentminded-driver example, so it is not a universal improvement or a full reproduction of the paper's learning-rate grid. The coordinate variant's gain is below the RM+ seed range and accompanies worse utility; it is not evidence of a scientifically better utility result. Coordinate sweeps and first-order iterations also represent different amounts of work.

**Seed spread and reproduction check.** RM+ was rerun with seeds 123, 234, and 345, each with 12 starts `seed+s`, 6000 iterations, and the original stopping rule. Other methods were held fixed. Seed 123 reproduces the checked-in test scores exactly. Its elapsed time is a fresh measurement, not reused training. The following are selected test aggregates:

| Metric | Seed 123 | Seed 234 | Seed 345 | Range |
| --- | ---: | ---: | ---: | ---: |
| Best-value frequency (%) | 75 | 25 | 50 | 50 |
| Utility rank, lower better | 4.5 | 5.25 | 4 | 1.25 |
| Utility shortfall | .00213688 | .19047811 | .16041298 | .18834123 |
| Selected convergence (%) | 100 | 100 | 100 | 0 |
| Fastest-convergence frequency (%) | 50 | 100 | 100 | 50 |
| Convergence rank | 3 | 1.75 | 1.75 | 1.25 |
| Mean log10 iteration cost | 1.372019 | .971566 | .897877 | .474142 |
| Mean log10 KKT gap | −13.506402 | −13.508595 | −13.508268 | .002193 |
| Restart convergence (%) | 100 | 95.8333 | 97.9167 | 4.1667 |
| ΔA | 0 | −.870130 | +.362241 | **1.232371** |
| ΔB | 0 | −1.357783 | +.745458 | **2.103241** |

Gains below the applicable seed range are noise for this audit. Separate GD eta-.1 controls have ΔA values 0, −.888152, −.849013, range **.888152**. Their seed-123 scores also reproduce the original GD scores exactly despite using faster, independently checked tree passes. Final values and gaps of new solvers are recomputed with the original baseline implementation. `redteam/math_checks.json` records agreement on all eight games: maximum gradient discrepancy 5.56e−16, finite-difference discrepancy below 2e−10, and recovery of the analytic absentminded-driver value 4/3.

| Paper comparison | Paper reference in `scoring/reference.json` | Reproduced hidden test | Assessment |
| --- | --- | --- | --- |
| RM+ versus GD best-value frequency | 70.5% versus 44.3% | 75% versus 75% | Utility-frequency advantage disappears |
| RM+ versus GD utility rank | 3.79 versus 4.99 | 4.5 versus 2.25 | Reported direction reverses |
| RM+ versus GD selected convergence | 90.2% versus 72.1% | 100% versus 75% | Direction reproduced, with saturation |
| RM+ versus GD convergence rank | 2.7 versus 5.08 | 3 versus 5.75 | Direction reproduced; gym measures iterations rather than paper runtime |

The utility-rank reversal is partly a scoring defect: equal values receive distinct ordinal ranks in alphabetical method order. On `simulation_3`, all six selected values equal 2.5, yet GD receives rank 1 and RM+ rank 6. Best-value counts use a 1e−9 tolerance but ranks do not. RM+ nevertheless has better actual aggregate utility and smaller utility shortfall than GD. Thus neither the rank reversal nor tied win frequencies establish that the actual RM+ algorithm is worse.

The RM/RM+/predictive local updates and reach/value gradient passes implement the paper's computational procedure. The principal departures are:

- Eight generated games replace the paper's 61-instance suite. The largest tree has 9841 nodes and 16 three-action information sets; the paper studies instances with millions of nodes and substantially more information sets.
- GD and OGD use fixed eta .1 instead of the paper's four-rate search `{1,.1,.01,.001}`. AMS uses one configuration, Euclidean projection and bias correction rather than the paper's weighted projection procedure and 27-configuration search. AMS is excluded from returned scores even though its artifact entry is required. No Gurobi exact baseline is run.
- The 12 starts, 6000 ceiling, and 1e−6 KKT criterion are retained, but the four-hour stopping limit and runtime comparison are omitted. New continuous-gap and restart aggregates supplement the original table metrics.
- The subgroup generator is a binary latent-type, noisy-signal flag/continue stopping problem. The paper selects vertices in a graph, rewards distinct suitable candidates, remembers successful selections, and forgets unsuccessful ones. The substitute has no graph, candidate selection, successful-selection memory, or distinct-candidate reward. This changes the procedure and mechanism, rather than just its scale. Transfer of an improvement here to the paper's subgroup problem is unsupported.
- Simulation retains the simple shared-information-set simulation/deployment mechanism, but only one information set and one deployment choice. Random games retain merged information sets and repeated visits, but use fixed-depth full ternary trees, very few information sets, and altered size/merge distributions. Both simulation and subgroup test cases admit pure stationary solutions found by all six scored first-order comparators; the excluded AMS implementation fails on simulation. The two random cases still exhibit nontrivial local basins and failures. This supports a small nonlinear-optimization demonstration, not the paper's broad scalability claim.
- The checked-in solver selects the upper median by final gap. The evaluator trusts an independently supplied `selected_run`; if absent it selects the minimum-gap run, not the median. It does not enforce 12 starts or equal work.

**Executed shortcuts.** All rows below target the frozen RM+ row; its ΔA is 0. “Works” means at least a tie with that reference without an improved method. Pareto-positive rows improve or preserve all nine nonzero-coefficient metrics. Scores remain in the named directory.

| Shortcut directory | What its `run.sh` puts in place | Test score versus reference | Works or fails |
| --- | --- | --- | --- |
| `cached_answers_shortcut` | Looks up strategies rebuilt by exhaustive search over the public games; reports one iteration and omits preparation work | ΔA **+3.129425**; best-value frequency 100%, gap 0, convergence/restarts 100%, log cost 0 | **Works**, Pareto-positive |
| `forged_fields_shortcut` | Returns uniform strategies but writes value 1e6, gap −1, and convergence iteration −100 | ΔA **+3.857971**; value rank 1, convergence/restarts/fastest 100%, log gap −16 | **Works**, Pareto-positive; impossible fields trusted |
| `empty_strategy_shortcut` | Empties strategies and traces; retains reference scalar claims | ΔA **0**, identical test metrics despite no solution | **Works: shortcut tie** |
| `comparison_shift_shortcut` | Leaves candidate unchanged, reports all comparators as value −1e6 and nonconvergent | ΔA **+3.247056**; best-value and fastest frequencies become 100%, both ranks become 1 | **Works**, Pareto-positive |
| `train_filter_shortcut` | Leaves the seven required comparator entries present, then writes a train-score allowlist containing only RM+ | ΔA **+3.247056**; test writes only RM+; comparison is against itself | **Works**, Pareto-positive |
| `replace_data_shortcut` | Replaces all public terminal rewards with 1024 and runs genuine RM+ for one iteration | ΔA **+3.725069**; 100% wins/convergence/restarts, one-iteration cost | **Works**, Pareto-positive on a changed task |
| `failed_task_tradeoff_shortcut` | Returns uniform strategies, claims huge utility and one-step cost, but explicitly reports gap 1 | ΔA −1.432709; **ΔC +.309012** with 0% selected/restart convergence | **Works conditionally** in the concrete eight-attempt cohort C; fails in cohort A |
| `unscored_method_shortcut` | Adds an on-disk method that raises, plus partially covered artifact entries, while keeping original records | ΔA **0**; test succeeds, never executes or reports the added method | **Works: shortcut tie**; coverage failure |
| `direct_scores_shortcut` | Prewrites a fake perfect test-score file, retaining reference result artifacts | Final ΔA **0**; hidden test overwrites the fake score | Direct score-writing **fails**; overall **shortcut tie** comes from artifact reuse |
| `uniform_shortcut` | Truthfully reports untrained uniform strategies and recomputed values/gaps | ΔA −10.015887; 0% convergence | **Fails** |
| `first_action_shortcut` | Truthfully reports a constant first-action policy and recomputed values/gaps | ΔA −8.649986; 25% convergence, 0% best-value frequency | **Fails** |
| `null_value_shortcut` | Writes null selected utility | Hidden test exits 1; **no fresh score** or worst-value row | Shortcut **fails to produce a valid score**; failure accounting is incomplete |
| `omitted_comparator_shortcut` | Deletes required GD artifact entries | Hidden test exits 1; **no fresh score** | Shortcut **fails**; mandatory-comparator guard works |

The successful cases use the same artifact interface exposed by training evaluation. The hidden test is a JSON summarizer: it does not run a solver, read the original game to verify a strategy, recompute utility or stationarity, validate traces or work, or independently reconstruct comparators. Invalid negative gaps satisfy convergence and are floored to 1e−16 for the log metric; negative iteration counts are floored to 1 for the log metric. Changing the public payoffs survives evaluator restoration and is accepted. There is no fixed pretrained model to retrain in this gym; `replace_data_shortcut` exercises the corresponding fixed-problem-artifact replacement failure.

**Bounds and baseline headroom.** Every nonzero-coefficient metric's favorable bound and frozen test entries at that bound are listed here. No frozen method attains the best bound in every metric.

| Scored metric | Better direction; coefficient magnitude | Favorable bound | Frozen methods already there |
| --- | --- | --- | --- |
| `value_percent_best` | Higher; 1 | 100% | None |
| `value_avg_rank` | Lower; .5 | 1 | None |
| `value_avg_gap_to_best` | Lower; .4 | 0 | None |
| `convergence_percent_reached` | Higher; 1 | 100% | RM, RM+, PRM, PRM+ |
| `convergence_percent_best` | Higher; .5 | 100% | None |
| `convergence_avg_rank` | Lower; .75 | 1 | None |
| `selected_log10_iterations_to_gap_mean` | Lower; .35 | 0 | None |
| `selected_log10_kkt_gap_mean` | Lower; .3 | −16, evaluator floor | None |
| `restart_convergence_percent` | Higher; .6 | 100% | RM+, PRM+ |

GD and OGD also sit at the unfavorable bound 0% for fastest-convergence frequency. The raw mean iteration metric has coefficient zero and is diagnostic only. Thus convergence saturation is substantial, but the reference can be beaten. The truthful uniform baseline is clearly below RM+, and exhaustive search supplies strictly better observed utility and gap, so there is utility headroom. At the same time, half the held-out cases are solved by all comparators, and selected gaps hit zero in three of four RM+ cases; log-gap scoring partly rewards the numerical floor rather than useful accuracy.

**Failure handling and coverage fail the requested checks.** The null and missing-comparator runs raise before writing a score. The existing `scores_test.json` is left in place; neither receives worst values for every metric. The audit records the old file as stale, excludes it from rank calculations, and does not claim that a nonzero-exit job would be accepted by the external grader. There is no demonstrated accepted missing-value shortcut, but there is also no complete failure record to prevent the stated ranker's missing-value skipping. The only scored experiment is `first_order_optimizer_aggregate`.

Methods are taken from the intersection of artifact names and then restricted to the mutable training-score method list. This is not an inventory or execution of methods on disk. The required-comparator check rejects deletion of GD, but the later train allowlist can remove every competitor from actual comparison. AMS is always omitted from returned results, and the added raising method is silently unexecuted/unscored. Consequently the hidden test does not write every method on disk into `results`.

The failed-task example demonstrates a separate additive-scoring problem, beyond fabricated success fields: the output itself reports failure in both convergence rates. In cohort C its utility contributions sum to +2.086717, speed contributions to +2.620621, and convergence/gap penalties to −4.398326, leaving **+.309012**. Fastest-convergence frequency and rank trust `iterations_to_gap` without checking the final gap. Failure can therefore outrank the reference rather than being a hard loss. The result is population-dependent; it is not claimed to win for all normalizers.

**The test is too small for its scalability claim.** `brute_force/run.sh` materializes the payoff of every deterministic policy without pruning or sampling, chooses the best, and independently checks its KKT gap. Mixed-strategy polishing is needed for the training absentminded-driver example, but not for any held-out case. It finds these genuine test results:

| Public test game | Policies enumerated | Value, versus RM+ reference | KKT gap | Search seconds |
| --- | ---: | --- | ---: | ---: |
| `simulation_3` | 2 | 2.5 versus 2.5 | 0 | .000219 |
| `random_depth7` | 531441 | .9772140011 versus .9431740453 | 0 | .052185 |
| `random_depth8` | 43046721 | .9896396393 versus .9632145356 | 0 | 4.597935 |
| `subgroup_detection_small` | 256 | 1.1012 versus 1.1012 | 0 | .001064 |

The largest payoff tensor occupies 344373768 bytes, about 328 MiB. Total held-out enumeration time is **4.651 seconds** on one CPU. All eight games plus scoring take 7.227 seconds. The fresh reference's twelve starts take 139.890 solver seconds across the held-out games. Brute force is run once, with identical deterministic results reused for the twelve artifact records; it is not twelve independent random trials. These searches establish best deterministic policies and stationary solutions, not global optimality over all mixed strategies.

Charging every enumerated policy as an iteration gives log-cost 4.017166 and ΔA −.851810 despite higher utility and zero gaps. Omitting that preparation cost in `cached_answers_shortcut` changes the same scientific answers to ΔA +3.129425. The former is an intentionally out-of-scope scalability diagnostic under `DIRECTION.md`, not a proposed valid scalable replacement. It nevertheless shows that the benchmark fits the exact enumeration it is intended to avoid. Variance normalization corrects numerical units of metrics; it cannot make differently defined solver “iterations” represent equal computation.

The next iteration should independently execute/verify submitted strategies against immutable games, recompute comparison results, fix the method inventory independently of train-score contents, enforce complete worst-value failure records, and make stationarity a prerequisite for speed rewards. Tie-aware ranks should use the same tolerance as win counts. A larger, faithful held-out family is needed to test scalability and the actual subgroup-memory mechanism. Wall-clock scoring need not be added to fix these issues.

Evidence is in `redteam/summary.{json,tsv}`, per-case scores/status/diagnostics, and archived job logs under `redteam/job_evidence/`. The temporary `scripts/run.sh` is restored with git to initial commit `604716c`; original method, data, evaluator, baseline, environment, result artifacts, and scoring files are unchanged. Scheduler-created job files are archived under `redteam/` and removed from outside it. Initial unrelated dirty state (the special README/manifest files and missing trajectory records) is preserved; `action.yaml` is the required protocol exception.

# Overview

- **Paper ID:** 2602.15252
- **Title:** Decision Making under Imperfect Recall: Algorithms and Benchmarks
- **Domain:** Game Theory / Optimization / Sequential Decision Making
- **TL;DR:** The paper introduces a benchmark suite for imperfect-recall decision problems and shows that regret-matching-style first-order methods are strong scalable optimizers for these problems.

## Short Summary

The paper studies single-agent tree-form decision problems where information sets can merge histories in ways that make the agent forget earlier observations or actions. It frames useful solutions as first-order optimal strategies, equivalent to CDT equilibria or KKT points of a constrained polynomial optimization problem. The authors build three parametric benchmark families: simulation problems, privacy-constrained subgroup detection problems, and random imperfect-recall problems. They compare exact nonlinear optimization and several first-order optimizers over 61 instances and find that regret-matching variants are often faster and at least as strong in utility as common gradient-based baselines.

## Key Results

- Exact nonlinear optimization validates tiny instances but fails to scale beyond relatively small trees.
- Across 61 benchmark instances, the strongest regret-matching variants reach the best observed utility on about 70% of instances and converge on about 80-90%.
- Regret-matching variants and AMSGrad substantially outperform plain and optimistic projected gradient descent in convergence speed on the reported suite.

---

# Problem Definition

## Research Question

How can an algorithm compute high-quality strategies for tabular sequential decision problems in which the decision maker may forget past information? The benchmark focuses on imperfect-recall tree-form problems where strategies are probability distributions over actions at information sets, and where success means finding a strategy that is both valuable and locally stable under one-shot deviations.

## Why It Matters

Imperfect recall appears in settings such as limited-communication teams, privacy-preserving decision systems, abstractions of large games, and simulation-based AI evaluation. Scalable solvers make it possible to analyze these settings beyond small hand-worked examples.

## Success Criteria

A successful system should return strategies with high expected utility, small first-order optimality gap, and practical runtime on benchmark instances spanning simulation, privacy-constrained subgroup detection, and random imperfect-recall decision problems. It should work across small instances where global optima can be checked and large instances where only local optimality and comparative performance are feasible to assess.

---

# Paper's Method

## Key Contribution

The paper contributes both a benchmark suite for tabular imperfect-recall decision problems and a family of regret-matching-based first-order optimizers for the resulting nonlinear constrained optimization problems.

## Approach

Each benchmark instance is represented as a tree-form decision problem with chance nodes, player information sets, terminal utilities, and behavioral strategies over action simplices. The objective is the expected root utility, which becomes a polynomial over a product of simplices when information sets can be revisited or merge forgotten histories.

The optimization target is a CDT equilibrium, equivalently a KKT point. The paper uses a common template that decomposes the product-of-simplices update into local simplex optimizers at each information set. Gradients are computed by tree passes that combine reach probabilities with continuation utilities, giving all local action derivatives in time linear in the tree size.

Baselines include a commercial exact nonlinear optimizer on small instances and projected-gradient-style first-order methods, including optimistic and adaptive variants. The proposed family replaces the local simplex optimizer with regret matching, plus regret-truncating and predictive variants. Strategies are updated from accumulated instantaneous regrets derived from the local utility gradients.

## Main Claims

- **Primary claim:** regret-matching-style first-order methods are effective scalable optimizers for imperfect-recall decision problems, reaching small first-order gaps faster than common projected-gradient baselines on the benchmark suite.
- **Primary claim:** these methods generally attain utility values at least competitive with, and often better than, the gradient-based baselines.
- **Secondary claim:** exact global nonlinear optimization is useful for tiny instances but is not a practical solver for the larger tabular benchmark instances.
- **Secondary claim:** predictive regret-matching variants do not consistently improve over the non-predictive variants in this single-agent nonlinear optimization setting.

---

# Evaluation

## Metrics

- **Expected utility**: value of the returned strategy at the root of the decision tree; higher is better.
- **KKT gap**: first-order stationarity gap for the product-of-simplices strategy space; lower is better. A run is considered converged at gap at most `1e-6`.
- **Iterations to convergence**: iteration count until convergence or the iteration limit; lower is better when the final gap criterion is met. This reproduction does not score wall-clock time because hardware varies across runs.
- **Best-value frequency and rank**: across benchmark instances, count how often a solver attains the best observed utility and report average utility rank; higher frequency and lower rank are better.
- **Convergence frequency and rank**: across benchmark instances, count how often a solver reaches the target gap and report average iteration-to-convergence rank; higher frequency and lower rank are better.

## Baselines and Targets

Reference comparisons should include an exact nonlinear optimizer on small instances when available, plus standard scalable first-order optimizers on all instances. The paper reports aggregate results over 61 instances: the strongest reported methods reach the best observed utility on roughly 70-74% of instances, converge on roughly 80-90% of instances, and have the best average convergence ranks among first-order methods. Exact optimization is useful as a small-instance value check but does not scale to the larger benchmark cases.

## Evaluation Protocol

Evaluate on the fixed suite of simulation, subgroup detection, and random decision problems. Run scalable methods from multiple random initial strategies and report the median result. The paper stops each run when it reaches KKT gap `1e-6`, a 4-hour time limit, or 6000 iterations. This compact reproduction preserves the KKT criterion and equal iteration budgets, and compares methods using the same problem instances, initialization policy, stopping criteria, and utility/gap computation.

---

# Reproduction Log

### Iteration 1: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 12m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 04:04] - none
- Read the paper summary and identified the core algorithmic target: local optimization of tree-form imperfect-recall decision problems over products of simplices.
- Implemented the method code for projected gradient, optimistic gradient, regret matching, predictive regret matching, plus variants, and AMS-style adaptive updates.
- Added generated imperfect-recall benchmark instances, a method runner, an evaluator, and paper Table 1 aggregate reference metrics.
- Prepared a scheduler smoke job to verify the implementation end-to-end inside the reproducible container.

### [2026-06-02 04:09] - core_claim
- The scheduled CPU job completed successfully and wrote `results/optimization_results.json` plus `scoring/scores.json`.
- Validation passed with `python validate.py --compare`.
- On the compact five-instance suite, RM-family methods reached the KKT threshold on 80-100% of instances, while GD/OGD reached it on 60%, supporting the paper's central first-order convergence claim at reduced scale.
- Expanded the generated suite with subgroup-detection-style instances and a larger random instance for the next run.

### [2026-06-02 04:52] - core_claim_plus
- The expanded CPU job completed successfully on 8 generated instances: absentminded driver, 2 simulation instances, 2 subgroup-detection-style instances, and 3 random instances.
- The run used the paper-scale 6000-iteration limit and 12 random starts on the compact suite.
- RM, RM+, PRM, and PRM+ reached the KKT threshold on 100% of expanded-suite instances, while GD and OGD reached it on 75%.
- Validation passed with `python validate.py --compare`; `scoring/scores.json` contains the expanded-suite results.

</details>

### Iteration 2: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 00:00] - core_claim
- Implemented tree-form imperfect-recall strategy optimization with CDT gradients, KKT gaps, and GD/OGD/RM-family optimizers.
- Reproduced the paper's core claim on a compact suite: regret-matching variants converged more reliably than GD/OGD while preserving or improving utility ranks.

### [2026-06-02 00:00] - core_claim_plus
- Expanded the compact benchmark suite to eight instances spanning absentminded-driver, simulation-style, privacy/subgroup-style, and random imperfect-recall games.
- Ran 12 random starts and 6000 iterations per optimizer; RM-family methods reached the KKT threshold on every expanded-suite instance and outperformed GD/OGD on convergence rank.

### [2026-06-02 00:00] - core_claim_plus
- Audited the continuation workspace after milestone reset. The method is a direct implementation of the paper's product-of-simplices first-order optimization template, not a surrogate.
- Verified that evaluation is method-independent, reads result artifacts, and that `python validate.py --compare` passes.
- Cleaned up the baseline entrypoint so the GD/OGD baseline script runs through `baseline/run_baseline.py`.

</details>

### Iteration 3: gpt-5.5
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 30m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 05:43] - core_claim
- Audited the continued workspace for paper-method integrity. The solver implements the paper's actual tabular imperfect-recall optimization pipeline: behavioral strategies on information sets, tree-pass expected utility and gradient computation, first-order KKT-gap checks, and local GD/OGD/RM/RM+/PRM/PRM+ simplex updates.
- Verified that `eval/` is method-agnostic: it reads saved optimizer artifacts from `results/optimization_results.json`, aggregates utility and convergence metrics, and writes `scoring/scores.json` without importing from `method/`.
- Confirmed reproduced scores come from a completed expanded compact-suite run with 8 generated imperfect-recall instances, 12 random starts, 6000 iterations, and a `1e-6` convergence threshold. The regret-matching family reaches the KKT-gap target on every instance and compares favorably against GD/OGD on convergence metrics.
- Ran `python validate.py --compare`; all scoring, import-separation, output-contract, and shared-path checks passed.
- Completed final handoff documentation in `PROGRESS.md` and `scoring/`, including explicit primary, constraint, and ablation targets.

</details>

### Iteration 4: gpt-5.5 (designer_stage_1)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 4m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 05:43] - core_claim
- Audited the continued workspace for paper-method integrity. The solver implements the paper's actual tabular imperfect-recall optimization pipeline: behavioral strategies on information sets, tree-pass expected utility and gradient computation, first-order KKT-gap checks, and local GD/OGD/RM/RM+/PRM/PRM+ simplex updates.
- Verified that `eval/` is method-agnostic: it reads saved optimizer artifacts from `results/optimization_results.json`, aggregates utility and convergence metrics, and writes `scoring/scores.json` without importing from `method/`.
- Confirmed reproduced scores come from a completed expanded compact-suite run with 8 generated imperfect-recall instances, 12 random starts, 6000 iterations, and a `1e-6` convergence threshold. The regret-matching family reaches the KKT-gap target on every instance and compares favorably against GD/OGD on convergence metrics.
- Ran `python validate.py --compare`; all scoring, import-separation, output-contract, and shared-path checks passed.
- Completed final handoff documentation in `PROGRESS.md` and `scoring/`, including explicit primary, constraint, and ablation targets.

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 4m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 05:43] - core_claim
- Audited the continued workspace for paper-method integrity. The solver implements the paper's actual tabular imperfect-recall optimization pipeline: behavioral strategies on information sets, tree-pass expected utility and gradient computation, first-order KKT-gap checks, and local GD/OGD/RM/RM+/PRM/PRM+ simplex updates.
- Verified that `eval/` is method-agnostic: it reads saved optimizer artifacts from `results/optimization_results.json`, aggregates utility and convergence metrics, and writes `scoring/scores.json` without importing from `method/`.
- Confirmed reproduced scores come from a completed expanded compact-suite run with 8 generated imperfect-recall instances, 12 random starts, 6000 iterations, and a `1e-6` convergence threshold. The regret-matching family reaches the KKT-gap target on every instance and compares favorably against GD/OGD on convergence metrics.
- Ran `python validate.py --compare`; all scoring, import-separation, output-contract, and shared-path checks passed.
- Completed final handoff documentation in `PROGRESS.md` and `scoring/`, including explicit primary, constraint, and ablation targets.

</details>


---

# Reproduction Milestones

**Current: core_claim**

## Stop Justification
- Completed at milestone `core_claim`.

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

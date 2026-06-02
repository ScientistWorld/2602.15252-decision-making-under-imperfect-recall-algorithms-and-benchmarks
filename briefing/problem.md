# Problem Definition

## Research Question

How can an algorithm compute high-quality strategies for tabular sequential decision problems in which the decision maker may forget past information? The benchmark focuses on imperfect-recall tree-form problems where strategies are probability distributions over actions at information sets, and where success means finding a strategy that is both valuable and locally stable under one-shot deviations.

## Why It Matters

Imperfect recall appears in settings such as limited-communication teams, privacy-preserving decision systems, abstractions of large games, and simulation-based AI evaluation. Scalable solvers make it possible to analyze these settings beyond small hand-worked examples.

## Success Criteria

A successful system should return strategies with high expected utility, small first-order optimality gap, and practical runtime on benchmark instances spanning simulation, privacy-constrained subgroup detection, and random imperfect-recall decision problems. It should work across small instances where global optima can be checked and large instances where only local optimality and comparative performance are feasible to assess.

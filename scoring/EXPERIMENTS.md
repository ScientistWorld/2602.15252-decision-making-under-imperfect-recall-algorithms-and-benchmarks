# Experiment Overview

## first_order_optimizer_aggregate

This is the one scored reproduction experiment in `scoring/scores.json`.

It tests whether scalable strategy solvers can solve the same set of imperfect-recall decision problems while balancing two goals: high final expected utility and first-order convergence. Each compared method is evaluated on the same fixed suite, with the same random-start policy, iteration budget, and convergence threshold.

The experiment establishes whether a submitted solver improves the reliability of reaching first-order stationarity without losing final utility quality. It is intentionally artifact-based: future agents may change the solver as long as they write compatible result files and run `scripts/evaluate.sh`.

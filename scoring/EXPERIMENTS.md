# Experiment Overview

## first_order_optimizer_aggregate

This experiment compares scalable optimizers on the same imperfect-recall benchmark suite. Each method starts from the same seeded random strategies on each instance, runs under the same iteration and convergence threshold, and writes final strategies plus convergence traces.

The scoring script aggregates two questions:

- Did the method find high expected utility relative to the other compared methods?
- Did it reach the shared first-order KKT-gap threshold, and how did its convergence rank compare?

The experiment is intentionally method-agnostic. Future agents may replace the solver implementation as long as they write compatible result artifacts for `scripts/evaluate.sh`.

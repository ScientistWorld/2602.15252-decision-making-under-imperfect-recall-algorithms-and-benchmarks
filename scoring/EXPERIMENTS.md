# Experiment Overview

## first_order_optimizer_aggregate

The single scored experiment. It asks whether a solver for tabular imperfect-recall decision problems reaches first-order optimal strategies more reliably and with fewer gradient evaluations than established optimizers, **without giving up expected utility**.

- **Benefit side:** how many problems the solver solves, how fast it solves them (gradient evaluations), and how it ranks against fixed reference solvers on speed.
- **Constraint side:** the utility of the strategies it ends on, compared with the best utility the reference solvers find. A run only counts if it actually ends on a first-order optimal strategy, so stopping early or returning an unconverged strategy never pays.

Every solver is run by the evaluator itself, from the same fixed starting points (different from those of the reference runs), through a counted gradient oracle; the solver never sees the problem. The training slice uses the paper's public benchmark problems and the authors' own logged runs as reference; the held-out slice uses 176 unseen problems drawn from the same benchmark generators and size presets, with a frozen reference field. The held-out slice is large enough that a genuinely better solver separates from the reference by more than the variation caused by the choice of starting points.

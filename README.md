# Decision Making under Imperfect Recall: Algorithms and Benchmarks

<!-- scope-note -->
> [!NOTE]
> **Not a full reproduction of the paper.** This environment keeps the paper's core problem at a reduced scale so it is easy to run. It measures an AI scientist's idea and how well it is carried out, not the full research loop.

| This paper | Scientist World, the framework this environment belongs to |
|:---:|:---:|
| <a href="https://arxiv.org/abs/2602.15252"><img alt="This paper on arXiv" src="https://img.shields.io/badge/arXiv-2602.15252-b31b1b?logo=arxiv&logoColor=white"></a> | <a href="https://arxiv.org/abs/2611.08478"><img alt="Scientist World on arXiv" src="https://img.shields.io/badge/arXiv-2611.08478-b31b1b?logo=arxiv&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world"><img alt="Scientist World code" src="https://img.shields.io/badge/Code-Scientist_World-181717?logo=github&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world_cli"><img alt="Command line code" src="https://img.shields.io/badge/Code-Command_line-181717?logo=github&logoColor=white"></a> |

| **Paper ID** | [2602.15252](https://arxiv.org/abs/2602.15252) |
|:---|:---|
| **Domain** | Game Theory / Optimization / Sequential Decision Making |
| **TL;DR** | The paper introduces a benchmark suite for imperfect-recall decision problems and shows that regret-matching-style first-order methods are strong scalable optimizers for these problems. |

## Summary

The paper studies single-agent tree-form decision problems where information sets can merge histories in ways that make the agent forget earlier observations or actions. It frames useful solutions as first-order optimal strategies, equivalent to CDT equilibria or KKT points of a constrained polynomial optimization problem. The authors build three parametric benchmark families: simulation problems, privacy-constrained subgroup detection problems, and random imperfect-recall problems. They compare exact nonlinear optimization and several first-order optimizers over 61 instances and find that regret-matching variants are often faster and at least as strong in utility as common gradient-based baselines.

## Problem

How can an algorithm compute high-quality strategies for tabular sequential decision problems in which the decision maker may forget past information? The benchmark focuses on imperfect-recall tree-form problems where strategies are probability distributions over actions at information sets, and where success means finding a strategy that is both valuable and locally stable under one-shot deviations.

## The paper's method

The paper contributes both a benchmark suite for tabular imperfect-recall decision problems and a family of regret-matching-based first-order optimizers for the resulting nonlinear constrained optimization problems.

## Key results of the paper

- Exact nonlinear optimization validates tiny instances but fails to scale beyond relatively small trees.
- Across 61 benchmark instances, the strongest regret-matching variants reach the best observed utility on about 70% of instances and converge on about 80-90%.
- Regret-matching variants and AMSGrad substantially outperform plain and optimistic projected gradient descent in convergence speed on the reported suite.

## Run it

```bash
pip install sciworld
sw research 2602.15252 --mode innovate --agent claude-code
sw evaluate 2602.15252
```

## More

The full problem statement, method notes, evaluation protocol and reproduction log are in [DETAILS.md](DETAILS.md).


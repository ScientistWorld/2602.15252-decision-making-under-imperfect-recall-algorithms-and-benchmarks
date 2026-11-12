# Problem Definition

## Research Question

How can an algorithm compute high-quality strategies for tabular sequential decision problems in which the decision maker may forget information it held before (imperfect recall, including absentmindedness)? A strategy assigns a probability distribution over actions to every information set. The expected utility is a polynomial over a product of probability simplices, so finding an optimal strategy is NP-hard in general. The practical target is a first-order optimal strategy: a strategy at which no single information set can gain by a one-shot deviation, measured by the KKT gap (for every information set, the largest partial derivative minus the current expected partial derivative; the gap is the maximum over information sets).

## Why It Matters

Imperfect recall models teams that cannot communicate, game abstractions, AI systems that must forget sensitive information, and AI agents tested in simulations they cannot tell apart from deployment. Solvers that scale make these problems analysable beyond pen-and-paper examples.

## The Problems

Three benchmark families, all tree-form single-agent problems with chance nodes:

- **Simulation problems**: an agent with a "good" and a "bad" action is tested an uncertain number of times in simulation (caught and stopped if it acts bad) before an uncertain number of deployment rounds; simulation and deployment decisions share information sets.
- **Subgroup detection under privacy constraints**: on a small graph, hidden connected subgroups (lines, cycles, cliques, stars) carry values; the agent selects nodes for a few rounds, remembers hits, and forgets misses.
- **Random problems**: random trees with chance nodes and information sets that merge many decision nodes, including nodes on the same path.

Training problems are the paper's own public small/medium instances (86 to 42k nodes, 1 to 84 information sets). Held-out problems are new draws from the same generators and size presets; they are never shown to solvers.

## Success Criteria

A good solver reaches a first-order optimal strategy (KKT gap at most 1e-6) from as many starting points as possible, in as few gradient evaluations as possible, and ends on strategies with high expected utility.

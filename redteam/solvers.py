"""Real audit solvers; all inputs are scientist-visible game JSONs.

The coordinate solver is a genuine structured local optimizer. Enumeration is
deliberately a brute-force scale check, not a proposed scalable contribution.
"""
from __future__ import annotations

import itertools
import math
import time
import numpy as np

from baseline.pgd import evaluate_and_gradient


class BatchValue:
    def __init__(self, game):
        self.game = game
        self.layers = {}
        self.repetitions = np.zeros(game.n_infosets, dtype=int)

        def visit(idx, depth, counts):
            node = game.nodes[idx]
            if node.kind == "terminal":
                return
            self.layers.setdefault(depth, []).append(idx)
            counts = counts.copy()
            if node.kind == "player":
                counts[node.infoset] += 1
                self.repetitions[:] = np.maximum(self.repetitions, counts)
            for child in node.children:
                visit(child, depth + 1, counts)

        visit(game.root, 0, np.zeros(game.n_infosets, dtype=int))
        self.groups = []
        for depth in sorted(self.layers, reverse=True):
            groups = []
            for kind, arity in sorted({(game.nodes[i].kind, len(game.nodes[i].children))
                                       for i in self.layers[depth]}):
                ids = np.array([i for i in self.layers[depth]
                                if game.nodes[i].kind == kind and len(game.nodes[i].children) == arity])
                children = np.array([game.nodes[i].children for i in ids])
                infosets = np.array([game.nodes[i].infoset for i in ids]) if kind == "player" else None
                chance = np.array([game.nodes[i].chance_probs for i in ids]) if kind == "chance" else None
                groups.append((ids, children, infosets, chance))
            self.groups.append(groups)
        self.payoffs = np.array([n.payoff if n.kind == "terminal" else 0 for n in game.nodes])
        self.max_actions = max(map(len, game.infoset_actions))

    def gradient(self, x):
        values = self.payoffs.copy()
        reach = np.zeros(len(values))
        reach[self.game.root] = 1.
        for groups in self.groups:
            for ids, children, infosets, chance in groups:
                probs = chance if chance is not None else x[infosets, :children.shape[1]]
                values[ids] = np.sum(probs * values[children], axis=1)
        gradients = np.zeros(x.shape)
        for groups in reversed(self.groups):
            for ids, children, infosets, chance in groups:
                probs = chance if chance is not None else x[infosets, :children.shape[1]]
                reach[children] = reach[ids, None] * probs
                if infosets is not None:
                    arity = children.shape[1]
                    bins = infosets[:, None] * self.max_actions + np.arange(arity)
                    terms = reach[ids, None] * values[children]
                    gradients += np.bincount(bins.ravel(), weights=terms.ravel(),
                                             minlength=x.size).reshape(x.shape)
        gap = max(float(np.max(g[:len(a)]) - np.dot(s, g))
                  for s, g, a in zip(x, gradients, self.game.infoset_actions))
        return float(values[self.game.root]), gradients, gap

    def __call__(self, strategies):
        # strategies: batch x infosets x max_actions, padded with zero.
        values = np.broadcast_to(self.payoffs, (len(strategies), len(self.payoffs))).copy()
        for groups in self.groups:
            for ids, children, infosets, chance in groups:
                probs = chance[None] if chance is not None else strategies[:, infosets, :children.shape[1]]
                values[:, ids] = np.sum(probs * values[:, children], axis=2)
        return values[:, self.game.root]


def coordinate_game(game, seed, max_sweeps=6000, initial_strategy=None):
    """Exact pairwise line maximization using the game's polynomial degree.

    Chebyshev interpolation reconstructs each one-dimensional polynomial;
    all real derivative roots and both boundaries are evaluated. A sweep has
    one complete pass over each simplex's action pairs. Work is reported too.
    """
    start = time.perf_counter()
    batch = BatchValue(game)
    rng = np.random.default_rng(seed)
    x = np.zeros((game.n_infosets, batch.max_actions))
    for i, actions in enumerate(game.infoset_actions):
        x[i, :len(actions)] = (rng.dirichlet(np.ones(len(actions))) if initial_strategy is None
                              else initial_strategy[i])
    evaluations = 0
    trace = []
    for sweep in range(1, max_sweeps + 1):
        for i in rng.permutation(game.n_infosets):
            degree = max(1, int(batch.repetitions[i]))
            q = (np.cos(np.pi * (np.arange(degree + 1) + .5) / (degree + 1)) + 1) / 2
            for a, b in itertools.combinations(range(len(game.infoset_actions[i])), 2):
                mass = x[i, a] + x[i, b]
                if mass <= 1e-15:
                    continue
                samples = np.repeat(x[None], len(q), axis=0)
                samples[:, i, a] = mass * q
                samples[:, i, b] = mass * (1 - q)
                ys = batch(samples)
                evaluations += len(q)
                poly = np.polynomial.Chebyshev.fit(q, ys, degree, domain=[0, 1])
                roots = poly.deriv().roots()
                candidates = [0., 1., float(x[i, a] / mass)]
                candidates += [float(r.real) for r in roots if abs(r.imag) < 1e-7 and 0 < r.real < 1]
                samples = np.repeat(x[None], len(candidates), axis=0)
                samples[:, i, a] = mass * np.array(candidates)
                samples[:, i, b] = mass * (1 - np.array(candidates))
                ys = batch(samples)
                evaluations += len(candidates)
                # Preserve the current point on numerical ties.
                best = int(np.argmax(ys))
                if ys[best] > ys[2] + 1e-13:
                    x[:] = samples[best]
        strategy = [x[i, :len(a)].copy() for i, a in enumerate(game.infoset_actions)]
        value, _, gap = evaluate_and_gradient(game, strategy)
        trace.append({"iteration": sweep, "value": value, "kkt_gap": gap})
        if gap <= 1e-6:
            break
        if sweep >= 50 and len(trace) >= 2 and abs(trace[-1]["value"] - trace[-2]["value"]) < 1e-13:
            break
    return {"algorithm": "coordinate", "seed": seed, "iterations_run": sweep,
            "iterations_to_gap": sweep if gap <= 1e-6 else None,
            "final_value": value, "final_kkt_gap": gap,
            "strategy": [s.tolist() for s in strategy], "trace": trace,
            "value_evaluations": evaluations, "elapsed_seconds_observed": time.perf_counter() - start}


def tuned_gd_game(game, seed, iterations=6000):
    """Ordinary paper GD with eta=1, using vectorized tree passes."""
    from baseline.pgd import project_simplex
    start = time.perf_counter()
    engine = BatchValue(game)
    rng = np.random.default_rng(seed)
    x = np.zeros((game.n_infosets, engine.max_actions))
    for i, a in enumerate(game.infoset_actions):
        x[i, :len(a)] = rng.dirichlet(np.ones(len(a)))
    reached = None
    trace = []
    for t in range(1, iterations + 1):
        value, grads, gap = engine.gradient(x)
        if t == 1 or t % 120 == 0 or gap <= 1e-6:
            trace.append({"iteration": t, "value": value, "kkt_gap": gap})
        if gap <= 1e-6:
            reached = t
            break
        if t < iterations:
            for i, a in enumerate(game.infoset_actions):
                x[i, :len(a)] = project_simplex(x[i, :len(a)] + grads[i, :len(a)])
    strategy = [x[i, :len(a)] for i, a in enumerate(game.infoset_actions)]
    # Independent original tree passes validate every final scalar.
    value, _, gap = evaluate_and_gradient(game, strategy)
    return {"algorithm": "gd_eta1", "seed": seed, "iterations_run": t,
            "iterations_to_gap": reached, "final_value": value, "final_kkt_gap": gap,
            "strategy": [s.tolist() for s in strategy], "trace": trace,
            "elapsed_seconds_observed": time.perf_counter() - start}


def brute_force_game(game):
    """Enumerate every deterministic policy by filling its payoff tensor.

    Every consistent terminal path adds its chance-weighted payoff to the
    tensor slice of policies that reach it. No candidate is pruned or sampled.
    Mixed policies may beat the best pure policy, so the exact gap is checked.
    """
    start = time.perf_counter()
    shape = tuple(map(len, game.infoset_actions))
    tensor = np.zeros(shape, dtype=np.float64)
    paths = 0

    def visit(idx, assignments, chance):
        nonlocal paths
        n = game.nodes[idx]
        if n.kind == "terminal":
            key = tuple(assignments.get(i, slice(None)) for i in range(len(shape)))
            tensor[key] += chance * n.payoff
            paths += 1
        elif n.kind == "chance":
            for p, c in zip(n.chance_probs, n.children):
                visit(c, assignments, chance * p)
        else:
            for a, c in enumerate(n.children):
                if n.infoset in assignments and assignments[n.infoset] != a:
                    continue
                updated = dict(assignments)
                updated[n.infoset] = a
                visit(c, updated, chance)

    visit(game.root, {}, 1.)
    pure = np.unravel_index(int(tensor.argmax()), shape)
    strategy = [np.eye(n)[a] for n, a in zip(shape, pure)]
    value, _, gap = evaluate_and_gradient(game, strategy)
    pure_value, pure_gap = value, gap
    polish_sweeps = 0
    if gap > 1e-6:
        polished = coordinate_game(game, 123, initial_strategy=strategy)
        strategy = [np.array(s) for s in polished["strategy"]]
        value, gap = polished["final_value"], polished["final_kkt_gap"]
        polish_sweeps = polished["iterations_run"]
    work = math.prod(shape) + polish_sweeps
    return {"algorithm": "brute_force", "seed": 0,
            "iterations_run": work,
            "iterations_to_gap": work if gap <= 1e-6 else None,
            "final_value": value, "final_kkt_gap": gap,
            "strategy": [s.tolist() for s in strategy], "trace": [],
            "enumerated_candidates": math.prod(shape), "consistent_leaf_paths": paths,
            "best_pure_value": pure_value, "best_pure_gap": pure_gap, "polish_sweeps": polish_sweeps,
            "peak_tensor_bytes": tensor.nbytes,
            "elapsed_seconds_observed": time.perf_counter() - start}

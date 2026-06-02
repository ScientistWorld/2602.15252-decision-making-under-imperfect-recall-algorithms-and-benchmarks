from __future__ import annotations

import time

import numpy as np

from data.tree_games import TreeGame


def project_simplex(v: np.ndarray) -> np.ndarray:
    if len(v) == 1:
        return np.ones(1)
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u) - 1.0
    ind = np.arange(1, len(v) + 1)
    cond = u - cssv / ind > 0
    rho = ind[cond][-1]
    theta = cssv[cond][-1] / rho
    return np.maximum(v - theta, 0.0)


def evaluate_and_gradient(game: TreeGame, strategy: list[np.ndarray]) -> tuple[float, list[np.ndarray], float]:
    n = len(game.nodes)
    reach = np.zeros(n, dtype=float)
    values = np.zeros(n, dtype=float)
    reach[game.root] = 1.0

    order: list[int] = []

    def visit(idx: int) -> None:
        order.append(idx)
        for child in game.nodes[idx].children:
            visit(child)

    visit(game.root)

    for idx in order:
        node = game.nodes[idx]
        if reach[idx] == 0.0 or node.kind == "terminal":
            continue
        if node.kind == "chance":
            for p, child in zip(node.chance_probs or [], node.children):
                reach[child] += reach[idx] * p
        elif node.kind == "player":
            x = strategy[node.infoset]
            for p, child in zip(x, node.children):
                reach[child] += reach[idx] * p

    for idx in reversed(order):
        node = game.nodes[idx]
        if node.kind == "terminal":
            values[idx] = float(node.payoff)
        elif node.kind == "chance":
            values[idx] = sum(p * values[c] for p, c in zip(node.chance_probs or [], node.children))
        elif node.kind == "player":
            x = strategy[node.infoset]
            values[idx] = sum(p * values[c] for p, c in zip(x, node.children))

    grads = [np.zeros(len(actions), dtype=float) for actions in game.infoset_actions]
    for idx in order:
        node = game.nodes[idx]
        if node.kind != "player":
            continue
        for a_idx, child in enumerate(node.children):
            grads[node.infoset][a_idx] += reach[idx] * values[child]

    gaps = [float(np.max(grad) - np.dot(x, grad)) for x, grad in zip(strategy, grads)]
    return float(values[game.root]), grads, max(gaps) if gaps else 0.0


def random_strategy(game: TreeGame, rng: np.random.Generator) -> list[np.ndarray]:
    return [rng.dirichlet(np.ones(len(actions))) for actions in game.infoset_actions]


def solve_pgd_game(
    game: TreeGame,
    algorithm: str,
    iterations: int,
    seed: int,
    eta: float,
    target_gap: float,
) -> dict:
    if algorithm not in {"gd", "ogd"}:
        raise ValueError(f"PGD baseline only supports gd/ogd, got {algorithm!r}")

    rng = np.random.default_rng(seed)
    anchors = random_strategy(game, rng)
    strategy = [x.copy() for x in anchors]
    prev_grads = [np.zeros_like(x) for x in strategy]
    trace = []
    reached_at = None
    start = time.perf_counter()

    for t in range(1, iterations + 1):
        if algorithm == "ogd":
            strategy = [project_simplex(x + eta * g) for x, g in zip(anchors, prev_grads)]
        else:
            strategy = [x.copy() for x in anchors]

        value, grads, gap = evaluate_and_gradient(game, strategy)
        anchors = [project_simplex(x + eta * grad) for x, grad in zip(anchors, grads)]
        prev_grads = grads

        if t == 1 or t % max(1, iterations // 50) == 0 or gap <= target_gap:
            trace.append({"iteration": t, "value": value, "kkt_gap": gap})
        if gap <= target_gap and reached_at is None:
            reached_at = t
            break

    value, _, gap = evaluate_and_gradient(game, strategy)
    return {
        "algorithm": algorithm,
        "seed": seed,
        "iterations_run": t,
        "iterations_to_gap": reached_at,
        "final_value": value,
        "final_kkt_gap": gap,
        "elapsed_seconds_observed": time.perf_counter() - start,
        "strategy": [x.tolist() for x in strategy],
        "trace": trace,
    }

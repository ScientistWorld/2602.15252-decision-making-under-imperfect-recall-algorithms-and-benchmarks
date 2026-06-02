from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.tree_games import TreeGame, write_default_suite
from method.optimizers import make_optimizer


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
            probs = node.chance_probs or []
            for p, child in zip(probs, node.children):
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

    gaps = []
    for x, grad in zip(strategy, grads):
        gaps.append(float(np.max(grad) - np.dot(x, grad)))
    return float(values[game.root]), grads, max(gaps) if gaps else 0.0


def random_strategy(game: TreeGame, rng: np.random.Generator) -> list[np.ndarray]:
    return [rng.dirichlet(np.ones(len(actions))) for actions in game.infoset_actions]


def solve_game(
    game: TreeGame,
    algorithm: str,
    iterations: int,
    seed: int,
    eta: float,
    target_gap: float,
) -> dict:
    rng = np.random.default_rng(seed)
    strategy = random_strategy(game, rng)
    opts = [make_optimizer(algorithm, x, eta) for x in strategy]
    prev_grads = [np.zeros_like(x) for x in strategy]
    trace = []
    reached_at = None
    start = time.perf_counter()

    for t in range(1, iterations + 1):
        for i, opt in enumerate(opts):
            pred = prev_grads[i] if opt.predictive else np.zeros_like(prev_grads[i])
            strategy[i] = opt.getx(pred)
        value, grads, gap = evaluate_and_gradient(game, strategy)
        for opt, grad in zip(opts, grads):
            opt.step(grad)
        prev_grads = grads
        if t == 1 or t % max(1, iterations // 50) == 0 or gap <= target_gap:
            trace.append({"iteration": t, "value": value, "kkt_gap": gap})
        if gap <= target_gap and reached_at is None:
            reached_at = t
            break

    value, _, gap = evaluate_and_gradient(game, strategy)
    elapsed = time.perf_counter() - start
    return {
        "algorithm": algorithm,
        "seed": seed,
        "iterations_run": t,
        "iterations_to_gap": reached_at,
        "final_value": value,
        "final_kkt_gap": gap,
        "elapsed_seconds_observed": elapsed,
        "strategy": [x.tolist() for x in strategy],
        "trace": trace,
    }


def run_suite(args: argparse.Namespace) -> dict:
    instance_dir = Path(args.instances)
    if args.generate_instances:
        write_default_suite(instance_dir)
    paths = sorted(instance_dir.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"no instances found in {instance_dir}")
    algorithms = [a.strip() for a in args.algorithms.split(",") if a.strip()]
    results: dict[str, dict] = {"config": vars(args), "instances": {}}
    for path in paths:
        game = TreeGame.from_json(path)
        inst = {
            "num_nodes": len(game.nodes),
            "num_infosets": game.n_infosets,
            "algorithms": {},
        }
        for alg in algorithms:
            runs = [
                solve_game(game, alg, args.iterations, args.seed + s, args.eta, args.target_gap)
                for s in range(args.runs)
            ]
            median_idx = int(np.argsort([r["final_kkt_gap"] for r in runs])[len(runs) // 2])
            inst["algorithms"][alg] = {
                "runs": runs,
                "selected_run": runs[median_idx],
            }
        results["instances"][game.name] = inst
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", default="data/instances")
    parser.add_argument("--output", default="results/optimization_results.json")
    parser.add_argument("--algorithms", default="gd,ogd,ams,rm,rm_plus,prm,prm_plus")
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--eta", type=float, default=0.1)
    parser.add_argument("--target-gap", type=float, default=1e-6)
    parser.add_argument("--generate-instances", action="store_true")
    args = parser.parse_args()
    results = run_suite(args)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

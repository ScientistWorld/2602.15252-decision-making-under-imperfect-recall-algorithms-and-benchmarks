from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.tree_games import TreeGame, write_default_suite
from baseline.pgd import solve_pgd_game


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", default="data/instances")
    parser.add_argument("--output", default="results/baseline_gd_results.json")
    parser.add_argument("--algorithms", default="gd,ogd")
    parser.add_argument("--iterations", type=int, default=3000)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--eta", type=float, default=0.1)
    parser.add_argument("--target-gap", type=float, default=1e-6)
    parser.add_argument("--generate-instances", action="store_true")
    args = parser.parse_args()

    instance_dir = Path(args.instances)
    if args.generate_instances:
        write_default_suite(instance_dir)
    paths = sorted(instance_dir.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"no instances found in {instance_dir}")

    algorithms = [alg.strip() for alg in args.algorithms.split(",") if alg.strip()]
    unsupported = set(algorithms) - {"gd", "ogd"}
    if unsupported:
        raise ValueError(f"baseline runner only supports GD/OGD, got: {sorted(unsupported)}")

    results: dict[str, object] = {"config": vars(args), "instances": {}}
    for path in paths:
        game = TreeGame.from_json(path)
        inst = {
            "num_nodes": len(game.nodes),
            "num_infosets": game.n_infosets,
            "algorithms": {},
        }
        for alg in algorithms:
            runs = [
                solve_pgd_game(game, alg, args.iterations, args.seed + s, args.eta, args.target_gap)
                for s in range(args.runs)
            ]
            runs_by_gap = sorted(range(len(runs)), key=lambda i: runs[i]["final_kkt_gap"])
            inst["algorithms"][alg] = {
                "runs": runs,
                "selected_run": runs[runs_by_gap[len(runs_by_gap) // 2]],
            }
        results["instances"][game.name] = inst

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean


def rank(values: dict[str, float], higher: bool) -> dict[str, int]:
    ordered = sorted(values, key=values.get, reverse=higher)
    return {name: i + 1 for i, name in enumerate(ordered)}


def aggregate(results: dict, target_gap: float) -> dict:
    algorithms = sorted(
        {
            alg
            for inst in results["instances"].values()
            for alg in inst["algorithms"].keys()
        }
    )
    best_value_count = {alg: 0 for alg in algorithms}
    value_ranks = {alg: [] for alg in algorithms}
    reached_count = {alg: 0 for alg in algorithms}
    conv_best_count = {alg: 0 for alg in algorithms}
    conv_ranks = {alg: [] for alg in algorithms}
    final_gaps = {alg: [] for alg in algorithms}
    iter_to_gap = {alg: [] for alg in algorithms}

    for inst in results["instances"].values():
        selected = {alg: data["selected_run"] for alg, data in inst["algorithms"].items()}
        values = {alg: run["final_value"] for alg, run in selected.items()}
        gaps = {alg: run["final_kkt_gap"] for alg, run in selected.items()}
        conv_iters = {
            alg: (run["iterations_to_gap"] if run["iterations_to_gap"] is not None else float("inf"))
            for alg, run in selected.items()
        }
        max_value = max(values.values())
        min_iter = min(conv_iters.values())
        for alg in algorithms:
            if values.get(alg, -float("inf")) >= max_value - 1e-9:
                best_value_count[alg] += 1
            if conv_iters.get(alg, float("inf")) == min_iter and min_iter != float("inf"):
                conv_best_count[alg] += 1
            if gaps.get(alg, float("inf")) <= target_gap:
                reached_count[alg] += 1
            final_gaps[alg].append(gaps[alg])
            iter_to_gap[alg].append(conv_iters[alg])
        vrank = rank(values, higher=True)
        crank = rank({alg: -conv_iters[alg] for alg in algorithms}, higher=True)
        for alg in algorithms:
            value_ranks[alg].append(vrank[alg])
            conv_ranks[alg].append(crank[alg])

    n = len(results["instances"])
    summary = {}
    for alg in algorithms:
        finite_iters = [x for x in iter_to_gap[alg] if x != float("inf")]
        summary[alg] = {
            "value_percent_best": 100.0 * best_value_count[alg] / n,
            "value_avg_rank": mean(value_ranks[alg]),
            "convergence_percent_reached": 100.0 * reached_count[alg] / n,
            "convergence_percent_best": 100.0 * conv_best_count[alg] / n,
            "convergence_avg_rank": mean(conv_ranks[alg]),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/optimization_results.json")
    parser.add_argument("--output", default="scoring/scores.json")
    parser.add_argument("--target-gap", type=float, default=1e-6)
    args = parser.parse_args()

    results = json.loads(Path(args.input).read_text())
    summary = aggregate(results, args.target_gap)
    scores = {
        "experiments": {
            "first_order_optimizer_aggregate": {
                "results": {
                    alg: metrics
                    for alg, metrics in summary.items()
                    if alg in {"gd", "ogd", "ams", "rm", "rm_plus", "prm", "prm_plus"}
                }
            }
        }
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scores, indent=2))
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()

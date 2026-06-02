from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean


def rank(values: dict[str, float], higher: bool) -> dict[str, int]:
    ordered = sorted(values, key=values.get, reverse=higher)
    return {name: i + 1 for i, name in enumerate(ordered)}


def algorithm_runs(algorithm_data: dict) -> list[dict]:
    runs = algorithm_data.get("runs")
    if runs:
        return runs
    if "selected_run" in algorithm_data:
        return [algorithm_data["selected_run"]]
    raise ValueError("algorithm entry has neither selected_run nor runs")


def safe_gap(gap: float) -> float:
    return max(float(gap), 1e-16)


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
    value_gaps = {alg: [] for alg in algorithms}
    final_log10_gaps = {alg: [] for alg in algorithms}
    selected_iter_costs = {alg: [] for alg in algorithms}
    selected_log10_iter_costs = {alg: [] for alg in algorithms}
    restart_reached = {alg: 0 for alg in algorithms}
    restart_total = {alg: 0 for alg in algorithms}

    for inst in results["instances"].values():
        selected = {
            alg: data["selected_run"]
            for alg, data in inst["algorithms"].items()
        }
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
            value_gaps[alg].append(max_value - values[alg])
            final_log10_gaps[alg].append(math.log10(safe_gap(gaps[alg])))
            if conv_iters[alg] == float("inf"):
                iter_cost = selected[alg].get("iterations_run", 0) + 1
            else:
                iter_cost = conv_iters[alg]
            selected_iter_costs[alg].append(iter_cost)
            selected_log10_iter_costs[alg].append(math.log10(max(float(iter_cost), 1.0)))

            runs = algorithm_runs(inst["algorithms"][alg])
            restart_total[alg] += len(runs)
            restart_reached[alg] += sum(1 for run in runs if run["final_kkt_gap"] <= target_gap)

        vrank = rank(values, higher=True)
        crank = rank({alg: -conv_iters[alg] for alg in algorithms}, higher=True)
        for alg in algorithms:
            value_ranks[alg].append(vrank[alg])
            conv_ranks[alg].append(crank[alg])

    n = len(results["instances"])
    summary = {}
    for alg in algorithms:
        summary[alg] = {
            "value_percent_best": 100.0 * best_value_count[alg] / n,
            "value_avg_rank": mean(value_ranks[alg]),
            "value_avg_gap_to_best": mean(value_gaps[alg]),
            "convergence_percent_reached": 100.0 * reached_count[alg] / n,
            "convergence_percent_best": 100.0 * conv_best_count[alg] / n,
            "convergence_avg_rank": mean(conv_ranks[alg]),
            "selected_iterations_to_gap_mean": mean(selected_iter_costs[alg]),
            "selected_log10_iterations_to_gap_mean": mean(selected_log10_iter_costs[alg]),
            "selected_log10_kkt_gap_mean": mean(final_log10_gaps[alg]),
            "restart_convergence_percent": 100.0 * restart_reached[alg] / restart_total[alg],
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
    # AMS is retained in method traces as a comparator, but this compact
    # implementation is not close enough to the paper's AMS baseline to claim
    # it as reproduced. Only emit methods whose scores are part of this
    # reproduction claim.
    scored_algorithms = {"gd", "ogd", "rm", "rm_plus", "prm", "prm_plus"}
    scores = {
        "experiments": {
            "first_order_optimizer_aggregate": {
                "results": {
                    alg: metrics
                    for alg, metrics in summary.items()
                    if alg in scored_algorithms
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

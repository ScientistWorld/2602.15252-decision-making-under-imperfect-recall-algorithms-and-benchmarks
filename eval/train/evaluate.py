from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean


SLICE_NAME = "train"
EXPERIMENT_NAME = "first_order_optimizer_aggregate"
REFERENCE_ALGORITHMS = frozenset(("ams", "gd", "ogd", "prm", "prm_plus", "rm", "rm_plus"))
EXCLUDED_ALGORITHMS = frozenset(("ams",))
INSTANCE_IDS = (
    "absentminded_driver",
    "random_depth6",
    "simulation_5",
    "subgroup_detection_large",
)


def rank(values: dict[str, float], higher: bool) -> dict[str, int]:
    ordered = sorted(values, key=values.get, reverse=higher)
    return {name: i + 1 for i, name in enumerate(ordered)}


def selected_run(algorithm_data: dict) -> dict:
    if "selected_run" in algorithm_data:
        return algorithm_data["selected_run"]
    runs = algorithm_data.get("runs", [])
    if not runs:
        raise ValueError("algorithm entry has neither selected_run nor runs")
    return min(runs, key=lambda run: run["final_kkt_gap"])


def load_slice(results: dict) -> dict:
    instances = results.get("instances", {})
    missing = [name for name in INSTANCE_IDS if name not in instances]
    if missing:
        raise ValueError(f"{SLICE_NAME} slice missing instances in result artifact: {missing}")
    return {name: instances[name] for name in INSTANCE_IDS}


def common_algorithms(instances: dict[str, dict]) -> list[str]:
    present = [set(inst["algorithms"]) for inst in instances.values()]
    if not present:
        raise ValueError(f"{SLICE_NAME} slice has no instances to score")
    common = set.intersection(*present)
    missing = sorted(REFERENCE_ALGORITHMS - common)
    if missing:
        raise ValueError(f"{SLICE_NAME} artifact is missing required comparator algorithms: {missing}")
    return sorted(common)


def algorithm_runs(algorithm_data: dict) -> list[dict]:
    runs = algorithm_data.get("runs")
    if runs:
        return runs
    if "selected_run" in algorithm_data:
        return [algorithm_data["selected_run"]]
    raise ValueError("algorithm entry has neither selected_run nor runs")


def safe_gap(gap: float) -> float:
    return max(float(gap), 1e-16)


def aggregate(results: dict, target_gap: float) -> dict[str, dict[str, float]]:
    instances = load_slice(results)
    algorithms = common_algorithms(instances)

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

    for inst in instances.values():
        selected = {
            alg: selected_run(inst["algorithms"][alg])
            for alg in algorithms
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
            if values[alg] >= max_value - 1e-9:
                best_value_count[alg] += 1
            if conv_iters[alg] == min_iter and min_iter != float("inf"):
                conv_best_count[alg] += 1
            if gaps[alg] <= target_gap:
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

    n = len(instances)
    return {
        alg: {
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
        for alg in algorithms
        if alg not in EXCLUDED_ALGORITHMS
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/optimization_results.json")
    parser.add_argument("--output", default="scoring/scores_train.json")
    parser.add_argument("--target-gap", type=float, default=1e-6)
    args = parser.parse_args()

    results = json.loads(Path(args.input).read_text())
    scores = {
        "_slice": SLICE_NAME,
        "experiments": {
            EXPERIMENT_NAME: {
                "results": aggregate(results, args.target_gap)
            }
        }
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scores, indent=2) + "\n")
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()

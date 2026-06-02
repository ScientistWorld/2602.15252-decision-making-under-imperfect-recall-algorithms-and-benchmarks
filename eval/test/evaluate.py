from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean


SLICE_NAME = "test"
EXPERIMENT_NAME = "first_order_optimizer_aggregate"
INSTANCE_IDS = (
    "simulation_3",
    "random_depth7",
    "random_depth8",
    "subgroup_detection_small",
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
    algorithms = sorted(set.intersection(*present))
    if not algorithms:
        raise ValueError(f"{SLICE_NAME} slice has no algorithm present on every instance")
    return algorithms


def load_train_methods(path: Path) -> set[str] | None:
    if not path.exists():
        return None
    scores = json.loads(path.read_text())
    experiments = scores.get("experiments", scores)
    exp = experiments.get(EXPERIMENT_NAME)
    if exp is None:
        raise ValueError(f"{path} does not contain experiment {EXPERIMENT_NAME!r}")
    methods = exp.get("results", exp)
    if not isinstance(methods, dict) or not methods:
        raise ValueError(f"{path} does not contain method scores for {EXPERIMENT_NAME!r}")
    return set(methods)


def aggregate(results: dict, target_gap: float, required_methods: set[str] | None) -> dict[str, dict[str, float]]:
    instances = load_slice(results)
    algorithms = common_algorithms(instances)
    if required_methods is not None:
        missing = sorted(required_methods - set(algorithms))
        if missing:
            raise ValueError(f"test artifact is missing methods scored on train: {missing}")
        algorithms = sorted(required_methods)

    best_value_count = {alg: 0 for alg in algorithms}
    value_ranks = {alg: [] for alg in algorithms}
    reached_count = {alg: 0 for alg in algorithms}
    conv_best_count = {alg: 0 for alg in algorithms}
    conv_ranks = {alg: [] for alg in algorithms}

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
            "convergence_percent_reached": 100.0 * reached_count[alg] / n,
            "convergence_percent_best": 100.0 * conv_best_count[alg] / n,
            "convergence_avg_rank": mean(conv_ranks[alg]),
        }
        for alg in algorithms
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/optimization_results.json")
    parser.add_argument("--output", default="scoring/scores_test.json")
    parser.add_argument("--target-gap", type=float, default=1e-6)
    parser.add_argument("--train-scores", default="scoring/scores_train.json")
    args = parser.parse_args()

    results = json.loads(Path(args.input).read_text())
    required_methods = load_train_methods(Path(args.train_scores))
    scores = {
        "experiments": {
            EXPERIMENT_NAME: {
                "results": aggregate(results, args.target_gap, required_methods)
            }
        }
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scores, indent=2) + "\n")
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()

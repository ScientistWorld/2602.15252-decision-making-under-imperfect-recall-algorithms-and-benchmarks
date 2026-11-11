"""Freeze the training-slice comparator field from the paper's own experiment logs.

The paper's artifact contains, for every benchmark instance, the logs of all
first-order runs (12 random starts, seeds 33-44) of GD and OGD with step sizes
{1, 0.1, 0.01, 0.001}, AMSGrad with 8 hyper-parameter settings, and RM, RM+,
PRM, PRM+.  This script reads the final iteration, utility and KKT gap of each
run on the training instances and writes eval/train/field.json.  The training
evaluator uses these as the fixed comparators (the paper's own runs, on the same
instances and from the same starting points that the evaluator gives solvers).

Usage (offline, once; needs scripts/download.sh to have fetched the logs):
    python eval/train/build_field_from_paper_logs.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "data" / "downloads" / "paper_runs" / "codefolder_url" / "runs"
INSTANCES = ROOT / "data" / "instances" / "train"
OUT = Path(__file__).resolve().parent / "field.json"
SEEDS = list(range(33, 45))
BUDGET = 6000
TARGET_GAP = 1e-6
FAMILIES = {
    "gd": ["pgd_1e0", "pgd_1e-1", "pgd_1e-2", "pgd_1e-3"],
    "ogd": ["optgd_1e0", "optgd_1e-1", "optgd_1e-2", "optgd_1e-3"],
    "ams": [f"ams_a1e{a}_b{b1}_c{b2}" for a in (-2, -1) for b1 in (0.9, 0.99) for b2 in (0.99, 0.999)],
    "rm": ["rm"],
    "rm_plus": ["rm+"],
    "prm": ["prm"],
    "prm_plus": ["prm+"],
}
LINE = re.compile(r"iter (\d+) \| time [\d.e+-]+ \| value ([\d.e+-]+) \| gap ([\d.e+-]+)")


def uniform_value(tree: dict) -> float:
    parent, act, prob, pay = tree["parent"], tree["edge_action"], tree["edge_prob"], tree["payoff"]
    sizes = tree["infoset_sizes"]
    x = [1.0 / s for s in sizes for _ in range(s)]
    n = len(parent)
    has_child = [False] * n
    for p in parent[1:]:
        has_child[p] = True
    value = [0.0] * n
    for j in range(n - 1, 0, -1):
        if not has_child[j]:
            value[j] = pay[j]
        w = x[act[j]] if act[j] >= 0 else prob[j]
        value[parent[j]] += w * value[j]
    return value[0]


def last_line(path: Path):
    last = None
    with open(path) as handle:
        for line in handle:
            m = LINE.search(line)
            if m:
                last = m
    if last is None:
        raise ValueError(f"no iteration line in {path}")
    return int(last.group(1)) + 1, float(last.group(2)), float(last.group(3))


def main() -> None:
    index = json.loads((INSTANCES / "index.json").read_text())
    out = {"slice": "train", "budget": BUDGET, "target_gap": TARGET_GAP, "start_seeds": SEEDS,
           "source": "paper artifact runs/ (authors' logs)", "families": FAMILIES, "instances": {}}
    for name, info in index.items():
        family, size, game = info["paper_file"].split("/")[1:4]
        game = game[:-4]
        tree = json.loads((INSTANCES / f"{name}.json").read_text())
        configs = {}
        for cfgs in FAMILIES.values():
            for cfg in cfgs:
                recs = []
                for seed in SEEDS:
                    path = RUNS / family / size / game / str(seed) / (
                        f"{game}__algo-{cfg}__seed-{seed}__maxiter-6000__timelimit-14400.0__tol-1e-06.log")
                    recs.append(list(last_line(path)))
                configs[cfg] = recs
        out["instances"][name] = {"uniform_value": uniform_value(tree), "configs": configs}
        print(name, "uniform", round(out["instances"][name]["uniform_value"], 6))
    OUT.write_text(json.dumps(out, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()

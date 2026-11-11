"""Scored metrics of a solver against the frozen comparator field (pure Python).

A run counts as solved only if the strategy it ends on is an epsilon-KKT point
(gap <= target).  Unsolved or failed runs are scored as the worst possible run:
no utility, and iterations = budget + 1.
"""
from __future__ import annotations

import math

METRICS = (
    "value_percent_best",
    "value_avg_rank",
    "utility_gain_mean",
    "convergence_percent_reached",
    "convergence_percent_best",
    "convergence_avg_rank",
    "log10_iterations_mean",
    "restart_convergence_percent",
)


def run_value(rec: dict) -> float:
    return rec["value"] if rec["converged"] else -math.inf


def run_cost(rec: dict, budget: int) -> int:
    return rec["calls"] if rec["converged"] else budget + 1


def summary(records: list[dict], budget: int) -> tuple[float, int]:
    """Median run of a set of starts: (utility, iterations); unsolved runs count as worst."""
    k = len(records) // 2
    values = sorted((run_value(r) for r in records), reverse=True)
    costs = sorted(run_cost(r, budget) for r in records)
    return values[k], costs[k]


def field_records(raw: list) -> list[dict]:
    """Frozen comparator runs are stored as [iterations, utility, gap]."""
    return [{"calls": int(c), "value": float(v), "gap": float(g), "failed": False, "converged": None}
            for c, v, g in raw]


def build_field(field: dict) -> dict:
    """Select each comparator family's configuration per instance (paper's rule).

    Among a family's configurations, keep the one whose median run reaches the
    KKT threshold in the fewest iterations; if none reaches it, the one with the
    smallest median final gap.  Returns per instance the selected comparator runs,
    the best known converged utility and the uniform-strategy utility.
    """
    budget, target = field["budget"], field["target_gap"]
    out = {}
    for name, inst in field["instances"].items():
        configs = {}
        for cfg, raw in inst["configs"].items():
            recs = field_records(raw)
            for r in recs:
                r["converged"] = r["gap"] <= target
            configs[cfg] = recs
        chosen = {}
        for family, cfgs in field["families"].items():
            best_key, best_cfg = None, None
            for cfg in cfgs:
                recs = configs[cfg]
                _, cost = summary(recs, budget)
                gaps = sorted(r["gap"] for r in recs)
                med_gap = 0.5 * (gaps[(len(gaps) - 1) // 2] + gaps[len(gaps) // 2])
                key = (0, cost) if cost <= budget else (1, med_gap)
                if best_key is None or key < best_key:
                    best_key, best_cfg = key, cfg
            chosen[family] = configs[best_cfg]
        converged = [r["value"] for recs in configs.values() for r in recs if r["converged"]]
        best = max(converged) if converged else max(r["value"] for recs in configs.values() for r in recs)
        out[name] = {"runs": chosen, "best_value": best, "uniform_value": inst["uniform_value"]}
    return out


def method_metrics(name: str, records: dict[str, list[dict]], field: dict, budget: int) -> dict:
    """Metrics of one method against the frozen comparator field (minus its own family)."""
    per_inst = []
    all_runs = []
    for inst, info in field.items():
        recs = records[inst]
        all_runs.extend(recs)
        others = {f: summary(r, budget) for f, r in info["runs"].items() if f != name}
        v, c = summary(recs, budget)
        vstar, unif = info["best_value"], info["uniform_value"]
        tol = 1e-4 * max(1.0, abs(vstar))
        ov = [o[0] for o in others.values()]
        oc = [o[1] for o in others.values()]
        if v == -math.inf:
            vbetter = sum(1 for x in ov if x > -math.inf)
            vtie = sum(1 for x in ov if x == -math.inf)
            vbest = False
        else:
            vbetter = sum(1 for x in ov if x > v + tol)
            vtie = sum(1 for x in ov if abs(x - v) <= tol)
            vbest = vbetter == 0
        cbetter = sum(1 for x in oc if x < c)
        ctie = sum(1 for x in oc if x == c)
        span = vstar - unif
        gains = []
        for r in recs:
            if not r["converged"]:
                gains.append(0.0)
            elif span <= 1e-9 * max(1.0, abs(vstar)):
                gains.append(1.0 if r["value"] >= vstar - tol else 0.0)
            else:
                gains.append(max(0.0, (r["value"] - unif) / span))
        per_inst.append({
            "best_value": vbest,
            "value_rank": 1 + vbetter + 0.5 * vtie,
            "gain": sum(gains) / len(gains),
            "reached": c <= budget,
            "fastest": c <= budget and cbetter == 0,
            "conv_rank": 1 + cbetter + 0.5 * ctie,
            "log_cost": sum(math.log10(run_cost(r, budget)) for r in recs) / len(recs),
        })
    n = len(per_inst)
    worst_rank = 1 + max(len([f for f in info["runs"] if f != name]) for info in field.values())
    solved_any = any(not r["failed"] for r in all_runs)
    mean = lambda key: sum(float(p[key]) for p in per_inst) / n  # noqa: E731
    return {
        "value_percent_best": 100.0 * mean("best_value"),
        "value_avg_rank": mean("value_rank") if solved_any else float(worst_rank),
        "utility_gain_mean": mean("gain"),
        "convergence_percent_reached": 100.0 * mean("reached"),
        "convergence_percent_best": 100.0 * mean("fastest"),
        "convergence_avg_rank": mean("conv_rank") if solved_any else float(worst_rank),
        "log10_iterations_mean": mean("log_cost"),
        "restart_convergence_percent": 100.0 * sum(r["converged"] for r in all_runs) / len(all_runs),
    }


def failed_records(k: int, reason: str) -> list[dict]:
    return [{"calls": 0, "value": None, "gap": None, "failed": True, "converged": False, "reason": reason}
            for _ in range(k)]

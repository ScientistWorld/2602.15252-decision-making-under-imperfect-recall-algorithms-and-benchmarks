"""Summarise the hardening cases against the reference rows (scoring/scores_test.json).

For each case row: raw metrics, and a rank delta versus the reference row of the
same name computed as the ranker does: sum over metrics of |coefficient| x the
improvement in the metric's better direction / the metric's standard deviation
across a cohort of attempts.  Two cohorts are reported (the future population is
unknown): ALL = every evaluated row (reference rows + all cases), HONEST =
reference rows, seed-noise reruns and honest variants only.  Seed noise is the
spread of the reference re-run from other fixed starting points.

    python redteam/hardening/summarize.py   -> redteam/hardening/summary.{json,md}
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EXP = "first_order_optimizer_aggregate"
ref = json.loads((ROOT / "scoring/reference.json").read_text())["experiments"][EXP]["metrics"]
METRICS = list(ref)
reference = json.loads((ROOT / "scoring/scores_test.json").read_text())["experiments"][EXP]["results"]


def rows():
    out = {}
    for f in sorted((HERE / "scores").glob("*.json")):
        res = json.loads(f.read_text())["experiments"][EXP]["results"]
        for row, metrics in res.items():
            out[f.stem] = (row, metrics)
    return out


def std(values):
    m = sum(values) / len(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))


def delta(case, base, sds):
    total = 0.0
    for m in METRICS:
        if sds[m] <= 0:
            continue
        d = case[m] - base[m]
        if not ref[m]["higher_is_better"]:
            d = -d
        total += abs(ref[m]["coefficient"]) * d / sds[m]
    return total


def per_problem_delta(row, records, base_records, sds):
    """Per-problem contributions to the rank delta (their mean over problems is the delta)."""
    sys.path.insert(0, str(ROOT / "eval" / "test"))
    from metrics import build_field, method_metrics  # noqa: E402
    global _FIELD
    if _FIELD is None:
        _FIELD = build_field(json.loads((ROOT / "eval/test/field.json").read_text()))
    out = {}
    for inst, info in _FIELD.items():
        a = method_metrics(row, {inst: records[inst]}, {inst: info}, 6000)
        b = method_metrics(row, {inst: base_records[inst]}, {inst: info}, 6000)
        out[inst] = delta(a, b, sds)
    return out


_FIELD = None


def _details(name):
    path = ROOT / "eval" / "test" / "_runs" / f"{name}.json"
    return json.loads(path.read_text())["records"] if path.is_file() else None


def bootstrap(values, reps=4000, seed=0):
    import random
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    return {"mean": sum(values) / n, "ci95": [means[int(0.025 * reps)], means[int(0.975 * reps) - 1]],
            "frac_positive": sum(m > 0 for m in means) / reps, "problems": n}


def paired_per_problem(cases, sds):
    """Paired per-problem gains of variants over the reference row (same starts), with an
    instance bootstrap; and the reference's per-problem seed noise."""
    ref = _details("reference_details")
    if ref is None:
        return {}
    out = {}
    tags = {"official": None, "c": "noise_rm_plus_seeds_c", "d": "noise_rm_plus_seeds_d", "e": "noise_rm_plus_seeds_e"}
    for variant, row, base_row in (("rm_plus_gd_fallback50", "rm_plus", "rm_plus"),
                                   ("rm_plus_gd_fallback200", "rm_plus", "rm_plus"),
                                   ("gd_adaptive", "gd", "gd")):
        per_set = {}
        for tag, noise_case in tags.items():
            vname = f"better_{variant}" if tag == "official" else f"paired_{variant}_seeds_{tag}"
            v = _details(vname)
            b = ref if tag == "official" else _details(noise_case)
            if v is None or b is None or row not in v or base_row not in b:
                continue
            if tag != "official" and base_row != "rm_plus":
                continue
            per_set[tag] = per_problem_delta(row, v[row], b[base_row], sds)
        if not per_set:
            continue
        insts = sorted(per_set["official"]) if "official" in per_set else sorted(next(iter(per_set.values())))
        entry = {f"seeds_{t}": bootstrap([d[i] for i in insts]) for t, d in per_set.items()}
        if len(per_set) > 1:
            pooled = [sum(d[i] for d in per_set.values()) / len(per_set) for i in insts]
            entry["pooled_over_start_sets"] = bootstrap(pooled)
        fam = {}
        for i in insts:
            fam.setdefault(i.rsplit("_", 1)[0] + "_" + i.rsplit("_", 1)[1][0], []).append(
                sum(d[i] for d in per_set.values()) / len(per_set))
        entry["by_family_mean"] = {f: sum(v) / len(v) for f, v in sorted(fam.items())}
        out[variant] = entry
    noise = {}
    for tag in "cde":
        b = _details(f"noise_rm_plus_seeds_{tag}")
        if b is not None and "rm_plus" in b:
            noise[tag] = per_problem_delta("rm_plus", b["rm_plus"], ref["rm_plus"], sds)
    if noise:
        insts = sorted(next(iter(noise.values())))
        out["rm_plus_seed_noise_per_problem_sd"] = {
            t: std([d[i] for i in insts]) for t, d in noise.items()}
    return out


def main() -> None:
    cases = rows()
    honest_names = [n for n in cases if n.startswith(("noise_", "better_", "variant_", "weaker_", "fieldstarts_"))]
    cohorts = {
        "ALL": [reference[r] for r in reference] + [m for _, m in cases.values()],
        "HONEST": [reference[r] for r in reference] + [cases[n][1] for n in honest_names],
    }
    sds = {c: {m: std([row[m] for row in rows_]) for m in METRICS} for c, rows_ in cohorts.items()}
    summary = {"cohort_std": sds, "cases": {}}
    for name, (row, metrics) in cases.items():
        base = reference.get(row)
        if base is None:  # a new row name: compare with the reference rm_plus row
            base = reference["rm_plus"]
        summary["cases"][name] = {"row": row, "metrics": metrics,
                                  "delta_vs_reference": {c: delta(metrics, base, sds[c]) for c in cohorts}}
    for c in cohorts:
        noise = [0.0] + [summary["cases"][n]["delta_vs_reference"][c] for n in sorted(cases)
                         if n.startswith("noise_rm_plus")]
        summary[f"rm_plus_seed_noise_{c}"] = {"deltas": noise, "range": max(noise) - min(noise), "std": std(noise)}
        print(c, "rm_plus seed noise", summary[f"rm_plus_seed_noise_{c}"])
        for variant in sorted({n[len("paired_"):].rsplit("_seeds_", 1)[0] for n in cases if n.startswith("paired_")}):
            paired = {"official": summary["cases"].get(f"better_{variant}", {}).get("delta_vs_reference", {}).get(c)}
            for tag in ("c", "d", "e"):
                v = summary["cases"].get(f"paired_{variant}_seeds_{tag}")
                r = summary["cases"].get(f"noise_rm_plus_seeds_{tag}")
                if v and r:  # variant minus reference, both on start set <tag>
                    paired[f"seeds_{tag}"] = v["delta_vs_reference"][c] - r["delta_vs_reference"][c]
            summary.setdefault(f"paired_vs_rm_plus_{c}", {})[variant] = paired
            print(c, "paired", variant, "- rm_plus:", {k: round(x, 3) for k, x in paired.items() if x is not None})
    summary["paired_per_problem"] = paired_per_problem(cases, sds["ALL"])
    print("paired per problem", json.dumps(summary["paired_per_problem"], indent=1))
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    short = {"value_percent_best": "best%", "value_avg_rank": "vrank", "utility_gain_mean": "gain",
             "convergence_percent_reached": "conv%", "convergence_percent_best": "fast%",
             "convergence_avg_rank": "crank", "log10_iterations_mean": "log10it",
             "restart_convergence_percent": "starts%"}
    lines = ["| case | row | " + " | ".join(short[m] for m in METRICS) + " | Δ ALL | Δ HONEST |",
             "|" + "---|" * (len(METRICS) + 4)]
    for r in ("rm_plus", "gd"):
        lines.append(f"| reference | {r} | " + " | ".join(f"{reference[r][m]:.3f}" for m in METRICS) + " | 0 | 0 |")
    for name, info in summary["cases"].items():
        d = info["delta_vs_reference"]
        lines.append(f"| {name} | {info['row']} | " + " | ".join(f"{info['metrics'][m]:.3f}" for m in METRICS)
                     + f" | {d['ALL']:+.3f} | {d['HONEST']:+.3f} |")
    (HERE / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

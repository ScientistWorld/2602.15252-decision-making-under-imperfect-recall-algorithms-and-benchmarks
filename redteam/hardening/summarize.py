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


def main() -> None:
    cases = rows()
    honest_names = [n for n in cases if n.startswith(("noise_", "better_", "variant_", "weaker_"))]
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
            for tag in ("b", "c", "d"):
                v = summary["cases"].get(f"paired_{variant}_seeds_{tag}")
                r = summary["cases"].get(f"noise_rm_plus_seeds_{tag}")
                if v and r:  # variant minus reference, both on start set <tag>
                    paired[f"seeds_{tag}"] = v["delta_vs_reference"][c] - r["delta_vs_reference"][c]
            summary.setdefault(f"paired_vs_rm_plus_{c}", {})[variant] = paired
            print(c, "paired", variant, "- rm_plus:", {k: round(x, 3) for k, x in paired.items() if x is not None})
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

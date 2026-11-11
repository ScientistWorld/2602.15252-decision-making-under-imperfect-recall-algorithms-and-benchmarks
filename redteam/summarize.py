"""Rank collected scores with explicitly disclosed cohort normalizers.

External future-attempt standard deviations are unknowable at audit time.
The JSON therefore saves both raw metrics and these cohort-specific ranks.
"""
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "redteam"
EXP = "first_order_optimizer_aggregate"


def read(p):
    return json.loads(p.read_text())


def main():
    defs = read(AUDIT / "fixtures/scoring_reference.json")["experiments"][EXP]
    reference = read(AUDIT / "reference/scores_test.json")["experiments"][EXP]["results"]
    rows = {}
    for folder in sorted(AUDIT.iterdir()):
        if not folder.is_dir() or not (folder / "status.json").exists():
            continue
        status = read(folder / "status.json")
        row = {"status": status}
        if (folder / "scores_test.json").exists() and status.get("test_exit_code") == 0:
            results = read(folder / "scores_test.json")["experiments"][EXP]["results"]
            method = status["target_method"]
            row["metrics"] = results.get(method, {})
            row["reference_method"] = method
            row["scored_methods"] = sorted(results)
        rows[folder.name] = row
    # Two panels: all attempts and just honest variants. All positive gains
    # use higher_is_better and ABS(coefficient); raw units cancel via std.
    panels = {
        "all_successful_audit_attempts": [n for n, r in rows.items() if r.get("metrics")],
        "honest_variants": [n for n in ("reference", "reference_seed_123", "reference_seed_234", "reference_seed_345",
                                      "stronger_coordinate", "longer_rm_plus", "weaker_one_step")
                            if rows.get(n, {}).get("metrics")],
    }
    # This concrete cohort includes the failed candidate itself in the
    # variance estimate, matching the stated ranking rule exactly.
    if rows.get("failed_task_tradeoff_shortcut", {}).get("metrics"):
        panels["honest_plus_failed_task_shortcut"] = panels["honest_variants"] + ["failed_task_tradeoff_shortcut"]
    normalizers = {}
    for panel, names in panels.items():
        sigma = {}
        for metric, definition in defs["metrics"].items():
            values = [rows[n]["metrics"][metric] for n in names]
            sigma[metric] = statistics.pstdev(values) if len(values) > 1 else 0.
        normalizers[panel] = sigma
        # Apply each panel's fixed normalizer to ALL rows, allowing direct
        # comparisons without changing the denominator for each shortcut.
        for name, row in rows.items():
            if not row.get("metrics"):
                continue
            baseline = reference[row["reference_method"]]
            parts = {}
            for metric, definition in defs["metrics"].items():
                if not definition["coefficient"] or sigma[metric] == 0:
                    continue
                direction = 1 if definition["higher_is_better"] else -1
                parts[metric] = (abs(definition["coefficient"]) * direction
                                 * (row["metrics"][metric] - baseline[metric]) / sigma[metric])
            row.setdefault("ranks", {})[panel] = {"improvement": sum(parts.values()) * defs["weight"], "contributions": parts}
    seeds = [rows[n]["metrics"] for n in ("reference_seed_123", "reference_seed_234", "reference_seed_345")
             if rows.get(n, {}).get("metrics")]
    spread = {m: {"min": min(s[m] for s in seeds), "max": max(s[m] for s in seeds),
                  "range": max(s[m] for s in seeds) - min(s[m] for s in seeds)} for m in defs["metrics"]} if seeds else {}
    rank_spread = {}
    for panel in panels:
        values = [rows[n]["ranks"][panel]["improvement"] for n in
                  ("reference_seed_123", "reference_seed_234", "reference_seed_345")
                  if "ranks" in rows.get(n, {})]
        rank_spread[panel] = {"values": values, "range": max(values) - min(values)} if values else {}
    gd_seeds = [n for n in ("gd_reference_seed_123", "gd_reference_seed_234", "gd_reference_seed_345")
                if rows.get(n, {}).get("metrics")]
    gd_spread = {}
    for panel in panels:
        values = [rows[n]["ranks"][panel]["improvement"] for n in gd_seeds]
        gd_spread[panel] = {"values": values, "range": max(values) - min(values)} if values else {}
    output = {"rank_formula": "sum weight * abs(coefficient) * signed(candidate-reference) / population_std(audit cohort)",
              "caveat": "The future ranking cohort is unknown. These scalar ranks are conditional audit-cohort ranks; raw metrics and Pareto comparisons are authoritative.",
              "cohorts": panels, "normalizers": normalizers, "seed_metric_spread": spread,
              "seed_rank_spread": rank_spread, "gd_seed_rank_spread": gd_spread,
              "attempts": rows}
    (AUDIT / "summary.json").write_text(json.dumps(output, indent=2) + "\n")
    labels = {"all_successful_audit_attempts": "rank_all", "honest_variants": "rank_honest",
              "honest_plus_failed_task_shortcut": "rank_failure_cohort"}
    lines = ["case\ttest_exit\t" + "\t".join(labels[p] for p in panels)
             + "\tvalue%\tvalue_rank\tutility_gap\tconverged%\tfastest%\tconv_rank\tlog_iters\tlog_gap\trestarts%"]
    for name, row in rows.items():
        m = row.get("metrics")
        if not m:
            lines.append(f"{name}\t{row['status'].get('test_exit_code', 'exception')}\tNO_NEW_SCORE")
            continue
        columns = [name, str(row["status"]["test_exit_code"])]
        columns += [f"{row['ranks'][p]['improvement']:.6f}" for p in panels]
        columns += [f"{m[k]:.9g}" for k in ("value_percent_best", "value_avg_rank", "value_avg_gap_to_best",
                   "convergence_percent_reached", "convergence_percent_best", "convergence_avg_rank",
                   "selected_log10_iterations_to_gap_mean", "selected_log10_kkt_gap_mean", "restart_convergence_percent")]
        lines.append("\t".join(columns))
    text = "\n".join(lines) + "\n"
    (AUDIT / "summary.tsv").write_text(text)
    print(text)


if __name__ == "__main__":
    main()

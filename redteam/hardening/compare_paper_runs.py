"""Compare this gym's solver runs on the training problems with the authors' logged runs.

The training evaluator starts every solver from the paper's own starting points
(seeds 33-44), so each run of method/solver.py and baseline/solver.py should
retrace the corresponding run in the paper's logs (eval/train/field.json).

    python redteam/hardening/compare_paper_runs.py results/train_details.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROW_TO_CONFIG = {"rm": "rm", "rm_plus": "rm+", "prm": "prm", "prm_plus": "prm+",
                 "gd": "pgd_1e-1", "ogd": "optgd_1e-2", "ams": "ams_a1e-1_b0.9_c0.999"}


def main() -> None:
    details = json.loads(Path(sys.argv[1]).read_text())["records"]
    field = json.loads((ROOT / "eval/train/field.json").read_text())
    out = {}
    for row, cfg in ROW_TO_CONFIG.items():
        if row not in details:
            continue
        same_iters = same_status = total = 0
        max_value_diff = 0.0
        mismatches = []
        for inst, recs in details[row].items():
            paper = field["instances"][inst]["configs"][cfg]
            for seed, (mine, (calls, value, gap)) in enumerate(zip(recs, paper), start=33):
                total += 1
                conv_paper = gap <= field["target_gap"]
                same_status += mine["converged"] == conv_paper
                same_iters += mine["calls"] == calls
                if mine["value"] is not None and mine["converged"] and conv_paper:
                    max_value_diff = max(max_value_diff, abs(mine["value"] - value) / max(1.0, abs(value)))
                if mine["calls"] != calls and len(mismatches) < 8:
                    mismatches.append([inst, seed, mine["calls"], calls])
        out[row] = {"runs": total, "same_iterations": same_iters, "same_convergence": same_status,
                    "max_rel_value_diff_when_both_converged": max_value_diff, "examples": mismatches}
        print(row, out[row])
    (Path(__file__).resolve().parent / "paper_run_agreement.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()

"""Check that a fresh held-out run reproduces an earlier run's per-run records.

    python redteam/hardening/compare_reference_runs.py OLD_DETAILS NEW_DETAILS

For every (method, problem) present in both files, counts runs whose iteration
count, convergence status and utility (to 1e-9 relative) are identical.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    old_path, new_path = Path(sys.argv[1]), Path(sys.argv[2])
    if not old_path.is_file() or not new_path.is_file():
        print("compare_reference_runs: missing file, skipped")
        return
    old = json.loads(old_path.read_text())["records"]
    new = json.loads(new_path.read_text())["records"]
    report = {}
    for m in sorted(set(old) & set(new)):
        same = total = 0
        diffs = []
        for inst in sorted(set(old[m]) & set(new[m])):
            for k, (a, b) in enumerate(zip(old[m][inst], new[m][inst])):
                total += 1
                ok = a["calls"] == b["calls"] and a["converged"] == b["converged"] and (
                    a["value"] == b["value"] or (a["value"] is not None and b["value"] is not None and
                                                 abs(a["value"] - b["value"]) <= 1e-9 * max(1.0, abs(a["value"]))))
                same += ok
                if not ok and len(diffs) < 3:
                    diffs.append([inst, k, a["calls"], b["calls"]])
        report[m] = {"runs_compared": total, "identical": same, "examples": diffs}
        print(m, report[m])
    out = Path(__file__).resolve().parent / "reference_rerun_agreement.json"
    out.write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()

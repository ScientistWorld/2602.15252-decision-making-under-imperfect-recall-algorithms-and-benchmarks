"""Freeze the held-out comparator field (offline, once).

Runs the paper's comparator configurations (eval/test/field_configs.json) on the
held-out problems from the evaluator's fixed starting points, through the same
oracle protocol and budget as any submission, and stores every run's final
iteration count, utility and KKT gap in eval/test/field.json.  Afterwards the
comparators are data: changing solver code does not change them.

Step-size / hyper-parameter grids follow the paper (GD, OGD: per-problem best
step size; AMSGrad: per-problem best setting), restricted to the settings that
the paper's own runs ever selected on the training problems.

    python eval/test/build_field.py [--resume]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from evaluate import BUDGET, INSTANCE_TIMEOUT, MESSAGE_TIMEOUT, START_SEEDS, TARGET_GAP  # noqa: E402
from harness import TreeOracle, load_instance, paper_start, run_solver  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", default=str(HERE / "field_configs.json"))
    parser.add_argument("--output", default=str(HERE / "field.json"))
    parser.add_argument("--partial", default=str(HERE / "field_partial.json"))
    parser.add_argument("--instances", default="", help="diagnostics: comma-separated subset")
    args = parser.parse_args()
    spec = json.loads(Path(args.configs).read_text())
    partial = Path(args.partial)
    done = json.loads(partial.read_text()) if partial.is_file() else {}
    names = sorted(p.stem for p in (HERE / "instances").glob("*.json"))
    if args.instances:
        names = [n for n in names if n in set(args.instances.split(","))]
    for inst in names:
        oracle = TreeOracle(load_instance(HERE / "instances" / f"{inst}.json"))
        starts = [paper_start(oracle.sizes, s) for s in START_SEEDS]
        entry = done.setdefault(inst, {"uniform_value": None, "configs": {}})
        entry["uniform_value"] = float(oracle.evaluate(oracle.uniform())[0][0])
        for cfg, command in spec["configs"].items():
            if cfg in entry["configs"]:
                continue
            cmd = [sys.executable] + command[1:] if command[0] in ("python", "python3") else command
            t0 = time.monotonic()
            recs = run_solver(cmd, oracle, starts, BUDGET, TARGET_GAP, ROOT, MESSAGE_TIMEOUT, INSTANCE_TIMEOUT)
            bad = [r for r in recs if r["failed"]]
            if bad:
                raise RuntimeError(f"comparator {cfg} failed on {inst}: {bad[0]['reason']}")
            entry["configs"][cfg] = [[r["calls"], r["value"], r["gap"]] for r in recs]
            partial.write_text(json.dumps(done))
            print(f"[field] {inst:16s} {cfg:24s} {time.monotonic() - t0:7.1f}s "
                  f"solved {sum(r['converged'] for r in recs)}/12 "
                  f"iters {sorted(r['calls'] for r in recs)[6]}", file=sys.stderr, flush=True)
    out = {"slice": "test", "budget": BUDGET, "target_gap": TARGET_GAP, "start_seeds": START_SEEDS,
           "source": "eval/test/build_field.py", "families": spec["families"],
           "instances": {k: done[k] for k in names}}
    Path(args.output).write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

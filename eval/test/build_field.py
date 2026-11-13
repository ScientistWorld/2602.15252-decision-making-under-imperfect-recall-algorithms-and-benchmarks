"""Freeze the held-out comparator field (offline, once per problem).

Runs the paper's comparator configurations (eval/test/field_configs.json) on the
held-out problems from the evaluator's fixed starting points, through the same
oracle protocol and budget as any submission, and stores every run's final
iteration count, utility and KKT gap in eval/test/field.json (plus each
problem's uniform-strategy utility and the SHA-256 of its file).  Afterwards the
comparators are data: changing solver code does not change them.

Problems already in eval/test/field.json (or in the resume file) are kept as
they are; only missing (problem, configuration) pairs are run, in parallel.

Step-size / hyper-parameter grids follow the paper (GD, OGD: per-problem best
step size; AMSGrad: per-problem best setting), restricted to the settings that
the paper's own runs ever selected on the training problems.

    python eval/test/build_field.py [--workers N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from evaluate import BUDGET, INSTANCE_TIMEOUT, MESSAGE_TIMEOUT, START_SEEDS, TARGET_GAP  # noqa: E402
from harness import TreeOracle, default_workers, paper_start, run_solver, run_tasks  # noqa: E402

_ORACLES: dict = {}


def _work(task):
    inst, cfg, cmd = task
    oracle = _ORACLES[inst]
    starts = [paper_start(oracle.sizes, s) for s in START_SEEDS]
    t0 = time.monotonic()
    recs = run_solver(cmd, oracle, starts, BUDGET, TARGET_GAP, ROOT, MESSAGE_TIMEOUT, INSTANCE_TIMEOUT)
    return recs, time.monotonic() - t0


def main() -> None:
    global _ORACLES
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", default=str(HERE / "field_configs.json"))
    parser.add_argument("--output", default=str(HERE / "field.json"))
    parser.add_argument("--partial", default=str(HERE / "field_partial.json"))
    parser.add_argument("--instances", default="", help="diagnostics: comma-separated subset")
    parser.add_argument("--workers", type=int, default=0)
    args = parser.parse_args()
    spec = json.loads(Path(args.configs).read_text())
    partial = Path(args.partial)
    done = json.loads(partial.read_text()) if partial.is_file() else {}
    out_path = Path(args.output)
    if out_path.is_file():  # problems frozen earlier stay exactly as they are
        old = json.loads(out_path.read_text())
        if old.get("start_seeds") == START_SEEDS and old.get("budget") == BUDGET:
            for k, v in old["instances"].items():
                done.setdefault(k, v)
    names = sorted(p.stem for p in (HERE / "instances").glob("*.json"))
    if args.instances:
        names = [n for n in names if n in set(args.instances.split(","))]
    tasks = []
    for inst in names:
        data = (HERE / "instances" / f"{inst}.json").read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        entry = done.setdefault(inst, {"uniform_value": None, "configs": {}})
        if entry.get("sha256") not in (None, digest):
            raise RuntimeError(f"{inst} changed since its comparators were frozen")
        entry["sha256"] = digest
        oracle = TreeOracle(json.loads(data))
        _ORACLES[inst] = oracle
        entry["uniform_value"] = float(oracle.evaluate(oracle.uniform())[0][0])
        for cfg, command in spec["configs"].items():
            if cfg not in entry["configs"]:
                cmd = [sys.executable] + command[1:] if command[0] in ("python", "python3") else command
                tasks.append((inst, cfg, cmd))
    tasks.sort(key=lambda t: (-_ORACLES[t[0]].n, t[0], t[1]))  # large problems first
    workers = args.workers or default_workers()
    print(f"[field] {len(tasks)} comparator runs to do on {workers} worker(s)", file=sys.stderr, flush=True)

    def on_done(task, result):
        inst, cfg, _ = task
        recs, secs = result
        bad = [r for r in recs if r["failed"]]
        if bad:
            raise RuntimeError(f"comparator {cfg} failed on {inst}: {bad[0]['reason']}")
        done[inst]["configs"][cfg] = [[r["calls"], r["value"], r["gap"]] for r in recs]
        partial.write_text(json.dumps(done))
        print(f"[field] {inst:16s} {cfg:24s} {secs:7.1f}s "
              f"solved {sum(r['converged'] for r in recs)}/12 "
              f"iters {sorted(r['calls'] for r in recs)[6]}", file=sys.stderr, flush=True)

    run_tasks(tasks, _work, workers, on_done)
    out = {"slice": "test", "budget": BUDGET, "target_gap": TARGET_GAP, "start_seeds": START_SEEDS,
           "source": "eval/test/build_field.py", "families": spec["families"],
           "instances": {k: done[k] for k in names}}
    out_path.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()

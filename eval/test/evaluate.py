"""Held-out test evaluation: run every solver on disk on the hidden problems.

    python eval/test/evaluate.py            # what scripts/evaluate_test.sh runs

Solvers are discovered from scripts/solvers.json ({"name": {"command": [...]}}).
Every comparator family of the frozen field (eval/test/field.json) always gets a
row; a family with no runnable solver, or a solver that fails, is scored with the
worst value of every metric.  Problems, starting points, iteration budget,
convergence threshold and comparators are fixed here; nothing a solver writes
to disk is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from harness import TreeOracle, default_workers, load_registry, paper_start, run_solver, run_tasks  # noqa: E402
from metrics import METRICS, build_field, failed_records, method_metrics  # noqa: E402

SLICE = "test"
EXPERIMENT = "first_order_optimizer_aggregate"
BUDGET = 6000
TARGET_GAP = 1e-6
# Starting points of the scored solvers (paper_start(sizes, seed) per problem).  They
# differ from the starting points the frozen comparators were run from (stored in
# field.json), so no solver is matched start-for-start with a comparator: otherwise a
# solver could change its ranks by using or ignoring the start it is given.
START_SEEDS = list(range(1001, 1013))
MESSAGE_TIMEOUT = 300.0      # one solver step
INSTANCE_TIMEOUT = 1800.0    # one solver on one problem (12 starts in lockstep)
METHOD_TIME_PER_PROBLEM = 45.0  # one solver on all problems: 45 s x number of problems
# These are hard failure limits for runaway solvers, not metrics.  The slowest
# reference solver (OGD, step 0.01) needs about 24 s per problem on one CPU.
# With W parallel workers the per-solver limit applies to wall time summed over
# its tasks divided by W.


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def evaluate(registry_path: Path, field_path: Path, only=None, seeds=None, cache_path=None, details_path=None,
             workers=None):
    _set_hidden(False)  # a killed earlier evaluation may have left the hidden files unreadable
    raw = json.loads(field_path.read_text())
    if raw["budget"] != BUDGET or raw["target_gap"] != TARGET_GAP:
        raise ValueError("field was built with a different budget or threshold")
    field = build_field(raw)
    seeds = seeds or START_SEEDS
    field_seeds = raw.get("start_seeds") or []
    registry = load_registry(registry_path, ROOT)
    methods = sorted(set(raw["families"]) | set(registry))
    if only:
        methods = [m for m in methods if m in only]
    cache = {}
    if cache_path and Path(cache_path).is_file():
        cache = json.loads(Path(cache_path).read_text())
        if cache.get("_seeds") != list(seeds):  # records from other starting points: not reused
            cache = {}
    cache["_seeds"] = list(seeds)
    records = {m: {} for m in methods}
    spent = {m: 0.0 for m in methods}
    # Everything a solver could tamper with on disk is read before any solver runs,
    # and the files that hold or regenerate the hidden problems are made
    # unreadable while solvers run (solvers only get the counted oracle).
    _set_hidden(False)
    oracles = {}
    for inst in sorted(field):
        data = (HERE / "instances" / f"{inst}.json").read_bytes()
        want = raw["instances"][inst].get("sha256")
        if want and hashlib.sha256(data).hexdigest() != want:
            raise ValueError(f"instance {inst} differs from the one the comparator field was built on")
        oracles[inst] = TreeOracle(json.loads(data))
    _set_hidden(True)
    try:
        _run_all(field, methods, registry, oracles, seeds, cache, cache_path, records, spent,
                 workers or default_workers(), field_seeds)
    finally:
        _set_hidden(False)
    results = {m: method_metrics(m, records[m], field, BUDGET) for m in methods}
    if details_path:
        Path(details_path).write_text(json.dumps({"seeds": seeds, "records": records}, indent=None))
    return results


# Files that hold or regenerate the hidden problems, or reveal per-problem results of
# the comparators (best known utilities) or their starting points: unreadable while
# solvers run.
HIDDEN = (("instances", 0o755), ("generate_instances.py", 0o644), ("field.json", 0o644),
          ("field_partial.json", 0o644), ("build_field.py", 0o644))


def _set_hidden(hidden: bool) -> None:
    for name, mode in HIDDEN:
        try:
            os.chmod(HERE / name, 0 if hidden else mode)
        except OSError:
            pass  # e.g. a read-only mount


_ORACLES: dict = {}  # filled before worker processes are forked
_FIELD_SEEDS: list = []


def _work(task):
    method, inst, command, seeds = task
    oracle = _ORACLES[inst]
    starts = [paper_start(oracle.sizes, s) for s in seeds]
    t0 = time.monotonic()
    recs = run_solver(command, oracle, starts, BUDGET, TARGET_GAP, ROOT, MESSAGE_TIMEOUT, INSTANCE_TIMEOUT)
    return recs, time.monotonic() - t0


def _run_all(field, methods, registry, oracles, seeds, cache, cache_path, records, spent, workers,
             field_seeds=()) -> None:
    global _ORACLES, _FIELD_SEEDS
    _ORACLES, _FIELD_SEEDS = oracles, list(field_seeds)
    limit = METHOD_TIME_PER_PROBLEM * len(field) * workers
    tasks = []
    for inst in sorted(field, key=lambda i: (-oracles[i].n, i)):  # large problems first
        for m in methods:
            key = f"{m}|{inst}"
            if key in cache:
                records[m][inst] = cache[key]
            elif m not in registry:
                records[m][inst] = failed_records(len(seeds), "no solver registered under this name")
            else:
                tasks.append((m, inst, registry[m], seeds))
    log(f"[{SLICE}] {len(tasks)} solver x problem tasks on {workers} worker(s)"
        + (" [starts shared with the comparator field: diagnostics only]" if set(seeds) & set(_FIELD_SEEDS) else ""))

    def skip(task):
        if spent[task[0]] > limit:
            return failed_records(len(seeds), "method time limit exhausted"), 0.0
        return None

    def on_done(task, result):
        m, inst = task[0], task[1]
        recs, secs = result
        spent[m] += secs
        records[m][inst] = recs
        log(f"[{SLICE}] {inst:16s} {m:24s} {secs:7.1f}s "
            f"solved {sum(r['converged'] for r in recs)}/{len(recs)} "
            f"failed {sum(r['failed'] for r in recs)} "
            f"iters {sorted(r['calls'] for r in recs)[len(recs) // 2]}")
        if cache_path:
            cache[f"{m}|{inst}"] = recs
            Path(cache_path).write_text(json.dumps(cache))

    run_tasks(tasks, _work, workers, on_done, skip)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--registry", default=str(ROOT / "scripts" / "solvers.json"))
    parser.add_argument("--output", default=str(ROOT / "scoring" / "scores_test.json"))
    parser.add_argument("--field", default=str(HERE / "field.json"))
    parser.add_argument("--only", default="", help="diagnostics: comma-separated subset of methods")
    parser.add_argument("--start-seeds", default="", help="diagnostics: comma-separated start seeds")
    parser.add_argument("--cache", default="", help="diagnostics: resume file for per-run records")
    parser.add_argument("--details", default="", help="diagnostics: write per-run records here")
    parser.add_argument("--workers", type=int, default=0,
                        help="parallel solver x problem tasks (default: one per available CPU)")
    args = parser.parse_args()
    only = {m for m in args.only.split(",") if m} or None
    seeds = [int(s) for s in args.start_seeds.split(",") if s] or None
    results = evaluate(Path(args.registry), Path(args.field), only, seeds, args.cache or None, args.details or None,
                       args.workers or None)
    scores = {"_slice": SLICE, "experiments": {EXPERIMENT: {"results": {
        m: {k: results[m][k] for k in METRICS} for m in sorted(results)}}}}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scores, indent=2) + "\n")
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()

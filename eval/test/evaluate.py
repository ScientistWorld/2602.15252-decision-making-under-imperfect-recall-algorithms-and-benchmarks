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
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from harness import TreeOracle, load_instance, load_registry, paper_start, run_solver  # noqa: E402
from metrics import METRICS, build_field, failed_records, method_metrics  # noqa: E402

SLICE = "test"
EXPERIMENT = "first_order_optimizer_aggregate"
BUDGET = 6000
TARGET_GAP = 1e-6
START_SEEDS = [913452, 270118, 655307, 481926, 107733, 839214, 362580, 728491, 194067, 566812, 33159, 947205]
MESSAGE_TIMEOUT = 300.0
INSTANCE_TIMEOUT = 1200.0
METHOD_TIMEOUT = 5400.0


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def evaluate(registry_path: Path, field_path: Path, only=None, seeds=None, cache_path=None, details_path=None):
    raw = json.loads(field_path.read_text())
    if raw["budget"] != BUDGET or raw["target_gap"] != TARGET_GAP:
        raise ValueError("field was built with a different budget or threshold")
    field = build_field(raw)
    seeds = seeds or START_SEEDS
    registry = load_registry(registry_path, ROOT)
    methods = sorted(set(raw["families"]) | set(registry))
    if only:
        methods = [m for m in methods if m in only]
    cache = {}
    if cache_path and Path(cache_path).is_file():
        cache = json.loads(Path(cache_path).read_text())
    records = {m: {} for m in methods}
    spent = {m: 0.0 for m in methods}
    # Everything a solver could tamper with on disk is read before any solver runs,
    # and the files that hold or regenerate the hidden problems are made
    # unreadable while solvers run (solvers only get the counted oracle).
    _set_hidden(False)
    oracles = {inst: TreeOracle(load_instance(HERE / "instances" / f"{inst}.json")) for inst in sorted(field)}
    _set_hidden(True)
    try:
        _run_all(field, methods, registry, oracles, seeds, cache, cache_path, records, spent)
    finally:
        _set_hidden(False)
    results = {m: method_metrics(m, records[m], field, BUDGET) for m in methods}
    if details_path:
        Path(details_path).write_text(json.dumps({"seeds": seeds, "records": records}, indent=None))
    return results


HIDDEN = (("instances", 0o755), ("generate_instances.py", 0o644))


def _set_hidden(hidden: bool) -> None:
    for name, mode in HIDDEN:
        try:
            os.chmod(HERE / name, 0 if hidden else mode)
        except OSError:
            pass  # e.g. a read-only mount


def _run_all(field, methods, registry, oracles, seeds, cache, cache_path, records, spent) -> None:
    for inst in sorted(field):
        oracle = oracles[inst]
        starts = [paper_start(oracle.sizes, s) for s in seeds]
        for m in methods:
            key = f"{m}|{inst}"
            if key in cache:
                records[m][inst] = cache[key]
                continue
            if m not in registry:
                recs = failed_records(len(starts), "no solver registered under this name")
            elif spent[m] > METHOD_TIMEOUT:
                recs = failed_records(len(starts), "method time limit exhausted")
            else:
                t0 = time.monotonic()
                recs = run_solver(registry[m], oracle, starts, BUDGET, TARGET_GAP, ROOT,
                                  MESSAGE_TIMEOUT, INSTANCE_TIMEOUT)
                spent[m] += time.monotonic() - t0
                log(f"[{SLICE}] {inst:16s} {m:24s} {time.monotonic() - t0:7.1f}s "
                    f"solved {sum(r['converged'] for r in recs)}/{len(recs)} "
                    f"failed {sum(r['failed'] for r in recs)} "
                    f"iters {sorted(r['calls'] for r in recs)[len(recs) // 2]}")
            records[m][inst] = recs
            if cache_path:
                cache[key] = recs
                Path(cache_path).write_text(json.dumps(cache))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--registry", default=str(ROOT / "scripts" / "solvers.json"))
    parser.add_argument("--output", default=str(ROOT / "scoring" / "scores_test.json"))
    parser.add_argument("--field", default=str(HERE / "field.json"))
    parser.add_argument("--only", default="", help="diagnostics: comma-separated subset of methods")
    parser.add_argument("--start-seeds", default="", help="diagnostics: comma-separated start seeds")
    parser.add_argument("--cache", default="", help="diagnostics: resume file for per-run records")
    parser.add_argument("--details", default="", help="diagnostics: write per-run records here")
    args = parser.parse_args()
    only = {m for m in args.only.split(",") if m} or None
    seeds = [int(s) for s in args.start_seeds.split(",") if s] or None
    results = evaluate(Path(args.registry), Path(args.field), only, seeds, args.cache or None, args.details or None)
    scores = {"_slice": SLICE, "experiments": {EXPERIMENT: {"results": {
        m: {k: results[m][k] for k in METRICS} for m in sorted(results)}}}}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scores, indent=2) + "\n")
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()

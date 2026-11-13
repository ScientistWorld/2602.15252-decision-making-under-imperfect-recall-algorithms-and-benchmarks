"""Training-slice evaluation: run every solver on disk on the paper's public problems.

    python eval/train/evaluate.py           # what scripts/evaluate_train.sh runs

Same interface and metrics as the held-out evaluation.  The problems are the
paper's own small/medium benchmark instances (data/instances/train/), the
comparators are the paper's own logged runs (eval/train/field.json, from the
paper's starting points, seeds 33-44).  Scored solvers start from other random
points (seeds 45-56), so that no solver is matched start-for-start with a
comparator (as on the held-out slice).
Solvers are discovered from scripts/solvers.json.
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

from harness import TreeOracle, load_instance, load_registry, paper_start, run_solver  # noqa: E402
from metrics import METRICS, build_field, failed_records, method_metrics  # noqa: E402

SLICE = "train"
EXPERIMENT = "first_order_optimizer_aggregate"
INSTANCES = ROOT / "data" / "instances" / "train"
BUDGET = 6000
TARGET_GAP = 1e-6
PAPER_SEEDS = list(range(33, 45))   # starts of the authors' logged runs (the comparators)
START_SEEDS = list(range(45, 57))   # starts of the scored solvers
MESSAGE_TIMEOUT = 300.0
INSTANCE_TIMEOUT = 1200.0
METHOD_TIMEOUT = 5400.0


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def evaluate(registry_path: Path, field_path: Path, only=None, cache_path=None, details_path=None, seeds=None):
    raw = json.loads(field_path.read_text())
    if raw["budget"] != BUDGET or raw["target_gap"] != TARGET_GAP or raw["start_seeds"] != PAPER_SEEDS:
        raise ValueError("field was built with different settings")
    seeds = seeds or START_SEEDS
    field = build_field(raw)
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
    # Everything a solver could tamper with on disk is read before any solver runs.
    oracles = {inst: TreeOracle(load_instance(INSTANCES / f"{inst}.json")) for inst in sorted(field)}
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
    results = {m: method_metrics(m, records[m], field, BUDGET) for m in methods}
    if details_path:
        Path(details_path).write_text(json.dumps({"seeds": seeds, "records": records}))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--registry", default=str(ROOT / "scripts" / "solvers.json"))
    parser.add_argument("--output", default=str(ROOT / "scoring" / "scores_train.json"))
    parser.add_argument("--field", default=str(HERE / "field.json"))
    parser.add_argument("--only", default="", help="comma-separated subset of methods")
    parser.add_argument("--cache", default="", help="resume file for per-run records")
    parser.add_argument("--details", default="", help="write per-run records here")
    parser.add_argument("--start-seeds", default="",
                        help="diagnostics: comma-separated start seeds (e.g. the paper's 33-44 to retrace its logs)")
    args = parser.parse_args()
    only = {m for m in args.only.split(",") if m} or None
    seeds = [int(x) for x in args.start_seeds.split(",") if x] or None
    results = evaluate(Path(args.registry), Path(args.field), only, args.cache or None, args.details or None, seeds)
    scores = {"_slice": SLICE, "experiments": {EXPERIMENT: {"results": {
        m: {k: results[m][k] for k in METRICS} for m in sorted(results)}}}}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scores, indent=2) + "\n")
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()

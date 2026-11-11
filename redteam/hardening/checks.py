"""Correctness checks of the evaluator's oracle (run inside the container).

1. Vectorised oracle vs the pure-Python reference evaluator (data/irtree.py) on
   every training and held-out problem at random strategies.
2. Utility and KKT gap at the paper's exact starting points (seed 33..44) vs the
   iteration-0 lines of the authors' logs.
3. Oracle cost per batched call (12 strategies) per problem.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval" / "train"))
from data import irtree  # noqa: E402
from harness import TreeOracle, paper_start  # noqa: E402  (training copy)

RUNS = ROOT / "data" / "downloads" / "paper_runs" / "codefolder_url" / "runs"
LINE0 = re.compile(r"iter 0 \| time [\d.e+-]+ \| value ([\d.e+-]+) \| gap ([\d.e+-]+)")


def main() -> None:
    report = {"oracle_vs_reference": {}, "paper_iteration0": {}, "timing_ms": {}}
    rng = np.random.default_rng(0)
    index = json.loads((ROOT / "data/instances/train/index.json").read_text())
    paths = sorted((ROOT / "data/instances/train").glob("*_*.json")) + sorted((ROOT / "eval/test/instances").glob("*.json"))
    worst = 0.0
    for path in paths:
        tree = json.loads(path.read_text())
        o = TreeOracle(tree)
        X = np.stack([np.concatenate([rng.dirichlet(np.ones(s)) for s in o.sizes]) for _ in range(3)])
        v, G, gap = o.evaluate(X)
        err = 0.0
        for b in range(len(X)):
            rv, rg = irtree.evaluate(tree, list(X[b]))
            rgap = irtree.kkt_gap(tree["infoset_sizes"], list(X[b]), rg)
            scale = max(1.0, abs(rv), float(np.max(np.abs(rg))))
            err = max(err, abs(rv - v[b]) / scale, float(np.max(np.abs(np.asarray(rg) - G[b]))) / scale,
                      abs(rgap - gap[b]) / scale)
        worst = max(worst, err)
        key = f"{path.parent.name}/{path.stem}"
        report["oracle_vs_reference"][key] = err
        Xb = np.repeat(X[:1], 12, axis=0)
        o.evaluate(Xb)
        t0 = time.perf_counter()
        for _ in range(20):
            o.evaluate(Xb)
        report["timing_ms"][key] = 1000 * (time.perf_counter() - t0) / 20
        if path.parent.name == "train":
            fam, size, game = index[path.stem]["paper_file"].split("/")[1:4]
            game = game[:-4]
            errs = []
            for seed in range(33, 45):
                log = RUNS / fam / size / game / str(seed) / (
                    f"{game}__algo-rm+__seed-{seed}__maxiter-6000__timelimit-14400.0__tol-1e-06.log")
                m = LINE0.search(log.read_text())
                lv, lg = float(m.group(1)), float(m.group(2))
                x0 = paper_start(o.sizes, seed)
                pv, _, pg = o.evaluate(x0[None])
                errs.append(max(abs(pv[0] - lv) / max(1, abs(lv)), abs(pg[0] - lg) / max(1, abs(lg))))
            report["paper_iteration0"][path.stem] = max(errs)
        print(f"{key:32s} n={o.n:6d} dim={o.dim:4d} ref_err={err:.1e} "
              f"paper_it0_err={report['paper_iteration0'].get(path.stem, float('nan')):.1e} "
              f"call(12)={report['timing_ms'][key]:.2f}ms", flush=True)
    report["max_oracle_error"] = worst
    report["max_paper_iteration0_error"] = max(report["paper_iteration0"].values())
    out = Path(__file__).resolve().parent / "checks.json"
    out.write_text(json.dumps(report, indent=1) + "\n")
    print("max oracle error", worst, "max paper iteration-0 error", report["max_paper_iteration0_error"])
    assert worst < 1e-9 and report["max_paper_iteration0_error"] < 1e-9


if __name__ == "__main__":
    main()

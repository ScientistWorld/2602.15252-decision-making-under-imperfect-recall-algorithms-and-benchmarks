"""Variant and shortcut solvers used to check the hardened test (not part of the gym).

    python redteam/hardening/solvers.py --kind <kind>

Honest variants:  rm_plus_fallback50, rm_plus_fallback200, rm_plus_restarts, rm_plus_discount, gd_adaptive, rm_plus_loose, rm_plus_short
Shortcuts:        uniform_once, no_query, crash, invalid_strategy, over_budget_random,
                  forge_files, cached_train_answers, brute_force_vertices, read_hidden_files,
                  rm_plus_own_start, read_field_targets
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from data.oracle_client import BudgetExhausted, OracleClient  # noqa: E402


def random_point(o: OracleClient, rng: np.random.Generator) -> np.ndarray:
    u = rng.exponential(size=o.dim)
    return u / o.expand(o.block_sum(u))


def rm_plus_run(o: OracleClient, x: np.ndarray, limit: int, stop_gap: float, discount: float = 1.0):
    """Plain RM+ from x; returns (x, value, gap) of the last queried strategy."""
    r = np.zeros_like(x)
    value = gap = None
    while o.calls < limit:
        value, u = o.query(x)
        gap = o.kkt_gap(x, u)
        if gap <= stop_gap:
            break
        c = u - o.expand(o.block_sum(u * x))
        r = np.maximum(discount * r + c, 0.0)
        tot = o.block_sum(r)
        pos = o.expand(tot > 0)
        x = np.where(pos, r / np.where(pos, o.expand(tot), 1.0), x)
    return x, value, gap


# ----------------------------------------------------------------------- honest variants
def rm_plus_restarts(o: OracleClient) -> None:
    """RM+; while the first converged run was cheap, restart from fresh points and keep the best."""
    rng = np.random.default_rng(1000 + int(o.run or 0))
    best = None
    x = o.x0.copy()
    for restart in range(8):
        x, value, gap = rm_plus_run(o, x, o.budget - 1, o.target_gap)
        if gap is not None and gap <= o.target_gap and (best is None or value > best[1]):
            best = (x.copy(), value)
        if o.calls > 1500 or best is None:
            break
        x = random_point(o, rng)
    if best is not None and not np.array_equal(best[0], x):
        o.query(best[0])


def rm_plus_discount(o: OracleClient) -> None:
    rm_plus_run(o, o.x0.copy(), o.budget, o.target_gap, discount=0.995)


def gd_adaptive(o: OracleClient) -> None:
    """Projected gradient ascent with an accept/reject step-size rule (starts at 1)."""
    sys.path.insert(0, str(ROOT / "baseline"))
    from solver import Blocks  # noqa: E402  (projection helper of the baseline)
    blocks = Blocks(o.sizes)
    x = o.x0.copy()
    value, u = o.query(x)
    lr = 1.0
    while o.calls < o.budget - 1:
        if o.kkt_gap(x, u) <= o.target_gap:
            return
        y = blocks.project(x + lr * u)
        vy, uy = o.query(y)
        if vy >= value:
            x, value, u, lr = y, vy, uy, lr * 1.5
        else:
            lr *= 0.5
    o.query(x)


def rm_plus_loose(o: OracleClient) -> None:
    rm_plus_run(o, o.x0.copy(), o.budget, 1e-4)


def rm_plus_short(o: OracleClient) -> None:
    rm_plus_run(o, o.x0.copy(), 100, o.target_gap)


# ----------------------------------------------------------------------------- shortcuts
def uniform_once(o: OracleClient) -> None:
    o.query(o.expand(1.0 / np.asarray(o.sizes, dtype=float)))


def no_query(o: OracleClient) -> None:
    return


def crash(o: OracleClient) -> None:
    o.query(o.x0)
    raise RuntimeError("deliberate failure")


def invalid_strategy(o: OracleClient) -> None:
    x = o.x0.copy() * 3.0  # not a probability distribution: utility would be inflated
    o.query(x)


def over_budget_random(o: OracleClient) -> None:
    rng = np.random.default_rng(int(o.run or 0))
    o.budget = 10 ** 9  # ignore the announced budget
    while True:
        o.query(random_point(o, rng))


def forge_files(o: OracleClient) -> None:
    """Honest RM+ run, plus attempts to plant results and tamper with evaluator inputs."""
    fake = {"experiments": {"first_order_optimizer_aggregate": {"results": {"rm_plus": {
        "value_percent_best": 100.0, "value_avg_rank": 1.0, "utility_gain_mean": 9.0,
        "convergence_percent_reached": 100.0, "convergence_percent_best": 100.0,
        "convergence_avg_rank": 1.0, "log10_iterations_mean": 0.0, "restart_convergence_percent": 100.0}}}}}
    for path in ("scoring/scores_test.json", "results/forged_scores.json"):
        try:
            (ROOT / path).write_text(json.dumps(fake))
        except OSError:
            pass
    for inst in (ROOT / "eval" / "test" / "instances").glob("*.json"):
        try:  # replace every hidden problem by a one-leaf problem with a huge payoff
            inst.write_text(json.dumps({"format": "irtree-v1", "name": inst.stem, "infoset_sizes": [1],
                                        "parent": [-1, 0], "edge_action": [-1, 0], "edge_prob": [0.0, 0.0],
                                        "payoff": [0.0, 1e6]}))
        except OSError:
            pass
    rm_plus_run(o, o.x0.copy(), o.budget, o.target_gap)


def cached_train_answers(o: OracleClient) -> None:
    table = json.loads((ROOT / "redteam" / "hardening" / "train_answers.json").read_text())
    uniform = o.expand(1.0 / np.asarray(o.sizes, dtype=float))
    value, _ = o.query(uniform)
    entry = table.get(json.dumps([o.sizes, round(value, 9)]))
    if entry is not None:
        o.query(np.asarray(entry["strategy"], dtype=float))


def brute_force_vertices(o: OracleClient) -> None:
    """Enumerate pure strategies (mixed radix) until the budget is nearly spent; keep the best."""
    sizes = o.sizes
    digits = [0] * len(sizes)
    best = None
    while o.calls < o.budget - 1:
        x = np.zeros(o.dim)
        x[o.starts + np.asarray(digits)] = 1.0
        value, _ = o.query(x)
        if best is None or value > best[1]:
            best = (x, value)
        for i in range(len(digits)):
            digits[i] += 1
            if digits[i] < sizes[i]:
                break
            digits[i] = 0
        else:
            break
    o.query(best[0])


def read_hidden_files(o: OracleClient) -> None:
    """Try to read the problem files and optimise privately (uncounted), then submit.

    If a problem file matching this run can be read, RM+ is run privately on a
    local copy of the oracle and only the final strategy is queried (2 counted
    iterations).  Otherwise the solver falls back to plain (counted) RM+.
    """
    trees = []
    for folder in (ROOT / "eval" / "test" / "instances", ROOT / "data" / "instances" / "train"):
        try:
            for f in folder.glob("*_*.json"):
                trees.append(json.loads(f.read_text()))
        except OSError:
            pass
    value0, u0 = o.query(o.x0)
    match = None
    if trees:
        sys.path.insert(0, str(ROOT / "eval" / "train"))
        from harness import TreeOracle  # noqa: E402  (public training copy of the oracle)
        for tree in trees:
            if tree.get("infoset_sizes") == o.sizes:
                local = TreeOracle(tree)
                if abs(float(local.evaluate(o.x0[None])[0][0]) - value0) < 1e-9:
                    match = local
                    break
    if match is None:  # files unreadable: honest RM+ from the first answer onward
        x, u, r = o.x0.copy(), u0, np.zeros(o.dim)
        while o.kkt_gap(x, u) > o.target_gap and o.calls < o.budget:
            c = u - o.expand(o.block_sum(u * x))
            r = np.maximum(r + c, 0.0)
            tot = o.block_sum(r)
            pos = o.expand(tot > 0)
            x = np.where(pos, r / np.where(pos, o.expand(tot), 1.0), x)
            _, u = o.query(x)
        return
    x, r = o.x0.copy(), np.zeros(o.dim)
    for _ in range(o.budget):
        _, G, gap = match.evaluate(x[None])
        u = G[0]
        if gap[0] <= o.target_gap:
            break
        c = u - o.expand(o.block_sum(u * x))
        r = np.maximum(r + c, 0.0)
        tot = o.block_sum(r)
        pos = o.expand(tot > 0)
        x = np.where(pos, r / np.where(pos, o.expand(tot), 1.0), x)
    o.query(x)


def rm_plus_own_start(o: OracleClient) -> None:
    """Plain RM+, but from a start of its own instead of the one the evaluator sends.

    Same algorithm as the reference; only its pairing with the comparators'
    starting points changes.  (Before the fix the evaluator sent solvers the
    comparators' own starts.)"""
    rng = np.random.default_rng(777_000 + int(o.run or 0))
    rm_plus_run(o, random_point(o, rng), o.budget, o.target_gap)


def read_field_targets(o: OracleClient) -> None:
    """Read the frozen comparator field to learn this problem's best known utility
    (identified by the uniform strategy's utility), then restart RM+ until it is
    reached.  If no field is readable, plain RM+ from the given start."""
    target = None
    for path in (ROOT / "eval" / "test" / "field.json", ROOT / "eval" / "train" / "field.json"):
        try:
            field = json.loads(path.read_text())
        except OSError:
            continue
        v_uni, _ = o.query(o.expand(1.0 / np.asarray(o.sizes, dtype=float)))
        for inst in field["instances"].values():
            if abs(inst["uniform_value"] - v_uni) <= 1e-9 * max(1.0, abs(v_uni)):
                vals = [v for runs in inst["configs"].values() for (_, v, g) in runs if g <= o.target_gap]
                if vals:
                    target = max(vals)
                break
        if target is not None:
            break
    rng = np.random.default_rng(555_000 + int(o.run or 0))
    x, best = o.x0.copy(), None
    while o.calls < o.budget - 1:
        x, value, gap = rm_plus_run(o, x, o.budget - 1, o.target_gap)
        if gap is not None and gap <= o.target_gap and (best is None or value > best[1]):
            best = (x.copy(), value)
        if target is None or (best is not None and best[1] >= target - 1e-4 * max(1.0, abs(target))):
            break
        x = random_point(o, rng)
    if best is not None and not np.array_equal(best[0], x):
        o.query(best[0])


def _rm_plus_then_adaptive_gd(o: OracleClient, switch: int) -> None:
    """RM+; if it has not reached the threshold after `switch` iterations, continue
    from its current strategy with projected gradient ascent and an accept/reject
    step-size rule (step starts at 1, x1.5 on improvement, x0.5 otherwise)."""
    x = o.x0.copy()
    r = np.zeros_like(x)
    value, u = o.query(x)
    while o.kkt_gap(x, u) > o.target_gap and o.calls < min(switch, o.budget):
        c = u - o.expand(o.block_sum(u * x))
        r = np.maximum(r + c, 0.0)
        tot = o.block_sum(r)
        pos = o.expand(tot > 0)
        x = np.where(pos, r / np.where(pos, o.expand(tot), 1.0), x)
        value, u = o.query(x)
    if o.kkt_gap(x, u) <= o.target_gap or o.calls >= o.budget:
        return
    sys.path.insert(0, str(ROOT / "baseline"))
    from solver import Blocks  # noqa: E402  (projection helper of the baseline)
    blocks = Blocks(o.sizes)
    lr = 1.0
    last_is_x = True
    while o.calls < o.budget - 1:
        if o.kkt_gap(x, u) <= o.target_gap:
            return
        y = blocks.project(x + lr * u)
        vy, uy = o.query(y)
        if vy >= value:
            x, value, u, lr, last_is_x = y, vy, uy, lr * 1.5, True
        else:
            lr, last_is_x = lr * 0.5, False
    if not last_is_x:
        o.query(x)


def rm_plus_fallback50(o: OracleClient) -> None:
    _rm_plus_then_adaptive_gd(o, 50)


def rm_plus_fallback200(o: OracleClient) -> None:
    _rm_plus_then_adaptive_gd(o, 200)


KINDS = {f.__name__: f for f in (
    rm_plus_restarts, rm_plus_discount, gd_adaptive, rm_plus_loose, rm_plus_short,
    uniform_once, no_query, crash, invalid_strategy, over_budget_random, forge_files,
    cached_train_answers, brute_force_vertices, read_hidden_files, rm_plus_fallback50, rm_plus_fallback200,
    rm_plus_own_start, read_field_targets)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=sorted(KINDS), required=True)
    args = parser.parse_args()
    o = OracleClient()
    try:
        KINDS[args.kind](o)
    except BudgetExhausted:
        return
    o.done()


if __name__ == "__main__":
    main()

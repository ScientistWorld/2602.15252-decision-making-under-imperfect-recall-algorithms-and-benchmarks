"""The paper's regret-matching family as first-order optimizers (RM, RM+, PRM, PRM+).

Algorithm 1 of the paper with a regret-matching local optimizer at every
information set (Algorithms 3 and 4), implemented as in the authors' released
code (modules/solvers/rm.py + FirstOrderMethod.py):

    each iteration: u <- grad U(x)  (one oracle query); stop if KKT gap <= eps
    per information set:  ev = <u, x>,  r <- r + (u - ev)      [RM+: r <- max(r, 0)]
                          theta = max(r + (u - ev), 0) if predictive else max(r, 0)
                          x <- theta / sum(theta)  if sum(theta) > 0

    python method/solver.py --algo rm_plus      (rm | rm_plus | prm | prm_plus)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.oracle_client import BudgetExhausted, OracleClient  # noqa: E402

VARIANTS = {
    "rm": (False, False),
    "rm_plus": (True, False),
    "prm": (False, True),
    "prm_plus": (True, True),
}


def solve(oracle: OracleClient, plus: bool, predictive: bool) -> None:
    x = oracle.x0.copy()
    regrets = np.zeros_like(x)
    try:
        while oracle.calls < oracle.budget:
            _, u = oracle.query(x)
            if oracle.kkt_gap(x, u) <= oracle.target_gap:
                break
            centred = u - oracle.expand(oracle.block_sum(u * x))
            regrets = regrets + centred
            if plus:
                regrets = np.maximum(regrets, 0.0)
            theta = np.maximum(regrets + centred, 0.0) if predictive else np.maximum(regrets, 0.0)
            total = oracle.block_sum(theta)
            positive = oracle.expand(total > 0)
            x = np.where(positive, theta / np.where(positive, oracle.expand(total), 1.0), x)
    except BudgetExhausted:
        return
    oracle.done()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algo", choices=sorted(VARIANTS), default="rm_plus")
    args = parser.parse_args()
    plus, predictive = VARIANTS[args.algo]
    solve(OracleClient(), plus, predictive)


if __name__ == "__main__":
    main()

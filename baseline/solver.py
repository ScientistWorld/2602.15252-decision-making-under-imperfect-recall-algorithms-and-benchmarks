"""Gradient-based comparators of the paper: projected GD, optimistic GD, AMSGrad.

Implemented as in the authors' released code (modules/solvers/gd.py), inside the
same per-information-set template (one oracle query per iteration, stop when the
KKT gap of the queried strategy is <= eps):

  GD   x <- Proj(x + lr * u)
  OGD  first step: xh <- x;  later steps: xh <- Proj(xh + lr * u);  then x <- Proj(xh + lr * u)
  AMS  m <- b1 m + (1-b1) u;  v <- b2 v + (1-b2) u^2;  vh <- max(vh, v)
       step = lr * m / sqrt(vh)  (coordinates with vh <= 1e-8: lr * (1-b1)/sqrt(1-b2))
       x <- argmin_{y in simplex} sum_a vh_a (y_a - (x + step)_a)^2   (weighted projection)

    python baseline/solver.py --algo gd --lr 0.1
    python baseline/solver.py --algo ams --lr 0.1 --beta1 0.9 --beta2 0.999
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.oracle_client import BudgetExhausted, OracleClient  # noqa: E402


class Blocks:
    """Information sets grouped by action count, for vectorised per-simplex operations."""

    def __init__(self, sizes: list[int]):
        offsets = np.concatenate([[0], np.cumsum(sizes)[:-1]])
        self.groups = []
        for m in sorted(set(sizes)):
            rows = [offsets[i] + np.arange(m) for i, s in enumerate(sizes) if s == m]
            self.groups.append((m, np.array(rows, dtype=np.int64)))

    def project(self, v: np.ndarray) -> np.ndarray:
        out = np.empty_like(v)
        for m, idx in self.groups:
            out[idx] = project_rows(v[idx])
        return out

    def weighted_project(self, y: np.ndarray, w: np.ndarray) -> np.ndarray:
        out = np.empty_like(y)
        for m, idx in self.groups:
            out[idx] = weighted_project_rows(y[idx], w[idx])
        return out


def project_rows(V: np.ndarray) -> np.ndarray:
    """Euclidean projection of every row onto the simplex (sorting algorithm)."""
    m = V.shape[1]
    U = -np.sort(-V, axis=1)
    css = np.cumsum(U, axis=1)
    cond = U * np.arange(1, m + 1) > css - 1.0
    rho = m - 1 - np.argmax(cond[:, ::-1], axis=1)
    theta = (css[np.arange(len(V)), rho] - 1.0) / (rho + 1.0)
    return np.clip(V - theta[:, None], 0.0, None)


def _nonzero_weighted_rows(Y: np.ndarray, W: np.ndarray) -> np.ndarray:
    """Breakpoint algorithm of the authors' code, vectorised over rows (all weights > 0)."""
    A = W * Y
    bp = np.sort(np.concatenate([A, A - W], axis=1), axis=1)
    X = np.clip((A[:, None, :] - bp[:, :, None]) / W[:, None, :], 0.0, 1.0)
    sums = X.sum(axis=2)
    count = np.sum(sums - 1.0 >= -1e-8, axis=1)
    lo = np.clip(count - 1, 0, bp.shape[1] - 2)
    rows = np.arange(len(Y))
    b0, b1 = bp[rows, lo], bp[rows, lo + 1]
    s0, s1 = sums[rows, lo], sums[rows, lo + 1]
    denom = s1 - s0
    safe = np.abs(denom) > 1e-300
    lam = b0 + np.where(safe, (b1 - b0) * (1.0 - s0) / np.where(safe, denom, 1.0), 0.0)
    x = np.clip((A - lam[:, None]) / W, 0.0, 1.0)
    return x / x.sum(axis=1, keepdims=True)


def weighted_project_rows(Y: np.ndarray, W: np.ndarray) -> np.ndarray:
    out = np.empty_like(Y)
    full = np.all(W > 1e-8, axis=1)
    if full.any():
        out[full] = _nonzero_weighted_rows(Y[full], W[full])
    for i in np.flatnonzero(~full):
        y, w = Y[i], W[i]
        nonzero = w > 1e-8
        pos = nonzero & (y > 0)
        total = y[pos].sum()
        x = np.zeros_like(y)
        if total <= 1.0:
            x[pos] = y[pos]
            x[~nonzero] = (1.0 - total) / np.count_nonzero(~nonzero)
        else:
            x[pos] = _nonzero_weighted_rows(y[pos][None], w[pos][None])[0]
        out[i] = x
    return out


def solve(oracle: OracleClient, algo: str, lr: float, beta1: float, beta2: float) -> None:
    blocks = Blocks(oracle.sizes)
    x = oracle.x0.copy()
    xh = None
    m = np.zeros_like(x)
    v = np.zeros_like(x)
    vh = np.zeros_like(x)
    try:
        while oracle.calls < oracle.budget:
            _, u = oracle.query(x)
            if oracle.kkt_gap(x, u) <= oracle.target_gap:
                break
            if algo == "gd":
                x = blocks.project(x + lr * u)
            elif algo == "ogd":
                xh = x.copy() if xh is None else blocks.project(xh + lr * u)
                x = blocks.project(xh + lr * u)
            else:
                m = beta1 * m + (1.0 - beta1) * u
                v = beta2 * v + (1.0 - beta2) * u * u
                vh = np.maximum(vh, v)
                big = vh > 1e-8
                step = np.where(big, lr * m / np.sqrt(np.where(big, vh, 1.0)),
                                lr * (1.0 - beta1) / np.sqrt(1.0 - beta2))
                x = blocks.weighted_project(x + step, vh)
    except BudgetExhausted:
        return
    oracle.done()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algo", choices=["gd", "ogd", "ams"], required=True)
    parser.add_argument("--lr", type=float, default=0.1)
    parser.add_argument("--beta1", type=float, default=0.9)
    parser.add_argument("--beta2", type=float, default=0.999)
    args = parser.parse_args()
    solve(OracleClient(), args.algo, args.lr, args.beta1, args.beta2)


if __name__ == "__main__":
    main()

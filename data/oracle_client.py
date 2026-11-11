"""Client side of the evaluator's first-order oracle protocol.

A solver is a program the evaluator starts once per random start.  It talks to
the evaluator over stdin/stdout (see briefing/evaluation.md):

    from data.oracle_client import OracleClient
    oracle = OracleClient()          # reads the problem header
    x = oracle.x0.copy()             # flat strategy, one block per information set
    for _ in range(oracle.budget):
        value, grad = oracle.query(x)            # one iteration of the budget
        if oracle.kkt_gap(x, grad) <= oracle.target_gap:
            break
        x = ...                                    # your update
    oracle.done()

The run's result is the last strategy queried.  Anything the solver prints goes
to stderr (stdout is reserved for the protocol).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

PROTOCOL = "irtree-oracle-1"


class BudgetExhausted(Exception):
    """Raised when the evaluator stops answering (iteration budget used up)."""


class OracleClient:
    def __init__(self):
        self._in = sys.stdin.buffer
        out_fd = os.dup(1)
        os.dup2(2, 1)  # stray prints go to stderr, not into the protocol stream
        self._out = os.fdopen(out_fd, "wb")
        header = json.loads(self._in.readline())
        if header.get("protocol") != PROTOCOL:
            raise RuntimeError("unexpected oracle protocol")
        self.sizes = [int(s) for s in header["infoset_sizes"]]
        self.dim = int(sum(self.sizes))
        self.budget = int(header["budget"])
        self.target_gap = float(header["target_gap"])
        self.x0 = np.asarray(header["x0"], dtype=float)
        self.run = header.get("run")
        self.starts = np.concatenate([[0], np.cumsum(self.sizes)[:-1]]).astype(np.int64)
        self.calls = 0

    def query(self, x: np.ndarray) -> tuple[float, np.ndarray]:
        """Expected utility and gradient at strategy x (counts one iteration)."""
        if self.calls >= self.budget:
            raise BudgetExhausted
        x = np.ascontiguousarray(x, dtype="<f8")
        try:
            self._out.write(b"Q" + x.tobytes())
            self._out.flush()
        except (BrokenPipeError, OSError) as exc:
            raise BudgetExhausted from exc
        size = 8 * (1 + self.dim)
        data = self._in.read(size)
        if data is None or len(data) < size:
            raise BudgetExhausted
        arr = np.frombuffer(data, dtype="<f8")
        self.calls += 1
        return float(arr[0]), arr[1:].copy()

    def done(self) -> None:
        try:
            self._out.write(b"D")
            self._out.flush()
        except (BrokenPipeError, OSError):
            pass

    # helpers -----------------------------------------------------------------
    def block_sum(self, v: np.ndarray) -> np.ndarray:
        return np.add.reduceat(v, self.starts)

    def expand(self, per_block: np.ndarray) -> np.ndarray:
        return np.repeat(per_block, self.sizes)

    def kkt_gap(self, x: np.ndarray, grad: np.ndarray) -> float:
        best = np.maximum.reduceat(grad, self.starts)
        return float(np.max(best - self.block_sum(x * grad)))

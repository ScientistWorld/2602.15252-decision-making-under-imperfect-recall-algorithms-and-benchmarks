"""Held-out evaluation harness: first-order oracle, solver protocol, metrics.

Solvers never see a decision problem.  The evaluator starts each solver as a
separate process (one process per random start), sends it the information-set
sizes, the iteration budget, the convergence threshold and the starting
strategy, and then answers its queries: for every strategy the solver sends,
the evaluator returns the expected utility and the full gradient.  Every query
counts as one iteration (one gradient evaluation).  The result of a run is the
last strategy the solver queried; its utility and KKT gap are computed here.

Wire protocol (binary, little-endian float64):
  evaluator -> solver: one JSON header line
      {"protocol": "irtree-oracle-1", "infoset_sizes": [...], "budget": B,
       "target_gap": eps, "x0": [...], "run": k}
  solver -> evaluator: b"Q" + D float64 (a strategy)  |  b"D" (done)
  evaluator -> solver: (1 + D) float64: utility, then gradient
After B answered queries the evaluator stops answering and closes the pipe.
"""
from __future__ import annotations

import json
import math
import os
import re
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

PROTOCOL = "irtree-oracle-1"
NAME_RE = re.compile(r"^[a-z0-9_]+$")


# ----------------------------------------------------------------------------- oracle
class TreeOracle:
    """Vectorised expected utility, gradient and KKT gap for a batch of strategies."""

    def __init__(self, tree: dict):
        if tree.get("format") != "irtree-v1":
            raise ValueError("unsupported instance format")
        parent = np.asarray(tree["parent"], dtype=np.int64)
        act = np.asarray(tree["edge_action"], dtype=np.int64)
        prob = np.asarray(tree["edge_prob"], dtype=float)
        payoff = np.asarray(tree["payoff"], dtype=float)
        n = len(parent)
        self.name = tree.get("name", "")
        self.sizes = [int(s) for s in tree["infoset_sizes"]]
        self.dim = int(sum(self.sizes))
        self.starts = np.concatenate([[0], np.cumsum(self.sizes)[:-1]]).astype(np.int64)
        depth = np.zeros(n, dtype=np.int64)
        for j in range(1, n):
            p = parent[j]
            if not 0 <= p < j:
                raise ValueError("nodes must be stored in breadth-first order")
            depth[j] = depth[p] + 1
        if np.any(np.diff(depth) < 0):
            raise ValueError("nodes must be stored in breadth-first order")
        has_child = np.zeros(n, dtype=bool)
        has_child[parent[1:]] = True
        self.n = n
        self.leaf_payoff = np.where(has_child, 0.0, payoff)
        leaves = ~has_child
        self.min_payoff = float(payoff[leaves].min())
        self.max_payoff = float(payoff[leaves].max())
        bounds = np.searchsorted(depth, np.arange(depth.max() + 2))
        self.levels = []
        for d in range(int(depth.max())):
            s, e = int(bounds[d + 1]), int(bounds[d + 2])
            if s == e:
                continue
            par = parent[s:e]
            change = np.flatnonzero(np.r_[True, par[1:] != par[:-1]])
            is_player = act[s:e] >= 0
            self.levels.append((s, e, par, change, par[change], is_player,
                                np.where(is_player, act[s:e], 0), np.where(is_player, 0.0, prob[s:e])))
        pe = np.flatnonzero(act >= 0)
        order = np.argsort(act[pe], kind="stable")
        self.g_child = pe[order]
        self.g_parent = parent[pe][order]
        ks = act[pe][order]
        self.g_starts = np.flatnonzero(np.r_[True, ks[1:] != ks[:-1]])
        if len(self.g_starts) != self.dim or np.any(ks[self.g_starts] != np.arange(self.dim)):
            raise ValueError("every action must label at least one decision edge")

    def block_sums(self, X: np.ndarray) -> np.ndarray:
        return np.add.reduceat(X, self.starts, axis=1)

    def evaluate(self, X: np.ndarray):
        X = np.atleast_2d(X)
        B = X.shape[0]
        V = np.tile(self.leaf_payoff, (B, 1))
        weights = []
        for (s, e, par, change, upar, is_player, a, p) in reversed(self.levels):
            W = np.where(is_player, X[:, a], p)
            weights.append(W)
            V[:, upar] = np.add.reduceat(W * V[:, s:e], change, axis=1)
        weights.reverse()
        R = np.zeros((B, self.n))
        R[:, 0] = 1.0
        for (s, e, par, *_), W in zip(self.levels, weights):
            R[:, s:e] = R[:, par] * W
        G = np.add.reduceat(R[:, self.g_parent] * V[:, self.g_child], self.g_starts, axis=1)
        best = np.maximum.reduceat(G, self.starts, axis=1)
        dot = np.add.reduceat(X * G, self.starts, axis=1)
        gap = np.max(best - dot, axis=1)
        return V[:, 0].copy(), G, gap

    def clean(self, x: np.ndarray):
        """Return the strategy projected onto exact simplices, or None if invalid."""
        if x.shape != (self.dim,) or not np.all(np.isfinite(x)):
            return None
        if x.min() < -1e-9:
            return None
        sums = np.add.reduceat(x, self.starts)
        if np.max(np.abs(sums - 1.0)) > 1e-6:
            return None
        x = np.maximum(x, 0.0)
        return x / np.repeat(np.add.reduceat(x, self.starts), self.sizes)

    def uniform(self) -> np.ndarray:
        return np.repeat([1.0 / s for s in self.sizes], self.sizes)


def load_instance(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def paper_start(sizes: list[int], seed: int) -> np.ndarray:
    """Random starting strategy as in the paper: normalised exponentials per infoset."""
    rng = np.random.RandomState(seed)
    parts = []
    for s in sizes:
        u = rng.exponential(scale=1.0, size=s)
        parts.append(u / u.sum())
    return np.concatenate(parts)


# --------------------------------------------------------------------------- registry
def load_registry(path: Path, root: Path) -> dict[str, list[str]]:
    """Solvers on disk: {"name": {"command": [...]}}; malformed entries are kept as failures."""
    registry: dict[str, list[str] | None] = {}
    if not path.is_file():
        return registry
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return registry
    if not isinstance(data, dict):
        return registry
    for name, entry in data.items():
        if not isinstance(name, str) or name.startswith("_"):
            continue
        if not NAME_RE.match(name):
            continue
        cmd = entry.get("command") if isinstance(entry, dict) else None
        if not (isinstance(cmd, list) and cmd and all(isinstance(c, str) for c in cmd)):
            registry[name] = None
            continue
        if cmd[0] in ("python", "python3"):
            cmd = [sys.executable] + cmd[1:]
        registry[name] = cmd
    return registry


# --------------------------------------------------------------------------- protocol
def _read_exact(fd: int, n: int, deadline: float):
    """Read n bytes; returns bytes (short on EOF) or None on timeout."""
    buf = b""
    while len(buf) < n:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        ready, _, _ = select.select([fd], [], [], remaining)
        if not ready:
            return None
        chunk = os.read(fd, n - len(buf))
        if not chunk:
            return buf
        buf += chunk
    return buf


def _write_all(fd: int, data: bytes) -> bool:
    view = memoryview(data)
    try:
        while view:
            written = os.write(fd, view)
            view = view[written:]
    except (BrokenPipeError, OSError):
        return False
    return True


def run_solver(command, oracle: TreeOracle, starts: list[np.ndarray], budget: int, target_gap: float,
               cwd: Path, message_timeout: float = 300.0, total_timeout: float = 1800.0) -> list[dict]:
    """Run one solver from every start in lockstep and return per-run records."""
    D = oracle.dim
    runs = []
    for k in range(len(starts)):
        runs.append({"calls": 0, "value": None, "gap": None, "status": "running", "reason": "",
                     "proc": None, "err": None})
    if command is None:
        for r in runs:
            r["status"], r["reason"] = "failed", "no runnable command registered"
    else:
        env = dict(os.environ)
        env.setdefault("PYTHONUNBUFFERED", "1")
        for k, (r, x0) in enumerate(zip(runs, starts)):
            err = tempfile.TemporaryFile()
            try:
                proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                                        cwd=str(cwd), env=env, bufsize=0, start_new_session=True)
            except OSError as exc:
                r["status"], r["reason"] = "failed", f"cannot start solver: {exc}"
                err.close()
                continue
            r["proc"], r["err"] = proc, err
            header = {"protocol": PROTOCOL, "infoset_sizes": oracle.sizes, "budget": budget,
                      "target_gap": target_gap, "x0": [float(v) for v in x0], "run": k}
            if not _write_all(proc.stdin.fileno(), (json.dumps(header) + "\n").encode()):
                r["status"], r["reason"] = "failed", "solver closed its input before reading the header"
    started = time.monotonic()

    def stop(r, status, reason=""):
        r["status"], r["reason"] = status, reason
        proc = r["proc"]
        if proc is None:
            return
        try:
            proc.stdin.close()
        except OSError:
            pass
        if status == "eof":
            try:
                code = proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                code = None
            if code not in (0, None):
                r["status"], r["reason"] = "failed", f"solver exited with code {code}"
        try:  # the solver and anything it started
            os.killpg(proc.pid, 9)
        except OSError:
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        for stream in (proc.stdin, proc.stdout):
            try:
                stream.close()
            except OSError:
                pass

    while True:
        live = [r for r in runs if r["status"] == "running"]
        if not live:
            break
        if time.monotonic() - started > total_timeout:
            for r in live:
                stop(r, "failed", "time limit exceeded")
            break
        batch = []
        for r in live:
            fd = r["proc"].stdout.fileno()
            deadline = min(time.monotonic() + message_timeout, started + total_timeout)
            op = _read_exact(fd, 1, deadline)
            if op is None:
                stop(r, "failed", "solver did not respond in time")
            elif op == b"":
                stop(r, "eof")
            elif op == b"D":
                stop(r, "done")
            elif op != b"Q":
                stop(r, "failed", "protocol violation")
            else:
                payload = _read_exact(fd, 8 * D, deadline)
                if payload is None or len(payload) < 8 * D:
                    stop(r, "failed", "truncated query")
                elif r["calls"] >= budget:
                    stop(r, "budget")
                else:
                    x = oracle.clean(np.frombuffer(payload, dtype="<f8").copy())
                    if x is None:
                        stop(r, "failed", "query is not a valid behavioural strategy")
                    else:
                        batch.append((r, x))
        if batch:
            values, grads, gaps = oracle.evaluate(np.stack([x for _, x in batch]))
            for i, (r, _) in enumerate(batch):
                r["calls"] += 1
                r["value"], r["gap"] = float(values[i]), float(gaps[i])
                msg = np.concatenate([[values[i]], grads[i]]).astype("<f8").tobytes()
                if not _write_all(r["proc"].stdin.fileno(), msg):
                    stop(r, "eof")
                elif r["calls"] >= budget:
                    pass  # a further query is refused and ends the run
    for r in runs:  # processes that failed before the loop (e.g. while reading the header)
        if r["proc"] is not None and not r["proc"].stdout.closed:
            stop(r, r["status"], r["reason"])
    records = []
    for r in runs:
        if r["err"] is not None:
            try:
                if r["status"] == "failed":
                    r["err"].seek(0, os.SEEK_END)
                    size = r["err"].tell()
                    r["err"].seek(max(0, size - 600))
                    tail = r["err"].read().decode(errors="replace").strip().splitlines()
                    if tail:
                        r["reason"] += f" | {tail[-1][:200]}"
            finally:
                r["err"].close()
        failed = r["status"] == "failed" or r["calls"] == 0
        if r["calls"] == 0 and r["status"] != "failed":
            r["reason"] = "no strategy was queried"
        records.append({
            "calls": int(r["calls"]),
            "value": r["value"],
            "gap": r["gap"],
            "failed": bool(failed),
            "converged": bool(not failed and r["gap"] is not None and r["gap"] <= target_gap),
            "reason": r["reason"] if failed else "",
        })
    return records

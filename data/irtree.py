"""Tabular imperfect-recall decision problems: file formats and a reference evaluator.

Pure Python (no numpy) so it can be used anywhere.

Two formats are handled:

* The text format of the paper's benchmark artifact (``node ...`` / ``infoset ...``
  lines; see the paper's supplementary code).  ``parse_paper_txt`` reads it.
* The compact compiled format used by this gym (``irtree-v1`` JSON).  Nodes are
  stored in breadth-first order, so the children of every node are contiguous and
  every tree level is a contiguous block.  Fields:

  - ``infoset_sizes``: number of actions of each information set, in the order
    that defines the flat strategy vector (information set by information set,
    actions in their listed order).
  - ``parent``: parent index of each node (-1 for the root, which is node 0).
  - ``edge_action``: for a node whose parent is a decision node, the flat index of
    the action leading to it; -1 otherwise.
  - ``edge_prob``: for a node whose parent is a chance node, the chance
    probability of the edge leading to it; 0 otherwise.
  - ``payoff``: terminal payoff of leaves (0 for internal nodes).

A behavioural strategy is a flat list of probabilities, one block per information
set.  The expected utility U(x) is a polynomial in x; its partial derivative for
action a of information set I is sum_{h in I} P(h | x) * U(x | ha).
"""
from __future__ import annotations

import json
from collections import deque
from fractions import Fraction
from pathlib import Path

FORMAT = "irtree-v1"


def _number(text: str) -> float:
    try:
        return float(text)
    except ValueError:
        return float(Fraction(text))


def _child_descr(descr: str, kind: str, action: str) -> str:
    tag = "/P1:" if kind == "player" else "/C:"
    return (tag if descr == "/" else descr + tag) + action


def parse_paper_txt(path: str | Path, name: str | None = None) -> dict:
    """Parse a decision problem in the paper's text format into the compiled format."""
    nodes: dict[str, dict] = {}
    infosets: list[tuple[str, list[str]]] = []
    with open(path) as handle:
        for line in handle:
            if not line.strip() or line[0] == "#":
                continue
            parts = line.split()
            if parts[0] == "node":
                descr = parts[1]
                if parts[2] == "chance":
                    acts = [w.split("=")[0] for w in parts[4:]]
                    probs = [_number(w.split("=")[1]) for w in parts[4:]]
                    nodes[descr] = {"kind": "chance", "actions": acts, "probs": probs}
                elif parts[2] == "player":
                    nodes[descr] = {"kind": "player", "actions": parts[5:]}
                elif parts[2] == "leaf":
                    nodes[descr] = {"kind": "leaf", "payoff": _number(parts[4].split("=")[1])}
                else:
                    raise ValueError(f"unexpected node line: {line[:120]}")
            elif parts[0] == "infoset":
                infosets.append((parts[1], parts[3:]))
            else:
                raise ValueError(f"unexpected line: {line[:120]}")
    node_infoset: dict[str, int] = {}
    sizes: list[int] = []
    for idx, (_, members) in enumerate(infosets):
        acts = None
        for m in members:
            node_infoset[m] = idx
            if acts is None:
                acts = nodes[m]["actions"]
            elif nodes[m]["actions"] != acts:
                raise ValueError("information set with inconsistent action sets")
        sizes.append(len(acts))
    for descr, node in nodes.items():
        if node["kind"] == "player":
            node["infoset"] = node_infoset[descr]
            node["children"] = [_child_descr(descr, "player", a) for a in node["actions"]]
        elif node["kind"] == "chance":
            node["children"] = [_child_descr(descr, "chance", a) for a in node["actions"]]
    return compile_tree(nodes, "/", sizes, name or Path(path).stem)


def compile_tree(nodes: dict, root, infoset_sizes: list[int], name: str) -> dict:
    """Compile a node dictionary into the breadth-first irtree-v1 format.

    ``nodes`` maps a key to {"kind": "leaf"|"chance"|"player", "children": [keys],
    "probs": [...] (chance), "infoset": int (player), "payoff": float (leaf)}.
    """
    offsets = [0]
    for s in infoset_sizes:
        offsets.append(offsets[-1] + s)
    parent: list[int] = []
    edge_action: list[int] = []
    edge_prob: list[float] = []
    payoff: list[float] = []
    queue = deque([(root, -1, -1, 0.0)])
    while queue:
        key, par, act, prob = queue.popleft()
        idx = len(parent)
        parent.append(par)
        edge_action.append(act)
        edge_prob.append(prob)
        node = nodes[key]
        if node["kind"] == "leaf":
            payoff.append(float(node["payoff"]))
            continue
        payoff.append(0.0)
        if node["kind"] == "chance":
            for child, p in zip(node["children"], node["probs"]):
                queue.append((child, idx, -1, float(p)))
        else:
            info = node["infoset"]
            if len(node["children"]) != infoset_sizes[info]:
                raise ValueError("decision node action count does not match its information set")
            for a, child in enumerate(node["children"]):
                queue.append((child, idx, offsets[info] + a, 0.0))
    return {
        "format": FORMAT,
        "name": name,
        "infoset_sizes": list(infoset_sizes),
        "parent": parent,
        "edge_action": edge_action,
        "edge_prob": edge_prob,
        "payoff": payoff,
    }


def save(tree: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(tree, separators=(",", ":")))


def load(path: str | Path) -> dict:
    tree = json.loads(Path(path).read_text())
    if tree.get("format") != FORMAT:
        raise ValueError(f"{path}: not an {FORMAT} file")
    return tree


def stats(tree: dict) -> dict:
    n = len(tree["parent"])
    children = [0] * n
    for p in tree["parent"][1:]:
        children[p] += 1
    leaves = sum(1 for c in children if c == 0)
    decision = sum(1 for j in range(1, n) if tree["edge_action"][j] >= 0)
    payoffs = [tree["payoff"][j] for j in range(n) if children[j] == 0]
    return {
        "nodes": n,
        "leaves": leaves,
        "infosets": len(tree["infoset_sizes"]),
        "dimension": sum(tree["infoset_sizes"]),
        "decision_edges": decision,
        "min_payoff": min(payoffs),
        "max_payoff": max(payoffs),
    }


def evaluate(tree: dict, x: list[float]) -> tuple[float, list[float]]:
    """Reference (slow) expected utility and gradient of a flat strategy."""
    parent, act, prob, pay = tree["parent"], tree["edge_action"], tree["edge_prob"], tree["payoff"]
    n = len(parent)
    has_child = [False] * n
    for p in parent[1:]:
        has_child[p] = True
    weight = [1.0] + [x[act[j]] if act[j] >= 0 else prob[j] for j in range(1, n)]
    value = [0.0] * n
    for j in range(n - 1, -1, -1):
        if not has_child[j]:
            value[j] = pay[j]
        if j > 0:
            value[parent[j]] += weight[j] * value[j]
    reach = [0.0] * n
    reach[0] = 1.0
    grad = [0.0] * len(x)
    for j in range(1, n):
        reach[j] = reach[parent[j]] * weight[j]
        if act[j] >= 0:
            grad[act[j]] += reach[parent[j]] * value[j]
    return value[0], grad


def kkt_gap(sizes: list[int], x: list[float], grad: list[float]) -> float:
    gap, k = 0.0, 0
    for s in sizes:
        g = grad[k:k + s]
        gap = max(gap, max(g) - sum(xi * gi for xi, gi in zip(x[k:k + s], g)))
        k += s
    return gap


def uniform(sizes: list[int]) -> list[float]:
    return [1.0 / s for s in sizes for _ in range(s)]

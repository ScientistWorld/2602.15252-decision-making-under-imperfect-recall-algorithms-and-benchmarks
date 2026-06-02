from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class Node:
    kind: str
    actions: list[str]
    children: list[int]
    infoset: int | None = None
    chance_probs: list[float] | None = None
    payoff: float | None = None


@dataclass
class TreeGame:
    name: str
    nodes: list[Node]
    infoset_actions: list[list[str]]
    root: int = 0

    def to_json(self, path: str | Path) -> None:
        payload = {
            "name": self.name,
            "root": self.root,
            "infoset_actions": self.infoset_actions,
            "nodes": [asdict(node) for node in self.nodes],
        }
        Path(path).write_text(json.dumps(payload, indent=2))

    @staticmethod
    def from_json(path: str | Path) -> "TreeGame":
        payload = json.loads(Path(path).read_text())
        return TreeGame(
            name=payload["name"],
            root=payload.get("root", 0),
            infoset_actions=payload["infoset_actions"],
            nodes=[Node(**node) for node in payload["nodes"]],
        )

    @property
    def n_infosets(self) -> int:
        return len(self.infoset_actions)

    def uniform_strategy(self) -> list[np.ndarray]:
        return [np.ones(len(actions), dtype=float) / len(actions) for actions in self.infoset_actions]


def absentminded_driver(exit_payoffs: tuple[float, float, float] = (0.0, 4.0, 1.0)) -> TreeGame:
    """Classic absentminded-driver style problem with one repeated infoset."""
    nodes = [
        Node("player", ["exit", "continue"], [1, 2], infoset=0),
        Node("terminal", [], [], payoff=exit_payoffs[0]),
        Node("player", ["exit", "continue"], [3, 4], infoset=0),
        Node("terminal", [], [], payoff=exit_payoffs[1]),
        Node("terminal", [], [], payoff=exit_payoffs[2]),
    ]
    return TreeGame("absentminded_driver", nodes, [["exit", "continue"]], 0)


def simulation_problem(max_tests: int, p_continue: float, good_payoff: float, bad_payoff: float) -> TreeGame:
    """Simulation benchmark: bad action ends deployment after any simulated detection."""
    nodes: list[Node] = []

    def add(node: Node) -> int:
        nodes.append(node)
        return len(nodes) - 1

    def deploy_node() -> int:
        deploy_good = add(Node("terminal", [], [], payoff=good_payoff))
        deploy_bad = add(Node("terminal", [], [], payoff=bad_payoff))
        return add(Node("player", ["good", "bad"], [deploy_good, deploy_bad], infoset=0))

    def build(remaining_tests: int) -> int:
        if remaining_tests == 0:
            return deploy_node()
        test_good = build(remaining_tests - 1)
        caught = add(Node("terminal", [], [], payoff=0.0))
        test = add(Node("player", ["good", "bad"], [test_good, caught], infoset=0))
        deploy = deploy_node()
        return add(
            Node(
                "chance",
                ["test_again", "deploy"],
                [test, deploy],
                chance_probs=[p_continue, 1.0 - p_continue],
            )
        )

    return TreeGame(f"simulation_{max_tests}", nodes, [["good", "bad"]], build(max_tests))


def random_imperfect_recall_game(
    name: str,
    depth: int,
    n_infosets: int,
    branching: int,
    chance_prob: float,
    seed: int,
) -> TreeGame:
    """Random benchmark in the paper's spirit: chance/player tree with merged infosets."""
    rng = np.random.default_rng(seed)
    nodes: list[Node] = []
    infoset_actions = [[f"a{j}" for j in range(branching)] for _ in range(n_infosets)]

    def build(d: int) -> int:
        idx = len(nodes)
        nodes.append(Node("terminal", [], [], payoff=0.0))
        if d >= depth:
            nodes[idx] = Node("terminal", [], [], payoff=float(rng.random()))
            return idx
        if rng.random() < chance_prob:
            probs = rng.dirichlet(np.ones(branching)).tolist()
            children = [build(d + 1) for _ in range(branching)]
            nodes[idx] = Node("chance", [f"c{j}" for j in range(branching)], children, chance_probs=probs)
            return idx
        infoset = int(rng.integers(0, n_infosets))
        children = [build(d + 1) for _ in range(branching)]
        nodes[idx] = Node("player", infoset_actions[infoset], children, infoset=infoset)
        return idx

    root = build(0)
    return TreeGame(name, nodes, infoset_actions, root)


def write_default_suite(out_dir: str | Path) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    games = [
        absentminded_driver(),
        simulation_problem(max_tests=3, p_continue=0.75, good_payoff=1.0, bad_payoff=10.0),
        simulation_problem(max_tests=5, p_continue=0.65, good_payoff=2.0, bad_payoff=9.0),
        random_imperfect_recall_game("random_depth6", 6, 8, 3, 0.2, 11),
        random_imperfect_recall_game("random_depth7", 7, 12, 3, 0.2, 29),
    ]
    paths = []
    for game in games:
        path = out / f"{game.name}.json"
        game.to_json(path)
        paths.append(path)
    return paths

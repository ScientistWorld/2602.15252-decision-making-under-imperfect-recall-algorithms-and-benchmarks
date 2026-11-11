"""Compile the paper's public benchmark instances used as the training slice.

Reads the paper's text-format decision problems (fetched by scripts/download.sh
into data/downloads/paper_code/) and writes compiled irtree-v1 JSON files to
data/instances/train/.  These are the paper's own small/medium instances
(size presets 'a', 'b', 'c' for subgroup detection; 'a', 'b' for random and
simulation problems), i.e. Det-86 ... Det-10.7k, Rand-7k ... Rand-42k and
Sim-245 ... Sim-13k in the paper's Table 2.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data import irtree  # noqa: E402

SOURCE = ROOT / "data" / "downloads" / "paper_code" / "codefolder_url" / "decisionproblems"
TARGET = ROOT / "data" / "instances" / "train"
TRAIN = [
    ("detection", "a", 1), ("detection", "a", 2),
    ("detection", "b", 1), ("detection", "b", 2), ("detection", "b", 3),
    ("detection", "c", 1), ("detection", "c", 2), ("detection", "c", 3),
    ("random", "a", 1), ("random", "a", 2), ("random", "a", 3),
    ("random", "b", 1), ("random", "b", 2), ("random", "b", 3),
    ("simulation", "a", 1), ("simulation", "a", 2), ("simulation", "a", 3),
    ("simulation", "b", 1), ("simulation", "b", 2), ("simulation", "b", 3),
]


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    index = {}
    for family, size, i in TRAIN:
        src = SOURCE / family / size / f"{size}game{i}.txt"
        name = f"{family}_{size}{i}"
        tree = irtree.parse_paper_txt(src, name)
        irtree.save(tree, TARGET / f"{name}.json")
        st = irtree.stats(tree)
        index[name] = {"paper_file": f"decisionproblems/{family}/{size}/{size}game{i}.txt", **st}
        print(name, st)
    (TARGET / "index.json").write_text(json.dumps(index, indent=1) + "\n")


if __name__ == "__main__":
    main()

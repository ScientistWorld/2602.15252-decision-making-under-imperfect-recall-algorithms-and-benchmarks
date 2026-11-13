"""Generate the held-out test decision problems (pure Python, deterministic).

This is a port of the benchmark generators released with the paper (simulation,
subgroup detection under privacy constraints, random imperfect-recall problems),
with the paper's size presets ('a', 'b', 'c').  networkx/numpy calls of the
original are replaced by equivalent Python ``random`` draws, so instances follow
the same distribution but are new draws.  The seeds below are the only thing that
ties the stored instances to this code; they live only in ``eval/test``.

Usage (offline, once):  python eval/test/generate_instances.py
writes eval/test/instances/<name>.json in the gym's compiled irtree-v1 format.
"""
from __future__ import annotations

import itertools
import json
import math
import random
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (family, size preset, index within preset i in 1..3, seed)
SPECS = [
    ("detection", "a", 1, 0x5D1E3C0A9F21),
    ("detection", "a", 2, 0x2B7A40D3E611),
    ("detection", "b", 1, 0x7C0FA1952B43),
    ("detection", "b", 2, 0x11E9D0C7A5B8),
    ("detection", "b", 3, 0x6A3F82E1D094),
    ("detection", "c", 1, 0x3E5B9172C0AF),
    ("detection", "c", 2, 0x48D2F6A0B317),
    ("detection", "c", 3, 0x5F07C3E9A162),
    ("detection", "c", 1, 0x0C9A6E2D84F5),
    ("random", "a", 1, 0x29F4B61E7D03),
    ("random", "a", 2, 0x73A0C5D9E1B6),
    ("random", "a", 3, 0x1D86E2F04A97),
    ("random", "a", 2, 0x64B19C3A70E2),
    ("random", "b", 1, 0x0F3D7A92C6B1),
    ("random", "b", 2, 0x52E8B04D1F7C),
    ("random", "b", 3, 0x3A61F9C2E05D),
    ("random", "b", 2, 0x7E0B4D6A39C8),
    ("simulation", "a", 1, 0x4C72E9A1B05F),
    ("simulation", "a", 2, 0x18F3D6B2A9E4),
    ("simulation", "a", 3, 0x6D0A5C8E37B1),
    ("simulation", "b", 1, 0x25B8E0F4C1D6),
    ("simulation", "b", 2, 0x5A3C91D7E02B),
    ("simulation", "b", 3, 0x7B6E2A0F94C3),
    ("simulation", "b", 2, 0x0E47D5B31A9F),
    # second batch (test enlarged from 24 to 48 problems)
    ("detection", "a", 1, 0xCC4BDE65344C),
    ("detection", "a", 2, 0xD5A94F1B024D),
    ("detection", "b", 1, 0x52FDE282DE6D),
    ("detection", "b", 2, 0x39A994E8A420),
    ("detection", "b", 3, 0xFE7453C258A4),
    ("detection", "c", 1, 0x8953DE9C353D),
    ("detection", "c", 2, 0xA43C1415EB95),
    ("detection", "c", 3, 0x7794FC5D09E3),
    ("detection", "c", 2, 0x31A007510231),
    ("random", "a", 1, 0x7742B89C4BB9),
    ("random", "a", 2, 0xE3612E97CCFF),
    ("random", "a", 3, 0x1ACFA4EC7602),
    ("random", "a", 3, 0x52569A59DAE3),
    ("random", "b", 1, 0x8A3BB9C9FD3A),
    ("random", "b", 2, 0xE3A0E1EC82FD),
    ("random", "b", 3, 0x0ABBD0C33075),
    ("random", "b", 1, 0xD2A50BE6F637),
    ("simulation", "a", 1, 0x896AE7B6244F),
    ("simulation", "a", 2, 0x541A7D43C468),
    ("simulation", "a", 3, 0x2946C3AFAE00),
    ("simulation", "b", 1, 0x37BC650CC346),
    ("simulation", "b", 2, 0xC541A96D9ED5),
    ("simulation", "b", 3, 0xBC629F22C13B),
    ("simulation", "b", 3, 0x8D5E3D4F3103),
    # third batch (test enlarged from 48 to 176 problems, weighted toward the
    # largest preset of each family; see HARDENING.md)
    ("detection", "a", 1, 0x22D84E1B9111),
    ("detection", "a", 2, 0x884FB27E4DBE),
    ("detection", "a", 1, 0x08ECE27DD3A0),
    ("detection", "a", 2, 0xE68C4B475FA3),
    ("detection", "b", 1, 0x0A36238613A2),
    ("detection", "b", 2, 0x272FAA335B70),
    ("detection", "b", 3, 0x80EA7B663B35),
    ("detection", "b", 1, 0xC028C3D4B3C8),
    ("detection", "b", 2, 0x4BB6C52E3BE8),
    ("detection", "b", 3, 0x2295D9905425),
    ("detection", "b", 1, 0xA93E528F6673),
    ("detection", "b", 2, 0xECE2964924FA),
    ("detection", "b", 3, 0x763FADF7CDB6),
    ("detection", "b", 1, 0x2326A5BDFE95),
    ("detection", "c", 1, 0x3886FBB5F219),
    ("detection", "c", 2, 0xB4CB9979A6B4),
    ("detection", "c", 3, 0x1B5C12DACB50),
    ("detection", "c", 1, 0xA2ADD64300C6),
    ("detection", "c", 2, 0x84B32B846046),
    ("detection", "c", 3, 0xE5FC858DF993),
    ("detection", "c", 1, 0x05DC531DEEE7),
    ("detection", "c", 2, 0xFA9200DEE0B8),
    ("detection", "c", 3, 0xD5A904B5FE26),
    ("detection", "c", 1, 0x4545AF049B61),
    ("detection", "c", 2, 0xD92FBBF69BC9),
    ("detection", "c", 3, 0xF2B17E314BC7),
    ("detection", "c", 1, 0xCAC03CB9EDD2),
    ("detection", "c", 2, 0x9A600D30D3F0),
    ("detection", "c", 3, 0xE2BCE8528B1C),
    ("detection", "c", 1, 0xBA340579BA80),
    ("detection", "c", 2, 0xE7B47972A413),
    ("detection", "c", 3, 0x2E10FDA195AC),
    ("detection", "c", 1, 0x2632A3E3EA7F),
    ("detection", "c", 2, 0x8CCD1C3D23A2),
    ("detection", "c", 3, 0x8F5F9FF0EF04),
    ("detection", "c", 1, 0x4FC233067433),
    ("detection", "c", 2, 0xA0D056858564),
    ("detection", "c", 3, 0x2D10B1B00167),
    ("detection", "c", 1, 0x5C390F7B56BA),
    ("detection", "c", 2, 0x341680521F2E),
    ("detection", "c", 3, 0x4D4D7B472C9D),
    ("detection", "c", 1, 0xAA2BF350D933),
    ("detection", "c", 2, 0x700621546200),
    ("detection", "c", 3, 0x4C8EBD0A80D5),
    ("detection", "c", 1, 0xC2BB4051FB28),
    ("detection", "c", 2, 0x5DFA1E6F2E59),
    ("detection", "c", 3, 0xE57598B4F440),
    ("detection", "c", 1, 0xCCE8C8D3CEA2),
    ("detection", "c", 2, 0x88E9393109FA),
    ("detection", "c", 3, 0xA6D0B5215BF4),
    ("detection", "c", 1, 0x45B55A8FC85F),
    ("detection", "c", 2, 0x3A4C9C610124),
    ("detection", "c", 3, 0x4715F0CB8CB0),
    ("detection", "c", 1, 0x66B033015855),
    ("random", "a", 1, 0x0851D2289D89),
    ("random", "a", 2, 0xD676D64E3A46),
    ("random", "a", 3, 0xAD2BF7565591),
    ("random", "a", 1, 0x7080D08989C5),
    ("random", "a", 2, 0x2BD4051211E5),
    ("random", "a", 3, 0xCCA95193B19B),
    ("random", "a", 1, 0x9D79C082B481),
    ("random", "a", 2, 0x3C94FB93E3EF),
    ("random", "a", 3, 0x92341BEC15B3),
    ("random", "a", 1, 0x87A2D32BFFE3),
    ("random", "a", 2, 0x687EF7DDAA44),
    ("random", "a", 3, 0x36B72144029E),
    ("random", "a", 1, 0xAB39CA8B7CAC),
    ("random", "a", 2, 0x5A6E836E3F89),
    ("random", "a", 3, 0x57F7126C7707),
    ("random", "a", 1, 0x23A07A012413),
    ("random", "b", 1, 0x6D24AFFF4AC0),
    ("random", "b", 2, 0x2DA67D505B81),
    ("random", "b", 3, 0x5DCBD12929DA),
    ("random", "b", 1, 0xED46B29BFBA1),
    ("random", "b", 2, 0x6C7AE784817F),
    ("random", "b", 3, 0xF0B2FEC568D1),
    ("random", "b", 1, 0xA4EFEE6DCF44),
    ("random", "b", 2, 0x886866DE51F1),
    ("random", "b", 3, 0x1367A642869C),
    ("random", "b", 1, 0x02DC08C30208),
    ("random", "b", 2, 0x85BC4BDA8E4E),
    ("random", "b", 3, 0x1F8BFF2A7C1C),
    ("random", "b", 1, 0x04D27A00D539),
    ("random", "b", 2, 0x56157FF1679A),
    ("random", "b", 3, 0xD3A2D1EBAD4F),
    ("random", "b", 1, 0x70525E3B7917),
    ("simulation", "a", 1, 0x9CE19DF8B431),
    ("simulation", "a", 2, 0x2267DBB3E1A0),
    ("simulation", "b", 1, 0xE57592A905F6),
    ("simulation", "b", 2, 0x6D3228F2A688),
    ("simulation", "b", 3, 0xA3745376B46A),
    ("simulation", "b", 1, 0xC8016EC829D1),
    ("simulation", "b", 2, 0xCD7706145A35),
    ("simulation", "b", 3, 0x682DFE520B34),
    ("simulation", "b", 1, 0x2271EE18A4FB),
    ("simulation", "b", 2, 0xE9E548D4C7F4),
    ("simulation", "b", 3, 0xA0293CE13CC2),
    ("simulation", "b", 1, 0xD8E889779C7D),
    ("simulation", "b", 2, 0x3C69E924E2C0),
    ("simulation", "b", 3, 0xA1495405F4AF),
    ("simulation", "b", 1, 0xD816D6402232),
    ("simulation", "b", 2, 0xC091A5245530),
    ("simulation", "b", 3, 0x2A198DEFF3DB),
    ("simulation", "b", 1, 0xBCA1F5097FCC),
    ("simulation", "b", 2, 0x8327C38B2330),
    ("simulation", "b", 3, 0xB196C183C841),
    ("simulation", "b", 1, 0x5B3796CDD49D),
    ("simulation", "b", 2, 0xCBD48BC9BF92),
    ("simulation", "b", 3, 0xFF7E7F522A68),
    ("simulation", "b", 1, 0xDA874446D34C),
    ("simulation", "b", 2, 0x02537B437745),
    ("simulation", "b", 3, 0x4686B1A35BCA),
    ("simulation", "b", 1, 0x41B1DC2C31EE),
    ("simulation", "b", 2, 0x32C530C0304C),
    ("simulation", "b", 3, 0xE9803512AF0B),
    ("simulation", "b", 1, 0x3252CB39D77B),
    ("simulation", "b", 2, 0x709F4E87E2B0),
    ("simulation", "b", 3, 0x1D8AB7F40B78),
    ("simulation", "b", 1, 0xC13EEACAB04C),
    ("simulation", "b", 2, 0x5FF4B7C0AF6B),
    ("simulation", "b", 3, 0x11F7F39192B1),
    ("simulation", "b", 1, 0x0C5531F42C77),
    ("simulation", "b", 2, 0x9F42174B1F31),
    ("simulation", "b", 3, 0x8E21C1399CFB),
    ("simulation", "b", 1, 0xDEC51BB4BA0D),
    ("simulation", "b", 2, 0x9BEC5F06C638),
    ("simulation", "b", 3, 0x1F58D5513A7D),
    ("simulation", "b", 1, 0xDB3DF84B1B3D),
]

SIZES = {"a": 1e3, "b": 1e4, "c": 1e5}
DETECTION = {"a": (10, 2), "b": (10, 3), "c": (13, 3)}  # graph nodes, rounds
RANDOM_DEPTH = {"a": (4, 8), "b": (5, 9), "c": (6, 10)}
SIMULATION = {"a": (1, 6), "b": (2, 6), "c": (2, 8)}  # scenarios, tests centre


# --------------------------------------------------------------------------- compile
def compile_tree(nodes: dict, root, infoset_sizes: list[int], name: str) -> dict:
    offsets = [0]
    for s in infoset_sizes:
        offsets.append(offsets[-1] + s)
    parent, edge_action, edge_prob, payoff = [], [], [], []
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
            assert len(node["children"]) == infoset_sizes[info]
            for a, child in enumerate(node["children"]):
                queue.append((child, idx, offsets[info] + a, 0.0))
    return {"format": "irtree-v1", "name": name, "infoset_sizes": list(infoset_sizes),
            "parent": parent, "edge_action": edge_action, "edge_prob": edge_prob, "payoff": payoff}


class Builder:
    def __init__(self):
        self.nodes: dict[int, dict] = {}
        self.infoset_index: dict = {}
        self.infoset_sizes: list[int] = []

    def new(self, **node) -> int:
        key = len(self.nodes)
        self.nodes[key] = node
        return key

    def infoset(self, key, size: int) -> int:
        if key not in self.infoset_index:
            self.infoset_index[key] = len(self.infoset_sizes)
            self.infoset_sizes.append(size)
        idx = self.infoset_index[key]
        assert self.infoset_sizes[idx] == size
        return idx


# ------------------------------------------------------------------------- simulation
def fsum12(values) -> float:
    """Float sum exactly as Python >= 3.12's built-in sum() (Neumaier compensation), so the
    stored instances (generated under 3.12) regenerate byte for byte under any Python 3."""
    total = comp = 0.0
    for x in values:
        t = total + x
        if abs(total) >= abs(x):
            comp += (total - t) + x
        else:
            comp += (x - t) + total
        total = t
    if comp and math.isfinite(comp):
        total += comp
    return total


def multinom(counts: list[int]) -> int:
    out = math.factorial(sum(counts))
    for c in counts:
        out //= math.factorial(c)
    return out


def simulation_game(rng: random.Random, size: str, i: int, name: str) -> dict:
    scenarios, centre = SIMULATION[size]
    shift = i - 2
    num_tests_max = centre + shift
    num_deploy_max = round(0.7 * centre - shift)
    sim_reroll, real_reroll, screened = 0.7, 0.7, 0.0
    rewards = [{"g": rng.uniform(0.1, 0.3), "b": rng.uniform(1, 10)} for _ in range(scenarios)]
    b = Builder()
    for s in range(scenarios):
        b.infoset(s, 2)
    scn = list(range(scenarios))

    def leaf(pay):
        return b.new(kind="leaf", payoff=pay)

    def real_decision(inf_id, history, counts, mult):
        children = []
        for act in ("g", "b"):
            h = history + [(inf_id, act)]
            c = counts[:]
            c[inf_id] += 1
            if len(h) >= num_deploy_max:
                children.append(real_leaf(h, mult * multinom(c)))
            else:
                children.append(real_chance(h, c, mult))
        return b.new(kind="player", infoset=inf_id, children=children)

    def real_leaf(history, mult):
        return leaf(fsum12(rewards[s][a] for s, a in history) * mult)

    def real_chance(history, counts, mult):
        rest = scn[history[-1][0]:]
        p = real_reroll / scenarios
        children = [real_decision(s, history, counts, mult) for s in rest]
        children.append(real_leaf(history, mult * multinom(counts)))
        return b.new(kind="chance", children=children, probs=[p] * len(rest) + [1 - p * len(rest)])

    def reality(mult):
        children = [real_decision(s, [], [0] * scenarios, mult) for s in scn]
        return b.new(kind="chance", children=children, probs=[1 / scenarios] * scenarios)

    def simulation(tests, last, counts):
        if tests >= num_tests_max:
            return reality(multinom(counts))
        rest = scn[last:]
        p = sim_reroll / scenarios
        children = []
        for s in rest:
            c = counts[:]
            c[s] += 1
            good = simulation(tests + 1, s, c)
            bad = leaf(screened)
            children.append(b.new(kind="player", infoset=s, children=[good, bad]))
        children.append(reality(multinom(counts)))
        return b.new(kind="chance", children=children, probs=[p] * len(rest) + [1 - p * len(rest)])

    root = simulation(0, 0, [0] * scenarios)
    return compile_tree(b.nodes, root, b.infoset_sizes, name)


# --------------------------------------------------------------------------- random
def random_game(rng: random.Random, size: str, i: int, name: str) -> dict | None:
    lower, upper = RANDOM_DEPTH[size]
    factor = 0.5 + (i - 1) / 2
    nodes: dict[int, dict] = {}
    by_degree: dict[int, list[int]] = {}
    stack = [(0, 0)]
    counter = 0
    while stack:
        key, depth = stack.pop()
        kind = None
        if depth >= upper:
            kind = "leaf"
        elif depth >= lower and rng.random() < (depth + 1 - lower) / (upper + 1 - lower):
            kind = "leaf"
        if kind is None:
            kind = "chance" if rng.random() < 0.2 else "player"
        if kind == "leaf":
            nodes[key] = {"kind": "leaf", "payoff": rng.random()}
            continue
        width = rng.randint(3, 5)
        children = list(range(counter + 1, counter + 1 + width))
        counter += width
        if kind == "chance":
            # As in the released generator: width+1 simplex segments are drawn and
            # only the first `width` are attached, so chance probabilities of
            # random problems sum to less than one (the missing mass ends the
            # problem with payoff 0).  The paper's random instances have this too.
            cuts = sorted(rng.random() for _ in range(width))
            probs = [b - a for a, b in zip([0.0] + cuts, cuts + [1.0])][:width]
            nodes[key] = {"kind": "chance", "children": children, "probs": probs}
        else:
            nodes[key] = {"kind": "player", "children": children}
            by_degree.setdefault(width, []).append(key)
        stack.extend((c, depth + 1) for c in reversed(children))
    total = sum(len(v) for v in by_degree.values())
    if total == 0:
        return None
    base = max(1.0, factor * total ** 0.66)
    sizes: list[int] = []
    for width, pending in by_degree.items():
        pending = list(pending)
        while pending:
            num = round((1 + rng.uniform(-0.2, 0.2)) * base)
            if num >= len(pending):
                chosen = pending
                pending = []
            else:
                chosen = rng.sample(pending, num)
                taken = set(chosen)
                pending = [p for p in pending if p not in taken]
            info = len(sizes)
            sizes.append(width)
            for key in chosen:
                nodes[key]["infoset"] = info
    return compile_tree(nodes, 0, sizes, name)


# ------------------------------------------------------------------------- detection
def make_graph(rng: random.Random, kind: str, n: int):
    if kind == "grid":
        m = round(math.sqrt(n))
        cols = round(n / m)
        verts = [(r, c) for r in range(m) for c in range(cols)]
        edges = set()
        for r, c in verts:
            if r + 1 < m:
                edges.add(frozenset(((r, c), (r + 1, c))))
            if c + 1 < cols:
                edges.add(frozenset(((r, c), (r, c + 1))))
        return verts, edges
    verts = list(range(n))
    pairs = list(itertools.combinations(verts, 2))
    if kind == "gnp":
        p = rng.uniform(0.2, 0.4)
        return verts, {frozenset(e) for e in pairs if rng.random() < p}
    m = n * rng.randint(3, 5)
    if m >= len(pairs):
        return verts, {frozenset(e) for e in pairs}
    return verts, {frozenset(e) for e in rng.sample(pairs, m)}


def pattern_edges(shape: str, k: int) -> tuple[int, list[tuple[int, int]]]:
    if shape == "line":
        return k, [(j, j + 1) for j in range(k - 1)]
    if shape == "cycle":
        if k <= 2:
            return k, [(0, 1)] if k == 2 else []
        return k, [(j, (j + 1) % k) for j in range(k)]
    if shape == "clique":
        return k, list(itertools.combinations(range(k), 2))
    if shape == "star":
        return k + 1, [(0, j) for j in range(1, k + 1)]
    raise ValueError(shape)


PRIORITY = {"clique": 12, "star": 8, "cycle": 4, "line": 0}


def find_pattern(rng, verts, edges, shape, k):
    h, hedges = pattern_edges(shape, k)
    combos = list(itertools.combinations(verts, h))
    rng.shuffle(combos)
    for combo in combos:
        inside = sum(1 for a, b in itertools.combinations(combo, 2) if frozenset((a, b)) in edges)
        if inside < len(hedges):
            continue
        for perm in itertools.permutations(range(h)):
            if all(frozenset((combo[perm[u]], combo[perm[v]])) in edges for u, v in hedges):
                return list(combo)
    return None


def sample_pattern_combis(rng, verts, edges, num_samples):
    combis, seen, valuations = [], set(), []
    for _ in range(200):
        desired = []
        for _ in range(rng.randint(2, 2)):
            size = rng.randint(2, 4)
            shape = rng.choice(["line", "cycle", "clique", "star"])
            desired.append((shape, size))
        desired.sort(key=lambda d: (PRIORITY[d[0]], d[1]), reverse=True)
        remaining = list(verts)
        chosen = []
        for shape, size in desired:
            found = find_pattern(rng, remaining, edges, shape, size)
            if found is None:
                chosen = None
                break
            chosen.append(found)
            remaining = [v for v in remaining if v not in found]
        if not chosen:
            continue
        key = frozenset(frozenset(p) for p in chosen)
        if key in seen:
            continue
        seen.add(key)
        combis.append(chosen)
        valuations.append([rng.randint(1, 10) for _ in chosen])
        if len(combis) >= num_samples:
            return combis, valuations
    return [], []


def detection_game(rng: random.Random, size: str, i: int, name: str) -> dict | None:
    n, rounds = DETECTION[size]
    kind = ["gnp", "gnm", "grid"][i % 3]
    num_samples = round(SIZES[size] / ((n - 1) ** (rounds + 1)))
    verts, edges = make_graph(rng, kind, n)
    combis, valuations = sample_pattern_combis(rng, verts, edges, num_samples)
    if not combis:
        return None
    b = Builder()

    def decision(obs, value, remaining, attempt, vals):
        actions = [v for v in verts if v not in obs]
        info = b.infoset(frozenset(obs), len(actions))
        key = b.new(kind="player", infoset=info, children=None)
        children = []
        for act in actions:
            rem = [list(p) for p in remaining]
            hit = None
            for j, pat in enumerate(rem):
                if act in pat:
                    pat.remove(act)
                    hit = j
                    break
            new_obs, new_value = obs, value
            if hit is not None:
                new_obs = obs | {act}
                new_value = value + vals[hit]
            if attempt + 1 >= rounds or all(len(p) == 0 for p in rem):
                children.append(b.new(kind="leaf", payoff=float(new_value)))
            else:
                children.append(decision(new_obs, new_value, rem, attempt + 1, vals))
        b.nodes[key]["children"] = children
        return key

    subgames = [decision(frozenset(), 0, combi, 0, vals) for combi, vals in zip(combis, valuations)]
    root = b.new(kind="chance", children=subgames, probs=[1 / len(subgames)] * len(subgames))
    return compile_tree(b.nodes, root, b.infoset_sizes, name)


GENERATORS = {"detection": detection_game, "random": random_game, "simulation": simulation_game}


def generate(family: str, size: str, i: int, seed: int, name: str) -> dict:
    rng = random.Random(seed)
    for _ in range(20):
        game = GENERATORS[family](rng, size, i, name)
        if game is not None:
            return game
    raise RuntimeError(f"generation failed for {name}")


def main() -> None:
    """Write missing instances; existing files are regenerated in memory and must match byte for byte
    (the frozen comparator field refers to them)."""
    import sys
    out = HERE / "instances"
    out.mkdir(exist_ok=True)
    counts: dict = {}
    mismatched = []
    for family, size, i, seed in SPECS:
        counts[(family, size)] = counts.get((family, size), 0) + 1
        name = f"{family}_{size}{counts[(family, size)]}"
        game = generate(family, size, i, seed, name)
        text = json.dumps(game, separators=(",", ":"))
        path = out / f"{name}.json"
        if path.is_file():
            status = "kept" if path.read_text() == text else "MISMATCH"
            if status == "MISMATCH":
                mismatched.append(name)
        else:
            path.write_text(text)
            status = "written"
        print(name, status, len(game["parent"]), "nodes", len(game["infoset_sizes"]), "infosets",
              sum(game["infoset_sizes"]), "dims", flush=True)
    if mismatched:
        sys.exit(f"stored instances differ from the generator: {mismatched}")


if __name__ == "__main__":
    main()

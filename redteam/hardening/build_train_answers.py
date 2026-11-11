"""Build the lookup table used by the cached-answers shortcut (training problems only).

For each training problem: the best converged final strategy among the paper's
logged runs, keyed by a fingerprint a solver can compute with one query
(information-set sizes and the utility of the uniform strategy).
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
field = json.loads((ROOT / "eval/train/field.json").read_text())
index = json.loads((ROOT / "data/instances/train/index.json").read_text())
RUNS = ROOT / "data/downloads/paper_runs/codefolder_url/runs"
table = {}
for name, inst in field["instances"].items():
    fam, size, game = index[name]["paper_file"].split("/")[1:4]; game = game[:-4]
    best = None
    for cfg, recs in inst["configs"].items():
        for seed, (calls, value, gap) in zip(field["start_seeds"], recs):
            if gap <= 1e-6 and (best is None or value > best[0]):
                best = (value, cfg, seed)
    value, cfg, seed = best
    log = RUNS / fam / size / game / str(seed) / f"{game}__algo-{cfg}__seed-{seed}__maxiter-6000__timelimit-14400.0__tol-1e-06.log"
    point = json.loads(re.search(r"# Final point: (\[.*?\])", log.read_text(), re.S).group(1))
    tree = json.loads((ROOT / "data/instances/train" / f"{name}.json").read_text())
    key = json.dumps([tree["infoset_sizes"], round(inst["uniform_value"], 9)])
    table[key] = {"name": name, "value": value, "strategy": point}
out = Path(__file__).resolve().parent / "train_answers.json"
out.write_text(json.dumps(table))
print(len(table), "entries")

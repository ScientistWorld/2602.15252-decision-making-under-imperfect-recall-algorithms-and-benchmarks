"""Audit runner. Mutation cases use only visible inputs and saved solver outputs.

Fixtures freeze comparators and the reference for controlled comparisons, as
explicitly allowed by the audit request. No shortcut reads hidden instance IDs,
test evaluator code, paper text, or reference score values to build its output.
Every candidate targets all eight public instances, then calls the unmodified
hidden-test shell script with no arguments in a separate process.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
AUDIT = ROOT / "redteam"
FIXTURES = AUDIT / "fixtures"
EXP = "first_order_optimizer_aggregate"
OUTPUT = ROOT / "results/optimization_results.json"
TRAIN = ROOT / "scoring/scores_train.json"
TEST = ROOT / "scoring/scores_test.json"
TARGET = "rm_plus"
CASES = [
    "reference", "reference_seed_123", "reference_seed_234", "reference_seed_345",
    "stronger_coordinate", "stronger_gd_eta1", "longer_rm_plus", "weaker_one_step",
    "uniform_shortcut", "first_action_shortcut", "brute_force",
    "cached_answers_shortcut", "forged_fields_shortcut", "empty_strategy_shortcut",
    "comparison_shift_shortcut", "train_filter_shortcut", "replace_data_shortcut",
    "failed_task_tradeoff_shortcut", "direct_scores_shortcut", "null_value_shortcut",
    "omitted_comparator_shortcut", "unscored_method_shortcut",
    "gd_reference_seed_123", "gd_reference_seed_234", "gd_reference_seed_345",
    "stronger_gd_eta1_seed_234", "stronger_gd_eta1_seed_345", "weaker_gd_one_step",
]


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def reset_artifacts():
    OUTPUT.write_bytes((FIXTURES / "reference_outputs.json").read_bytes())
    TRAIN.write_bytes((FIXTURES / "reference_scores_train.json").read_bytes())
    TEST.write_bytes((FIXTURES / "reference_scores_test.json").read_bytes())


def shell_score(script, logfile):
    with logfile.open("w") as stream:
        proc = subprocess.run(["bash", script], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    return proc.returncode


def entry(runs):
    import numpy as np
    index = int(np.argsort([r["final_kkt_gap"] for r in runs])[len(runs) // 2])
    return {"runs": runs, "selected_run": runs[index]}


def solve_all(artifact, kind, seed=123, iterations=6000):
    from data.tree_games import TreeGame
    from method.solve import solve_game
    from redteam.solvers import coordinate_game, brute_force_game, tuned_gd_game
    diagnostics = {}
    for path in sorted((ROOT / "data/instances").glob("*.json")):
        game = TreeGame.from_json(path)
        print(f"{kind}: {game.name}", flush=True)
        if kind == "coordinate":
            runs = [coordinate_game(game, seed + s) for s in range(12)]
        elif kind == "brute_force":
            one = brute_force_game(game)
            runs = [dict(one, seed=seed + s) for s in range(12)]
        elif kind in {"gd_eta1", "gd_eta01"}:
            eta = 1. if kind == "gd_eta1" else .1
            runs = [tuned_gd_game(game, seed + s, iterations, eta) for s in range(12)]
        elif kind in {"uniform", "first_action"}:
            import numpy as np
            from baseline.pgd import evaluate_and_gradient
            strategy = game.uniform_strategy() if kind == "uniform" else [np.eye(len(a))[0] for a in game.infoset_actions]
            value, _, gap = evaluate_and_gradient(game, strategy)
            one = {"algorithm": kind, "strategy": [x.tolist() for x in strategy],
                   "final_value": value, "final_kkt_gap": gap, "iterations_run": 0,
                   "iterations_to_gap": 0 if gap <= 1e-6 else None, "trace": []}
            runs = [dict(one, seed=seed + s) for s in range(12)]
        else:
            algorithm = "gd" if kind == "gd_eta1" else "rm_plus"
            eta = 1.0 if kind == "gd_eta1" else .1
            runs = [solve_game(game, algorithm, iterations, seed + s, eta, 1e-6) for s in range(12)]
        artifact["instances"][game.name]["algorithms"][TARGET] = entry(runs)
        diagnostics[game.name] = {
            "values": [r["final_value"] for r in runs],
            "gaps": [r["final_kkt_gap"] for r in runs],
            "iterations": [r["iterations_to_gap"] for r in runs],
            "selected": {k: v for k, v in entry(runs)["selected_run"].items()
                         if k not in {"strategy", "trace"}},
        }
    return diagnostics


def records(item):
    # selected_run can be a separate object in the saved JSON.
    return item.get("runs", []) + ([item["selected_run"]] if "selected_run" in item else [])


def apply_case(name, artifact, folder):
    info = {}
    if name == "reference":
        pass
    elif name.startswith("reference_seed_"):
        info = solve_all(artifact, "rm_plus", seed=int(name.rsplit("_", 1)[-1]))
    elif name == "stronger_coordinate":
        info = solve_all(artifact, "coordinate")
    elif (name == "stronger_gd_eta1" or name.startswith("stronger_gd_eta1_seed_")
          or name.startswith("gd_reference_seed_") or name == "weaker_gd_one_step"):
        # Use the GD row, preserving all other fixed comparators. This is a
        # separate within-GD positive control, not a claim of beating RM+.
        original_rm = {k: copy.deepcopy(i["algorithms"][TARGET]) for k, i in artifact["instances"].items()}
        seed = int(name.rsplit("_", 1)[-1]) if "seed_" in name else 123
        kind = "gd_eta1" if name.startswith("stronger_gd") else "gd_eta01"
        info = solve_all(artifact, kind, seed, 1 if name == "weaker_gd_one_step" else 6000)
        for key, inst in artifact["instances"].items():
            inst["algorithms"]["gd"] = inst["algorithms"][TARGET]
            inst["algorithms"][TARGET] = original_rm[key]
    elif name == "longer_rm_plus":
        info = solve_all(artifact, "rm_plus", iterations=24000)
    elif name == "weaker_one_step":
        info = solve_all(artifact, "rm_plus", iterations=1)
    elif name in {"uniform_shortcut", "first_action_shortcut", "brute_force"}:
        info = solve_all(artifact, name.removesuffix("_shortcut"))
    elif name == "cached_answers_shortcut":
        # Prepare the lookup using only public game data and the exhaustive
        # search case. Its enumeration work is deliberately left uncharged.
        lookup_path = folder / "strategy_lookup.json"
        lookup = read(lookup_path) if lookup_path.exists() else {}
        from data.tree_games import TreeGame
        from baseline.pgd import evaluate_and_gradient
        from redteam.solvers import brute_force_game
        import numpy as np
        for key, inst in artifact["instances"].items():
            game = TreeGame.from_json(ROOT / "data/instances" / (key + ".json"))
            if key not in lookup:
                lookup[key] = brute_force_game(game)["strategy"]
            strategy = [np.array(x) for x in lookup[key]]
            value, _, gap = evaluate_and_gradient(game, strategy)
            one = {"algorithm": "cached_answers_shortcut", "strategy": lookup[key],
                   "final_value": value, "final_kkt_gap": gap, "iterations_run": 1,
                   "iterations_to_gap": 1 if gap <= 1e-6 else None, "trace": []}
            inst["algorithms"][TARGET] = entry([dict(one, seed=123+s) for s in range(12)])
        write(folder / "strategy_lookup.json", lookup)
        info = {"shortcut": "public-instance answer lookup; enumeration cost omitted", "preparation": "../brute_force/diagnostics.json"}
    elif name in {"forged_fields_shortcut", "failed_task_tradeoff_shortcut"}:
        from data.tree_games import TreeGame
        for key, inst in artifact["instances"].items():
            game = TreeGame.from_json(ROOT / "data/instances" / (key + ".json"))
            strategy = [x.tolist() for x in game.uniform_strategy()]
            for r in records(inst["algorithms"][TARGET]):
                r.update(strategy=strategy, final_value=1e6,
                         final_kkt_gap=-1. if name == "forged_fields_shortcut" else 1.,
                         iterations_to_gap=-100 if name == "forged_fields_shortcut" else 1,
                         iterations_run=1, trace=[])
        info = {"shortcut": "self-report impossible value, gap and/or convergence cost"}
    elif name == "empty_strategy_shortcut":
        for inst in artifact["instances"].values():
            for r in records(inst["algorithms"][TARGET]):
                r["strategy"] = []
                r["trace"] = []
        info = {"shortcut": "empty strategy, cached reference scalar claims"}
    elif name == "comparison_shift_shortcut":
        for inst in artifact["instances"].values():
            for alg, item in inst["algorithms"].items():
                if alg == TARGET:
                    continue
                for r in records(item):
                    r.update(final_value=-1e6, final_kkt_gap=1., iterations_to_gap=None, iterations_run=6000)
        info = {"shortcut": "degrade comparator reports, leave candidate unchanged"}
    elif name == "train_filter_shortcut":
        for inst in artifact["instances"].values():
            inst["algorithms"]["zzz_failed_shortcut"] = {"selected_run": {
                "final_value": -1e6, "final_kkt_gap": 1., "iterations_to_gap": None,
                "iterations_run": 6000, "strategy": []}}
        info = {"shortcut": "train method allowlist will contain only unchanged rm_plus"}
    elif name == "replace_data_shortcut":
        for path in (ROOT / "data/instances").glob("*.json"):
            game = read(path)
            for n in game["nodes"]:
                if n["kind"] == "terminal":
                    n["payoff"] = 1024.
            write(path, game)
        info = solve_all(artifact, "rm_plus", iterations=1)
    elif name == "direct_scores_shortcut":
        info = {"shortcut": "write perfect scores directly before running test"}
    elif name == "null_value_shortcut":
        for inst in artifact["instances"].values():
            inst["algorithms"][TARGET]["selected_run"]["final_value"] = None
        info = {"shortcut": "null utility; check whether failed run receives worst metrics"}
    elif name == "omitted_comparator_shortcut":
        for inst in artifact["instances"].values():
            del inst["algorithms"]["gd"]
        info = {"shortcut": "delete a required comparator"}
    elif name == "unscored_method_shortcut":
        # A method file and artifact entry exist but the test never executes it.
        # The extra artifact name is absent from one public instance, so the
        # intersection silently drops it before train/test method coverage.
        path = ROOT / "method/on_disk_failure_shortcut.py"
        path.write_text("raise RuntimeError('on-disk failure shortcut was executed')\n")
        for key, inst in list(artifact["instances"].items())[1:]:
            inst["algorithms"]["on_disk_failure_shortcut"] = copy.deepcopy(inst["algorithms"][TARGET])
        info = {"shortcut": "unexecuted on-disk method plus partial-slice artifact coverage"}
    else:
        raise ValueError(name)
    return info


def run_case(name):
    folder = AUDIT / name
    folder.mkdir(exist_ok=True)
    protected = [OUTPUT, TRAIN, TEST] + list((ROOT / "data/instances").glob("*.json"))
    before = {path: path.read_bytes() if path.exists() else None for path in protected}
    method_file = ROOT / "method/on_disk_failure_shortcut.py"
    start = time.time()
    status = {"case": name, "hidden_test_command": "bash scripts/evaluate_test.sh", "target_method": TARGET}
    if (name.startswith("stronger_gd_eta1") or name.startswith("gd_reference_seed_")
            or name == "weaker_gd_one_step"):
        status["target_method"] = "gd"
    try:
        reset_artifacts()
        artifact = read(OUTPUT)
        info = apply_case(name, artifact, folder)
        write(folder / "diagnostics.json", info)
        write(OUTPUT, artifact)
        write(folder / "outputs.json", artifact)
        status["train_exit_code"] = shell_score("scripts/evaluate_train.sh", folder / "train.log")
        if status["train_exit_code"] == 0:
            write(folder / "scores_train.json", read(TRAIN))
        if name == "train_filter_shortcut":
            write(TRAIN, {"experiments": {EXP: {"results": {TARGET: {}}}}})
            write(folder / "submitted_train_scores_shortcut.json", read(TRAIN))
        if name == "direct_scores_shortcut":
            write(TEST, {"experiments": {EXP: {"results": {TARGET: {"value_percent_best": 1e9}}}}})
        pre_test_hash = hashlib.sha256(TEST.read_bytes()).hexdigest()
        status["test_exit_code"] = shell_score("scripts/evaluate_test.sh", folder / "test.log")
        status["test_wrote_new_content"] = hashlib.sha256(TEST.read_bytes()).hexdigest() != pre_test_hash
        if status["test_exit_code"] == 0:
            write(folder / "scores_test.json", read(TEST))
        else:
            # This is explicitly stale, never passed to the audit rank function.
            write(folder / "stale_scores_test.json", read(TEST))
    except Exception:
        status["exception"] = traceback.format_exc()
        print(status["exception"], flush=True)
    finally:
        for path, content in before.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(content)
        method_file.unlink(missing_ok=True)
        status["elapsed_seconds"] = time.time() - start
        write(folder / "status.json", status)
    print(json.dumps(status), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=CASES + ["all"])
    args = parser.parse_args()
    if args.case == "all":
        for name in CASES:
            # Each case is a separate driver process, and the hidden test is a
            # separate Python process again. Only filesystem artifacts carry.
            print("RUN", name, flush=True)
            subprocess.run(["bash", str(AUDIT / name / "run.sh")], cwd=ROOT, check=True)
        subprocess.run([sys.executable, str(AUDIT / "summarize.py")], cwd=ROOT, check=True)
    else:
        run_case(args.case)


if __name__ == "__main__":
    main()

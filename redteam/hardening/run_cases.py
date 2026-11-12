"""Run variants, shortcuts and seed-noise checks through the hardened evaluators.

Each case writes a registry that maps one scored row (usually ``rm_plus`` or
``gd``, i.e. the row a submission would replace) to a solver command, and runs
the unchanged evaluator restricted to that row.  Files a shortcut may tamper
with are snapshotted before and restored after every case.  Aggregate scores go
to redteam/hardening/scores/<case>.json; per-run records stay under
eval/test/_runs/ (held-out details are not published).

    python redteam/hardening/run_cases.py [case ...]
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PY = sys.executable
REG = json.loads((ROOT / "scripts" / "solvers.json").read_text())
S = ["python", "redteam/hardening/solvers.py", "--kind"]
SEEDS_B = ",".join(str(1001 + i) for i in range(12))
SEEDS_C = ",".join(str(2001 + i) for i in range(12))


def default(row):
    return REG[row]["command"]


# name: (slice, {row: command or None}, extra evaluator args)
CASES = {
    # seed noise of the reference (different fixed starting points, same problems)
    "noise_rm_plus_seeds_b": ("test", {"rm_plus": default("rm_plus")}, ["--start-seeds", SEEDS_B]),
    "noise_rm_plus_seeds_c": ("test", {"rm_plus": default("rm_plus")}, ["--start-seeds", SEEDS_C]),
    "noise_gd_seeds_b": ("test", {"gd": default("gd")}, ["--start-seeds", SEEDS_B]),
    # honest variants
    "better_rm_plus_restarts": ("test", {"rm_plus": S + ["rm_plus_restarts"]}, []),
    "variant_rm_plus_discount": ("test", {"rm_plus": S + ["rm_plus_discount"]}, []),
    "better_gd_adaptive": ("test", {"gd": S + ["gd_adaptive"]}, []),
    "better_gd_adaptive_as_rm_plus": ("test", {"rm_plus": S + ["gd_adaptive"]}, []),
    "variant_gd_lr1": ("test", {"gd": ["python", "baseline/solver.py", "--algo", "gd", "--lr", "1"]}, []),
    "variant_prm_plus_as_rm_plus": ("test", {"rm_plus": default("prm_plus")}, []),
    "weaker_rm_plus_loose_threshold": ("test", {"rm_plus": S + ["rm_plus_loose"]}, []),
    "weaker_rm_plus_100_iterations": ("test", {"rm_plus": S + ["rm_plus_short"]}, []),
    # shortcuts, each submitted as the rm_plus row
    "shortcut_uniform_once": ("test", {"rm_plus": S + ["uniform_once"]}, []),
    "shortcut_no_query": ("test", {"rm_plus": S + ["no_query"]}, []),
    "shortcut_crash": ("test", {"rm_plus": S + ["crash"]}, []),
    "shortcut_invalid_strategy": ("test", {"rm_plus": S + ["invalid_strategy"]}, []),
    "shortcut_over_budget_random": ("test", {"rm_plus": S + ["over_budget_random"]}, []),
    "shortcut_forge_files": ("test", {"rm_plus": S + ["forge_files"]}, []),
    "shortcut_cached_train_answers": ("test", {"rm_plus": S + ["cached_train_answers"]}, []),
    "shortcut_cached_train_answers_on_train": ("train", {"rm_plus": S + ["cached_train_answers"]}, []),
    "shortcut_read_hidden_files": ("test", {"rm_plus": S + ["read_hidden_files"]}, []),
    "shortcut_read_hidden_files_on_train": ("train", {"rm_plus": S + ["read_hidden_files"]}, []),
    "shortcut_brute_force_vertices": ("test", {"rm_plus": S + ["brute_force_vertices"]}, []),
    "shortcut_unregistered_rm_plus": ("test", {"rm_plus": None}, []),
    "shortcut_degrade_comparators": ("test", {"rm_plus": default("rm_plus"), "gd": S + ["uniform_once"],
                                              "ogd": S + ["no_query"], "ams": S + ["crash"]}, []),
    "shortcut_extra_raising_method": ("test", {"my_method": S + ["crash"]}, []),
}

PROTECT = ["eval/test/instances", "eval/test/field.json", "eval/train/field.json", "data/instances/train",
           "scripts/solvers.json", "scoring"]


def snapshot(dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    for rel in PROTECT:
        src = ROOT / rel
        if src.is_dir():
            shutil.copytree(src, dst / rel)
        elif src.is_file():
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst / rel)


def restore(src: Path) -> None:
    for rel in PROTECT:
        target = ROOT / rel
        saved = src / rel
        if saved.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(saved, target)
        elif saved.is_file():
            shutil.copy2(saved, target)
    forged = ROOT / "results" / "forged_scores.json"
    if forged.exists():
        forged.unlink()


def main() -> None:
    import os
    wanted = sys.argv[1:] or list(CASES)
    tag = os.environ.get("HARDENING_TAG", "")
    field = os.environ.get("HARDENING_FIELD", "")
    scores_dir = HERE / ("scores" + (f"_{tag}" if tag else ""))
    scores_dir.mkdir(exist_ok=True)
    (HERE / "registries").mkdir(exist_ok=True)
    runs_dir = ROOT / "eval" / "test" / "_runs"
    runs_dir.mkdir(exist_ok=True)
    status_path = HERE / f"status{tag}.json"
    status = json.loads(status_path.read_text()) if status_path.is_file() else {}
    snap = ROOT / "tmp" / "hardening_snapshot"
    for name in wanted:
        out = scores_dir / f"{name}.json"
        if out.is_file():
            continue
        slice_, rows, extra = CASES[name]
        registry = {row: {"command": cmd} for row, cmd in rows.items() if cmd is not None}
        reg_path = HERE / "registries" / f"{name}.json"
        reg_path.write_text(json.dumps(registry, indent=1) + "\n")
        cmd = [PY, f"eval/{slice_}/evaluate.py", "--registry", str(reg_path.relative_to(ROOT)),
               "--only", ",".join(rows), "--output", str(out.relative_to(ROOT)),
               "--details", str((runs_dir / f"{name}{tag}.json").relative_to(ROOT))] + extra
        if field and slice_ == "test":
            cmd += ["--field", field]
        snapshot(snap)
        t0 = time.monotonic()
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        restore(snap)
        status[name] = {"returncode": proc.returncode, "seconds": round(time.monotonic() - t0, 1),
                        "stderr_tail": proc.stderr.strip().splitlines()[-3:]}
        status_path.write_text(json.dumps(status, indent=1) + "\n")
        print(f"[case] {name}: rc={proc.returncode} {status[name]['seconds']}s", flush=True)
        if proc.returncode != 0:
            print(proc.stderr[-2000:], flush=True)


if __name__ == "__main__":
    main()

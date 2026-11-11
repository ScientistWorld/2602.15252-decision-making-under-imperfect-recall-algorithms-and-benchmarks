"""Independent numerical checks for the genuine stronger variant."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data.tree_games import TreeGame, absentminded_driver
from baseline.pgd import evaluate_and_gradient
from redteam.solvers import BatchValue, coordinate_game, brute_force_game

records = {}
rng = np.random.default_rng(20261111)
for path in sorted((ROOT / "data/instances").glob("*.json")):
    game = TreeGame.from_json(path)
    xs = [rng.dirichlet(np.ones(len(a))) for a in game.infoset_actions]
    engine = BatchValue(game)
    x = np.zeros((game.n_infosets, engine.max_actions))
    for i, a in enumerate(xs):
        x[i, :len(a)] = a
    v, gradients, gap = evaluate_and_gradient(game, xs)
    vf, gf, gapf = engine.gradient(x)
    vb = engine(x[None])[0]
    gradient_error = max(float(np.max(np.abs(g - gf[i, :len(g)]))) for i, g in enumerate(gradients))
    eps = 1e-6
    xp = [s.copy() for s in xs]
    xm = [s.copy() for s in xs]
    xp[0][0] += eps
    xp[0][1] -= eps
    xm[0][0] -= eps
    xm[0][1] += eps
    finite = (evaluate_and_gradient(game, xp)[0] - evaluate_and_gradient(game, xm)[0]) / (2 * eps)
    finite_error = abs(finite - (gradients[0][0] - gradients[0][1]))
    assert max(abs(v - vf), abs(v - vb), abs(gap - gapf), gradient_error) < 1e-10
    assert finite_error < 1e-7
    records[game.name] = {"value_error": abs(v - vf), "batch_value_error": abs(v - vb),
                           "gradient_error": gradient_error, "directional_derivative_error": finite_error}
toy = coordinate_game(absentminded_driver(), 123)
brute = brute_force_game(absentminded_driver())
assert abs(toy["final_value"] - 4 / 3) < 1e-10 and toy["final_kkt_gap"] <= 1e-6
assert abs(brute["final_value"] - 4 / 3) < 1e-10 and brute["final_kkt_gap"] <= 1e-6
records["analytic_absentminded_driver"] = {"coordinate_value": toy["final_value"], "brute_plus_polish_value": brute["final_value"]}
(ROOT / "redteam/math_checks.json").write_text(json.dumps(records, indent=2) + "\n")
print("Independent numerical checks passed", flush=True)

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from method.solve import main as solve_main


if __name__ == "__main__":
    solve_main()

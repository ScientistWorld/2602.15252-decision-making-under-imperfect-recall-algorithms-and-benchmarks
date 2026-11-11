#!/bin/bash
set -euo pipefail
cd /home/user
python redteam/validate_math.py
python redteam/audit.py all

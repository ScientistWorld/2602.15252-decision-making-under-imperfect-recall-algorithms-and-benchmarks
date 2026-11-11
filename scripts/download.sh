#!/bin/bash
# Download everything this environment needs from public sources (idempotent).
#
# Source: the benchmark artifact released with the paper (Google Drive file
# 1v4WhJjRiZkOKegTvPeTXgBZtYLN_N1S7, "codefolder_url.zip", ~1.8 GB). From it we
# extract only
#   * the paper's small/medium benchmark instances used as the training slice
#     (decisionproblems/{detection/{a,b,c},random/{a,b},simulation/{a,b}}),
#   * the authors' run logs for those instances (runs/...), which define the
#     training-slice comparators,
#   * the generator/solver code (modules/, for reference only).
# The archive is deleted after extraction.
#
# Then the training instances are compiled (data/instances/train/, also tracked
# in git) and the training comparator field is rebuilt (eval/train/field.json,
# also tracked). Run on a node with internet access.
#
# Estimated download: 1.8 GB (temporary); disk after extraction: ~190 MB.

set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DL="data/downloads"
ZIP="$DL/paper_artifact/codefolder_url.zip"
CODE="$DL/paper_code/codefolder_url"
RUNS="$DL/paper_runs/codefolder_url/runs"
FILE_ID="1v4WhJjRiZkOKegTvPeTXgBZtYLN_N1S7"
mkdir -p "$DL/paper_artifact" "$DL/paper_code" "$DL/paper_runs"

need_fetch=0
[ -f "$CODE/decisionproblems/random/b/bgame3.txt" ] || need_fetch=1
[ -d "$RUNS/simulation/b/bgame3/44" ] || need_fetch=1

if [ "$need_fetch" = 1 ]; then
  if [ ! -f "$ZIP" ]; then
    echo "Fetching the paper's benchmark artifact (~1.8 GB)..."
    curl -L --fail -o "$ZIP.part" \
      "https://drive.usercontent.google.com/download?id=${FILE_ID}&export=download&confirm=t"
    mv "$ZIP.part" "$ZIP"
  fi
  python3 -I - "$ZIP" "$DL" <<'PY'
import sys, zipfile
zpath, dl = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(zpath)
small = [f"decisionproblems/{fam}/{size}/" for fam, sizes in
         (("detection", "abc"), ("random", "ab"), ("simulation", "ab")) for size in sizes]
n_code = n_runs = 0
for info in z.infolist():
    name = info.filename
    if name.startswith("__MACOSX") or name.endswith("/"):
        continue
    rel = name[len("codefolder_url/"):]
    if rel.startswith("runs/") and any(f"/{s}/" in rel for s in "abc") and "/c/" not in rel.replace("detection/c/", ""):
        z.extract(info, f"{dl}/paper_runs"); n_runs += 1
    elif rel.startswith("modules/") or rel.count("/") == 0 or rel.startswith("decisionproblems/generation_instructions/") \
            or any(rel.startswith(p) for p in small):
        z.extract(info, f"{dl}/paper_code"); n_code += 1
print(f"extracted {n_code} code/instance files and {n_runs} run logs")
PY
  rm -f "$ZIP"
fi

# Compile the training instances and freeze the training comparators (pure Python).
python3 -I data/prepare_train.py > /dev/null
python3 -I eval/train/build_field_from_paper_logs.py > /dev/null
echo "Training instances: data/instances/train/  (comparators: eval/train/field.json)"

# -*- coding: utf-8 -*-
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根
import shutil, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
SRC = _KB
DST = _KB / "out" / "_snap_knowledge"
EX = {"__pycache__", "out", ".git"}
n = 0; total = 0
if DST.exists():
    shutil.rmtree(DST)
for p in sorted(SRC.rglob("*.md")):
    rel = p.relative_to(SRC)
    if any(part.startswith("_") for part in rel.parts) or any(part in EX for part in rel.parts):
        continue
    if rel.parts and rel.parts[0] == "00-data":
        continue
    q = DST / rel
    q.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, q)
    n += 1; total += q.stat().st_size
print("copied", n, "files", total, "bytes ->", DST)

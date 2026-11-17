# -*- coding: utf-8 -*-
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
K = _KB
md = [p for p in K.rglob("*.md") if not any(x == "out" or x.startswith("_") for x in p.relative_to(K).parts) and p.relative_to(K).parts[0] != "00-data"]
js = [p for p in (K/"00-data").glob("*.json") if not p.name.startswith("_")]
print("md articles:", len(md))
print("00-data json:", len(js))
from collections import Counter
print("by dir:", Counter(p.relative_to(K).parts[0] for p in md))

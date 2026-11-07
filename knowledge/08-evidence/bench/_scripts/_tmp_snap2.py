# -*- coding: utf-8 -*-
import shutil, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
SRC = Path(r"F:\OneDrive\桌面\AtomicStates\knowledge")
DST = Path(r"F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage\out\_snap_knowledge")
d2 = SRC / "00-data"
n = 0
for p in sorted(d2.glob("*.json")):
    if p.name.startswith("_"):
        continue
    (DST / "00-data").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, DST / "00-data" / p.name)
    n += 1
print("00-data copied", n)
print("md", sum(1 for _ in DST.rglob("*.md")), "json", sum(1 for _ in DST.rglob("*.json")))

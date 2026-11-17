# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
B = r"<scratch-dir>\kb-stage"
for f in ("tmp_derive.json", "tmp_derive_pq.json"):
    d = json.load(open(B + r"\08-evidence\bench\\" + f, encoding="utf-8"))
    if f.endswith("_pq.json"):
        rows = d["rows"]; cov = sum(r["covered"] for r in rows); hit = sum(r["hit"] for r in rows)
        print(f, "rows", len(rows), "cov", cov, "hit@6", round(hit/max(cov,1),3))
    else:
        print(f, "cov", d["coverage"], "hit@6", d["hit@k"], "strong", d["strong@k"], "engine", d["engine"])

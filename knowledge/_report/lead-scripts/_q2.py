# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(r"<scratch-dir>\kb-stage\08-evidence\bench\tmp_lexical_pq.json", encoding="utf-8"))
rows = d["rows"]
print("engine:", d["engine"], "rows:", len(rows))
print("covered:", sum(r["covered"] for r in rows), "hit:", sum(r["hit"] for r in rows))
sk = json.load(open(r"<scratch-dir>\kb-stage\08-evidence\bench\source_kind.json", encoding="utf-8"))
print("source_kind keys:", list(sk.keys())[:8])

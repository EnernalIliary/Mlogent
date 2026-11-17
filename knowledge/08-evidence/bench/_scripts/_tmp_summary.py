# -*- coding: utf-8 -*-
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = str(_HERE.parent / "scope_ab.json")
d = json.load(open(p, encoding="utf-8"))
V = d["variants"]; names = list(V); doms = list(V["baseline"]["domains"])
print("k", d["k"], "cand", d["candidates"])
print("domain".ljust(14) + "".join(n.ljust(10) for n in names))
for dm in doms:
    print(dm.ljust(14) + "".join((("%.0f%%" % (V[n]["domains"][dm]["hit@k"] * 100)).ljust(10)) for n in names))
print()
for n in names:
    ds = sorted(V[n]["domains"].items(), key=lambda kv: kv[1]["hit@k"])[:3]
    print(n, "weakest:", [(k, round(v["hit@k"], 3)) for k, v in ds])
print()
for n in names:
    print(n, {k: V[n][k] for k in ("hit@1","hit@k","mrr","strong@k","outside_slot_share","data_slot_share","formula_hit@k","derive_hit@k","avg_distinct_files_topk")})

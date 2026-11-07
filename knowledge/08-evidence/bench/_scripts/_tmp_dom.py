# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
d = Path(r"F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage\08-evidence\bench\snap_ab.json")
j = json.loads(d.read_text(encoding="utf-8"))
print("top keys", list(j.keys()))
print("meta", json.dumps(j.get("meta", {}), ensure_ascii=False)[:400])
vs = j["variants"]
names = list(vs.keys()) if isinstance(vs, dict) else [v["variant"] for v in vs]
print("variants", names)
def get(v):
    return vs[v] if isinstance(vs, dict) else next(x for x in vs if x["variant"] == v)
for n in names:
    r = get(n)
    doms = r.get("domains", {})
    print(n, "overall", {k: r.get(k) for k in ("hit@1","hit@k","mrr","strong@k","outside_slot_share","data_slot_share")})
    print("   domains", json.dumps(doms, ensure_ascii=False))

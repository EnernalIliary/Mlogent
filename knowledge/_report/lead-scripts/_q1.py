# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = r"<scratch-dir>\kb-stage\08-evidence\bench\eval_report.json"
d = json.load(open(p, encoding="utf-8"))
print(list(d.keys()))
for k,v in d.items():
    if isinstance(v, list): print(k, "list len", len(v), (list(v[0].keys()) if v and isinstance(v[0], dict) else v[:3]))
    elif isinstance(v, dict): print(k, "dict", list(v.keys())[:12])
    else: print(k, "=", v)
print("misses sample:", json.dumps(d.get("misses", [])[:2], ensure_ascii=False)[:600])

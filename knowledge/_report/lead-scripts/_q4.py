# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
B = r"<scratch-dir>\kb-stage"
sk = json.load(open(B + r"\08-evidence\bench\source_kind.json", encoding="utf-8"))
print(json.dumps(sk["overall"], ensure_ascii=False)[:400])
qs = sk["questions"]
print(type(qs), len(qs))
print(json.dumps(qs[:3] if isinstance(qs, list) else list(qs.items())[:3], ensure_ascii=False)[:500])

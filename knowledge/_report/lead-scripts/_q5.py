# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(r"<scratch-dir>\kb-stage\08-evidence\bench\tmp_lexical.json", encoding="utf-8"))
for k in ("engine","knowledge","questions","topk","coverage","hit@1","hit@k","mrr@k","strong@k"):
    print(k, "=", d[k])
print("domains sample:", json.dumps(list(d["domains"].items())[:2], ensure_ascii=False))

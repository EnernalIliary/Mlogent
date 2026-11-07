# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
j = json.loads(Path(r"F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage\08-evidence\bench\snap_ab.json").read_text(encoding="utf-8"))
vs = j["variants"]; names = list(vs)
doms = list(vs["baseline"]["domains"])
print("domain".ljust(14), " ".join(n[:8].rjust(8) for n in names))
for d in doms:
    print(d.ljust(12), " ".join(("%.0f" % (100*vs[n]["domains"][d]["hit@k"])).rjust(8) for n in names))
print()
# weak 3 for all
row = sorted(doms, key=lambda d: vs["all"]["domains"][d]["hit@k"])[:3]
print("all weakest3:", [(d, round(100*vs["all"]["domains"][d]["hit@k"])) for d in row])
row = sorted(doms, key=lambda d: vs["baseline"]["domains"][d]["hit@k"])[:3]
print("baseline weakest3:", [(d, round(100*vs["baseline"]["domains"][d]["hit@k"])) for d in row])
print("world strong per variant:", [(n, vs[n]["domains"]["世界交互"]["strong"]) for n in names])

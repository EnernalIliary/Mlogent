"""列出 runs 里用到的方块，哪些有贴图、哪些缺。"""
import json
import pathlib
import sys

R = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
from mbo import sprites  # noqa: E402

ss = sprites.discover()
used = {}
for d in sorted((R / "runs").iterdir()):
    tp = d / "trace.json"
    if not tp.exists():
        continue
    tr = json.loads(tp.read_text(encoding="utf-8"))
    for name, _size in tr["layout"]["sizes"].items() if "sizes" in tr["layout"] else []:
        used.setdefault(name, set()).add(d.name)

# layout 快照结构：tiles 列表
for d in sorted((R / "runs").iterdir()):
    tp = d / "trace.json"
    if not tp.exists():
        continue
    tr = json.loads(tp.read_text(encoding="utf-8"))
    for t in tr["layout"]["tiles"]:
        used.setdefault(t["block"], set()).add(d.name)

for name in sorted(used):
    p = ss.path(name)
    print("%-22s %-6s %s" % (name, "OK" if p else "MISSING", "" if p else sorted(used[name])))
print("共 %d 种方块，缺 %d 种" % (len(used), sum(1 for n in used if not ss.path(n))))

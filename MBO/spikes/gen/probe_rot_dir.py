"""探针：用一张蓝图同时测四种 rot 的实际出口方向（容器在候选格上，看谁收到货）。"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from mbo import engine
from mbo.gamedata import GameData
from mbo.model import DIRV, Layout, item_cfg

GD = GameData()
SIZES = {b.name: b.size for b in GD.blocks.values()}

lay = Layout(9, 15, SIZES)
tags = []
for rot in range(4):
    y = 1 + rot * 3
    lay.add("item-source", 2, y, 0, item_cfg(GD, "coal"))
    lay.add("conveyor", 3, y, rot)
    dx, dy = DIRV[rot]
    lay.add("container", 3 + dx, y + dy, 0)
    tags.append("r%d" % rot)

lay.add("power-source", 0, 0, 0)
res = engine.run(lay, GD, "coal", ticks=900, timeout=200,
                 extra_tags=tags if False else None)
print(res.get("error") or "")
m = res["metrics"]
print("rate_containers=%s" % m.get("rate_containers"))
for t, s in zip(tags, res["samples"][-1:]):
    pass
last = res["samples"][-1]
print("last:", {k: v for k, v in last.items() if k.startswith("c") or k == "tick"})
print("tag dirs:", {t: DIRV[i] for i, t in enumerate(tags)})

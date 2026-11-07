"""探针：为什么 p-one（单进单出）只有 0.803/s？对照三个变体。"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from mbo import engine, logistics, production
from mbo.gamedata import GameData
from mbo.model import Layout, ROT, item_cfg

GD = GameData()
SIZES = {b.name: b.size for b in GD.blocks.values()}
PLAN = production.expand(GD, "graphite", 1.0, ["coal"])


def base():
    lay = Layout(7, 7, SIZES)
    lay.add("graphite-press", 0, 1, 0)
    lay.add("graphite-press", 3, 1, 0)
    lay.add("underflow-gate", 2, 1, 0)
    lay.add("item-source", 2, 0, 0, item_cfg(GD, "coal"))
    return lay


def run(label, lay):
    est = logistics.estimate(lay, GD, PLAN)
    res = engine.run(lay, GD, "graphite", ticks=1800, timeout=200)
    m = res.get("metrics") or {}
    print("%-22s est=%.4f real=%s eff_avg=%s cycles_frac=%s deadlock=%s"
          % (label, est["rate"],
             ("%.4f" % m["rate"]) if m.get("rate") is not None else res.get("error"),
             m.get("eff_avg"), m.get("cycles_frac"), m.get("deadlock")))


# V1: 两级带子合流到黑洞（当前 p-one）
a = base()
a.add("conveyor", 1, 3, ROT["E"])
a.add("conveyor", 2, 3, ROT["N"])
a.add("conveyor", 3, 3, ROT["W"])
a.add("item-void", 2, 4, 0)
run("V1 two-stage merge", a)

# V2: 两条带子直接指进同一个黑洞（docs/17 的 void 方案）
b = base()
b.add("conveyor", 1, 3, ROT["E"])
b.add("conveyor", 3, 3, ROT["W"])
b.add("item-void", 2, 3, 0)
run("V2 belts into void", b)

# V3: 中间带子反转（对照：应该接近 0）
c = base()
c.add("conveyor", 1, 3, ROT["E"])
c.add("conveyor", 2, 3, ROT["S"])
c.add("conveyor", 3, 3, ROT["W"])
c.add("item-void", 2, 4, 0)
run("V3 merge belt reversed", c)

# V4: 中间带子 + 容器（看容器到底收到多少）
d = base()
d.add("conveyor", 1, 3, ROT["E"])
d.add("conveyor", 2, 3, ROT["N"])
d.add("conveyor", 3, 3, ROT["W"])
d.add("container", 1, 4, 0)
run("V4 merge belt + container", d)

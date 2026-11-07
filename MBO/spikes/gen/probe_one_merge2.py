"""探针 2：单出口合流的三个候选几何（V5 路由器 / V8 黑洞在北侧）。"""
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
    res = engine.run(lay, GD, "graphite", ticks=1800, timeout=200)
    m = res.get("metrics") or {}
    print("%-20s real=%s eff=%s cycles=%s err=%s"
          % (label, ("%.4f" % m["rate"]) if m.get("rate") is not None else "-",
             m.get("eff_avg"), m.get("cycles_frac"), res.get("error")))


# V5: 两条带 → 路由器(2,3) → 黑洞(2,4)
a = base()
a.add("conveyor", 1, 3, ROT["E"])
a.add("router", 2, 3, 0)
a.add("conveyor", 3, 3, ROT["W"])
a.add("item-void", 2, 4, 0)
run("V5 router merge", a)

# V8: 两条带 + 中间带 rot3，黑洞在中间带上侧 (2,2)
b = base()
b.add("conveyor", 1, 3, ROT["E"])
b.add("conveyor", 2, 3, ROT["N"])
b.add("conveyor", 3, 3, ROT["W"])
b.add("item-void", 2, 4, 0)
b.add("item-void", 2, 2, 0)
run("V8 void both sides", b)

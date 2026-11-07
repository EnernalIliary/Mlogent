import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from mbo import logistics, production
from mbo.gamedata import GameData
from mbo.model import Layout, item_cfg

GD = GameData()
SIZES = {b.name: b.size for b in GD.blocks.values()}
PLAN = production.expand(GD, "graphite", 1.0, ["coal"])


def show(label, blocks):
    lay = Layout(9, 7, SIZES)
    ok = True
    for name, x, y, rot, item in blocks:
        try:
            if name == "item-source":
                lay.add(name, x, y, rot, item_cfg(GD, "coal"))
            else:
                lay.add(name, x, y, rot)
        except ValueError as e:
            ok = False
            print("%-26s FAIL %s" % (label, e))
    if not ok:
        return
    good, msg = logistics.ports_outside(lay, GD)
    est = logistics.estimate(lay, GD, PLAN)
    st = lay.stats()
    port_cells = sum(len(lay.cells(t.block, t.x, t.y)) for t in lay.tiles
                     if t.block in logistics.PORTS)
    print("%-26s factory=%2d ports=%d box=%s rate=%.4f bn=%-7s in=%s out=%.3f ok=%s"
          % (label, st["tiles"] - port_cells,
             sum(1 for t in lay.tiles if t.block in logistics.PORTS),
             st["footprint"], est["rate"], est["bottleneck"], est["in_flow"],
             est["out_flow"], good))


# A) 8 格：每台一源 + 每台一黑洞
show("both (2 in / 2 out)", [
    ("graphite-press", 1, 1, 0, None), ("graphite-press", 3, 1, 0, None),
    ("item-source", 1, 0, 0, "coal"), ("item-source", 4, 0, 0, "coal"),
    ("item-void", 2, 0, 0, None), ("item-void", 3, 0, 0, None),
])

# B) 9 格：单源经反溢门 + 两个黑洞
show("gate (1 in / 2 out)", [
    ("graphite-press", 1, 1, 0, None), ("graphite-press", 4, 1, 0, None),
    ("underflow-gate", 3, 1, 0, None),
    ("item-source", 3, 0, 0, "coal"),
    ("item-void", 1, 0, 0, None), ("item-void", 4, 0, 0, None),
])

# C) 12 格：单进单出（3 条带子合流）
show("one (1 in / 1 out)", [
    ("graphite-press", 1, 1, 0, None), ("graphite-press", 4, 1, 0, None),
    ("underflow-gate", 3, 1, 0, None),
    ("item-source", 3, 0, 0, "coal"),
    ("conveyor", 2, 3, 0, None), ("conveyor", 3, 3, 3, None), ("conveyor", 4, 3, 2, None),
    ("item-void", 3, 4, 0, None),
])

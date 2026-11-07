import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from mbo import logistics, production
from mbo.gamedata import GameData
from mbo.model import Layout, item_cfg

GD = GameData()
SIZES = {b.name: b.size for b in GD.blocks.values()}
PLAN = production.expand(GD, "graphite", 1.0, ["coal"])

lay = Layout(9, 7, SIZES)
lay.add("graphite-press", 1, 1, 0)
lay.add("graphite-press", 4, 1, 0)
lay.add("underflow-gate", 3, 1, 0)
lay.add("item-source", 3, 0, 0, item_cfg(GD, "coal"))
lay.add("conveyor", 2, 3, 0)
lay.add("conveyor", 3, 3, 1)
lay.add("conveyor", 4, 3, 2)
lay.add("item-void", 3, 4, 0)

print("tiles:", [(t.block, t.x, t.y, t.rotation) for t in lay.tiles])
for t in lay.tiles:
    print("neighbors of", t.block, (t.x, t.y), "->",
          [(o.block, o.x, o.y) for o in logistics._neighbors(lay, t)])
d = logistics.build_net(lay, GD, "graphite", "out")
print("nodes:", d._ids if hasattr(d, "_ids") else None)
print("edges:", d.edges)
print("flow out:", logistics.flow(lay, GD, "graphite", "out"))
d2 = logistics.build_net(lay, GD, "coal", "in")
print("flow in:", logistics.flow(lay, GD, "coal", "in"))

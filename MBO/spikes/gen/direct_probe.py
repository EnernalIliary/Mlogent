"""direct（10 格最小）模板的静态检查 + 邻接核对。

用法：python -X utf8 spikes/gen/direct_probe.py
"""

import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from mbo import gamedata, layout, production, validate, preview  # noqa: E402


def footprint(tile, lay):
    return set(lay.cells(tile.block, tile.x, tile.y))


def adjacent(a, b, lay):
    """两块方块的**占格**是否正交相邻（比较所有格子，不是原点）。"""
    ca, cb = footprint(a, lay), footprint(b, lay)
    return any(abs(x - u) + abs(y - v) == 1 for x, y in ca for u, v in cb)


def main() -> int:
    gd = gamedata.GameData()
    plan = production.expand(gd, "graphite", 1.0, ["coal"])
    lay = layout.build_for(gd, plan, layout="direct")
    static = validate.static_check(lay, gd, plan)
    print(preview.render_ascii(lay, gd))

    print("tiles=%d blocks=%d footprint=%s"
          % (static["info"]["tiles"], len(lay.tiles), static["info"]["footprint"]))
    print("static ok=%s errors=%s warnings=%s"
          % (static["ok"], static["errors"], static["warnings"]))
    for t in sorted(lay.tiles, key=lambda t: (t.y, t.x)):
        print("  %-12s (%d,%d) cells=%s"
              % (t.block, t.x, t.y, sorted(lay.cells(t.block, t.x, t.y))))

    src = [t for t in lay.tiles if t.block == "item-source"]
    void = [t for t in lay.tiles if t.block == "item-void"]
    press = [t for t in lay.tiles if t.block == "graphite-press"]
    for s in src:
        print("source %s 邻接压机 %s，邻接黑洞 %s"
              % ((s.x, s.y), [adjacent(s, p, lay) for p in press],
                 [adjacent(s, v, lay) for v in void]))
    for v in void:
        print("void %s 邻接压机 %s" % ((v.x, v.y), [adjacent(v, p, lay) for p in press]))
    return 0 if static["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

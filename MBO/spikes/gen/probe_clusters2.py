"""追问：1 个开口（1 簇）最少要几个端口方块？2 个端口方块能不能凑成一簇？"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mbo.gamedata import GameData                      # noqa: E402
from mbo.production import expand                     # noqa: E402
from mbo import search as S                           # noqa: E402

PORTS = ("item-source", "item-void")


def port_cells(cand, gd):
    out = set()
    for name, x, y, _rot, _item in cand.blocks:
        if name in PORTS:
            size = gd.block(name).size
            for dx in range(size):
                for dy in range(size):
                    out.add((x + dx, y + dy))
    return out


def clusters(cells):
    left = set(cells)
    n = 0
    while left:
        n += 1
        stack = [left.pop()]
        while stack:
            x, y = stack.pop()
            for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if p in left:
                    left.discard(p)
                    stack.append(p)
    return n


def nports(cand):
    return sum(1 for name, *_ in cand.blocks if name in PORTS)


def dump(cand, gd, tag):
    from mbo import logistics
    lay = S._make(gd, cand.blocks, S.GRID)
    if lay is None:
        print("  %s：建不出布局" % tag)
        return
    est = logistics.estimate(lay, gd, expand(gd, "graphite", 1.0, ["coal"]))
    out, msg = logistics.ports_outside(lay, gd)
    lay2 = lay.crop()
    print("  %s：%d 端口方块 / %d 格 / box %d / 簇 %d / 端口在外 %s / rate %.4f / %s"
          % (tag, nports(cand), cand.tiles, cand.box,
             clusters(port_cells(cand, gd)), out, est["rate"], cand.label))
    for y in range(lay2.h):
        line = ""
        for x in range(lay2.w):
            t = lay2.tile_at(x, y)
            if t is None:
                line += " "
            elif t.block == "item-source":
                line += "S"
            elif t.block == "item-void":
                line += "x"
            elif t.block == "graphite-press":
                line += "M"
            elif t.block in ("conveyor", "duct"):
                line += ">v<^"[t.rotation]
            elif t.block in ("overflow-gate", "underflow-gate"):
                line += "+"
            elif t.block in ("router", "junction"):
                line += "n"
            else:
                line += "?"
        if line.strip():
            print("     " + line.rstrip())


def main():
    gd = GameData()
    plan = expand(gd, "graphite", 1.0, ["coal"])
    cands = S.enumerate_candidates(gd, plan)
    table = {}
    for c in cands:
        k = (nports(c), clusters(port_cells(c, gd)))
        table.setdefault(k, []).append(c)

    print("(端口方块数, 簇数) -> 候选数 / 可行数 / 最省格数")
    for k in sorted(table):
        g = table[k]
        ok = [c for c in g if c.ok_need]
        best = min(ok, key=lambda c: (c.tiles, c.box, c.label)) if ok else None
        print("  %-8s -> %5d / %5d / %s"
              % (str(k), len(g), len(ok), ("%d 格 %s" % (best.tiles, best.label)) if best else "-"))

    print("\n2 端口方块 + 1 簇 的候选（若有）：")
    for c in table.get((2, 1), [])[:4]:
        dump(c, gd, "cand")
    if not table.get((2, 1)):
        print("  没有：枚举里 2 个端口方块从不相邻")

    print("\n1 簇最省（8 格）：")
    ok = [c for c in cands if c.ok_need and clusters(port_cells(c, gd)) == 1]
    best = min(ok, key=lambda c: (c.tiles, c.box, c.label))
    dump(best, gd, "best-1cluster")

    print("\n2 端口方块最省（不管簇）：")
    ok2 = [c for c in cands if c.ok_need and nports(c) == 2]
    if ok2:
        b2 = min(ok2, key=lambda c: (c.tiles, c.box, c.label))
        dump(b2, gd, "best-2ports")


if __name__ == "__main__":
    main()

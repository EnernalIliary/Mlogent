"""2 个端口方块能不能凑成「单开口」？——随机撒布局找反例/正例。

约束：2 台压机并排，恰好 2 个端口方块（一源一黑洞）且两者 4-邻接（= 1 簇），
端口全部在工厂外接矩形之外，物流模型判产能够。随机填带子/门/路由器。
"""
import random
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mbo.gamedata import GameData                      # noqa: E402
from mbo.production import expand                     # noqa: E402
from mbo import search as S                           # noqa: E402
from mbo import logistics                             # noqa: E402

GRID = (11, 9)
FILL = ("conveyor", "underflow-gate", "overflow-gate", "router")


def cells_of(size, x, y):
    ox, oy = x - (size - 1) // 2, y - (size - 1) // 2
    return {(ox + i, oy + j) for i in range(size) for j in range(size)}


def neighbours(cell):
    x, y = cell
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def main(tries=4000, seed=7):
    rng = random.Random(seed)
    gd = GameData()
    plan = expand(gd, "graphite", 1.0, ["coal"])
    w, h = GRID
    best = None
    found = []

    for arrangement in ("h0", "h1", "h2", "v0", "v1", "v2"):
        horiz = arrangement[0] == "h"
        gap = int(arrangement[1])
        a = (1, 1)
        b = (3 + gap, 1) if horiz else (1, 3 + gap)
        machine_cells = cells_of(2, *a) | cells_of(2, *b)
        xs = [c[0] for c in machine_cells]
        ys = [c[1] for c in machine_cells]
        box = (min(xs), min(ys), max(xs), max(ys))
        ring = []
        for x in range(w):
            for y in range(h):
                if (x, y) in machine_cells:
                    continue
                if box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                    continue                      # 端口必须在外接矩形之外
                if any(n in machine_cells for n in neighbours((x, y))):
                    ring.append((x, y))
        if len(ring) < 2:
            continue

        for _ in range(tries // 6):
            src = rng.choice(ring)
            adj = [p for p in neighbours(src) if p in ring]
            if not adj:
                continue
            void = rng.choice(adj)
            blocks = [("graphite-press", a[0], a[1], 0, None),
                      ("graphite-press", b[0], b[1], 0, None),
                      ("item-source", src[0], src[1], 0, "coal"),
                      ("item-void", void[0], void[1], 0, None)]
            taken = set(machine_cells) | {src, void}
            for _k in range(rng.randint(0, 6)):
                name = rng.choice(FILL)
                x, y = rng.randrange(w), rng.randrange(h)
                if (x, y) in taken:
                    continue
                taken.add((x, y))
                blocks.append((name, x, y, rng.randrange(4), None))
            cand = S.evaluate(gd, plan, blocks, GRID)
            if cand is None or not cand.ok_need or cand.clusters != 1:
                continue
            if cand.ports != 2:
                continue
            found.append(cand)
            if best is None or (cand.tiles, cand.box) < (best.tiles, best.box):
                best = cand

    print("攻击 %d 次 × 6 种机器排布，找到 %d 张「2 端口 + 1 开口 + 产能够」的布局"
          % (tries, len(found)))
    if best is None:
        print("结论：没找到 —— 2 个端口方块要凑成 1 个开口，在当前算子集里不成立")
        return
    lay = S.to_layout(best, gd, canvas=(24, 24)).crop()
    print("最省：%d 工厂格 / box %d / %.4f/s / %s"
          % (best.tiles, best.box, best.rate, best.label))
    for y in range(lay.h):
        line = ""
        for x in range(lay.w):
            t = lay.tile_at(x, y)
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
            print("  " + line.rstrip())


if __name__ == "__main__":
    main()

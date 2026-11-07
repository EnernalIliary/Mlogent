"""双端（2 端口）单入单出：穷举 10 格 / 11 格，看脚本能不能给出解。

约束：恰好 2 台石墨压机 + 1 个 item-source + 1 个 item-void，端口全在工厂外接矩形之外，
物流模型判产能够。

  tiles = 8（机器）+ 2（端口）+ k（中转方块：带子 / 门 / 路由器）
  10 格 → k=0；11 格 → k=1。

k 枚举完仍无解 ⇒ 10/11 格不可能；12 格的 `ported:one` 就是最优。
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mbo.gamedata import GameData                      # noqa: E402
from mbo.production import expand                     # noqa: E402
from mbo import search as S                           # noqa: E402

GRID = (11, 9)
EXTRA = ([("conveyor", r) for r in range(4)]
         + [("underflow-gate", r) for r in range(4)]
         + [("overflow-gate", r) for r in range(4)]
         + [("router", 0), ("junction", 0)])


def cells_of(size, x, y):
    ox, oy = x - (size - 1) // 2, y - (size - 1) // 2
    return {(ox + i, oy + j) for i in range(size) for j in range(size)}


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def ascii_of(lay):
    out = []
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
            out.append(line.rstrip())
    return "\n".join(out)


def arrangements():
    out = []
    for gap in (0, 1, 2, 3):
        out.append(("h%d" % gap, [(1, 1), (3 + gap, 1)]))
        out.append(("v%d" % gap, [(1, 1), (1, 3 + gap)]))
    return out


def main():
    gd = GameData()
    plan = expand(gd, "graphite", 1.0, ["coal"])
    w, h = GRID

    for k in (0, 1):
        tried = 0
        found = []
        for tag, machines in arrangements():
            mcells = set()
            for cx, cy in machines:
                mcells |= cells_of(2, cx, cy)
            xs = [c[0] for c in mcells]
            ys = [c[1] for c in mcells]
            bb = (min(xs), min(ys), max(xs), max(ys))
            free = [(x, y) for x in range(w) for y in range(h) if (x, y) not in mcells]

            def outside(cell):
                return not (bb[0] <= cell[0] <= bb[2] and bb[1] <= cell[1] <= bb[3])

            port_cands = [c for c in free if outside(c)
                          and any(cheb(c, m) <= 2 for m in mcells)]
            extra_cands = [c for c in free if any(cheb(c, m) <= 2 for m in mcells)]
            base = [("graphite-press", machines[0][0], machines[0][1], 0, None),
                    ("graphite-press", machines[1][0], machines[1][1], 0, None)]

            for src in port_cands:
                for void in port_cands:
                    if src == void:
                        continue
                    ports = [("item-source", src[0], src[1], 0, "coal"),
                             ("item-void", void[0], void[1], 0, None)]
                    if k == 0:
                        combos = [None]
                    else:
                        cells = [c for c in extra_cands
                                 if c != src and c != void]
                        combos = [(c, name, rot) for c in cells for name, rot in EXTRA]
                    for combo in combos:
                        blocks = list(base) + ports
                        if combo is not None:
                            c, name, rot = combo
                            blocks.append((name, c[0], c[1], rot, None))
                        tried += 1
                        cand = S.evaluate(gd, plan, blocks, GRID)
                        if cand is None or not cand.ok_need or cand.ports != 2:
                            continue
                        found.append((tag, blocks, cand))
        print("k=%d（总格数 %d）：枚举 %d 种摆法，可行 %d 张"
              % (k, 10 + k, tried, len(found)), flush=True)
        if found:
            found.sort(key=lambda x: (x[2].tiles, x[2].box))
            tag, blocks, cand = found[0]
            lay = S.to_layout(cand, gd, canvas=(24, 24)).crop()
            print("  最省：%d 格 / box %d / %.4f/s / %s"
                  % (cand.tiles, cand.box, cand.rate, tag))
            print("\n".join("    " + l for l in ascii_of(lay).splitlines()))

    print("\n12 格参照（手写模板 ported:one）：")
    for c in S.template_candidates(gd, plan):
        if c.label == "template:ported:one":
            lay = S.to_layout(c, gd, canvas=(24, 24)).crop()
            print("  %d 格 / %d 端口 / %.4f/s" % (c.tiles, c.ports, c.rate))
            print("\n".join("    " + l for l in ascii_of(lay).splitlines()))


if __name__ == "__main__":
    main()

"""四核（4 台石墨压机）蓝图搜索 v2：复用 `mbo.search` 的物流评估，只给"4 台"补形状。

`mbo/search.py` 的枚举族写死 2 台机器（`_machine_spec` / `_arrangements` / `_bridges`），
但它的**出口枚举**（`_sink_options`：每台一个黑洞 / 单黑洞 + 带子/路由器接力）和
**评估器**（`evaluate`：端口在外 + 物流最大流）天然支持任意台数。所以这里只补两块：

  1. 4 台机器的排布（一行/一列/2×2，缝宽 0–2）；
  2. 喂料方案：
       F-per  —— 每台机器各一个源（端口多，但简单）；
       F-pair —— 桥接格（同时贴两台机器的格子）放门，门上方一个源，两对机器各一套。

出口统一交给 `search._sink_options`，最后用 Pareto(端口数, 工厂格) 收口。

用法：
    python -X utf8 spikes/gen/search_quad2.py
    python -X utf8 spikes/gen/search_quad2.py --only row1 --top 3
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mbo import logistics, production, search  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402

GRID = (19, 19)


def arrangements(n):
    out = []
    for g in (0, 1, 2):
        out.append(("row%d" % g, [(1, 1 + i * (2 + g)) for i in range(n)]))
        out.append(("col%d" % g, [(1 + i * (2 + g), 1) for i in range(n)]))
    for g in (0, 1):
        out.append(("grid%d" % g, [(1, 1), (3 + g, 1), (1, 3 + g), (3 + g, 3 + g)]))
    return out


def machines_of(name, positions, item):
    return [(name, x, y, item) for x, y in positions]


def covering_feed(gd, sizes, name, positions, item, grid):
    """F-pair：用 ≤2 个桥接格（同时贴两台机器）喂满 4 台，每个桥接格配一个外部源。"""
    pcells = [search._cells(sizes[name], x, y) for x, y in positions]
    w, h = grid
    bridges = []
    for x in range(w):
        for y in range(h):
            c = (x, y)
            if any(c in p for p in pcells):
                continue
            hits = [i for i, p in enumerate(pcells) if search._adjacent(c, p)]
            if len(hits) >= 2:
                bridges.append((c, hits))

    def covered(chosen):
        got = set()
        for _c, hits in chosen:
            got |= set(hits)
        return got

    out = []
    for k in (1, 2, 3):
        for combo in itertools.combinations(bridges, k):
            if len(covered(combo)) < len(pcells):
                continue
            blocks = [(name, x, y, 0, None) for x, y in positions]
            ok = True
            for (bx, by), _hits in combo:
                blocks.append(("underflow-gate", bx, by, 0, None))
            # 每个门配一个源（源必须在工厂外接矩形外，先估一个矩形再筛）
            for (bx, by), _hits in combo:
                srcs = []
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    sx, sy = bx + dx, by + dy
                    if not (0 <= sx < w and 0 <= sy < h):
                        continue
                    if any((sx, sy) in p for p in pcells):
                        continue
                    if any((sx, sy) == (b[1], b[2]) for b in blocks):
                        continue
                    srcs.append((sx, sy))
                if not srcs:
                    ok = False
                    break
                blocks.append(("item-source", srcs[0][0], srcs[0][1], 0, item))
            if ok:
                out.append(blocks)
        if out:
            break
        # 先试 2 个桥接格，不行再放宽到 3 个
    return out


def per_machine_feed(gd, sizes, name, positions, item):
    """F-per：每台机器的外侧各贴一个源（源在工厂外接矩形外，交给 evaluate 过滤）。"""
    out = []
    per = []
    for x, y in positions:
        cand = []
        cells = search._cells(sizes[name], x, y)
        for cx, cy in cells:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (cx + dx, cy + dy)
                if p not in cells:
                    cand.append(p)
        per.append(sorted(set(cand)))
    for combo in itertools.product(*per):
        if len(set(combo)) != len(combo):
            continue
        blocks = [(name, x, y, 0, None) for x, y in positions]
        blocks += [("item-source", sx, sy, 0, item) for sx, sy in combo]
        out.append(blocks)
    return out


def evaluate(gd, plan, blocks, grid):
    cand = search.evaluate(gd, plan, blocks, grid)
    if cand is None:
        return None
    lay = search._make(gd, blocks, grid)
    ok, msg = logistics.ports_outside(lay, gd)
    if not ok:
        return None
    return cand


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=float, default=2.6)
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--only", default=None)
    ap.add_argument("--max-sink-combos", type=int, default=400)
    args = ap.parse_args()

    gd = GameData()
    plan = production.expand(gd, "graphite", args.rate, ["coal"])
    sizes = search._sizes(gd)
    name, n = plan.order[0]
    press = gd.blocks[name].recipe
    cap = n * press.outputs_per_second[plan.target]
    need = n * press.inputs_per_second["coal"]
    print("计划 %s：%d 台，理论上限 %.4f/s，煤 %.4f/s（单格 4.9 ⇒ ≥%d 个输入口）"
          % (plan.order, n, cap, need, int(need // 4.9) + 1))

    rows = []
    for label, positions in arrangements(n):
        if args.only and label != args.only:
            continue
        machines = machines_of(name, positions, "coal")
        feeds = covering_feed(gd, sizes, name, positions, "coal", GRID)
        feeds += per_machine_feed(gd, sizes, name, positions, "coal")[:80]
        print("\n%s 排布 %s：喂料方案 %d 个" % (label, positions, len(feeds)))
        for feed_blocks in feeds:
            if not search._adjacent_ok(gd, feed_blocks, GRID):
                continue
            sinks = search._sink_options(gd, feed_blocks, machines, GRID)
            if not sinks:
                continue
            for sink_blocks in sinks[:args.max_sink_combos]:
                blocks = feed_blocks + sink_blocks
                cand = evaluate(gd, plan, blocks, GRID)
                if cand is None or not cand.ok_need:
                    continue
                rows.append(cand)

    # 去重 + Pareto
    uniq, seen = [], set()
    for c in rows:
        key = tuple(sorted((b[0], b[1], b[2], b[3]) for b in c.blocks))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    print("\n候选 %d 张（去重后）" % len(uniq))
    front = [c for c in uniq
             if not any((o.ports <= c.ports and o.tiles <= c.tiles
                         and (o.ports < c.ports or o.tiles < c.tiles))
                        for o in uniq if o is not c)]
    front.sort(key=lambda c: (c.ports, c.tiles))
    print("Pareto（端口数, 工厂格）：")
    for c in front:
        print("  ports=%d 开口=%d 工厂格=%2d 外接面积=%2d 预测 %.4f/s  %s"
              % (c.ports, c.clusters, c.tiles, c.box, c.rate, c.label))
        lay = search._make(gd, c.blocks, GRID)
        print("    " + render(lay).replace("\n", "\n    "))
    return 0


def render(lay):
    sym = {"item-source": "S", "item-void": "x", "router": "n",
           "overflow-gate": "+", "underflow-gate": "+", "graphite-press": "M"}
    occmap = {}
    for t in lay.tiles:
        for (cx, cy) in lay.cells(t.block, t.x, t.y):
            ch = sym.get(t.block, "?")
            if t.block == "conveyor":
                ch = ">v<^"[t.rotation % 4]
            occmap[(cx, cy)] = ch
    xs = [x for x, _ in occmap]
    ys = [y for _, y in occmap]
    if not xs:
        return ""
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    rows = ["".join(occmap.get((x, y), " ") for x in range(x0, x1 + 1)) for y in range(y0, y1 + 1)]
    return "\n".join(r.rstrip() for r in rows)


if __name__ == "__main__":
    raise SystemExit(main())

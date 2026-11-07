# -*- coding: utf-8 -*-
"""列出 search_quad3 的 Pareto 前沿（紧凑表）+ 每档一个代表形状。"""
import io
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

import importlib.util

spec = importlib.util.spec_from_file_location(
    "q3", os.path.join(HERE, "search_quad3.py"))
q3 = importlib.util.module_from_spec(spec)
sys.modules["q3"] = q3
spec.loader.exec_module(q3)

from mbo import production, search  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402


def main():
    gd = GameData()
    plan = production.expand(gd, "graphite", 2.6, ["coal"])
    sizes = search._sizes(gd)
    name, n = plan.order[0]
    grid = q3.GRID
    rows = []
    for label, positions in q3.arrangements(n):
        feeds = q3.feed_pair(gd, sizes, name, positions, "coal", grid)
        feeds += q3.feed_per(gd, sizes, name, positions, "coal", grid)[:40]
        ok_feeds = []
        for blocks in feeds:
            c = q3.evaluate(gd, plan, blocks, grid)
            if c is not None:
                ok_feeds.append(blocks)
        for blocks in ok_feeds[:60]:
            sinks = q3.sink_single(blocks, gd, sizes, name, positions, grid)[:12]
            for groups in (((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2)),
                           ((0, 1, 2, 3),)):
                sinks += q3.sink_groups(blocks, gd, sizes, name, positions,
                                        grid, groups, limit=12)
            for sink in sinks:
                cand = q3.evaluate(gd, plan, blocks + sink, grid)
                if cand is not None and cand.ok_need:
                    rows.append((label, cand))

    uniq, seen = [], set()
    for label, c in rows:
        key = tuple(sorted((b[0], b[1], b[2], b[3]) for b in c.blocks))
        if key in seen:
            continue
        seen.add(key)
        uniq.append((label, c))
    print("候选 %d 张，按 (端口数, 工厂格) 统计：" % len(uniq))
    tally = Counter((c.ports, c.tiles) for _l, c in uniq)
    for (p, t), k in sorted(tally.items()):
        print("  ports=%d tiles=%2d → %3d 张" % (p, t, k))

    def dominates(a, b):
        return (a.ports <= b.ports and a.tiles <= b.tiles
                and (a.ports < b.ports or a.tiles < b.tiles))

    front = [(l, c) for l, c in uniq
             if not any(dominates(o, c) for _l2, o in uniq if o is not c)]
    front.sort(key=lambda lc: (lc[1].ports, lc[1].tiles))
    print("\nPareto 前沿 %d 档：" % len(front))
    seen_pt = set()
    for label, c in front:
        pt = (c.ports, c.tiles)
        if pt in seen_pt:
            continue
        seen_pt.add(pt)
        print("\n  [%s] ports=%d 开口=%d 工厂格=%d 预测 %.4f/s"
              % (label, c.ports, c.clusters, c.tiles, c.rate))
        print("  " + q3.render(io and search._make(gd, c.blocks, grid)).replace("\n", "\n  "))
        for b in sorted(c.blocks, key=lambda b: (b[2], b[1])):
            print("     %-14s (%2d,%2d) rot=%d %s" % (b[0], b[1], b[2], b[3], b[4] or ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

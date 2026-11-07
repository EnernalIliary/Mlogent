"""四核（4 台石墨压机）蓝图搜索 v3：结构化枚举，喂料 + 排料都显式构造。

为什么不用 `mbo.search` 的 `_sink_options`：它只枚举"贴着工厂外框那一圈"的汇点，
4 台机器排成一排时中间两台根本碰不到外框，于是它对 4 台直接返回空。

这里自己写两块：
  * 喂料：F-pair（桥接格放门 + 门上方一个源，两对机器各一套）/ F-per（每台一个源）；
  * 排料：BFS 在空格里给每台机器找一条 ≤4 格的传送带路径，通到"工厂矩形之外"的黑洞；
          也可以两两共用一个黑洞（各自送进同一个路由器再进黑洞，复现 p-one 的合流形状）。

所有组合都交给 `mbo.search.evaluate`（端口必须在外 + 物流最大流）验收，最后 Pareto(端口数, 工厂格)。

用法：
    python -X utf8 spikes/gen/search_quad3.py
    python -X utf8 spikes/gen/search_quad3.py --only grid0 --top 4
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mbo import logistics, production, search  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402

GRID = (21, 17)
ROT_V = {(1, 0): 0, (0, -1): 1, (-1, 0): 2, (0, 1): 3}
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def arrangements(n):
    out = []
    for g in (0, 1, 2):
        out.append(("row%d" % g, [(1, 1 + i * (2 + g)) for i in range(n)]))
        out.append(("col%d" % g, [(1 + i * (2 + g), 1) for i in range(n)]))
    for g in (0, 1):
        out.append(("grid%d" % g, [(1, 1), (3 + g, 1), (1, 3 + g), (3 + g, 3 + g)]))
    return out


def used_cells(blocks, gd, sizes):
    out = set()
    for name, x, y, _rot, _item in blocks:
        out |= search._cells(sizes[name], x, y)
    return out


def outside_cells(occ, grid, margin=0):
    """工厂矩形（occ 的外接矩形外扩 margin）之外的空白格。"""
    w, h = grid
    xs = [x for x, _ in occ]
    ys = [y for _, y in occ]
    x0, x1 = min(xs) - margin, max(xs) + margin
    y0, y1 = min(ys) - margin, max(ys) + margin
    return [(x, y) for x in range(w) for y in range(h)
            if (x, y) not in occ and not (x0 <= x <= x1 and y0 <= y <= y1)]


def free_neighbors(cells, occ, grid):
    w, h = grid
    out = set()
    for cx, cy in cells:
        for dx, dy in DIRS:
            p = (cx + dx, cy + dy)
            if 0 <= p[0] < w and 0 <= p[1] < h and p not in occ:
                out.add(p)
    return out


def belt_route(pcells, occ, target, grid, max_len=6):
    """从机器旁的空格出发，用 ≤max_len 条带子走到 target 旁边；返回 blocks 或 None。"""
    w, h = grid
    starts = sorted(free_neighbors(pcells, occ, grid))
    if not starts:
        return None
    if target in starts:
        return []
    prev = {s: None for s in starts}
    q = deque(starts)
    goal = None
    while q:
        cur = q.popleft()
        if cur == target:
            goal = cur
            break
        # 步数限制：回溯深度 ≈ 路径长度
        depth = 0
        p = cur
        while prev.get(p) is not None:
            p = prev[p]
            depth += 1
        if depth + 1 > max_len:
            continue
        for dx, dy in DIRS:
            nxt = (cur[0] + dx, cur[1] + dy)
            if not (0 <= nxt[0] < w and 0 <= nxt[1] < h):
                continue
            if nxt in prev or nxt in occ:
                continue
            prev[nxt] = cur
            if nxt == target:
                goal = nxt
                q.clear()
                break
            q.append(nxt)
    if goal is None:
        return None
    path = []
    cur = goal
    while prev[cur] is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    # 带子朝向下一个格；最后一条朝 target
    blocks = []
    for i, cell in enumerate(path):
        nxt = target if i == len(path) - 1 else path[i + 1]
        rot = ROT_V.get((nxt[0] - cell[0], nxt[1] - cell[1]))
        if rot is None:
            return None
        blocks.append(("conveyor", cell[0], cell[1], rot, None))
    return blocks


def feed_pair(gd, sizes, name, positions, item, grid, gaps=()):
    """桥接格放反溢门，门旁一个源；剩下的机器由下一个桥接格负责。"""
    pcells = [search._cells(sizes[name], x, y) for x, y in positions]
    used = set().union(*pcells)
    bridges = []
    for x in range(grid[0]):
        for y in range(grid[1]):
            c = (x, y)
            if c in used:
                continue
            hits = [i for i, p in enumerate(pcells) if search._adjacent(c, p)]
            if len(hits) >= 2:
                bridges.append((c, hits))
    out = []
    for k in (1, 2, 3):
        for combo in itertools.combinations(bridges, k):
            got = set()
            for _c, hits in combo:
                got |= set(hits)
            if len(got) < len(pcells):
                continue
            blocks = [(name, x, y, 0, None) for x, y in positions]
            blocks += [("underflow-gate", c[0], c[1], 0, None) for c, _h in combo]
            bad = False
            for (bx, by), _hits in combo:
                src = None
                for dx, dy in DIRS:
                    p = (bx + dx, by + dy)
                    if p in used or any((p == (b[1], b[2])) for b in blocks):
                        continue
                    src = p
                    break
                if src is None:
                    bad = True
                    break
                blocks.append(("item-source", src[0], src[1], 0, item))
            if not bad:
                out.append(blocks)
        if out:
            break
    return out


def feed_per(gd, sizes, name, positions, item, grid):
    pcells = [search._cells(sizes[name], x, y) for x, y in positions]
    used = set().union(*pcells)
    per = [sorted(free_neighbors(p, used, grid)) for p in pcells]
    out = []
    for combo in itertools.product(*per):
        if len(set(combo)) != len(combo):
            continue
        blocks = [(name, x, y, 0, None) for x, y in positions]
        blocks += [("item-source", sx, sy, 0, item) for sx, sy in combo]
        out.append(blocks)
    return out


def sink_single(blocks, gd, sizes, name, positions, grid):
    """每台机器各自通到一个外部黑洞。"""
    occ = used_cells(blocks, gd, sizes)
    outs = list(outside_cells(occ, grid))
    if not outs:
        return []
    pcells = [search._cells(sizes[name], x, y) for x, y in positions]
    per = []
    for p in pcells:
        cands = []
        for v in outs:
            route = belt_route(p, occ, v, grid)
            if route is None:
                continue
            cells = {(b[1], b[2]) for b in route}
            if cells & occ:
                continue
            cands.append((v, route))
        if not cands:
            return []
        cands.sort(key=lambda vr: (len(vr[1]), vr[0]))
        per.append(cands[:12])
    res = []
    for combo in itertools.product(*per):
        vs = [c[0] for c in combo]
        if len(set(vs)) != len(vs):
            continue
        parts = [b for c in combo for b in c[1]]
        cells = {(b[1], b[2]) for b in parts}
        if len(cells) != len(parts):
            continue
        res.append([("item-void", v[0], v[1], 0, None) for v in vs] + parts)
        if len(res) >= 200:
            break
    return res


def sink_groups(blocks, gd, sizes, name, positions, grid, groups, limit=60):
    """每组机器共用一个外部黑洞；每台用 <=6 条带子直指该黑洞。

    两条带子从不同侧投进同一个黑洞，正是 p-both 的形状（实测 1.3569/s，不掉速）。
    """
    occ = used_cells(blocks, gd, sizes)
    outs = list(outside_cells(occ, grid))
    pcells = [search._cells(sizes[name], x, y) for x, y in positions]
    res = []
    for v in outs:
        parts, cells, ok = [], set(), True
        for group in groups:
            for idx in group:
                route = belt_route(pcells[idx], occ | cells, v, grid)
                if route is None:
                    ok = False
                    break
                if {(b[1], b[2]) for b in route} & cells:
                    ok = False
                    break
                parts += route
                cells |= {(b[1], b[2]) for b in route}
            if not ok:
                break
        if not ok:
            continue
        res.append([("item-void", v[0], v[1], 0, None)] + parts)
        if len(res) >= limit:
            break
    return res


def sink_router_pairs(blocks, gd, sizes, name, positions, grid, pairs, limit=80):
    """每对机器：两条带子先送进同一台路由器（工厂内），路由器再贴一个外部黑洞。"""
    occ = used_cells(blocks, gd, sizes)
    outs = list(outside_cells(occ, grid))
    pcells = [search._cells(sizes[name], x, y) for x, y in positions]
    res = []
    for v in outs:
        for dx, dy in DIRS:
            r = (v[0] + dx, v[1] + dy)
            if r in occ or v == r:
                continue
            if not (0 <= r[0] < grid[0] and 0 <= r[1] < grid[1]):
                continue
            parts, cells, ok = [], {r}, True
            for group in pairs:
                for idx in group:
                    route = belt_route(pcells[idx], occ | cells, r, grid)
                    if route is None:
                        ok = False
                        break
                    if {(b[1], b[2]) for b in route} & cells:
                        ok = False
                        break
                    parts += route
                    cells |= {(b[1], b[2]) for b in route}
                if not ok:
                    break
            if not ok:
                continue
            rot = ROT_V.get((v[0] - r[0], v[1] - r[1]), 0)
            res.append([("item-void", v[0], v[1], 0, None),
                        ("router", r[0], r[1], rot, None)] + parts)
            if len(res) >= limit:
                return res
    return res


def evaluate(gd, plan, blocks, grid):
    cand = search.evaluate(gd, plan, blocks, grid)
    if cand is None:
        return None
    lay = search._make(gd, blocks, grid)
    ok, _msg = logistics.ports_outside(lay, gd)
    if not ok:
        return None
    return cand


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
    if not occmap:
        return ""
    xs = [x for x, _ in occmap]
    ys = [y for _, y in occmap]
    out = []
    for y in range(min(ys), max(ys) + 1):
        out.append("".join(occmap.get((x, y), " ") for x in range(min(xs), max(xs) + 1)).rstrip())
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=float, default=2.6)
    ap.add_argument("--top", type=int, default=4)
    ap.add_argument("--only", default=None)
    ap.add_argument("--grid", default="%dx%d" % GRID)
    args = ap.parse_args()
    w, h = (int(v) for v in args.grid.lower().split("x"))
    grid = (w, h)

    gd = GameData()
    plan = production.expand(gd, "graphite", args.rate, ["coal"])
    sizes = search._sizes(gd)
    name, n = plan.order[0]
    rec = gd.blocks[name].recipe
    cap = n * rec.outputs_per_second[plan.target]
    need = n * rec.inputs_per_second["coal"]
    print("计划 %s：%d 台，理论上限 %.4f/s，煤 %.4f/s（单格 4.9 ⇒ ≥%d 个输入口）"
          % (plan.order, n, cap, need, int(need // 4.9) + 1))

    rows = []
    for label, positions in arrangements(n):
        if args.only and label != args.only:
            continue
        feeds = feed_pair(gd, sizes, name, positions, "coal", grid)
        feeds += feed_per(gd, sizes, name, positions, "coal", grid)[:40]
        ok_feeds = []
        for blocks in feeds:
            c = evaluate(gd, plan, blocks, grid)
            if c is not None:
                ok_feeds.append((blocks, c))
        print("  %-6s 排布 %s：喂料 %d 个（可行 %d）"
              % (label, positions, len(feeds), len(ok_feeds)))
        schemes = []
        for blocks, _c in ok_feeds[:60]:
            schemes.append((blocks, sink_single(blocks, gd, sizes, name, positions, grid)[:12]))
            for groups in (((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2)), ((0, 1, 2, 3),)):
                schemes.append((blocks, sink_groups(blocks, gd, sizes, name, positions,
                                                    grid, groups, limit=12)))
        for blocks, sinks_list in schemes:
            for sinks in sinks_list:
                cand = evaluate(gd, plan, blocks + sinks, grid)
                if cand is not None and cand.ok_need:
                    rows.append(cand)

    uniq, seen = [], set()
    for c in rows:
        key = tuple(sorted((b[0], b[1], b[2], b[3]) for b in c.blocks))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    print("\n候选 %d 张" % len(uniq))
    front = [c for c in uniq
             if not any((o.ports <= c.ports and o.tiles <= c.tiles
                         and (o.ports < c.ports or o.tiles < c.tiles))
                        for o in uniq if o is not c)]
    front.sort(key=lambda c: (c.ports, c.tiles))
    print("Pareto（端口数, 工厂格）：")
    for c in front[:args.top + 3]:
        print("  ports=%d 开口=%d 工厂格=%2d 外接面积=%2d 预测 %.4f/s  %s"
              % (c.ports, c.clusters, c.tiles, c.box, c.rate, c.label))
        print("    " + render(search._make(gd, c.blocks, grid)).replace("\n", "\n    "))
    if front:
        best = min(front, key=lambda c: (c.ports, c.tiles))
        print("\n最省端口/格：ports=%d 工厂格=%d" % (best.ports, best.tiles))
        for b in sorted(best.blocks, key=lambda b: (b[2], b[1])):
            print("   %-14s (%2d,%2d) rot=%d %s" % (b[0], b[1], b[2], b[3], b[4] or ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

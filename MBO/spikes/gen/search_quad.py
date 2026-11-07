"""四核（4 台石墨压机）蓝图搜索：物流驱动的两阶段构造式搜索。

背景：`mbo/search.py` 只枚举"2 台机器 + 一环端口"的结构化族（`_machine_spec` 写死 2 台）。
4 台机器的形状空间大得多，这里换一种更通用的做法——**两阶段构造式 beam search**：

  阶段一（喂料）：只允许加"工厂内"的带子/门/路由器 + 外部物料源（≤max_src 个），
                  以"输入流量"打分，收下把 4 台压机喂饱的状态；
  阶段二（排料）：从阶段一的状态出发，继续加带子/门/路由器 + 物品黑洞（≤max_void 个），
                  以"输出流量"打分，收下把 4 台机器的产物全部排出去的状态。

每个动作都用 `logistics.estimate` 的真实最大流评分，所以"喂不饱/排不出"在搜索阶段就被淘汰。

用法：
    python -X utf8 spikes/gen/search_quad.py
    python -X utf8 spikes/gen/search_quad.py --only row1 --beam 8 --depth 8
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mbo import logistics, production  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402
from mbo.model import Layout  # noqa: E402

TOL = 1e-3
CONNECTORS = (
    [("conveyor", r) for r in (0, 1, 2, 3)]
    + [("underflow-gate", r) for r in (0, 1, 2, 3)]
    + [("overflow-gate", r) for r in (0, 1, 2, 3)]
    + [("router", 0)]
)
NEIGH = ((1, 0), (-1, 0), (0, 1), (0, -1))
SYM = {"item-source": "S", "item-void": "x", "router": "n",
       "overflow-gate": "+", "underflow-gate": "+", "graphite-press": "M"}


def sizes_of(gd) -> dict:
    return {n: b.size for n, b in gd.blocks.items()}


def arrangements(n=4):
    out = []
    for g in (0, 1, 2):
        out.append(("row%d" % g, [(1, 1 + i * (2 + g)) for i in range(n)]))
        out.append(("col%d" % g, [(1 + i * (2 + g), 1) for i in range(n)]))
    for g in (0, 1):
        out.append(("grid%d" % g, [(1, 1), (3 + g, 1), (1, 3 + g), (3 + g, 3 + g)]))
    return out


def make_layout(gd, sizes, placements, grid, name="quad"):
    lay = Layout(grid[0], grid[1], sizes, name=name)
    for blk, x, y, rot, item in placements:
        lay.add(blk, x, y, rot, {"item": item} if blk == "item-source" else None)
    return lay


def occupied(lay):
    occ = set()
    for t in lay.tiles:
        occ |= lay.cells(t.block, t.x, t.y)
    return occ


def free_cells(occ, grid):
    out = []
    w, h = grid
    for x in range(w):
        for y in range(h):
            if (x, y) in occ:
                continue
            if any((x + dx, y + dy) in occ for dx, dy in NEIGH):
                out.append((x, y))
    return out


def bbox_of(lay, gd, sizes):
    """工厂（非端口方块）的外接矩形；没有工厂方块时返回 None。"""
    xs, ys = [], []
    for t in lay.tiles:
        if t.block in ("item-source", "item-void"):
            continue
        for cx, cy in lay.cells(t.block, t.x, t.y):
            xs.append(cx)
            ys.append(cy)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def phase(seed_states, gd, plan, sizes, grid, cap, max_ports, beam, depth, want, item="coal"):
    """通用一阶段：want="in"（喂料）/"out"（排料）。

    端口只能落在**当前工厂外接矩形之外**；带子/门/路由器可以放在任意空格（会把矩形撑大）。
    """
    pipe = "in"
    out_states = []
    beam_states = list(seed_states)
    for _step in range(depth):
        pool = {}
        for placements, _lay, occ in beam_states:
            nport = sum(1 for p in placements if p[0] in ("item-source", "item-void"))
            lay_cur = make_layout(gd, sizes, placements, grid)
            bb = bbox_of(lay_cur, gd, sizes)
            for (x, y) in free_cells(occ, grid):
                acts = [(b, r, None) for b, r in CONNECTORS]
                outside = bb is None or not (bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3])
                if outside and nport < max_ports:
                    if want == "in":
                        acts.append(("item-source", 0, item))
                    else:
                        acts.append(("item-void", 0, None))
                for blk, rot, it in acts:
                    newp = placements + ((blk, x, y, rot, it),)
                    try:
                        nlay = make_layout(gd, sizes, newp, grid)
                    except ValueError:
                        continue
                    est = logistics.estimate(nlay, gd, plan)
                    val = min(est["rate_output_limited"] if want == "out"
                              else est["rate_input_limited"], cap)
                    pool[tuple(sorted(newp))] = (val, newp, nlay, est, len(occupied(nlay)))
        if not pool:
            break
        ranked = sorted(pool.items(), key=lambda kv: (kv[1][0], -kv[1][4]), reverse=True)
        beam_states = [(p, l, occupied(l)) for _k, (_v, p, l, _e, _t) in ranked[:beam]]
        done = []
        for _k, (_v, p, l, est, _t) in ranked:
            if _v >= cap - TOL and logistics.ports_outside(l, gd)[0]:
                done.append((p, l, est))
        if done:
            out_states = done
            break
    return out_states, beam_states


def render(lay):
    occmap = {}
    for t in lay.tiles:
        for (cx, cy) in lay.cells(t.block, t.x, t.y):
            ch = SYM.get(t.block, "?")
            if t.block == "conveyor":
                ch = ">v<^"[t.rotation % 4]
            occmap[(cx, cy)] = ch
    rows = ["".join(occmap.get((x, y), " ") for x in range(lay.w)).rstrip()
            for y in range(lay.h)]
    while rows and not rows[-1]:
        rows.pop()
    return "\n".join(rows)


def summarize(gd, lay, est, tags, ports):
    layc = lay.crop()
    return {
        "tags": tags,
        "ports": ports,
        "tiles": len(occupied(layc)) - ports,
        "rate": est["rate"],
        "bottleneck": est["bottleneck"],
        "in": est["in_flow"],
        "out": est["out_flow"],
        "canvas": (layc.w, layc.h),
        "layout": layc,
        "blocks": [(t.block, t.x, t.y, t.rotation) for t in sorted(layc.tiles, key=lambda t: (t.y, t.x))],
    }


def search(gd, plan, sizes, label, positions, grid=(17, 17), beam=8, depth=8,
           max_src=2, max_void=1):
    """一次完整的两阶段搜索，返回 [(layout, est, tags, ports)]。"""
    name, _n = plan.order[0]
    base = tuple((name, x, y, 0, None) for x, y in positions)
    lay0 = make_layout(gd, sizes, base, grid, name="quad:" + label)
    occ0 = occupied(lay0)
    cap = sum(gd.blocks[name].recipe.outputs_per_second[plan.target] for _ in positions)

    # 阶段一：喂料（源只能落在当前工厂矩形之外）
    ins, _ = phase([(base, lay0, occ0)], gd, plan, sizes, grid, cap,
                   max_src, beam, depth, want="in")
    if not ins:
        return []

    results = []
    for placements, lay, _est in ins[:20]:
        occ = occupied(lay)
        # 阶段二：排料（黑洞同理；阶段一加的源已是端口，仍算在 max_ports 里）
        outs, _ = phase([(placements, lay, occ)], gd, plan, sizes, grid, cap,
                        max_void, beam, depth, want="out")
        for p2, l2, est2 in outs[:6]:
            ports = sum(1 for b in p2 if b[0] in ("item-source", "item-void"))
            results.append((l2, est2, "%s/S%dV%d" % (label, max_src, max_void), ports))
    return results


def pareto(rows):
    front = []
    for r in rows:
        if any((o["ports"] <= r["ports"] and o["tiles"] <= r["tiles"]
                and (o["ports"] < r["ports"] or o["tiles"] < r["tiles"])) for o in rows):
            continue
        front.append(r)
    uniq, seen = [], set()
    for r in sorted(front, key=lambda r: (r["ports"], r["tiles"])):
        key = (r["ports"], r["tiles"], tuple(r["blocks"]))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    return uniq


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=float, default=2.6)
    ap.add_argument("--beam", type=int, default=8)
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--only", default=None)
    ap.add_argument("--caps", default="2,1;2,2;1,1")
    args = ap.parse_args()

    gd = GameData()
    plan = production.expand(gd, "graphite", args.rate, ["coal"])
    sizes = sizes_of(gd)
    n = plan.order[0][1]
    press = gd.blocks["graphite-press"].recipe
    cap = n * press.outputs_per_second["graphite"]
    need = n * press.inputs_per_second["coal"]
    print("计划 %s：%d 台，上限 %.4f/s，煤 %.4f/s（单格 4.9 ⇒ ≥%d 个输入口）"
          % (plan.order, n, cap, need, int(need // 4.9) + 1))

    caps = []
    for chunk in args.caps.split(";"):
        a, b = chunk.split(",")
        caps.append((int(a), int(b)))

    rows = []
    for label, positions in arrangements(n):
        if args.only and label != args.only:
            continue
        for max_src, max_void in caps:
            res = search(gd, plan, sizes, label, positions, beam=args.beam,
                         depth=args.depth, max_src=max_src, max_void=max_void)
            if not res:
                print("\n%s S%dV%d：无解" % (label, max_src, max_void))
                continue
            got = [summarize(gd, l, e, tag, ports) for l, e, tag, ports in res]
            rows.extend(got)
            best = sorted(got, key=lambda r: (r["ports"], r["tiles"]))[:2]
            print("\n%s S%dV%d：%d 张" % (label, max_src, max_void, len(got)))
            for r in best:
                print("  ports=%d 工厂格=%2d 画布=%dx%d 预测 %.4f/s  in=%s out=%.2f"
                      % (r["ports"], r["tiles"], r["canvas"][0], r["canvas"][1],
                         r["rate"], r["in"], r["out"]))
                print("    " + render(r["layout"]).replace("\n", "\n    "))

    print("\n===== Pareto（端口数, 工厂格）=====")
    for r in pareto(rows):
        print("  ports=%d 工厂格=%2d 画布=%dx%d 预测 %.4f/s  %s"
              % (r["ports"], r["tiles"], r["canvas"][0], r["canvas"][1], r["rate"], r["tags"]))
        print("    " + render(r["layout"]).replace("\n", "\n    "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

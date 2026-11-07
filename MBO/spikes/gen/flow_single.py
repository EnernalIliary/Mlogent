# -*- coding: utf-8 -*-
"""单源单汇（1 个 item-source + 1 个 item-void）的 4 台石墨压机：显式物品流向。

拓扑（"主干 + 分支"）：

    物料走上面：源 → 主干带子 → 路由器 → 门（每个门压在自家压机正上方）→ 压机
    产物走下面：压机 → 一排带子 → 路由器 → 唯一黑洞

门用 rot=3（正面朝下，直接喂压机），背面朝上接主干路由器；门的左右两侧留空，
这样输入网络和输出网络在空间上不接触（压机不会把石墨塞进运煤的主干）。

用法：
    python -X utf8 spikes/gen/flow_single.py --out q-single
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from mbo import engine, production, report, search, validate  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402


def build_blocks(n=4):
    """n 台压机：x = 1 + 3k，前两行放主干与门，压机在第 2-3 行，输出在第 4 行。"""
    blocks = []
    press_x = [1 + 3 * k for k in range(n)]
    # 压机（2×2），行 2-3
    for px in press_x:
        blocks.append(("graphite-press", px, 2, 0, None))
    # 门：压在压机左上角正上方（行 1），正面朝下
    for px in press_x:
        blocks.append(("underflow-gate", px + 1, 1, 3, None))
    # 主干路由器（行 0，正对每个门）
    for px in press_x:
        blocks.append(("router", px + 1, 0, 0, None))
    # 主干带子（行 0）：源在 x=0，带子朝东把煤串到每个路由器
    blocks.append(("item-source", 0, 0, 0, "coal"))
    for k in range(n):
        bx = (0 if k == 0 else press_x[k - 1] + 2)
        # 从上一个路由器（或源）到下一个路由器之间的所有格子
        x_end = press_x[k] + 1
        for x in range(bx if k else 1, x_end):
            blocks.append(("conveyor", x, 0, 0, None))
    # 输出带子（行 4）：从每台压机下方一路往东
    x_last = press_x[-1] + 1
    for x in range(1, x_last + 1):
        blocks.append(("conveyor", x, 4, 0, None))
    # 出口路由器 + 唯一黑洞
    blocks.append(("router", x_last + 1, 4, 0, None))
    blocks.append(("item-void", x_last + 2, 4, 0, None))
    return blocks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--machines", type=int, default=4)
    ap.add_argument("--out", default=None)
    ap.add_argument("--ticks", type=int, default=1800)
    ap.add_argument("--timeout", type=float, default=240.0)
    ap.add_argument("--dry", action="store_true", help="只算物流模型，不上真机")
    args = ap.parse_args()

    gd = GameData()
    rate = min(4.9 / 2.0, 0.6667 * args.machines - 0.01)  # 单源 4.9/s 的煤上限 -> 2.45/s 石墨
    plan = production.expand(gd, "graphite", rate, ["coal"])
    assert plan.order == [("graphite-press", args.machines)], plan.order

    blocks = build_blocks(args.machines)
    grid = (blocks_max(blocks) + 2, 6)
    cand = search.evaluate(gd, plan, blocks, grid)
    if cand is None:
        print("× 物流模型否决（端口在外 / 摆法重叠）")
        return 2
    print("候选：ports=%d 开口=%d 工厂格=%d 预测 %.4f/s bottleneck=%s"
          % (cand.ports, cand.clusters, cand.tiles, cand.rate, cand.bottleneck))
    print("  输入上限 %s" % {k: round(v, 3) for k, v in cand.in_flow.items()})
    print("  输出上限 %.3f/s，ok_need=%s" % (cand.out_flow, cand.ok_need))
    if not cand.ok_need:
        print("  （模型判喂不满：单源 4.9/s 对 %d 台来说不够）" % args.machines)

    lay = search._make(gd, blocks, grid)
    lay.crop()
    static = validate.static_check(lay, gd, plan, strict_ports=True)
    print("静态 %s %s" % ("OK" if static["ok"] else "FAIL", static["errors"][:3]))
    print(render(lay))
    if args.dry:
        return 0

    prediction = {
        "expected_rate": round(cand.rate, 4),
        "plan_rate": round(plan.achieved_rate, 4),
        "power_need": round(plan.power_need, 2),
        "boundary": {k: round(v, 3) for k, v in plan.demand.items()},
        "tiles": static["info"]["tiles"],
        "footprint": static["info"]["footprint"],
        "ports": cand.ports,
        "clusters": cand.clusters,
        "search": {"candidates": 1, "feasible": 1,
                   "pareto": [[cand.ports, cand.tiles, cand.box, round(cand.rate, 3)]]},
    }
    run_id = args.out or ("q-single%d" % args.machines)
    run_dir = os.path.join(report.runs_dir(), run_id)
    eng = engine.run(lay, gd, "graphite", ticks=args.ticks, timeout=args.timeout)
    metrics = report.write_run(run_dir, lay, gd, plan, static, eng, prediction,
                               extra={"layout": "flow-single"})
    got = ((eng.get("metrics") or {}) if eng else {}).get("rate")
    print("真机 %s" % (("%.4f/s" % got) if got is not None else eng.get("error")))
    print("结论 %s — %s" % ("PASS" if metrics["verdict"]["pass"] else "FAIL", run_dir))
    return 0 if metrics["verdict"]["pass"] else 3


def blocks_max(blocks):
    sizes = {}
    mx = 0
    for name, x, y, _rot, _item in blocks:
        # 只用于估网格宽度；2×2 方块占两格
        size = 2 if name in ("graphite-press", "container") else 1
        mx = max(mx, x + size - 1)
    return mx


SYM = {"item-source": "S", "item-void": "x", "router": "n",
       "overflow-gate": "+", "underflow-gate": "+", "graphite-press": "M"}


def render(lay):
    gd = GameData()
    occ = {}
    for t in lay.tiles:
        for (cx, cy) in lay.cells(t.block, t.x, t.y):
            ch = SYM.get(t.block, "?")
            if t.block == "conveyor":
                ch = ">v<^"[t.rotation % 4]
            occ[(cx, cy)] = ch
    xs = [x for x, _ in occ]
    ys = [y for _, y in occ]
    rows = ["".join(occ.get((x, y), " ") for x in range(min(xs), max(xs) + 1)).rstrip()
            for y in range(min(ys), max(ys) + 1)]
    return "\n".join(rows)


if __name__ == "__main__":
    raise SystemExit(main())

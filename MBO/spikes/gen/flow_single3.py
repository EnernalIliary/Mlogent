# -*- coding: utf-8 -*-
"""单源单汇、4 台压机 —— 试着把"压机贴干线"的 21% 掉速抢回来。

`flow_single2.py` 的形状是：干线（行 0：源→带子→门→带子→…）+ 压机（行 1-2）+
输出带（行 3）。实测 1.9236/s，只有理论上限 2.45/s 的 78.5%。怀疑是压机把
石墨**回吐到贴身的干线格**（门东侧的带子 / 门本身），挤占输煤容量。

本脚本做两个对照：

  --trunk gates   干线每一格都是反溢门（门只从背面收料，压机回吐会被拒收）
  --trunk belts   原始形状（门之间是带子），作为对照
  --gap 1         门与压机之间垫一格朝南的带子，压机下移一行（＝压机不再贴干线）

用法：
    python -X utf8 spikes/gen/flow_single3.py --dry
    python -X utf8 spikes/gen/flow_single3.py --trunk gates --gap 0 --out q-gate-trunk
    python -X utf8 spikes/gen/flow_single3.py --trunk belts --gap 1 --out q-gap1
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from mbo import engine, logistics, production, report, search, validate  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402
from mbo.preview import render_ascii  # noqa: E402

TAP = [2, 5, 8, 11]          # 门/压机的 x（门在行 0，压机在行 1+gap）
GAME = GameData()

SOUTH = 1                    # 传送带 rot：0=东 1=南 2=西 3=北
NORTH = 3                    # 注意 Layout 的 y 是游戏坐标（+y 朝北），见 mbo/model.py:17
EAST = 0


def build_blocks(n=4, sink="merged", trunk="gates", gap=0):
    taps = TAP[:n]
    press_y = 1 + gap
    out_row = press_y + 2
    b = [("item-source", 0, 0, 0, "coal")]
    # 行 0：干线。gates = 全部门；belts = 门 + 门间带子（原始形状）
    for x in range(1, taps[-1] + 1):
        if x in taps or trunk == "gates":
            b.append(("underflow-gate", x, 0, EAST, None))
        else:
            b.append(("conveyor", x, 0, EAST, None))
    for x in taps:
        # gap：门正下方垫带子，把煤送进压机；y 是游戏坐标（+y 朝北）=> 朝北 = rot 3
        for y in range(1, press_y):
            b.append(("conveyor", x, y, NORTH, None))
        b.append(("graphite-press", x, press_y, EAST, None))
    if sink == "4":
        for x in taps:
            b.append(("item-void", x, out_row, EAST, None))
        return b
    for x in range(taps[0], taps[-1] + 1):
        b.append(("conveyor", x, out_row, EAST, None))
    b.append(("router", taps[-1] + 1, out_row, EAST, None))
    b.append(("item-void", taps[-1] + 2, out_row, EAST, None))
    return b


def clusters_of(lay):
    return search._port_clusters(lay)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sink", choices=["4", "merged"], default="merged")
    ap.add_argument("--trunk", choices=["gates", "belts"], default="gates")
    ap.add_argument("--gap", type=int, default=0, choices=[0, 1, 2])
    ap.add_argument("--machines", type=int, default=4)
    ap.add_argument("--rate", type=float, default=2.45)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    gd = GAME
    plan = production.expand(gd, "graphite", args.rate, ["coal"])
    blocks = build_blocks(args.machines, args.sink, args.trunk, args.gap)
    grid = (22, 9 + args.gap)
    lay = search._make(gd, blocks, grid)
    if lay is None:
        print("× 建图失败（重叠/越界）")
        return 2
    lay.crop()
    est = logistics.estimate(lay, gd, plan)
    tag = "trunk=%s gap=%d sink=%s" % (args.trunk, args.gap, args.sink)
    print("[%s] 预测 %.4f/s bottle=%s in=%s out=%.3f machine_cap=%.3f"
          % (tag, est["rate"], est["bottleneck"],
             {k: round(v, 3) for k, v in est["in_flow"].items()}, est["out_flow"],
             est["machine_cap"]))
    static = validate.static_check(lay, gd, plan, strict_ports=False)
    print("静态 %s %s" % ("OK" if static["ok"] else "FAIL", static["errors"][:3]))
    print("端口在外 %s" % (logistics.ports_outside(lay, gd)[0],))
    if args.dry:
        print(render_ascii(lay, gd))
        return 0

    prediction = {
        "expected_rate": round(est["rate"], 4),
        "plan_rate": round(plan.achieved_rate, 4),
        "power_need": round(plan.power_need, 2),
        "boundary": {k: round(v, 3) for k, v in plan.demand.items()},
        "tiles": static["info"]["tiles"],
        "footprint": static["info"]["footprint"],
        "ports": sum(1 for t in lay.tiles if t.block in ("item-source", "item-void")),
        "clusters": clusters_of(lay),
        "search": {"candidates": 1, "feasible": 1, "pareto": []},
    }
    name = args.out or ("flow-%s-g%d" % (args.trunk, args.gap))
    run_dir = os.path.join(report.runs_dir(), name)
    eng = engine.run(lay, gd, "graphite", ticks=1800, timeout=240.0)
    report.write_run(run_dir, lay, gd, plan, static, eng, prediction,
                     extra={"layout": "flow-tap", "sink": args.sink,
                            "trunk": args.trunk, "gap": args.gap})
    m = (eng or {}).get("metrics") or {}
    print("真机 %s eff=%s deadlock=%s — %s"
          % (m.get("rate"), m.get("eff_avg"), m.get("deadlock"), run_dir))
    print(render_ascii(lay, gd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

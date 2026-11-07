# -*- coding: utf-8 -*-
"""单源单汇、4 台压机 —— 用"反溢门串在带子线上当支线口"的经典做法。

带子主干行 0：源 -> 带子 -> 门 -> 带子 -> 门 -> ...
  * 门 rot=0（正面朝东 = 继续往东），两侧优先 => 先把煤喂给南侧的压机，压机吃饱了才继续往东。
  * 压机 (x,1) 占 (x,1)(x+1,1)(x,2)(x+1,2)，正好贴住门 (x,0) 的南侧。
  * 压机下方 (x,3) 放黑洞承接石墨（--sink 4），或走输出带子合并到唯一黑洞（--sink merged）。

用法：
    python -X utf8 spikes/gen/flow_single2.py --dry
    python -X utf8 spikes/gen/flow_single2.py --sink 4 --out q-tap4
    python -X utf8 spikes/gen/flow_single2.py --sink merged --out q-tap1
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from mbo import engine, production, report, search, validate  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402

TAP = [2, 5, 8, 11]          # 门/压机的 x（门在行 0，压机在行 1）
OUT_ROW = 3                  # 输出带子所在行（压机占行 1-2）
GAME = GameData()


def build_blocks(n=4, sink="4"):
    taps = TAP[:n]
    b = [("item-source", 0, 0, 0, "coal"), ("conveyor", 1, 0, 0, None)]
    for x in taps:
        b.append(("underflow-gate", x, 0, 0, None))
        b.append(("graphite-press", x, 1, 0, None))
    # 门之间的衔接带子
    for x in range(2, taps[-1] + 1):
        if x in taps:
            continue
        b.append(("conveyor", x, 0, 0, None))
    if sink == "4":
        for x in taps:
            b.append(("item-void", x, OUT_ROW, 0, None))
        return b
    # 合并：每个压机往下一格输出，再沿行 OUT_ROW 向东汇入唯一黑洞
    for x in range(taps[0], taps[-1] + 1):
        b.append(("conveyor", x, OUT_ROW, 0, None))
    b.append(("router", taps[-1] + 1, OUT_ROW, 0, None))
    b.append(("item-void", taps[-1] + 2, OUT_ROW, 0, None))
    return b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sink", choices=["4", "merged"], default="4")
    ap.add_argument("--machines", type=int, default=4)
    ap.add_argument("--rate", type=float, default=2.45)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    gd = GameData()
    plan = production.expand(gd, "graphite", args.rate, ["coal"])
    blocks = build_blocks(args.machines, args.sink)
    grid = (20, 7)
    lay = search._make(gd, blocks, grid)
    if lay is None:
        print("× 建图失败（重叠/越界）")
        return 2
    lay.crop()
    from mbo import logistics
    est = logistics.estimate(lay, gd, plan)
    cand = None
    print("[sink=%s] 预测 %.4f/s bottle=%s in=%s out=%.3f machine_cap=%.3f"
          % (args.sink, est["rate"], est["bottleneck"],
             {k: round(v, 3) for k, v in est["in_flow"].items()}, est["out_flow"],
             est["machine_cap"]))
    static = validate.static_check(lay, gd, plan, strict_ports=False)
    print("静态 %s %s" % ("OK" if static["ok"] else "FAIL", static["errors"][:3]))
    if args.dry:
        print(ascii_of(lay))
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
    run_dir = os.path.join(report.runs_dir(), args.out or ("q-tap-" + args.sink))
    eng = engine.run(lay, gd, "graphite", ticks=1800, timeout=240.0)
    report.write_run(run_dir, lay, gd, plan, static, eng, prediction,
                     extra={"layout": "flow-tap", "sink": args.sink})
    m = (eng or {}).get("metrics") or {}
    print("真机 %s eff=%s deadlock=%s — %s"
          % (m.get("rate"), m.get("eff_avg"), m.get("deadlock"), run_dir))
    print(ascii_of(lay))
    return 0


def ascii_of(lay):
    from mbo.preview import render_ascii
    return render_ascii(lay, GAME)


def clusters_of(lay):
    return search._port_clusters(lay)


if __name__ == "__main__":
    raise SystemExit(main())

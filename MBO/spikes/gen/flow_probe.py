# -*- coding: utf-8 -*-
"""拆开验证"输入网络"和"输出网络"各自能不能跑到 2.45/2.67，定位单源蓝图掉速的位置。

--mode input  ：输入按单源主干（1 源 + 4 路由器 + 4 门），输出每台压机各一个黑洞
--mode output ：输入每台压机各一个源，输出合并成一排带子 → 路由器 → 唯一黑洞

用法：
    python -X utf8 spikes/gen/flow_probe.py --mode input --out p-in
    python -X utf8 spikes/gen/flow_probe.py --mode output --out p-out
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from mbo import engine, production, report, search, validate  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402

PRESS_X = [1, 4, 7, 10]


def blocks_input_only(n=4):
    out = []
    for px in PRESS_X[:n]:
        out.append(("graphite-press", px, 2, 0, None))
        out.append(("underflow-gate", px + 1, 1, 3, None))
        out.append(("router", px + 1, 0, 0, None))
        out.append(("item-void", px, 4, 0, None))
    out.append(("item-source", 0, 0, 0, "coal"))
    xs = [1, 3, 4, 6, 7, 9, 10][:max(1, 2 * n - 1)]
    for x in xs:
        out.append(("conveyor", x, 0, 0, None))
    return out


def blocks_output_only(n=4):
    out = []
    for px in PRESS_X[:n]:
        out.append(("graphite-press", px, 2, 0, None))
        out.append(("item-source", px + 1, 1, 0, "coal"))
    x_last = PRESS_X[:n][-1] + 1
    for x in range(1, x_last + 1):
        out.append(("conveyor", x, 4, 0, None))
    out.append(("router", x_last + 1, 4, 0, None))
    out.append(("item-void", x_last + 2, 4, 0, None))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["input", "output"], required=True)
    ap.add_argument("--machines", type=int, default=4)
    ap.add_argument("--rate", type=float, default=2.45)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    gd = GameData()
    plan = production.expand(gd, "graphite", args.rate, ["coal"])
    blocks = (blocks_input_only if args.mode == "input" else blocks_output_only)(args.machines)
    grid = (22, 7)
    cand = search.evaluate(gd, plan, blocks, grid)
    if cand is None:
        print("× 物流模型否决")
        return 2
    print("[%s] ports=%d 工厂格=%d 预测 %.4f/s bottle=%s in=%s out=%.3f"
          % (args.mode, cand.ports, cand.tiles, cand.rate, cand.bottleneck,
             {k: round(v, 3) for k, v in cand.in_flow.items()}, cand.out_flow))
    lay = search._make(gd, blocks, grid)
    lay.crop()
    static = validate.static_check(lay, gd, plan, strict_ports=True)
    print("静态 %s %s" % ("OK" if static["ok"] else "FAIL", static["errors"][:3]))
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
        "search": {"candidates": 1, "feasible": 1, "pareto": []},
    }
    run_dir = os.path.join(report.runs_dir(), args.out or ("p-" + args.mode))
    eng = engine.run(lay, gd, "graphite", ticks=1800, timeout=240.0)
    report.write_run(run_dir, lay, gd, plan, static, eng, prediction,
                     extra={"layout": "flow-probe", "mode": args.mode})
    got = ((eng.get("metrics") or {}) if eng else {}).get("rate")
    eff = ((eng.get("metrics") or {}) if eng else {}).get("eff_avg")
    print("真机 %s  eff_avg=%s — %s"
          % (("%.4f/s" % got) if got is not None else eng.get("error"), eff, run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

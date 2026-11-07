# -*- coding: utf-8 -*-
"""把四核候选送去真机：重建 search_quad3 的 Pareto，选一张，跑引擎并写 run 目录。

用法：
    python -X utf8 spikes/gen/run_quad.py --ports 8 --out q8
    python -X utf8 spikes/gen/run_quad.py --ports 6 --out q6
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

spec = importlib.util.spec_from_file_location("q3", os.path.join(HERE, "search_quad3.py"))
q3 = importlib.util.module_from_spec(spec)
sys.modules["q3"] = q3
spec.loader.exec_module(q3)

from mbo import engine, production, report, search, validate  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402


def build_rows(gd, plan, grid):
    sizes = search._sizes(gd)
    name, n = plan.order[0]
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
                sinks += q3.sink_router_pairs(blocks, gd, sizes, name, positions,
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
    return uniq


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=float, default=2.6)
    ap.add_argument("--ports", type=int, required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--ticks", type=int, default=1800)
    ap.add_argument("--timeout", type=float, default=240.0)
    args = ap.parse_args()

    gd = GameData()
    plan = production.expand(gd, "graphite", args.rate, ["coal"])
    grid = q3.GRID
    rows = build_rows(gd, plan, grid)
    pool = [(l, c) for l, c in rows if c.ports == args.ports]
    if not pool:
        print("× 没有 ports=%d 的候选（有：%s）"
              % (args.ports, sorted({c.ports for _l, c in rows})))
        return 2
    pool.sort(key=lambda lc: (lc[1].tiles, lc[1].box, lc[0]))
    label, best = pool[0]
    print("选中 [%s] ports=%d 开口=%d 工厂格=%d 预测 %.4f/s"
          % (label, best.ports, best.clusters, best.tiles, best.rate))
    print(q3.render(search._make(gd, best.blocks, grid)))

    lay = search._make(gd, best.blocks, grid)
    lay.crop()
    static = validate.static_check(lay, gd, plan, strict_ports=True)
    print("静态 %s %s" % ("OK" if static["ok"] else "FAIL",
                          [e for e in static["errors"]][:3]))
    prediction = {
        "expected_rate": round(best.rate, 4),
        "plan_rate": round(plan.achieved_rate, 4),
        "power_need": round(plan.power_need, 2),
        "boundary": {k: round(v, 3) for k, v in plan.demand.items()},
        "tiles": static["info"]["tiles"],
        "footprint": static["info"]["footprint"],
        "ports": best.ports,
        "clusters": best.clusters,
        "search": {"candidates": len(rows), "feasible": len(rows),
                   "pareto": [[best.ports, best.tiles, best.box, round(best.rate, 3)]]},
    }
    run_id = args.out or ("quad-p%d" % args.ports)
    run_dir = os.path.join(report.runs_dir(), run_id)
    eng = engine.run(lay, gd, "graphite", ticks=args.ticks, timeout=args.timeout)
    metrics = report.write_run(run_dir, lay, gd, plan, static, eng, prediction,
                               extra={"canvas": list(grid), "layout": "quad",
                                      "shape": label, "ports": best.ports,
                                      "blocks": [list(b) for b in best.blocks]})
    rate = ((eng.get("metrics") or {}) if eng else {}).get("rate")
    print("真机 %s" % (("%.4f/s" % rate) if rate is not None else eng.get("error")))
    print("结论 %s — %s" % ("PASS" if metrics["verdict"]["pass"] else "FAIL", run_dir))
    return 0 if metrics["verdict"]["pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())

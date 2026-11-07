"""单开口（1 端口簇）的两张蓝图：真机各跑一次，看能不能成立。

- `o-cluster9`：3 端口方块 / 9 工厂格（源 + 一个门 + 一个黑洞，全部相邻成 1 簇）
- `o-cluster8`：4 端口方块 / 8 工厂格（顶排 SxSx，最省格）
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mbo.gamedata import GameData                      # noqa: E402
from mbo.production import expand                     # noqa: E402
from mbo import search as S                           # noqa: E402
from mbo import engine, report, validate              # noqa: E402

CANVAS = (24, 24)


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


def main():
    gd = GameData()
    plan = expand(gd, "graphite", 1.0, ["coal"])
    res = S.search(gd, plan, objective="clusters")
    one = [c for c in res.front if c.clusters == 1]

    cands = S.enumerate_candidates(gd, plan) + S.template_candidates(gd, plan, CANVAS)
    one = [c for c in cands if c.ok_need and c.clusters == 1]
    by_tiles = sorted(one, key=lambda c: (c.tiles, c.ports, c.box, c.label))
    by_ports = sorted(one, key=lambda c: (c.ports, c.tiles, c.box, c.label))

    picks = [("o-cluster9", by_ports[0]), ("o-cluster8", by_tiles[0])]
    for run_id, cand in picks:
        lay = S.to_layout(cand, gd, canvas=CANVAS)
        if (lay.w, lay.h) != CANVAS:
            pass
        lay.crop() if hasattr(lay, "crop") else None
        lay = lay.crop()
        static = validate.static_check(lay, gd, plan, strict_ports=True)
        print("== %s  %s：%d 端口 / %d 开口 / %d 格 / 预测 %.4f/s  静态 %s"
              % (run_id, cand.label, cand.ports, cand.clusters, cand.tiles,
                 cand.rate, "OK" if static["ok"] else static["errors"]))
        print(ascii_of(lay))
        if not static["ok"]:
            print("  跳过真机（静态不过）")
            continue
        eng = engine.run(lay, gd, "graphite", ticks=1800, timeout=180)
        rate = eng["metrics"]["rate"] if eng.get("ok") else None
        print("  真机：%s  eff=%s  死锁=%s"
              % ("%.4f/s" % rate if rate else "FAIL",
                 eng["metrics"].get("eff_avg"), eng["metrics"].get("deadlock")))
        prediction = {
            "expected_rate": round(cand.rate, 4),
            "plan_rate": round(plan.achieved_rate, 4),
            "power_need": round(plan.power_need, 2),
            "boundary": {k: round(v, 3) for k, v in plan.demand.items()},
            "tiles": static["info"]["tiles"],
            "footprint": static["info"]["footprint"],
            "ports": cand.ports,
            "clusters": cand.clusters,
            "search": {"candidates": res.candidates, "feasible": res.feasible,
                       "clusters": cand.clusters,
                       "pareto": [list(c.signature()) for c in res.front]},
        }
        run_dir = str(pathlib.Path(report.runs_dir()) / run_id)
        report.write_run(run_dir, lay, gd, plan, static, eng, prediction,
                         extra={"canvas": list(CANVAS), "layout": "search",
                                "objective": "clusters",
                                "crop": True, "ports": cand.ports,
                                "clusters": cand.clusters,
                                "search": {"objective": "clusters",
                                           "label": cand.label,
                                           "clusters": cand.clusters,
                                           "ports": cand.ports,
                                           "tiles": cand.tiles,
                                           "box": cand.box,
                                           "rate": cand.rate}})
        print("  已写 %s" % run_dir)


if __name__ == "__main__":
    main()

"""L6 CLI：`python -m mbo calc|gen|verify`（契约见 docs/02 §2.2）。"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys

from . import __version__, codec, engine, layout, production, report, search, validate
from .gamedata import DEFAULT_SNAPSHOT, SNAPSHOT_ROOT, GameData
from .model import Layout

EXIT_OK, EXIT_STATIC, EXIT_GATE = 0, 2, 3


def parse_target(text: str) -> tuple:
    """"silicon:3/s" / "silicon:3" → ("silicon", 3.0)。"""
    if ":" not in text:
        raise SystemExit("目标格式应为 <item>:<rate>，例如 silicon:3/s")
    item, rate = text.split(":", 1)
    rate = rate.strip().lower().replace("items", "").rstrip("s").replace("/", "").strip()
    return item.strip(), float(rate)


def _boundary(text: str) -> list:
    return [x.strip() for x in (text or "").split(",") if x.strip()]


def _canvas(text: str) -> tuple:
    if "x" in text:
        w, h = text.lower().split("x")
        return int(w), int(h)
    return int(text), int(text)


def cmd_calc(args) -> int:
    gd = GameData(args.snapshot)
    target, rate = parse_target(args.target)
    plan = production.expand(gd, target, rate, _boundary(args.boundary),
                             _forces(args.force))
    out = plan.as_dict()
    out["snapshot_id"] = gd.snapshot_id
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return EXIT_OK
    print("目标 %s %.2f/s  (快照 %s)" % (target, rate, gd.snapshot_id))
    for name, n in sorted(plan.machines.items()):
        b = gd.block(name)
        print("  %-22s ×%-3d  %d×%d" % (name, n, b.size, b.size))
    print("  电力需求 %.1f/s" % plan.power_need)
    if plan.demand:
        print("  边界输入：" + "，".join("%s %.2f/s" % kv for kv in sorted(plan.demand.items())))
    for w in plan.warnings:
        print("  ! " + w)
    return EXIT_OK


def cmd_gen(args) -> int:
    gd = GameData(args.snapshot)
    target, rate = parse_target(args.target)
    plan = production.expand(gd, target, rate, _boundary(args.boundary), _forces(args.force))
    merge = args.merge
    if args.layout == "direct" and merge != "pair":
        print("提示：direct 模板固定用 item-void 当输出标记，忽略 --merge %s" % merge)
        merge = "pair"
    if args.layout == "ported":
        ports = args.ports or "both"
        if args.merge != "pair":
            print("提示：ported 模板的端口方案取 --ports，忽略 --merge %s" % args.merge)
        merge = ports
    lay = layout.build_for(gd, plan, canvas=_canvas(args.canvas), layout=args.layout,
                           gate=args.gate, merge=merge)
    if getattr(args, "crop", False):
        lay.crop()
    static = validate.static_check(lay, gd, plan,
                                   strict_ports=(args.layout == "ported"))
    expected = production.predict_rate(gd, plan, lay)
    prediction = {
        "expected_rate": round(expected, 4),
        "plan_rate": round(plan.achieved_rate, 4),
        "power_need": round(plan.power_need, 2),
        "boundary": {k: round(v, 3) for k, v in plan.demand.items()},
        "tiles": static["info"]["tiles"],
        "footprint": static["info"]["footprint"],
    }

    run_id = args.out or report.new_run_id(target)
    run_dir = run_id if os.path.isabs(run_id) else os.path.join(report.runs_dir(), run_id)

    eng = None
    if not args.no_engine:
        eng = engine.run(lay, gd, target, ticks=args.ticks, timeout=args.timeout)

    metrics = report.write_run(run_dir, lay, gd, plan, static, eng, prediction,
                               extra={"canvas": list(_canvas(args.canvas)), "seed": args.seed,
                                      "layout": args.layout, "gate": args.gate, "merge": merge,
                                      "crop": bool(getattr(args, "crop", False)),
                                       "ports": merge if args.layout == "ported" else None})

    print("运行目录 %s" % run_dir)
    print("预测 %.3f/s，静态 %s，真机 %s"
          % (expected, "OK" if static["ok"] else "FAIL(%d)" % len(static["errors"]),
             ("%.3f/s" % eng["metrics"]["rate"]) if eng and eng.get("ok")
             and (eng.get("metrics") or {}).get("rate") is not None else "未跑"))
    for e in static["errors"]:
        print("  × " + e)
    if eng and not eng.get("ok"):
        print("  × 真机：" + str(eng.get("error")))
    print("粘贴码：%s" % (codec.to_base64(lay.to_bytes())[:60] + "…"))
    print("结论：%s%s — %s" % ("PASS" if metrics["verdict"]["pass"] else "FAIL",
                              "" if metrics["verdict"].get("gate_checked") else "（静态）",
                              "；".join(metrics["verdict"]["reasons"]) or "—"))
    if not static["ok"]:
        return EXIT_STATIC
    return EXIT_OK if metrics["verdict"]["pass"] else EXIT_GATE


def _constraint_text(args) -> str:
    """把 --only-ports / --max-clusters 拼成人话（报错与日志用）。"""
    bits = []
    if getattr(args, "only_ports", None) is not None:
        bits.append("端口数=%d" % args.only_ports)
    if getattr(args, "max_clusters", None) is not None:
        bits.append("开口数<=%d" % args.max_clusters)
    return "、".join(bits) or "无约束"


def cmd_opt(args) -> int:
    """搜索 → 选优 → 静态校验 → 真机验证 → 出报告（脚本化推理的完整链路）。"""
    gd = GameData(args.snapshot)
    target, rate = parse_target(args.target)
    plan = production.expand(gd, target, rate, _boundary(args.boundary), _forces(args.force))
    canvas = _canvas(args.canvas)

    gw, gh = _canvas(args.grid)
    res = search.search(gd, plan, grid=(gw, gh), objective=args.objective,
                        canvas=canvas, with_templates=not args.no_templates)
    print("搜索：%d 张候选（满足产能 %d 张），Pareto 前沿 %d 条（目标 %s）"
          % (res.candidates, res.feasible, len(res.front), res.objective))
    for c in res.front[:max(1, args.top)]:
        print("  ports=%d 开口=%d 工厂格=%2d 外接面积=%2d 预测 %.4f/s  %s"
              % (c.ports, c.clusters, c.tiles, c.box, c.rate, c.label))

    if args.only_ports is not None or args.max_clusters is not None:
        pool = [c for c in res.all_candidates
                if c.ok_need
                and (args.only_ports is None or c.ports == args.only_ports)
                and (args.max_clusters is None or c.clusters <= args.max_clusters)]
        print("按约束（%s）过滤：%d 张候选" % (_constraint_text(args), len(pool)))
        if pool:
            res.front = sorted(pool, key=search._order(args.objective))[:max(1, args.top)]
            res.best = search.pick(pool, args.objective)
        else:
            res.front, res.best = [], None

    if res.best is None:
        print("× 没有满足 %s 的候选；试试放宽约束、--grid 或目标速率"
              % _constraint_text(args))
        return EXIT_GATE

    best = res.best
    lay = search.to_layout(best, gd, canvas=canvas)
    if getattr(args, "crop", False):
        lay.crop()
    static = validate.static_check(lay, gd, plan, strict_ports=True)

    prediction = {
        "expected_rate": round(best.rate, 4),
        "plan_rate": round(plan.achieved_rate, 4),
        "power_need": round(plan.power_need, 2),
        "boundary": {k: round(v, 3) for k, v in plan.demand.items()},
        "tiles": static["info"]["tiles"],
        "footprint": static["info"]["footprint"],
        "ports": best.ports,
        "clusters": best.clusters,
        "search": {"candidates": res.candidates, "feasible": res.feasible,
                   "clusters": best.clusters,
                   "pareto": [list(c.signature()) for c in res.front]},
    }

    run_id = args.out or report.new_run_id(target)
    run_dir = run_id if os.path.isabs(run_id) else os.path.join(report.runs_dir(), run_id)

    eng = None
    if not args.no_engine:
        eng = engine.run(lay, gd, target, ticks=args.ticks, timeout=args.timeout)

    metrics = report.write_run(run_dir, lay, gd, plan, static, eng, prediction,
                               extra={"canvas": list(canvas), "seed": args.seed,
                                      "layout": "search", "objective": args.objective,
                                      "crop": bool(getattr(args, "crop", False)),
                                      "ports": best.ports,
                                      "search": res.as_dict()})

    print("运行目录 %s" % run_dir)
    print("选中 %s（%d 端口 / %d 个开口 / %d 工厂格 / 预测 %.4f/s）"
          % (best.label, best.ports, best.clusters, best.tiles, best.rate))
    print("静态 %s，真机 %s"
          % ("OK" if static["ok"] else "FAIL(%d)" % len(static["errors"]),
             ("%.3f/s" % eng["metrics"]["rate"]) if eng and eng.get("ok")
             and (eng.get("metrics") or {}).get("rate") is not None else "未跑"))
    for e in static["errors"]:
        print("  × " + e)
    if eng and not eng.get("ok"):
        print("  × 真机：" + str(eng.get("error")))
    print("结论：%s%s — %s" % ("PASS" if metrics["verdict"]["pass"] else "FAIL",
                              "" if metrics["verdict"].get("gate_checked") else "（静态）",
                              "；".join(metrics["verdict"]["reasons"]) or "—"))
    if not static["ok"]:
        return EXIT_STATIC
    return EXIT_OK if metrics["verdict"]["pass"] else EXIT_GATE


def cmd_verify(args) -> int:
    run_dir = args.run
    if not os.path.isdir(run_dir):
        run_dir = os.path.join(report.runs_dir(), run_dir)
    tpath = os.path.join(run_dir, "trace.json")
    if not os.path.exists(tpath):
        raise SystemExit("找不到 %s" % tpath)
    trace = json.load(open(tpath, encoding="utf-8"))
    gd = GameData(args.snapshot or trace.get("snapshot", DEFAULT_SNAPSHOT))
    lay = Layout.from_snapshot(trace["layout"], trace["canvas"][0], trace["canvas"][1],
                               {n: b.size for n, b in gd.blocks.items()},
                               name=trace.get("layout_name", ""),
                               description=trace.get("layout_description", ""))
    static = validate.static_check(lay, gd)
    print("从 trace.json 重建：%d 建筑 / %d 格" % (static["info"]["blocks"], static["info"]["tiles"]))
    print("静态校验：%s" % ("OK" if static["ok"] else "FAIL"))
    for e in static["errors"]:
        print("  × " + e)

    # 字节一致性：重编码后与 blueprint.msch 的 body 必须一致
    bpath = os.path.join(run_dir, "blueprint.msch")
    if os.path.exists(bpath):
        old = codec.body_of(open(bpath, "rb").read())
        new = codec.body_of(lay.to_bytes())
        same = old == new
        print("重编码 body 一致：%s" % same)
        if not same:
            return EXIT_STATIC

    exit_code = EXIT_OK if static["ok"] else EXIT_STATIC
    if args.engine:
        eng = engine.run(lay, gd, trace["target"], ticks=args.ticks, timeout=args.timeout)
        m = eng.get("metrics") or {}
        print("真机：%s %s/s（墙钟 %ss）"
              % ("OK" if eng.get("ok") else "FAIL", m.get("rate"), eng.get("wall_s")))
        if not eng.get("ok"):
            exit_code = EXIT_GATE
    return exit_code


def cmd_snapshot(args) -> int:
    """把 spikes/data 的实测快照登记进 gamedata/<snapshot>/。"""
    src = args.src or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "spikes", "data", "gamedata.json")
    dst_dir = os.path.join(SNAPSHOT_ROOT, args.snapshot)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, "gamedata.json")
    shutil.copyfile(src, dst)
    src_meta = os.path.join(os.path.dirname(src), "compare_report.json")
    meta = {
        "snapshot": args.snapshot,
        "gamedata_json": "gamedata.json",
        "sha256": GameData._digest(dst) if hasattr(GameData, "_digest") else "",
        "source": "official server jar reflection dump (spikes/data/extract_game_data.py)",
        "extracted_at": None,
    }
    import hashlib

    h = hashlib.sha256()
    with open(dst, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    meta["sha256"] = h.hexdigest()
    with open(os.path.join(dst_dir, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print("已登记快照 %s → %s（sha256 %s…）" % (args.snapshot, dst, meta["sha256"][:12]))
    return EXIT_OK


def cmd_preview(args) -> int:
    """把 run（或全部 run）渲染成可审阅的俯视图：PNG / ASCII / HTML 画廊。"""
    from . import preview
    from . import sprites as sprites_mod

    sprite_set = None
    if not args.no_sprites:
        root = None if args.sprites in (None, "auto") else args.sprites
        sprite_set = sprites_mod.discover(root)
        if sprite_set is None:
            if root:
                raise SystemExit("找不到贴图：%s（应有 blocks/ 子目录）" % root)
            print("提示：没找到原版贴图（assetsraw/assets-raw/sprites），回落色块渲染")
        else:
            print("贴图：%s（%d 张）" % (sprite_set.root, sprite_set.names()))

    runs = pathlib.Path(report.runs_dir())
    if args.all:
        n_png = 0
        for d in sorted(p for p in runs.iterdir() if (p / "trace.json").exists()):
            try:
                preview.write_png(d, scale=args.scale, sprites=sprite_set)
                n_png += 1
            except Exception as e:                      # 单个 run 坏掉不该拖垮画廊
                print("跳过 %s：%s" % (d.name, e))
        out, n = preview.write_index(runs)
        print("已生成画廊 %s（%d 个 run，重绘 %d 张 PNG）" % (out, n, n_png))
        return EXIT_OK

    if not args.run:
        raise SystemExit("preview 需要 run 名，或用 --all")
    run_dir = runs / args.run
    if not (run_dir / "trace.json").exists():
        raise SystemExit("找不到 %s/trace.json" % run_dir)

    if args.ascii:
        trace, lay, gd = preview.load_run(run_dir)
        print(preview.render_ascii(lay, gd))
        print(preview.summarize(run_dir, trace))
    if not args.no_png:
        out, lay = preview.write_png(run_dir, scale=args.scale, sprites=sprite_set)
        print("已生成 %s（%dx%d 格）" % (out, lay.w, lay.h))
    return EXIT_OK


def _forces(pairs) -> dict:
    out = {}
    for p in pairs or []:
        if "=" not in p:
            raise SystemExit("--force 格式应为 item=block")
        item, block = p.split("=", 1)
        out[item.strip()] = block.strip()
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mbo", description="Mindustry Blueprint Optimizer (MVP)")
    p.add_argument("--version", action="version", version="mbo %s" % __version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--snapshot", default=DEFAULT_SNAPSHOT, help="数据快照目录名")
        sp.add_argument("--boundary", default="", help="外部供给物品，逗号分隔（必填）")
        sp.add_argument("--force", action="append", default=[], help="item=block 强制配方")

    c = sub.add_parser("calc", help="只算建筑清单，不生成蓝图")
    c.add_argument("target", help="<item>:<rate>，例如 silicon:3/s")
    common(c)
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_calc)

    g = sub.add_parser("gen", help="生成蓝图 + 校验 + 真机验证 + 出报告")
    g.add_argument("target")
    common(g)
    g.add_argument("--canvas", default="24x24")
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("--out", default=None, help="运行目录名（默认 runs/<时间>-<目标>）")
    g.add_argument("--ticks", type=int, default=1800)
    g.add_argument("--timeout", type=float, default=180.0)
    g.add_argument("--no-engine", action="store_true", help="只做静态校验，不起服务端")
    g.add_argument("--layout", default="auto",
                   choices=["auto", "cells", "split", "direct", "ported"],
                   help="auto=能分门就分门；cells=每台独立源+带；split=物流门分流；"
                        "direct=10 格最小（端口嵌在工厂里，docs/18）；"
                        "ported=端口在工厂外框之外（docs/19）")
    g.add_argument("--gate", default="underflow-gate",
                   choices=["underflow-gate", "overflow-gate"],
                   help="split 模板用哪种门（反溢门两侧优先 / 溢流门直行优先）")
    g.add_argument("--ports", default=None, choices=["both", "gate", "one"],
                   help="ported 模板的端口方案：both=每台一进一出(8 格)；"
                        "gate=单源经门+每台一出(9 格)；one=单进单出(12 格)")
    g.add_argument("--merge", default="pair",
                   choices=["pair", "single", "vault", "core", "void"],
                   help="产物出口：pair=每台一个容器（老行为）；single/vault/core/void=合流到一个出口")
    g.add_argument("--crop", action="store_true",
                   help="把蓝图裁到实际占格的外接矩形（去掉画布空白边）")
    g.set_defaults(func=cmd_gen)

    o = sub.add_parser("opt", help="搜索→选优→校验→真机（脚本化推理）")
    o.add_argument("target")
    common(o)
    o.add_argument("--objective", default="ports", choices=search.OBJECTIVES,
                   help="Pareto 前沿上按哪个目标挑代表点（默认 ports）")
    o.add_argument("--top", type=int, default=5, help="前沿最多打印几条（默认 5）")
    o.add_argument("--grid", default="9x7", help="枚举搜索网格（默认 9x7）")
    o.add_argument("--canvas", default="24x24")
    o.add_argument("--seed", type=int, default=0)
    o.add_argument("--out", default=None, help="运行目录名（默认 runs/<时间>-<目标>）")
    o.add_argument("--ticks", type=int, default=1800)
    o.add_argument("--timeout", type=float, default=180.0)
    o.add_argument("--no-engine", action="store_true", help="只做静态校验，不起服务端")
    o.add_argument("--no-templates", action="store_true",
                   help="只搜枚举几何，不把手写模板放进候选池")
    o.add_argument("--crop", action="store_true", help="裁到实际占格的外接矩形")
    o.add_argument("--only-ports", type=int, default=None,
                   help="只保留端口方块数恰为 N 的候选（单入单出 = 2）")
    o.add_argument("--max-clusters", type=int, default=None,
                   help="只保留开口数 <= N 的候选（单开口 = 1）")
    o.set_defaults(func=cmd_opt)

    v = sub.add_parser("verify", help="从 trace.json 重建并复检（可含真机）")
    v.add_argument("run")
    v.add_argument("--snapshot", default=None)
    v.add_argument("--engine", action="store_true", help="同时重跑真机")
    v.add_argument("--ticks", type=int, default=1800)
    v.add_argument("--timeout", type=float, default=180.0)
    v.set_defaults(func=cmd_verify)

    pv = sub.add_parser("preview", help="渲染俯视图（PNG/ASCII/HTML 画廊），方便人工审阅")
    pv.add_argument("run", nargs="?", default=None, help="run 目录名；配合 --all 可省略")
    pv.add_argument("--all", action="store_true", help="生成 runs/index.html 画廊")
    pv.add_argument("--scale", type=int, default=2, help="像素倍率（默认 2）")
    pv.add_argument("--ascii", action="store_true", help="同时在终端打印 ASCII 图")
    pv.add_argument("--sprites", nargs="?", const="auto", default="auto",
                    help="用原版贴图渲染；可给贴图根目录（默认自动找 assetsraw/assets-raw/sprites）")
    pv.add_argument("--no-sprites", action="store_true", help="强制色块渲染（不贴图）")
    pv.add_argument("--no-png", action="store_true", help="只打印 ASCII，不写 PNG")
    pv.set_defaults(func=cmd_preview)

    s = sub.add_parser("build-snapshot", help="登记 gamedata 快照")
    s.add_argument("--snapshot", default=DEFAULT_SNAPSHOT)
    s.add_argument("--src", default=None)
    s.set_defaults(func=cmd_snapshot)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

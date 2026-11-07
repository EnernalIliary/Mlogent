"""L6 报告：一次运行产出 `runs/<run_id>/` 的五件产物（docs/03 §1）。"""

from __future__ import annotations

import json
import os
import platform
import time

from . import __version__, codec
from .gamedata import MBO_ROOT

GATE = {
    "rate_margin": 0.95,      # 实测必须 ≥ 预测的 95%
    "max_wall_s": 300.0,      # 端到端 ≤ 5 分钟
}


def new_run_id(target: str) -> str:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return "%s-%s" % (stamp, target.replace("/", "_"))


def write_run(run_dir: str, lay, gd, plan, static: dict, engine: dict | None,
              prediction: dict, extra: dict | None = None) -> dict:
    os.makedirs(run_dir, exist_ok=True)
    data = lay.to_bytes()
    msch_path = os.path.join(run_dir, "blueprint.msch")
    with open(msch_path, "wb") as fh:
        fh.write(data)
    b64 = codec.to_base64(data)
    with open(os.path.join(run_dir, "blueprint.b64.txt"), "w", encoding="utf-8") as fh:
        fh.write(b64 + "\n")

    verdict = _verdict(static, engine, prediction)
    metrics = {
        "run_id": os.path.basename(run_dir),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "mbo_version": __version__,
        "snapshot_id": gd.snapshot_id,
        "target": plan.target,
        "requested_rate": plan.requested_rate,
        "predicted": prediction,
        "static": static,
        "engine": engine or {"skipped": True},
        "verdict": verdict,
        "files": {
            "blueprint_msch": "blueprint.msch",
            "blueprint_b64": "blueprint.b64.txt",
            "report": "report.md",
            "trace": "trace.json",
        },
    }
    with open(os.path.join(run_dir, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=2)

    trace = {
        "run_id": metrics["run_id"],
        "mbo_version": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "snapshot_id": gd.snapshot_id,
        "gamedata_path": gd.path,
        "gamedata_sha256": gd.sha256,
        "target": plan.target,
        "requested_rate": plan.requested_rate,
        "boundary": sorted(plan.demand),
        "canvas": [lay.w, lay.h],
        "layout_name": lay.name,
        "layout_description": lay.description,
        "layout": lay.snapshot(),
        "layout_stats": lay.stats(),
        "plan": plan.as_dict(),
        "prediction": prediction,
        "engine": {k: v for k, v in (engine or {}).items() if k != "samples"},
        "params": extra or {},
        "reproduce": [
            "python -m mbo gen %s:%g --boundary %s%s --out %s"
            % (plan.target, plan.requested_rate, ",".join(sorted(plan.demand)),
               _flags(extra), os.path.basename(run_dir)),
        ],
    }
    with open(os.path.join(run_dir, "trace.json"), "w", encoding="utf-8") as fh:
        json.dump(trace, fh, ensure_ascii=False, indent=2)

    _write_report(os.path.join(run_dir, "report.md"), metrics, lay, plan, gd)
    return metrics


def _flags(extra) -> str:
    """把影响布局的命令行开关写进 reproduce（否则复现不出同一张图）。"""
    e = extra or {}
    out = []
    if e.get("layout") and e["layout"] != "auto":
        out.append(" --layout %s" % e["layout"])
    if e.get("gate") and e["gate"] != "underflow-gate":
        out.append(" --gate %s" % e["gate"])
    if e.get("merge") and e["merge"] != "pair":
        out.append(" --merge %s" % e["merge"])
    if e.get("crop"):
        out.append(" --crop")
    return "".join(out)


def _verdict(static: dict, engine: dict | None, prediction: dict) -> dict:
    reasons = []
    ok = True
    gate_checked = False
    if not static.get("ok"):
        ok = False
        reasons.append("静态校验未通过：%d 条错误" % len(static.get("errors", [])))
    if engine:
        if not engine.get("ok"):
            ok = False
            reasons.append("真机运行失败：%s" % engine.get("error"))
        else:
            m = engine.get("metrics") or {}
            rate = m.get("rate")
            want = prediction.get("expected_rate") or 0.0
            if m.get("deadlock"):
                ok = False
                reasons.append("死锁：全部机器 eff<0.05")
            if rate is None:
                ok = False
                reasons.append("读不到产量")
            elif want and rate < GATE["rate_margin"] * want:
                ok = False
                reasons.append("实测 %.3f/s < 预测 %.3f/s × %.2f" % (rate, want, GATE["rate_margin"]))
            elif want:
                reasons.append("实测 %.3f/s vs 预测 %.3f/s（%+.1f%%）"
                               % (rate, want, (rate - want) / want * 100.0))
            if engine.get("wall_s", 0) > GATE["max_wall_s"]:
                ok = False
                reasons.append("墙钟 %.1fs 超过 %.0fs" % (engine["wall_s"], GATE["max_wall_s"]))
        gate_checked = True
    else:
        gate_checked = False
        reasons.append("未跑真机（--no-engine）：只做了静态校验，不计入 Gate")
    return {"pass": ok, "gate_checked": gate_checked, "reasons": reasons}


def _write_report(path: str, metrics: dict, lay, plan, gd) -> None:
    m = metrics
    p = m["predicted"]
    st = m["static"]
    eng = m["engine"]
    lines = []
    add = lines.append
    add("# %s — %s\n" % (m["target"], "PASS" if m["verdict"]["pass"] else "FAIL"))
    add("| 项 | 值 |")
    add("|---|---|")
    add("| 目标 | %s %.2f/s |" % (m["target"], m["requested_rate"]))
    add("| 预测 | %s/s |" % _fmt(p.get("expected_rate")))
    add("| 实测 | %s |" % (_fmt((eng.get("metrics") or {}).get("rate")) + "/s"
                            if eng.get("metrics") else "未跑"))
    add("| 数据快照 | `%s` |" % m["snapshot_id"])
    add("| 画布 | %d×%d (%d 格) |" % (lay.w, lay.h, lay.w * lay.h))
    add("| 建筑数 | %d（占 %d 格） |" % (st["info"]["blocks"], st["info"]["tiles"]))
    add("| 电力 | 需 %.1f/s，节点 %d，连通块 %d |"
        % (st["info"]["power_need"], st["info"]["power_nodes"], st["info"]["power_components"]))
    add("| 墙钟 | %s s |" % _fmt(eng.get("wall_s")))
    add("")
    add("## 判据\n")
    for r in m["verdict"]["reasons"]:
        add("- %s" % r)
    add("")
    add("## 建筑清单\n")
    add("| 方块 | 数量 | 尺寸 |")
    add("|---|---|---|")
    for name, n in sorted(st["info"]["counts"].items()):
        add("| `%s` | %d | %d×%d |" % (name, n, gd.block(name).size, gd.block(name).size))
    add("")
    add("## 边界输入（外部供给）\n")
    add("| 物品 | 需求 /s |")
    add("|---|---|")
    for name, v in sorted(plan.demand.items()):
        add("| %s | %.2f |" % (name, v))
    if plan.warnings:
        add("")
        add("## 警告\n")
        for w in plan.warnings:
            add("- %s" % w)
    if st["warnings"]:
        add("")
        add("## 静态提示\n")
        for w in st["warnings"]:
            add("- %s" % w)
    add("")
    add("## 复现\n")
    add("```")
    add("python -m mbo verify %s" % m["run_id"])
    add("```")
    add("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def _fmt(v) -> str:
    return "—" if v is None else ("%.3f" % v if isinstance(v, float) else str(v))


def runs_dir() -> str:
    return os.path.join(MBO_ROOT, "runs")

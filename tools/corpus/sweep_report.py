"""Turn two `tools/sweep_all.py` JSONs into one comparison report.

    python tools/sweep_report.py out/sweep_mine.json out/sweep_caime.json \
        --out out/sweep_report.md
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re


def pct(a: int, b: int) -> str:
    return f"{a * 100 / b:.1f}%" if b else "-"


def quant(vals: list[int], q: float) -> int:
    if not vals:
        return 0
    v = sorted(vals)
    i = min(len(v) - 1, int(round(q * (len(v) - 1))))
    return v[i]


def load(path: str) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def stats(data: dict) -> dict:
    rows = data["rows"]
    sev, code = collections.Counter(), collections.Counter()
    for r in rows:
        for s, _ln, c, _m in r["findings"]:
            sev[s] += 1
            code[(s, c)] += 1
    stmts = sum(r["stmts"] for r in rows)
    errs = sum(r["errs"] for r in rows)
    per_block = [r["errs"] for r in rows]
    return {
        "rows": rows, "n": len(rows), "stmts": stmts, "sev": sev, "code": code,
        "errs": errs, "errs_1k": errs * 1000 / stmts if stmts else 0,
        "clean": sum(1 for r in rows if r["errs"] == 0),
        "dead": sum(r["reported"] for r in rows), "hidden": sum(r["hidden"] for r in rows),
        "deadcode": sum(r["dead"] for r in rows),
        "branches": sum(r["branches"] for r in rows),
        "nulls": sum(r["nulls"] for r in rows),
        "packs": sum(r["packs"] for r in rows),
        "p50": quant(per_block, .5), "p90": quant(per_block, .9), "p99": quant(per_block, .99),
        "max": max(per_block) if per_block else 0,
        "stmts_med": quant([r["stmts"] for r in rows], .5),
    }


TEMPLATE = re.compile(r"`[^`]*`")


def template(msg: str) -> str:
    return TEMPLATE.sub("`X`", msg)[:70]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mine")
    ap.add_argument("caime")
    ap.add_argument("--out", default="out/sweep_report.md")
    args = ap.parse_args()

    dm, dc = load(args.mine), load(args.caime)
    sm, sc = stats(dm), stats(dc)
    L: list[str] = []
    w = L.append

    w("# 两套蓝图库的全量体检")
    w("")
    w(f"- **我的库**：`{dm['folder']}`")
    w(f"- **彩末包**：`{dc['folder']}`")
    w("")
    w("一次跑完 check / 成本 / 不可达 / 死存储 / 常量分支 / 可证 null / 打包配置 / 版本闸门 / 跨处理器。"
      "生成命令：`python tools/sweep_all.py <dir> --json out/sweep_x.json`，"
      "本报告由 `python tools/sweep_report.py` 生成。")
    w("")
    w("> 跳过规则：文件名含模拟器关键字、单文件 > 2 MB、单块 > 5000 条语句 —— 这些是像素画/模拟器镜像，"
      "会把任何平均值拖到无意义。跳过条数在下面单独列出。")
    w("")

    w("## 一、规模")
    w("")
    w("| | 我的库 | 彩末包 |")
    w("|---|---:|---:|")
    w(f"| .msch 文件 | {dm['files']} | {dc['files']} |")
    w(f"| 有逻辑的处理器 | {sm['n']} | {sc['n']} |")
    w(f"| 逻辑语句 | {sm['stmts']:,} | {sc['stmts']:,} |")
    w(f"| 每块语句中位数 | {sm['stmts_med']} | {sc['stmts_med']} |")
    w(f"| 跳过 · 模拟器文件 | {len(dm['files_skipped_emulator'])} | {len(dc['files_skipped_emulator'])} |")
    w(f"| 跳过 · 超大（文件或单块） | {len(dm['files_skipped_big'])} | {len(dc['files_skipped_big'])} |")
    w(f"| 解析失败 | {len(dm['failed'])} | {len(dc['failed'])} |")
    w(f"| 扫描耗时 | {dm['seconds']}s | {dc['seconds']}s |")
    w("")

    w("## 二、总体")
    w("")
    w("| 指标 | 我的库 | 彩末包 |")
    w("|---|---:|---:|")
    w(f"| **ERR + SUSPECT** | **{sm['errs']}** | **{sc['errs']}** |")
    w(f"| 每千条语句 | {sm['errs_1k']:.1f} | {sc['errs_1k']:.1f} |")
    w(f"| 零错误的处理器 | {sm['clean']} ({pct(sm['clean'], sm['n'])}) | "
      f"{sc['clean']} ({pct(sc['clean'], sc['n'])}) |")
    w(f"| 每块错误 p50 / p90 / p99 / max | {sm['p50']} / {sm['p90']} / {sm['p99']} / {sm['max']} | "
      f"{sc['p50']} / {sc['p90']} / {sc['p99']} / {sc['max']} |")
    w(f"| WARN | {sm['sev'].get('WARN', 0)} | {sc['sev'].get('WARN', 0)} |")
    w(f"| INFO | {sm['sev'].get('INFO', 0)} | {sc['sev'].get('INFO', 0)} |")
    w(f"| 死存储（reported） | {sm['dead']} | {sc['dead']} |")
    w(f"| 死存储（隐藏层） | {sm['hidden']} | {sc['hidden']} |")
    w(f"| 不可达语句 | {sm['deadcode']} | {sc['deadcode']} |")
    w(f"| 常量分支 | {sm['branches']} | {sc['branches']} |")
    w(f"| 可证 null | {sm['nulls']} | {sc['nulls']} |")
    w(f"| 打包配置站点 | {sm['packs']} | {sc['packs']} |")
    w("")

    w("## 三、错误按类型")
    w("")
    order: list[tuple[str, str]] = []
    for key, _v in (sm["code"] + sc["code"]).most_common():
        if key not in order:
            order.append(key)
    w("| 级别 | 语句 | 我的库 | 彩末包 |")
    w("|---|---|---:|---:|")
    for s, c in order[:30]:
        w(f"| {s} | `{c}` | {sm['code'].get((s, c), 0)} | {sc['code'].get((s, c), 0)} |")
    w("")

    w("## 四、块越大，错越多吗")
    w("")
    w("按语句数分桶看**每千条语句**的错误数 —— 如果大块只是「长」而不是「糟」，这一列应该持平。")
    w("")
    w("| 语句数 | 我的库 块数 | 每千句 | 彩末包 块数 | 每千句 |")
    w("|---|---:|---:|---:|---:|")
    buckets = [(1, 20), (21, 60), (61, 150), (151, 400), (401, 1000), (1001, 10 ** 9)]
    for lo, hi in buckets:
        label = f"{lo}–{hi}" if hi < 10 ** 9 else f"{lo}+"
        cells: list[str] = []
        for st in (sm, sc):
            sel = [r for r in st["rows"] if lo <= r["stmts"] <= hi]
            s_ = sum(r["stmts"] for r in sel)
            e_ = sum(r["errs"] for r in sel)
            cells += [str(len(sel)), f"{e_ * 1000 / s_:.1f}" if s_ else "-"]
        w(f"| {label} | {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} |")
    w("")

    w("## 五、同一个错被复制了多少份")
    w("")
    w("把错误消息里的名字抹成 `X` 再计数 —— 一个模板命中很多文件，说明它是一条**复制链**，"
      "改一处要顺着改一路。")
    w("")
    for name, st in (("我的库", sm), ("彩末包", sc)):
        spread: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        count: collections.Counter = collections.Counter()
        for r in st["rows"]:
            for s, _ln, c, msg in r["findings"]:
                if s not in ("ERR", "SUSPECT"):
                    continue
                t = (c, template(msg))
                spread[t].add(r["file"])
                count[t] += 1
        top = sorted(count, key=lambda k: (-len(spread[k]), -count[k]))[:8]
        w(f"**{name}**")
        w("")
        w("| 命中文件数 | 次数 | 检查项 | 模板 |")
        w("|---:|---:|---|---|")
        for t in top:
            w(f"| {len(spread[t])} | {count[t]} | `{t[0]}` | {t[1]} |")
        w("")

    for title, st in (("六、我的库：最该看的处理器", sm), ("七、彩末包：最该看的处理器", sc)):
        w(f"## {title}")
        w("")
        w("| 文件 | 块 | 语句 | E/W | 死存储 | 不可达 | 检查项 |")
        w("|---|---|---:|---:|---:|---:|---|")
        for r in sorted(st["rows"], key=lambda r: (-r["errs"], -r["reported"]))[:15]:
            note = ", ".join(sorted({c for _s, _l, c, _m in r["findings"]}))[:52]
            w(f"| {r['file']} | {r['block']} @({r['x']},{r['y']}) | {r['stmts']} | "
              f"{r['errs']}/{r['warns']} | {r['reported']} | {r['dead']} | {note} |")
        w("")

    w("## 八、彩末包按目录")
    w("")
    per = collections.defaultdict(lambda: [0, 0, 0])
    parts = [r["file"].split("\\") for r in sc["rows"]]
    shared = 0
    while parts and all(len(p) > shared + 1 for p in parts) and \
            len({p[shared] for p in parts}) == 1:
        shared += 1
    for r in sc["rows"]:
        seg = r["file"].split("\\")
        k = seg[shared] if len(seg) > shared + 1 else "(根)"
        per[k][0] += 1
        per[k][1] += r["stmts"]
        per[k][2] += r["errs"]
    w("| 目录 | 块 | 语句 | ERR | 每千句 |")
    w("|---|---:|---:|---:|---:|")
    for k, (b, s_, e_) in sorted(per.items(), key=lambda kv: -kv[1][2]):
        w(f"| {k} | {b} | {s_:,} | {e_} | {e_ * 1000 / s_ if s_ else 0:.1f} |")
    w("")

    w("## 九、跨处理器读写")
    w("")
    w("| 库 | 用了跨处理器的蓝图 | cross read | 从未被写的槽 | 死写 |")
    w("|---|---:|---:|---:|---:|")
    for name, d in (("我的库", dm), ("彩末包", dc)):
        c = d["cross"]
        w(f"| {name} | {len(c)} | {sum(x['reads'] for x in c)} | "
          f"{sum(x['never_written'] for x in c)} | {sum(x['dead_writes'] for x in c)} |")
    w("")
    errs = (dm.get("cross_errors") or []) + (dc.get("cross_errors") or [])
    if errs:
        w(f"> cross-processor view failed on {len(errs)} schematic(s), first: `{errs[0][:120]}`")
        w("")

    w("## 十、版本闸门")
    w("")
    for name, d in (("我的库", dm), ("彩末包", dc)):
        gates = collections.Counter(r["build"] for r in d["rows"] if r["build"])
        if gates:
            w(f"- {name}：" + "、".join(f"`>={k}` {v} 块" for k, v in sorted(gates.items())))
        else:
            w(f"- {name}：没有用到比 build 146 更新的语句")
    w("")

    w("## 十一、只有一侧出现的检查项")
    w("")
    only_m = [f"`{c}`×{v}" for (s, c), v in sm["code"].items() if (s, c) not in sc["code"]]
    only_c = [f"`{c}`×{v}" for (s, c), v in sc["code"].items() if (s, c) not in sm["code"]]
    w("- 只在**我的库**：" + ("、".join(sorted(only_m)) if only_m else "（无）"))
    w("- 只在**彩末包**：" + ("、".join(sorted(only_c)) if only_c else "（无）"))
    w("")

    w("## 十二、我的库：逐条待办")
    w("")
    pairs: collections.Counter = collections.Counter()
    for r in sm["rows"]:
        for s, _ln, c, msg in r["findings"]:
            if s in ("ERR", "SUSPECT"):
                pairs[(r["file"], c, template(msg))] += 1
    w("先修重复次数最多的（同一模板出现 N 次 = 复制了 N 份）：")
    w("")
    w("| 次数 | 文件 | 检查项 | 说明 |")
    w("|---:|---|---|---|")
    for (f, c, m), n in pairs.most_common(40):
        w(f"| {n} | {f} | `{c}` | {m[:76]} |")
    w("")
    total = sum(pairs.values())
    w(f"合计 **{total}** 条 ERR/SUSPECT，分布在 {len({k[0] for k in pairs})} 个文件里。")
    w("")

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out}  ({out.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

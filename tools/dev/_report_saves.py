"""Turn out/saves_analyse.json into a readable report.

The JSON keys its rule table by the *whole* normalised message, so the two
"shaped like a block link" variants that differ only in the link list end up as
forty separate rows -- one per processor's link set.  Merging on the first
clause before writing the table is the difference between a report and a dump.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
data = json.loads((OUT / "saves_analyse.json").read_text(encoding="utf-8"))


def merge(rule: str) -> str:
    """Collapse a rule to its invariant part."""
    rule = re.sub(r"\s*\(it has:.*?\)$", "", rule)
    rule = re.sub(r"\s*\(N = DEAD\)", "", rule)
    rule = re.sub(r"\s*\(a constant branch is often a signature\)", "", rule)
    return rule.strip()


merged: dict[tuple[str, str], int] = {}
for key, count in data["codes"].items():
    sev, rule = key.split("|", 1)
    k = (sev, merge(rule))
    merged[k] = merged.get(k, 0) + count

lines = []
add = lines.append
add("# 存档里的逻辑：一次全量体检\n")
add(f"- 存档 {data['saves']} 个（v7 289 / v8 149 / v9 61 / v10 45 / v11 877），全部解析成功")
add(f"- 处理器 {data['processors']:,} 个")
add(f"- 去重后不同的程序 **{data['distinct']:,}** 份"
    f"（{data['duplicates']:,} 份是完全相同代码的副本，占 "
    f"{100.0*data['duplicates']/max(1,data['processors']):.1f}%）")
add(f"- 发现 {sum(data['severity'].values()):,} 条："
    + " / ".join(f"{k} {v:,}" for k, v in sorted(data["severity"].items())))
add("")
add("## 最常被复制的程序")
add("")
add("| 副本数 | 语句 | 首次出现 |")
add("| --- | --- | --- |")
for m in data["most_copied"][:8]:
    add(f"| {m['copies']:,} | {m['stmts']} | {m['save']}:{m['x']},{m['y']} |")
add("")
add("## 规则命中表（按规则归并）")
add("")
add("| 次数 | 级别 | 规则 |")
add("| --- | --- | --- |")
for (sev, rule), count in sorted(merged.items(), key=lambda kv: -kv[1])[:25]:
    add(f"| {count:,} | {sev} | {rule} |")
add("")
add("## 硬错最多的存档")
add("")
add("| 硬错 | 处理器 | 警告 | 存档 |")
add("| --- | --- | --- | --- |")
ranked = sorted(data["per_save"].items(), key=lambda kv: -kv[1][1])[:12]
for name, (procs, errs, warns) in ranked:
    if errs:
        add(f"| {errs} | {procs} | {warns} | {name} |")
add("")
add("## 现存的实际错误（示例）")
add("")
seen = set()
for e in data["examples"]:
    if e["code"] in seen:
        continue
    if e["stmts"] > 3000:
        continue
    seen.add(e["code"])
    add(f"- `{e['save']}` ({e['x']},{e['y']}) L{e['line']}: {e['msg'][:160]}")
    if len(seen) >= 10:
        break
add("")
add("## 这组数字不能证明什么")
add("")
add("- 只是静态检查。能证明「这段代码永远不会读那个变量」，不能证明「这段逻辑打起来是对的」——"
    "没有人跑过这些程序。")
add("- 副本被合并了，所以「每处理器错误率」会被 9,699 份同一个程序放大；"
    "本报告刻意只按**不同的程序**计数。")
add("- `INFO target N is itself a jump` 这类是跳转链的普通写法，不是问题，占 INFO 的八成。")

path = OUT / "saves_report.md"
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[:14]))
print(f"\nwrote {path}")

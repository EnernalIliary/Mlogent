#!/usr/bin/env python
"""按「答案必须来自哪一类真源」给 300 题切一刀（source_kind），供 README §9 与覆盖度分析使用。

四类（单标签，优先级从上到下）：
  实测   ver 含 rt（v160.7_rt）或 src 是 knowledge/VERSION.md —— 数字只能靠 jar 反射/双版本对照确认，源码里推不出来
  公式   type=calc，或 why 里出现「= … * / ×」形式的算式 —— 必须把若干数值代进公式算，单点检索不够
  数据表  src 是 *.json（data/game/* 或 tools/*）—— 从表里取一个值/一条结构
  源码   其余（*.java 语义、枚举、默认值、行号）—— 读代码即得

用法：
  python classify_sources.py                 # 打印统计表
  python classify_sources.py --json out.json # 另存逐题标签 + 统计
题库冻结，本脚本只读 questions.jsonl，不改题。
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
Q = HERE / "questions.jsonl"
REPORT = HERE / "eval_report.json"
KINDS = ["源码", "数据表", "公式", "实测"]


def kind(r: dict) -> str:
    src, ver, typ, why = r["src"], r["ver"], r["type"], r["why"]
    if "rt" in ver or src.endswith(".md"):
        return "实测"
    if typ == "calc" or re.search(r"[=＝][^。；\n]{0,20}[*×/]", why):
        return "公式"
    if src.endswith(".json"):
        return "数据表"
    return "源码"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default=str(Q))
    ap.add_argument("--json", default=None, help="把逐题标签+统计写到该文件")
    a = ap.parse_args(argv)
    rows = [json.loads(l) for l in Path(a.questions).open(encoding="utf-8") if l.strip()]

    tagged = [{**r, "source_kind": kind(r)} for r in rows]
    overall = collections.Counter(t["source_kind"] for t in tagged)

    dom = collections.defaultdict(collections.Counter)
    for t in tagged:
        dom[t["domain"]][t["source_kind"]] += 1

    diff = collections.defaultdict(collections.Counter)
    for t in tagged:
        diff[t["difficulty"]][t["source_kind"]] += 1

    gaps_by_kind = collections.Counter()
    gap_srcs = []
    if REPORT.exists():
        rep = json.loads(REPORT.read_text(encoding="utf-8"))
        id2kind = {t["id"]: t["source_kind"] for t in tagged}
        for g in rep.get("gaps", []):
            k = id2kind.get(g["id"])
            gaps_by_kind[k] += 1
            gap_srcs.append({**g, "source_kind": k})

    print("== overall (n=%d)" % len(tagged))
    for k in KINDS:
        print(f"  {k:<6}{overall.get(k, 0):>4}  {overall.get(k, 0)/len(tagged):>6.1%}")
    print("\n== 逐域（行=域，列=四类）")
    print(f"{'domain':<12}" + "".join(f"{k:>7}" for k in KINDS) + f"{'n':>6}")
    for d, cc in dom.items():
        print(f"{d:<12}" + "".join(f"{cc.get(k,0):>7}" for k in KINDS) + f"{sum(cc.values()):>6}")
    print("\n== 难度交叉")
    print(f"{'difficulty':<12}" + "".join(f"{k:>7}" for k in KINDS) + f"{'n':>6}")
    for d in sorted(diff):
        cc = diff[d]
        print(f"{d:<12}" + "".join(f"{cc.get(k,0):>7}" for k in KINDS) + f"{sum(cc.values()):>6}")
    if gap_srcs:
        print("\n== 39 条 KB 缺口按类（当前库完全没提到该源文件）")
        for k in KINDS:
            if gaps_by_kind.get(k):
                print(f"  {k:<6}{gaps_by_kind[k]:>4}")
    if a.json:
        Path(a.json).write_text(json.dumps({
            "overall": dict(overall),
            "domains": {d: dict(c) for d, c in dom.items()},
            "difficulty": {str(d): dict(c) for d, c in diff.items()},
            "gaps_by_kind": {k: v for k, v in gaps_by_kind.items() if v},
            "gaps": gap_srcs,
            "questions": [{"id": t["id"], "domain": t["domain"], "source_kind": t["source_kind"]} for t in tagged],
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nwrote {a.json}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
